"""One source-linked public research report for local and live PubMed searches.

The public endpoint never calls a language model. All abstract quotations and
PICO candidates are source-derived and explicitly *not* clinically validated.
"""
from __future__ import annotations

import re
import time
from .open_topics import plan_public, public_live_search
from .orchestrator import orchestrate
from .ai_orchestration import _fetch_abstracts, _heldout
from .structured import extract_candidates, validate_candidate
from .evidence import extract_abstract_evidence, _verify_quote

PICO_FIELDS = ('population', 'intervention', 'comparator', 'outcome', 'result')


def run_public_report(question: str, limit: int = 5, source: str = 'auto',
                      *, live_search=None, abstract_fetch=None, heldout=None):
    if not isinstance(question, str) or not 2 <= len(question.strip()) <= 500:
        raise ValueError('Question must contain 2 to 500 characters')
    if type(limit) is not int or not 1 <= limit <= 5:
        raise ValueError('Limit must be 1 to 5')
    if source not in ('auto', 'live', 'corpus'):
        raise ValueError('Unknown research source')
    question = question.strip()
    parsed = plan_public(question)
    if source == 'corpus' and not parsed['local_corpus_supported']:
        raise ValueError('This topic is not in the five-topic development corpus; choose Automatic')
    if source != 'live' and parsed['local_corpus_supported']:
        found = orchestrate(question, limit=min(limit, 3))
        found['source'] = 'corpus'
        found['model_used'] = False
        found['report_mode'] = 'research'
        return found

    start = time.monotonic()
    found = public_live_search(question, limit=limit, pubmed_search=live_search)
    papers = [dict(p) for p in found['papers']]
    blocked = _heldout() if heldout is None else set(heldout)
    papers = [p for p in papers if p['pmid'] not in blocked]
    fetch = abstract_fetch or _fetch_abstracts
    abstracts = {}
    if papers:
        try:
            abstracts = fetch([p['pmid'] for p in papers])
        except Exception:
            # Metadata-only results remain accessible if EFetch is temporarily down.
            abstracts = {}
    source_count = 0
    candidate_count = 0
    for paper in papers:
        pmid = paper['pmid']
        paper['evidence'] = []
        paper['pico'] = {key: None for key in PICO_FIELDS}
        paper['evidence_scope'] = 'metadata_only'
        abstract = abstracts.get(pmid, '')
        if not isinstance(abstract, str) or len(abstract.split()) < 25:
            continue
        paper['evidence_scope'] = 'abstract'
        source_count += 1
        snippets = extract_abstract_evidence(abstract, pmid, paper['url'])
        paper['evidence'] = [s for s in snippets[:3] if
                             s.get('pmid') == pmid and s.get('source_url') == paper['url']
                             and _verify_quote(s.get('quote_en', ''), abstract)]
        try:
            pico = extract_candidates(abstract)['pico']
        except ValueError:
            # External abstracts may have unexpected section formats.
            pico = {}
        for key in PICO_FIELDS:
            item = pico.get(key)
            if item and validate_candidate(item, abstract):
                paper['pico'][key] = item
                candidate_count += 1
    elapsed = round((time.monotonic()-start)*1000, 1)
    # These are SOFTWARE steps, not autonomous or DeepSeek agents.
    trace = [
        {'agent':'Query Interpretation', 'method':parsed['translation_method'], 'status':'completed', 'model_invoked':False, 'elapsed_ms':0},
        {'agent':'PubMed Discovery', 'method':'ESearch/ESummary bibliographic retrieval', 'status':'completed', 'model_invoked':False, 'elapsed_ms':elapsed},
        {'agent':'Abstract Retrieval', 'method':'PubMed EFetch XML; accessible abstracts only', 'status':'completed', 'model_invoked':False, 'elapsed_ms':0},
        {'agent':'PICO Candidate Screening', 'method':'Source-anchored lexical screening; not medical appraisal', 'status':'completed', 'model_invoked':False, 'elapsed_ms':0},
        {'agent':'Source Verification', 'method':'PMID and literal abstract-quote checks', 'status':'completed', 'model_invoked':False, 'elapsed_ms':0},
        {'agent':'Report Assembly', 'method':'Deterministic source-linked report; no LLM', 'status':'completed', 'model_invoked':False, 'elapsed_ms':0},
    ]
    return {
        'question_bn':question, 'source':'live', 'report_mode':'research',
        'topic':parsed['topic'], 'english_search_query':parsed['english_search_query'],
        'paper_count':len(papers), 'papers':papers,
        'abstracts_retrieved':source_count, 'pico_candidate_count':candidate_count,
        'bangla_report':(
            f'PubMed-এ {len(papers)}টি গবেষণাপত্র পাওয়া গেছে। '
            f'{source_count}টির সারাংশ থেকে উৎস-যাচাইকৃত উদ্ধৃতি এবং '
            f'{candidate_count}টি সম্ভাব্য PICO তথ্য পাওয়া গেছে। '
            'এগুলো চিকিৎসাগতভাবে যাচাইকৃত সিদ্ধান্ত নয়।'
            if not found.get('needs_ai_translation') else
            'এই বাংলা পরিভাষাটির জন্য স্বয়ংক্রিয় অনুবাদ পাওয়া যায়নি। '
            'DeepSeek মোড ব্যবহার করুন অথবা ইংরেজিতে অনুসন্ধান করুন।'),
        'needs_ai_translation':found.get('needs_ai_translation',False),
        'model_used':False, 'model_invocations':0,
        'agent_trace':trace, 'heldout_exposure':0,
        'clinical_accuracy':'not_measured',
        'disclaimer':'Public results are retrieved papers and unreviewed PICO candidates. No DeepSeek model invoked.',
    }
