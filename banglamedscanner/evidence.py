"""Five-stage auditable research pipeline, with strict corpus split isolation.

Stages are specialized *software agents*; they are not five autonomous LLMs.
Model-assisted Bangla synthesis is opt-in and only runs with an explicit API key.
"""

from pathlib import Path
import re
import sqlite3

from .corpus import DEFAULT_DB
from .query import interpret
from .research import search_development
from .llm_report import LLMMissingConfiguration, generate_bangla_report, is_configured

MAX_EVIDENCE_WORDS = 12
SECTIONS = {
    'RESULT': 'results', 'RESULTS': 'results', 'FINDINGS': 'results',
    'CONCLUSION': 'conclusions', 'CONCLUSIONS': 'conclusions',
    'METHOD': 'methods', 'METHODS': 'methods',
    'OBJECTIVE': 'objectives', 'OBJECTIVES': 'objectives',
    'BACKGROUND': 'background',
}


def _clean(text):
    return ' '.join((text or '').split())


def _quoted_excerpt(text, word_limit=MAX_EVIDENCE_WORDS):
    return ' '.join(_clean(text).split()[:word_limit])


def extract_abstract_evidence(abstract, pmid, paper_url):
    """Extract short verbatim English evidence; never invent conclusions."""
    snippets = []
    for line in abstract.splitlines():
        match = re.match(r'^([A-Za-z ]{3,20}):\s*(.+)$', line.strip(), re.S)
        if not match:
            continue
        category = SECTIONS.get(match.group(1).upper().strip())
        if category not in ('methods', 'results', 'conclusions'):
            continue
        quote = _quoted_excerpt(match.group(2))
        if not quote:
            continue
        snippets.append({
            'pmid': str(pmid), 'source_url': paper_url,
            'section': category, 'quote_en': quote,
            'evidence_status': 'verbatim_excerpt_not_independently_appraised',
        })
    # Select results + conclusion first. Fallback is explicitly unclassified.
    priority = {'results': 0, 'conclusions': 1, 'methods': 2}
    snippets.sort(key=lambda s: priority[s['section']])
    if snippets:
        return snippets[:2]
    quote = _quoted_excerpt(abstract)
    return ([{
        'pmid': str(pmid), 'source_url': paper_url,
        'section': 'unstructured_abstract', 'quote_en': quote,
        'evidence_status': 'unclassified_excerpt_not_a_verified_finding',
    }] if quote else [])


def _verify_quote(quote, abstract):
    return bool(quote) and _clean(quote) in _clean(abstract)


def read_abstracts_by_pmid(pmids, db_path=DEFAULT_DB):
    """Read only development articles; evaluation candidates are inaccessible."""
    path = Path(db_path).resolve()
    uri = 'file:' + str(path) + '?mode=ro'
    with sqlite3.connect(uri, uri=True) as db:
        db.row_factory = sqlite3.Row
        records = {}
        for pmid in pmids:
            row = db.execute(
                'SELECT pmid, abstract, url, split FROM papers WHERE pmid=? AND split=?',
                (str(pmid), 'development'),
            ).fetchone()
            if row:
                records[str(pmid)] = dict(row)
        return records


def _ban_report(count, evidence_count):
    return (
        f'আপনার প্রশ্নের জন্য {count}টি গবেষণাপত্র নির্বাচন করা হয়েছে। '
        f'সেগুলো থেকে {evidence_count}টি সংক্ষিপ্ত ইংরেজি প্রমাণ-উদ্ধৃতি সংগ্রহ করা হয়েছে। '
        'প্রতিটি উদ্ধৃতির সঙ্গে মূল PubMed সূত্র দেওয়া আছে। '
        'এগুলো স্বয়ংক্রিয়ভাবে সংগৃহীত তথ্য, চিকিৎসাগতভাবে যাচাইকৃত সিদ্ধান্ত বা পরামর্শ নয়।'
    )


def analyze(question, limit=3, db_path=DEFAULT_DB, ai_summary=False):
    """Query -> retrieve -> extract -> validate -> produce Bangla metadata report.

    If ai_summary=True, an explicitly configured external model adds a Bangla
    evidence explanation marked as machine-generated, not clinically validated.
    """
    if not 1 <= int(limit) <= 5:
        raise ValueError('Limit must be 1 through 5')
    query = interpret(question)
    cards = search_development(query['topic'], query['english_search_query'], limit, db_path)
    stored = read_abstracts_by_pmid([card['pmid'] for card in cards], db_path)
    papers = []
    rejected = 0
    for card in cards:
        row = stored.get(str(card['pmid']))
        if not row:
            rejected += 1
            continue
        chunks = extract_abstract_evidence(row['abstract'], card['pmid'], card['url'])
        valid = [
            chunk for chunk in chunks
            if (chunk['pmid'] == str(row['pmid'])
                and chunk['source_url'] == row['url']
                and _verify_quote(chunk['quote_en'], row['abstract'])
                and len(chunk['quote_en'].split()) <= MAX_EVIDENCE_WORDS)
        ]
        if not valid:
            rejected += 1
            continue
        papers.append({
            'pmid': card['pmid'], 'title_en': card['title_en'],
            'year': card['year'], 'journal': card['journal'],
            'study_type': card['study_type'], 'url': card['url'],
            'doi': card['doi'], 'corpus_split': 'development',
            'evidence': valid,
        })
    count = len(papers)
    excerpts = sum(len(p['evidence']) for p in papers)
    result = {
        'question_bn': question.strip(), 'topic': query['topic'],
        'english_query': query['english_search_query'],
        'analysis_status': 'structured_extraction_not_clinically_validated',
        'papers': papers, 'paper_count': count,
        'evidence_count': excerpts,
        'rejected_papers': rejected,
        'bangla_report': _ban_report(count, excerpts),
        'bangla_report_type': 'deterministic_metadata_only',
        'llm_configured': is_configured(),
        'agent_trace': [
            {'agent': 'query_interpreter', 'status': 'completed', 'method': 'curated_lexicon_v1'},
            {'agent': 'retrieval', 'status': 'completed', 'method': 'SQLite_FTS5_BM25_development_only'},
            {'agent': 'evidence_extractor', 'status': 'completed', 'method': 'structured_abstract_section_quotes'},
            {'agent': 'citation_validator', 'status': 'completed', 'method': 'exact_excerpt_and_pmid_source_checks'},
            {'agent': 'bangla_reporter', 'status': 'completed', 'method': 'metadata_template'},
        ],
        'disclaimer_bn': ('গবেষণা বোঝার সহায়ক টুল; চিকিৎসা পরামর্শ নয়। '
                          'গবেষণার মান, পক্ষপাত ও পূর্ণ পাঠ এখনো আলাদাভাবে যাচাই করা হয়নি।'),
    }
    if ai_summary:
        if not count:
            raise ValueError('No source evidence is available for Bangla synthesis')
        result['ai_report'] = generate_bangla_report(question, papers)
        result['bangla_report_type'] = 'llm_generated_not_independently_verified'
        result['agent_trace'][-1]['method'] = 'configured_external_llm'
    return result
