"""Source-anchored PICO candidate extraction for BanglaMedScanner.

This deterministic component is deliberately NOT a clinically validated
information extractor. Every field points to a short verbatim excerpt and
retains a cryptographic hash for its originating sentence.

Never load evaluation_candidate papers in this module.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from .corpus import DEFAULT_DB
from .evidence import analyze, read_abstracts_by_pmid

MAX_WORDS = 12
FIELDS = ('population', 'intervention', 'comparator', 'outcome', 'result')
SECTIONS = {'OBJECTIVE': 'objective', 'OBJECTIVES': 'objective',
            'BACKGROUND': 'background', 'METHOD': 'methods',
            'METHODS': 'methods', 'DESIGN': 'methods',
            'RESULT': 'results', 'RESULTS': 'results',
            'FINDING': 'results', 'FINDINGS': 'results',
            'CONCLUSION': 'conclusions', 'CONCLUSIONS': 'conclusions'}
PATTERNS = {
    'population': re.compile(
        r'\b(?:patients?|participants?|adults?|children|adolescents?|subjects?|'
        r'individuals|women|men|pregnant|older adults?|people with|'
        r'persons with|n\s*=\s*\d+)\b', re.I),
    'intervention': re.compile(
        r'\b(?:intervention|treated|treatment|therapy|therapies|'
        r'random(?:ly|ized|ised)|received|administered|medication|'
        r'pharmacotherapy|drug|exercise|training|counseling|counselling)\b', re.I),
    'comparator': re.compile(
        r'\b(?:placebo|control group|controls|comparator|usual care|'
        r'standard care|versus|compared with|compared to|vs\.?|'
        r'no treatment)\b', re.I),
    'outcome': re.compile(
        r'\b(?:outcomes?|endpoints?|efficacy|mortality|remission|'
        r'hospitali[sz]ation|hba1c|glycated hemoglobin|blood pressure|'
        r'lung function|fev1|symptoms?|exacerbations?)\b', re.I),
}
NUMBER_MENTION = re.compile(
    r'\b(?:\d+(?:\.\d+)?\s*%|(?:p\s*[<=>]\s*\d+(?:\.\d+)?)|'
    r'(?:OR|HR|RR)\s*[=:]?\s*\d+(?:\.\d+)?|95\s*%\s*CI)\b', re.I)
STUDY_HINT = re.compile(
    r'\b(randomi[sz]ed(?: controlled)? trial|cohort study|case.control|'
    r'cross.sectional|systematic review|meta.analysis|observational study)\b', re.I)
SECT_RE = re.compile(
    r'(?im)^\s*(BACKGROUND|OBJECTIVES?|METHODS?|DESIGN|RESULTS?|'
    r'FINDINGS?|CONCLUSIONS?)\s*:\s*')
SENTENCE_BREAK = re.compile(r'(?<=[.!?])\s+(?=[A-Z(\[0-9])')


def _clean(value: str) -> str:
    return ' '.join((value or '').split())


def _short_quote(sentence: str) -> str:
    return ' '.join(_clean(sentence).split()[:MAX_WORDS])


def _sections(abstract: str):
    """Yield section-labeled text; source remains unmodified for verification."""
    markers = list(SECT_RE.finditer(abstract))
    if not markers:
        yield 'unstructured', abstract
        return
    if abstract[:markers[0].start()].strip():
        yield 'unstructured', abstract[:markers[0].start()]
    for i, marker in enumerate(markers):
        end = markers[i + 1].start() if i + 1 < len(markers) else len(abstract)
        content = abstract[marker.end():end]
        if content.strip():
            yield SECTIONS[marker.group(1).upper()], content


def _sentences(abstract: str):
    for section, content in _sections(abstract):
        # Only make candidate fragments shorter than a full paragraph.
        for piece in SENTENCE_BREAK.split(_clean(content)):
            sentence = piece.strip()
            if sentence and len(sentence.split()) >= 4:
                yield section, sentence


def _candidate(section: str, sentence: str, abstract: str):
    quote = _short_quote(sentence)
    if not quote or quote not in _clean(abstract):
        raise ValueError('Candidate quotation does not appear in source abstract')
    return {
        'section': section,
        'quote_en': quote,
        'source_sentence_sha256': hashlib.sha256(
            sentence.encode('utf-8')).hexdigest(),
        'status': 'lexical_candidate_needs_human_review',
    }


def extract_candidates(abstract: str, study_type: str = '') -> dict:
    """Surface possible PICO evidence without classifying medical truth."""
    if not isinstance(abstract, str):
        raise ValueError('Abstract must be text')
    candidates = {field: None for field in FIELDS}
    result_section_only = ('results', 'conclusions')
    result_keywords = re.compile(
        r'\b(?:increased|decreased|improved|reduced|higher|lower|'
        r'associated|significant|difference|observed|found|effect)\b', re.I)
    design = None
    for section, sentence in _sentences(abstract):
        for field in FIELDS:
            if candidates[field] is not None:
                continue
            if field == 'result':
                # Never infer a finding from background, objectives, or methods.
                if section not in result_section_only:
                    continue
                if not result_keywords.search(sentence) and not NUMBER_MENTION.search(sentence):
                    continue
            elif not PATTERNS[field].search(sentence):
                continue
            candidates[field] = _candidate(section, sentence, abstract)
        if design is None and STUDY_HINT.search(sentence):
            design = _candidate(section, sentence, abstract)

    return {
        'pico': candidates,
        'study_design': {
            'publication_type_metadata': str(study_type or ''),
            'abstract_design_candidate': design,
            'verification_status': 'metadata_or_keyword_hint_not_appraised',
        },
        'coverage': {
            'fields_with_candidate': sum(v is not None for v in candidates.values()),
            'fields_total': len(FIELDS),
        },
        'extraction_method': 'source_anchored_lexical_candidates_v1',
        'warning': ('PICO fields are possible mentions, not confirmed clinical '
                    'entities, comparative effects, or conclusions.'),
    }


def validate_candidate(candidate, abstract):
    if candidate is None:
        return True
    if not isinstance(candidate, dict):
        return False
    quote = candidate.get('quote_en')
    if (not isinstance(quote, str) or not 0 < len(quote.split()) <= MAX_WORDS
            or candidate.get('status') != 'lexical_candidate_needs_human_review'):
        return False
    return any(
        section == candidate.get('section')
        and _short_quote(sentence) == quote
        and hashlib.sha256(sentence.encode('utf-8')).hexdigest()
            == candidate.get('source_sentence_sha256')
        for section, sentence in _sentences(abstract)
    )


def _is_pubmed_url(url: str, pmid: str) -> bool:
    parsed = urlparse(url)
    return (parsed.scheme == 'https'
            and parsed.hostname == 'pubmed.ncbi.nlm.nih.gov'
            and parsed.port is None and parsed.username is None
            and parsed.path.rstrip('/') == '/' + pmid
            and not parsed.query and not parsed.fragment)


def structured_analyze(question: str, limit: int = 3,
                       db_path=DEFAULT_DB) -> dict:
    """Query -> retrieve -> source-proven PICO candidates; no model calls."""
    if not isinstance(limit, int) or not 1 <= limit <= 3:
        raise ValueError('limit must be an integer from 1 to 3')
    foundation = analyze(question, limit=limit, db_path=db_path, ai_summary=False)
    papers = foundation['papers']
    source = read_abstracts_by_pmid([p['pmid'] for p in papers], db_path=db_path)
    output = []
    for item in papers:
        pmid = str(item['pmid'])
        stored = source.get(pmid)
        if not stored or stored['split'] != 'development':
            raise ValueError('Source paper not in development split')
        canonical = f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/'
        if not _is_pubmed_url(item['url'], pmid) or not _is_pubmed_url(stored['url'], pmid):
            raise ValueError('Untrusted source URL; refusing candidate extraction')
        result = extract_candidates(stored['abstract'], item.get('study_type') or '')
        if not all(validate_candidate(v, stored['abstract'])
                   for v in result['pico'].values()):
            raise ValueError('Invalid excerpt or source association')
        if not validate_candidate(
                result['study_design']['abstract_design_candidate'], stored['abstract']):
            raise ValueError('Invalid study-design excerpt')
        output.append({
            'pmid': pmid,
            'title_en': item['title_en'],
            'year': item['year'],
            'journal': item['journal'],
            'url': canonical,
            'split': 'development',
            'structured': result,
        })
    return {
        'question': question.strip(),
        'topic': foundation['topic'],
        'english_search_query': foundation['english_query'],
        'paper_count': len(output),
        'papers': output,
        'model_used': False,
        'clinical_accuracy': 'not_measured',
        'method': 'deterministic_candidate_extraction_from_development_abstracts',
        'disclaimer': ('Research-only prototype: keyword candidates are not '
                       'verified outcomes or medical recommendations.'),
        'agent_trace': foundation['agent_trace'] + [
            {'agent': 'pico_candidate_extractor',
             'status': 'completed', 'method': 'source_anchored_lexical_v1'},
            {'agent': 'pico_provenance_validator',
             'status': 'completed', 'method': 'excerpt_and_pmid_checks'},
        ],
    }


def audit_seed_questions(questions_csv: str, db_path=DEFAULT_DB):
    """No AI calls; create reviewer-ready rows and honest coverage counts."""
    from .query import TOPICS
    reports = []
    review_rows = []
    with Path(questions_csv).open(newline='', encoding='utf-8') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ['question_id', 'topic', 'question_bn']:
            raise ValueError('Unexpected question seed schema')
        seeds = list(reader)
    if not seeds:
        raise ValueError('No evaluation seed questions')
    ids = set()
    for row in seeds:
        qid = row['question_id']
        if not qid or qid in ids or row['topic'] not in TOPICS:
            raise ValueError('Invalid question id or topic')
        ids.add(qid)
        answer = structured_analyze(row['question_bn'], limit=3, db_path=db_path)
        if answer['topic'] != row['topic']:
            raise ValueError('Topic mismatch in evaluation seed')
        per_field = {key: 0 for key in FIELDS}
        for paper in answer['papers']:
            pico = paper['structured']['pico']
            for key in FIELDS:
                per_field[key] += int(pico[key] is not None)
            review_rows.append({
                'question_id': qid,
                'pmid': paper['pmid'],
                'pubmed_url': paper['url'],
                **{f'{key}_candidate_excerpt': (
                    pico[key]['quote_en'] if pico[key] else '')
                   for key in FIELDS},
                'population_correct_0or1': '',
                'intervention_correct_0or1': '',
                'comparator_correct_0or1': '',
                'outcome_correct_0or1': '',
                'result_correct_0or1': '',
                'reviewer_notes': '',
            })
        reports.append({
            'question_id': qid,
            'topic': answer['topic'],
            'retrieved_papers': answer['paper_count'],
            'candidate_counts': per_field,
        })
    return {
        'audit': {
            'status': 'candidate_coverage_only_not_accuracy',
            'questions': len(reports),
            'review_rows': len(review_rows),
            'heldout_exposure': 0,
            'medical_accuracy': 'not_measured',
            'model_quality': 'not_measured',
            'field_candidate_totals': {
                key: sum(r['candidate_counts'][key] for r in reports)
                for key in FIELDS},
            'questions_summary': reports,
        },
        'review_rows': review_rows,
    }


def write_audit(output_dir: str, result: dict):
    out = Path(output_dir)
    if out.exists():
        raise ValueError('Output directory already exists')
    out.mkdir(mode=0o700, parents=False)
    report = out / 'pico_candidate_audit.json'
    sheet = out / 'pico_human_review.csv'
    report.write_text(json.dumps(result['audit'], ensure_ascii=False, indent=2)
                      + '\n', encoding='utf-8')
    rows = result['review_rows']
    fields = ['question_id', 'pmid', 'pubmed_url',
              *(f'{field}_candidate_excerpt' for field in FIELDS),
              'population_correct_0or1', 'intervention_correct_0or1',
              'comparator_correct_0or1', 'outcome_correct_0or1',
              'result_correct_0or1', 'reviewer_notes']
    with sheet.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return report, sheet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['audit'])
    parser.add_argument('--questions', required=True)
    parser.add_argument('--database', required=True)
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args()
    result = audit_seed_questions(args.questions, args.database)
    paths = write_audit(args.output_dir, result)
    print(json.dumps({k:v for k,v in result['audit'].items()
                      if k != 'questions_summary'}, ensure_ascii=False))
    print('Private source audit:', paths[0])
    print('Private reviewer worksheet:', paths[1])


if __name__ == '__main__':
    main()
