"""Bangla query -> auditable retrieval; not an LLM or validated medical summary."""
import re
import sqlite3
from pathlib import Path
from .query import interpret
from .corpus import DEFAULT_DB
from .pubmed import search_pubmed


def excerpt(text, max_words=22):
    """Short excerpt from source abstract, not a generated claim."""
    candidates = re.findall(r'(?im)^(?:RESULTS?|CONCLUSIONS?|FINDINGS):\s*(.+)', text)
    source = candidates[0] if candidates else text.replace('\n', ' ')
    words = source.split()
    return ' '.join(words[:max_words]) + (' ...' if len(words) > max_words else '')


def search_development(topic, english_query, limit=5, db_path=DEFAULT_DB):
    """Search development split only; never leak evaluation candidates."""
    terms = re.findall(r'[A-Za-z][A-Za-z0-9]{1,}', english_query)[:12]
    if not terms:
        return []
    match = ' OR '.join('"' + term + '"' for term in terms)
    uri = Path(db_path).resolve().as_uri().replace('file://', 'file:') + '?mode=ro'
    with sqlite3.connect(uri, uri=True) as db:
        db.row_factory = sqlite3.Row
        rows = db.execute('''
            SELECT p.pmid, p.topic, p.title, p.journal, p.year, p.doi,
                   p.pmcid, p.study_type, p.url, p.abstract, p.split
            FROM papers_fts JOIN papers p ON p.rowid = papers_fts.rowid
            WHERE papers_fts MATCH ? AND p.topic = ? AND p.split = 'development'
            ORDER BY bm25(papers_fts) LIMIT ?
        ''', (match, topic, min(max(int(limit),1),10))).fetchall()
    return [{
        'pmid': r['pmid'], 'title_en': r['title'], 'journal': r['journal'],
        'year': r['year'], 'doi': r['doi'], 'pmcid': r['pmcid'],
        'study_type': r['study_type'], 'url': r['url'], 'topic': r['topic'],
        'abstract_excerpt_en': excerpt(r['abstract']),
        'excerpt_type': 'verbatim_abstract_excerpt_not_verified_conclusion',
        'corpus_split': r['split'],
    } for r in rows]


def research(question, source='corpus', limit=5, db_path=DEFAULT_DB):
    parsed = interpret(question)
    if source not in ('corpus', 'live'):
        raise ValueError('Source must be corpus or live')
    if not 1 <= int(limit) <= 10:
        raise ValueError('Limit must be between 1 and 10')
    if source == 'corpus':
        papers = search_development(parsed['topic'], parsed['english_search_query'], limit, db_path)
        method = 'Local SQLite FTS5 (80 development abstracts; 20 evaluation candidates withheld)'
    else:
        results = search_pubmed(parsed['english_search_query'], limit=min(int(limit),5))
        papers = [{
            'pmid': p['pmid'], 'title_en': p['title'], 'journal': p['journal'],
            'year': p.get('date',''), 'doi': p.get('doi',''),
            'url': p['url'], 'abstract_excerpt_en': None,
            'excerpt_type': None, 'corpus_split': None,
            'study_type': None, 'pmcid': None, 'topic': parsed['topic'],
        } for p in results]
        method = 'Live NCBI PubMed ESearch + ESummary; metadata only'
    return {
        'question_bn': question.strip(),
        'interpretation': parsed,
        'source': source, 'method': method,
        'count': len(papers), 'papers': papers,
        'heading_bn': f'আপনার প্রশ্নের জন্য {len(papers)}টি ইংরেজি গবেষণাপত্র পাওয়া গেছে।',
        'limitations_bn': (
            'এটি অনুসন্ধান ও তথ্য প্রদর্শনের প্রাথমিক সংস্করণ। '
            'ইংরেজি উদ্ধৃতিগুলো গবেষণাপত্রের সারাংশ থেকে নেওয়া, যাচাইকৃত চিকিৎসা উপসংহার নয়। '
            'AI-ভিত্তিক প্রমাণ মূল্যায়ন এবং নির্ভরযোগ্য বাংলা সারাংশ এখনো যুক্ত করা হয়নি। '
            'এটি চিকিৎসা পরামর্শ নয়।'
        ),
    }
