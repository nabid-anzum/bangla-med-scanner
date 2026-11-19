
"""A real, bounded *software-agent* orchestrator for sourced research evidence.

Six explicit roles communicate through a request-local context. They are
not autonomous LLMs. DeepSeek synthesis remains in the separate authenticated
/api/ai/jobs flow; this public endpoint never starts a model job.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter
from threading import BoundedSemaphore
from urllib.parse import urlparse
import re
import secrets

from .corpus import DEFAULT_DB
from .query import interpret
from .research import search_development
from .evidence import (
    read_abstracts_by_pmid, extract_abstract_evidence, _verify_quote,
    MAX_EVIDENCE_WORDS,
)
from .structured import extract_candidates, validate_candidate, _sections

# This limit is process-local (the dedicated BMS Uvicorn uses one worker).
# It is intentionally lower than the overall host capacity to protect ERP.
MAX_CONCURRENT = 3
_SLOTS = BoundedSemaphore(MAX_CONCURRENT)
PICO_FIELDS = ('population', 'intervention', 'comparator', 'outcome', 'result')
ALLOWED_SECTIONS = {
    'population': {'methods', 'results'},
    'intervention': {'methods', 'results'},
    'comparator': {'methods', 'results'},
    'outcome': {'methods', 'results'},
    'result': {'results', 'conclusions'},
}


class OrchestrationBusy(RuntimeError):
    pass


class ProvenanceError(RuntimeError):
    pass


@dataclass
class Context:
    question: str
    limit: int
    db_path: Path | str
    interpretation: dict = field(default_factory=dict)
    cards: list = field(default_factory=list)
    records: dict = field(default_factory=dict)
    papers: list = field(default_factory=list)
    trace: list = field(default_factory=list)
    report_bn: str = ''


def pubmed_url(pmid, url):
    pmid = str(pmid)
    if re.fullmatch(r'[0-9]{1,10}', pmid) is None:
        return False
    if not isinstance(url, str):
        return False
    parsed = urlparse(url)
    return (
        parsed.scheme == 'https'
        and parsed.netloc == 'pubmed.ncbi.nlm.nih.gov'
        and parsed.path == f'/{pmid}/'
        and not parsed.params and not parsed.query and not parsed.fragment
    )


class QueryAgent:
    name = 'Query Agent'
    method = 'Bangla medical lexicon and intent mapping'

    def run(self, ctx):
        ctx.interpretation = interpret(ctx.question)
        return {'topic': ctx.interpretation['topic']}


class RetrievalAgent:
    name = 'Retrieval Agent'
    method = 'SQLite FTS5/BM25; development split only'

    def run(self, ctx):
        i = ctx.interpretation
        ctx.cards = search_development(
            i['topic'], i['english_search_query'], ctx.limit, ctx.db_path
        )
        if len(ctx.cards) > ctx.limit:
            raise ProvenanceError('Retrieval returned too many papers')
        for card in ctx.cards:
            if card.get('corpus_split') != 'development':
                raise ProvenanceError('Evaluation paper reached retrieval')
        return {'retrieved': len(ctx.cards)}


class EvidenceAgent:
    name = 'Evidence Agent'
    method = 'Verbatim abstract passage selection'

    def run(self, ctx):
        ctx.records = read_abstracts_by_pmid(
            [x['pmid'] for x in ctx.cards], db_path=ctx.db_path
        )
        papers = []
        for card in ctx.cards:
            pmid = str(card['pmid'])
            row = ctx.records.get(pmid)
            if row is None or row.get('split') != 'development':
                raise ProvenanceError('Research source not in development corpus')
            if str(row.get('pmid')) != pmid:
                raise ProvenanceError('Mismatched source identifier')
            if not (pubmed_url(pmid, card.get('url'))
                    and pubmed_url(pmid, row.get('url'))):
                raise ProvenanceError('Noncanonical PubMed source')
            quote_blocks = extract_abstract_evidence(
                row['abstract'], pmid, row['url']
            )
            if not quote_blocks:
                raise ProvenanceError('Empty source excerpts')
            papers.append({
                'pmid': pmid,
                'url': row['url'],
                'title_en': card['title_en'],
                'journal': card.get('journal', ''),
                'year': card.get('year', ''),
                'study_type': card.get('study_type') or '',
                'split': 'development',
                'evidence': quote_blocks,
            })
        ctx.papers = papers
        return {'papers_with_evidence': len(papers)}


class PICOAgent:
    name = 'PICO Agent'
    method = 'Conservative source-anchored section screening'

    def run(self, ctx):
        candidate_count = 0
        for paper in ctx.papers:
            abstract = ctx.records[paper['pmid']]['abstract']
            # AIMS/objective sentences caused false PICO candidates earlier.
            # Screen only methods/results/conclusions to favour precision.
            sections = [(section, content) for section, content in _sections(abstract)
                        if section in ('methods', 'results', 'conclusions')]
            filtered = '\n'.join(
                f'{section.upper()}: {content.strip()}'
                for section, content in sections
            )
            candidates = extract_candidates(filtered, paper['study_type'])
            for key in PICO_FIELDS:
                value = candidates['pico'][key]
                if value is None:
                    continue
                if (value['section'] not in ALLOWED_SECTIONS[key]
                        or not validate_candidate(value, abstract)):
                    candidates['pico'][key] = None
                else:
                    candidate_count += 1
            paper['pico'] = candidates['pico']
            paper['pico_method'] = 'conservative_lexical_candidates_v2'
        return {'source_anchored_candidates': candidate_count}


class VerificationAgent:
    name = 'Verification Agent'
    method = 'Exact excerpt, PMID, section, and held-out checks'

    def run(self, ctx):
        verified = 0
        for paper in ctx.papers:
            pmid = paper['pmid']
            record = ctx.records[pmid]
            abstract = record['abstract']
            if paper['split'] != 'development' or record['split'] != 'development':
                raise ProvenanceError('Evaluation split exposure refused')
            if not pubmed_url(pmid, paper['url']):
                raise ProvenanceError('Unsafe reference')
            for e in paper['evidence']:
                if (str(e['pmid']) != pmid or e['source_url'] != paper['url']
                        or not _verify_quote(e['quote_en'], abstract)
                        or len(e['quote_en'].split()) > MAX_EVIDENCE_WORDS):
                    raise ProvenanceError('Unverified evidence excerpt')
                verified += 1
            for key in PICO_FIELDS:
                if not validate_candidate(paper['pico'][key], abstract):
                    raise ProvenanceError('Unverified PICO candidate')
        return {'verified_excerpts': verified, 'heldout_exposure': 0}


class ReportAgent:
    name = 'Report Agent'
    method = 'Conservative Bangla metadata template; NO LLM call'

    def run(self, ctx):
        count = len(ctx.papers)
        verified = sum(len(p['evidence']) for p in ctx.papers)
        ctx.report_bn = (
            f'এই প্রশ্নের জন্য {count}টি ইংরেজি গবেষণাপত্র পাওয়া গেছে। '
            f'{verified}টি সংক্ষিপ্ত উৎস-যাচাইকৃত উদ্ধৃতি নির্বাচন করা হয়েছে। '
            'PICO ক্ষেত্রগুলো সম্ভাব্য তথ্য, চিকিৎসাগতভাবে যাচাইকৃত সিদ্ধান্ত নয়। '
            'এটি চিকিৎসা পরামর্শ নয়।'
        )
        return {'report_type': 'deterministic_metadata_only'}


AGENTS = (
    QueryAgent(), RetrievalAgent(), EvidenceAgent(),
    PICOAgent(), VerificationAgent(), ReportAgent(),
)


def orchestrate(question: str, limit: int = 3, db_path=DEFAULT_DB):
    """Bounded, request-isolated and auditable, not an autonomous LLM chain."""
    if not isinstance(question, str) or not 2 <= len(question.strip()) <= 500:
        raise ValueError('Question length must be 2 to 500 characters')
    if type(limit) is not int or not 1 <= limit <= 3:
        raise ValueError('Limit must be 1, 2, or 3')
    if not _SLOTS.acquire(blocking=False):
        raise OrchestrationBusy('Research concurrency limit reached; retry shortly')
    try:
        ctx = Context(question.strip(), limit, db_path)
        request_id = secrets.token_hex(8)
        for agent in AGENTS:
            started = perf_counter()
            metrics = agent.run(ctx)
            ctx.trace.append({
                'agent': agent.name,
                'status': 'completed',
                'method': agent.method,
                'elapsed_ms': round((perf_counter() - started) * 1000, 1),
                'output': metrics,
            })
        return {
            'request_id': request_id,
            'question_bn': ctx.question,
            'topic': ctx.interpretation['topic'],
            'english_search_query': ctx.interpretation['english_search_query'],
            'orchestration': 'six_specialized_deterministic_software_agents',
            'max_concurrent_requests_per_worker': MAX_CONCURRENT,
            'paper_count': len(ctx.papers),
            'papers': ctx.papers,
            'bangla_report': ctx.report_bn,
            'report_type': 'deterministic_metadata_only',
            'ai_status': 'self_hosted_DeepSeek_separate_admin_only_not_called',
            'model_used': False,
            'clinically_validated': False,
            'heldout_exposure': 0,
            'agent_trace': ctx.trace,
            'disclaimer': 'Research prototype; evidence candidates require human review.',
        }
    finally:
        _SLOTS.release()
