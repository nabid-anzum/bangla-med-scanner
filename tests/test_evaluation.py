import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path

from banglamedscanner.evaluation import (
    EvaluationError, parse_pmids, score_retrieval, score_worksheet, write_snapshot,
    LABEL_FIELDS,
)


class EvaluationTests(unittest.TestCase):
    def test_retrieval_metrics(self):
        scores = score_retrieval(['11', '12', '13'], ['12', '99'], 3)
        self.assertAlmostEqual(scores['precision_at_k'], 1 / 3, places=5)
        self.assertEqual(scores['recall_at_k'], 0.5)
        self.assertEqual(scores['reciprocal_rank_at_k'], 0.5)
        self.assertEqual(scores['hit_at_k'], 1)

    def test_no_gold_cannot_be_scored(self):
        with self.assertRaises(EvaluationError):
            score_retrieval(['11'], [], 3)

    def test_invalid_and_duplicate_pmids_are_rejected(self):
        for invalid in ['11|11', '11|oops', '11|', '12345678901']:
            with self.subTest(value=invalid), self.assertRaises(EvaluationError):
                parse_pmids(invalid)

    def test_unlabeled_worksheet_has_no_fake_accuracy(self):
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / 'corpus.sqlite3'
            with sqlite3.connect(database) as db:
                db.execute('CREATE TABLE papers (pmid TEXT, split TEXT)')
                db.executemany('INSERT INTO papers VALUES (?,?)',
                               [('11', 'development'), ('12', 'development'),
                                ('13', 'evaluation_candidate')])
            worksheet = Path(folder) / 'labels.csv'
            with worksheet.open('w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=LABEL_FIELDS)
                writer.writeheader()
                writer.writerow({'question_id': 'Q1', 'topic': 'diabetes',
                                 'question_bn': 'ডায়াবেটিস',
                                 'retrieved_pmids': '11|12',
                                 'gold_relevant_pmids': ''})
            scores = score_worksheet(str(worksheet), str(database))
            self.assertEqual(scores['questions_with_manual_gold'], 0)
            self.assertEqual(scores['status'], 'not_scored_no_gold_labels')
            self.assertNotIn('macro_precision_at_k', scores)

    def test_heldout_gold_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / 'corpus.sqlite3'
            with sqlite3.connect(database) as db:
                db.execute('CREATE TABLE papers (pmid TEXT, split TEXT)')
                db.executemany('INSERT INTO papers VALUES (?,?)',
                               [('11', 'development'), ('13', 'evaluation_candidate')])
            worksheet = Path(folder) / 'labels.csv'
            with worksheet.open('w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=LABEL_FIELDS)
                writer.writeheader()
                writer.writerow({'question_id': 'Q1', 'topic': 'diabetes',
                                 'question_bn': 'ডায়াবেটিস',
                                 'retrieved_pmids': '11',
                                 'gold_relevant_pmids': '13'})
            with self.assertRaises(EvaluationError):
                score_worksheet(str(worksheet), str(database))

    def test_private_audit_export_does_not_contain_abstracts(self):
        with tempfile.TemporaryDirectory() as folder:
            snapshot = {'queries': [{'question_id': 'Q01', 'topic': 'diabetes',
                                     'question_bn': 'ডায়াবেটিস',
                                     'retrieved_pmids': '11',
                                     'paper_count': 1,
                                     'verified_excerpt_count': 1,
                                     'elapsed_ms': 2}]}
            outputs = write_snapshot(str(Path(folder) / 'results'), snapshot)
            self.assertEqual(len(outputs), 2)
            raw = outputs[0].read_text(encoding='utf-8')
            self.assertNotIn('quote_en', raw)
            with self.assertRaises(EvaluationError):
                write_snapshot(str(Path(folder) / 'results'), snapshot)


if __name__ == '__main__':
    unittest.main()
