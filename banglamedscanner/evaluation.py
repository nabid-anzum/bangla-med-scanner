"""Reproducible, conservative BanglaMedScanner research evaluation.

This module never calls the LLM. Snapshot audits measure *mechanical*
provenance, not scientific claim quality. Gold labels must come from humans.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import statistics
import time
from pathlib import Path
from urllib.parse import urlparse

LABEL_FIELDS = (
    'question_id', 'topic', 'question_bn', 'retrieved_pmids',
    'gold_relevant_pmids', 'evidence_support_0to2',
    'bangla_adequacy_1to5', 'safety_flag_0or1', 'reviewer_notes',
)
SEED_FIELDS = ('question_id', 'topic', 'question_bn')


class EvaluationError(ValueError):
    pass


def parse_pmids(value: str) -> list[str]:
    """Parse pipe-delimited PMIDs, rejecting malformed and duplicate identifiers."""
    if not isinstance(value, str):
        raise EvaluationError('PMID list must be text')
    if not value.strip():
        return []
    values = [part.strip() for part in value.split('|')]
    if any(not re.fullmatch(r'[0-9]{1,10}', part) for part in values):
        raise EvaluationError('PMIDs must be 1-10 decimal digits separated by |')
    if len(values) != len(set(values)):
        raise EvaluationError('Duplicate PMID in list')
    return values


def score_retrieval(predicted, gold, k=3):
    """Return metrics only for a genuinely labeled, nonempty gold set."""
    if not isinstance(k, int) or not 1 <= k <= 20:
        raise EvaluationError('k must be between 1 and 20')
    pred = list(predicted)
    reference = list(gold)
    if not reference:
        raise EvaluationError('No manually labeled relevant documents; cannot score')
    if len(pred) != len(set(pred)) or len(reference) != len(set(reference)):
        raise EvaluationError('Duplicate PMIDs in predicted or gold set')
    for pmid in pred + reference:
        if not isinstance(pmid, str) or not re.fullmatch(r'[0-9]{1,10}', pmid):
            raise EvaluationError('Invalid PMID in evaluation')
    found = [i + 1 for i, pmid in enumerate(pred[:k]) if pmid in set(reference)]
    matches = len(found)
    return {
        'precision_at_k': round(matches / k, 6),
        'recall_at_k': round(matches / len(reference), 6),
        'reciprocal_rank_at_k': round(1 / found[0], 6) if found else 0.0,
        'hit_at_k': int(bool(found)),
    }


def _open_ro(database_path: str):
    uri = Path(database_path).resolve().as_uri() + '?mode=ro'
    return sqlite3.connect(uri, uri=True)


def _pmid_sets(database_path: str):
    with _open_ro(database_path) as db:
        rows = db.execute('SELECT pmid, split FROM papers').fetchall()
    development = {str(pmid) for pmid, split in rows if split == 'development'}
    heldout = {str(pmid) for pmid, split in rows if split == 'evaluation_candidate'}
    if development & heldout:
        raise EvaluationError('Corpus split overlap found')
    if len(rows) != len(development) + len(heldout):
        raise EvaluationError('Unknown split or duplicate PMID in corpus')
    return development, heldout


def score_worksheet(csv_path: str, database_path: str, k: int = 3):
    """Assess a human-completed worksheet; blanks are never treated as negatives."""
    development, _ = _pmid_sets(database_path)
    with open(csv_path, encoding='utf-8', newline='') as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not set(LABEL_FIELDS).issubset(reader.fieldnames):
            raise EvaluationError('Worksheet is missing required columns')
        records = list(reader)
    if not records:
        raise EvaluationError('Worksheet has no questions')
    results, seen = [], set()
    for row in records:
        qid = row['question_id']
        if not qid or qid in seen:
            raise EvaluationError('Duplicate or empty question ID')
        seen.add(qid)
        ranked = parse_pmids(row['retrieved_pmids'])
        if not set(ranked).issubset(development):
            raise EvaluationError(f'{qid}: retrieved PMID outside development pool')
        manually_labeled = parse_pmids(row['gold_relevant_pmids'])
        if not manually_labeled:
            continue  # Blank gold is UNLABELED, not 0 relevant.
        if not set(manually_labeled).issubset(development):
            raise EvaluationError(f'{qid}: gold PMID outside development pool')
        results.append({'question_id': qid,
                        **score_retrieval(ranked, manually_labeled, k=k)})
    aggregated = {'status': 'not_scored_no_gold_labels' if not results else
                  'partial_or_complete_human_labeled_development_evaluation',
                  'questions_total': len(records),
                  'questions_with_manual_gold': len(results),
                  'k': k,
                  'medical_claim_accuracy': 'not_measured',
                  'bangla_translation_quality': 'not_measured',
                  'caution': 'Development-split scores are not held-out generalization results.'}
    if results:
        for field in ('precision_at_k', 'recall_at_k', 'reciprocal_rank_at_k', 'hit_at_k'):
            aggregated['macro_' + field] = round(statistics.mean(row[field] for row in results), 4)
    return aggregated


def audit_questions(seed_csv: str, database_path: str, limit: int = 3):
    """Audit live *source code* against private read-only development abstracts."""
    from .corpus import stats
    from .evidence import _verify_quote, analyze
    from .query import TOPICS

    development, heldout = _pmid_sets(database_path)
    with open(seed_csv, encoding='utf-8', newline='') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(SEED_FIELDS):
            raise EvaluationError('Seed CSV must contain question_id,topic,question_bn')
        seeds = list(reader)
    if not seeds:
        raise EvaluationError('No seed questions')
    if not 1 <= limit <= 5:
        raise EvaluationError('Invalid retrieval limit')

    audit, seen_qids = [], set()
    for row in seeds:
        qid, topic, question = (row[c].strip() for c in SEED_FIELDS)
        if not qid or qid in seen_qids or topic not in TOPICS or not question:
            raise EvaluationError('Invalid/duplicate seed question or unsupported topic')
        seen_qids.add(qid)
        started = time.perf_counter()
        result = analyze(question, limit=limit, db_path=database_path, ai_summary=False)
        duration = (time.perf_counter() - started) * 1000
        if result.get('topic') != topic:
            raise EvaluationError(f'{qid}: incorrect topic interpretation')
        if result.get('bangla_report_type') != 'deterministic_metadata_only':
            raise EvaluationError(f'{qid}: unexpected model call or report type')
        papers = result['papers']
        if len(papers) > limit:
            raise EvaluationError(f'{qid}: result exceeds limit')
        pmids = [str(p['pmid']) for p in papers]
        if len(pmids) != len(set(pmids)) or not set(pmids).issubset(development):
            raise EvaluationError(f'{qid}: duplicate PMID or held-out contamination')
        if set(pmids) & heldout:
            raise EvaluationError(f'{qid}: held-out PMID leaked')
        with _open_ro(database_path) as db:
            abstracts = {str(pmid): abstract for pmid, abstract in db.execute(
                'SELECT pmid, abstract FROM papers WHERE split=?', ('development',))}
        verified = 0
        for paper in papers:
            url = urlparse(paper['url'])
            if (url.scheme != 'https' or url.hostname != 'pubmed.ncbi.nlm.nih.gov'
                    or not url.path.rstrip('/').endswith('/' + str(paper['pmid']))):
                raise EvaluationError(f'{qid}: noncanonical PubMed URL')
            for item in paper['evidence']:
                quote = item.get('quote_en', '')
                if (item.get('pmid') != str(paper['pmid'])
                        or item.get('source_url') != paper['url']
                        or len(quote.split()) > 12
                        or not _verify_quote(quote, abstracts[str(paper['pmid'])])):
                    raise EvaluationError(f'{qid}: invalid source excerpt')
                verified += 1
        if verified != result['evidence_count']:
            raise EvaluationError(f'{qid}: evidence count mismatch')
        audit.append({'question_id': qid, 'topic': topic, 'question_bn': question,
                      'retrieved_pmids': '|'.join(pmids), 'paper_count': len(papers),
                      'verified_excerpt_count': verified,
                      'elapsed_ms': round(duration, 2)})
    snapshot = {
        'protocol': 'development_provenance_audit_v1',
        'corpus_total': len(development) + len(heldout),
        'development_articles': len(development),
        'heldout_candidate_articles': len(heldout),
        'questions': len(audit),
        'nonempty_results': sum(bool(row['paper_count']) for row in audit),
        'verified_excerpts': sum(row['verified_excerpt_count'] for row in audit),
        'heldout_exposure': 0,
        'mechanical_provenance_check': 'passed',
        'medical_accuracy': 'not_measured',
        'ai_summary_quality': 'not_measured',
        'note': 'Short excerpts and valid PMIDs do not establish clinical claim support.',
        'queries': audit,
    }
    return snapshot


def write_snapshot(output_dir: str, snapshot: dict):
    path = Path(output_dir)
    if path.exists() and not path.is_dir():
        raise EvaluationError('Output location is not a directory')
    path.mkdir(parents=True, exist_ok=True)
    snapshot_file = path / 'mechanical_audit.json'
    worksheet_file = path / 'human_annotation_worksheet.csv'
    for output in (snapshot_file, worksheet_file):
        if output.exists():
            raise EvaluationError('Refusing to overwrite prior evaluation artifacts')
    snapshot_file.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    with worksheet_file.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=LABEL_FIELDS)
        writer.writeheader()
        for item in snapshot['queries']:
            writer.writerow({
                **{key: item[key] for key in SEED_FIELDS},
                'retrieved_pmids': item['retrieved_pmids'],
                'gold_relevant_pmids': '',
                'evidence_support_0to2': '',
                'bangla_adequacy_1to5': '',
                'safety_flag_0or1': '',
                'reviewer_notes': '',
            })
    return snapshot_file, worksheet_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    audit = sub.add_parser('audit')
    audit.add_argument('--questions', required=True)
    audit.add_argument('--database', required=True)
    audit.add_argument('--output-dir', required=True)
    scoring = sub.add_parser('score')
    scoring.add_argument('--worksheet', required=True)
    scoring.add_argument('--database', required=True)
    args = parser.parse_args()
    try:
        if args.action == 'audit':
            snapshot = audit_questions(args.questions, args.database)
            outputs = write_snapshot(args.output_dir, snapshot)
            print(json.dumps({key: snapshot[key] for key in (
                'questions', 'nonempty_results', 'verified_excerpts',
                'heldout_exposure', 'mechanical_provenance_check',
                'medical_accuracy', 'ai_summary_quality')}, ensure_ascii=False))
            print('Saved private audit:', outputs[0])
            print('Saved private worksheet:', outputs[1])
        else:
            print(json.dumps(score_worksheet(args.worksheet, args.database), ensure_ascii=False))
    except (EvaluationError, OSError, sqlite3.Error) as exc:
        parser.exit(2, f'Evaluation stopped: {exc}\n')


if __name__ == '__main__':
    main()
