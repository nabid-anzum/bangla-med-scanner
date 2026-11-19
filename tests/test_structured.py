"""Network-free checks for deterministic PICO candidates and provenance."""
import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from banglamedscanner.structured import (
    FIELDS, MAX_WORDS, extract_candidates, validate_candidate,
    structured_analyze, audit_seed_questions, write_audit,
)

ABSTRACT = (
    'BACKGROUND: Diabetes burden remains important.\n'
    'METHODS: We randomized 120 adults with diabetes to treatment or placebo. '
    'The primary outcome was glycated hemoglobin at 12 weeks.\n'
    'RESULTS: HbA1c decreased compared with placebo (p=0.02) during the study.\n'
    'CONCLUSIONS: Researchers observed differences, but the study requires review.'
)
PMID = '12345678'
URL = f'https://pubmed.ncbi.nlm.nih.gov/{PMID}/'


def paper():
    return {'pmid': PMID, 'title_en': 'Diabetes randomized trial',
            'journal': 'Trial Journal', 'year': 2025, 'url': URL,
            'study_type': 'Randomized Controlled Trial',
            'corpus_split': 'development'}


def report():
    return {'papers': [paper()], 'topic': 'diabetes',
            'english_query': 'type 2 diabetes treatment',
            'agent_trace': [{'agent': 'retrieval', 'status': 'completed'}]}


class StructuredTests(unittest.TestCase):
    def test_fields_present(self):
        result = extract_candidates(ABSTRACT, 'Randomized Controlled Trial')
        self.assertEqual(set(result['pico']), set(FIELDS))
        self.assertEqual(result['coverage']['fields_total'], 5)

    def test_population_anchored(self):
        result = extract_candidates(ABSTRACT)
        field = result['pico']['population']
        self.assertIsNotNone(field)
        self.assertTrue(validate_candidate(field, ABSTRACT))
        self.assertEqual(field['section'], 'methods')

    def test_results_only_from_results_or_conclusions(self):
        result = extract_candidates(ABSTRACT)
        self.assertIsNotNone(result['pico']['result'])
        self.assertEqual(result['pico']['result']['section'], 'results')

    def test_no_results_in_objectives_only(self):
        abstract = 'OBJECTIVE: Investigate possible improvement after treatment.'
        result = extract_candidates(abstract)
        self.assertIsNone(result['pico']['result'])

    def test_short_excerpts_no_abstract_leak(self):
        result = extract_candidates(ABSTRACT)
        for value in result['pico'].values():
            if value:
                self.assertLessEqual(len(value['quote_en'].split()), MAX_WORDS)
                self.assertNotIn('abstract', value)

    def test_tampered_source_hash_fails(self):
        value = extract_candidates(ABSTRACT)['pico']['population'].copy()
        value['source_sentence_sha256'] = '0' * 64
        self.assertFalse(validate_candidate(value, ABSTRACT))

    def test_tampered_quote_fails(self):
        value = extract_candidates(ABSTRACT)['pico']['population'].copy()
        value['quote_en'] = 'Completely fabricated clinical conclusion'
        self.assertFalse(validate_candidate(value, ABSTRACT))

    def test_empty_does_not_invent(self):
        result = extract_candidates('There were no relevant details in the summary.')
        self.assertTrue(all(v is None for v in result['pico'].values()))
        self.assertEqual(result['coverage']['fields_with_candidate'], 0)

    def test_study_type_is_hint_not_verified(self):
        result = extract_candidates(ABSTRACT, 'Systematic Review')
        self.assertEqual(result['study_design']['publication_type_metadata'], 'Systematic Review')
        self.assertIn('not_appraised', result['study_design']['verification_status'])

    @patch('banglamedscanner.structured.read_abstracts_by_pmid')
    @patch('banglamedscanner.structured.analyze')
    def test_pipeline_never_calls_ai(self, analyze_mock, stored_mock):
        analyze_mock.return_value = report()
        stored_mock.return_value = {PMID: {'pmid': PMID, 'url': URL,
                                           'split': 'development', 'abstract': ABSTRACT}}
        result = structured_analyze('diabetes treatment', 1)
        analyze_mock.assert_called_once()
        self.assertEqual(analyze_mock.call_args.kwargs['ai_summary'], False)
        self.assertFalse(result['model_used'])
        self.assertNotIn('ai_report', result)
        self.assertEqual(result['papers'][0]['split'], 'development')

    @patch('banglamedscanner.structured.read_abstracts_by_pmid')
    @patch('banglamedscanner.structured.analyze')
    def test_heldout_rejected(self, analyze_mock, stored_mock):
        analyze_mock.return_value = report()
        stored_mock.return_value = {PMID: {'pmid': PMID, 'url': URL,
                                           'split': 'evaluation_candidate', 'abstract': ABSTRACT}}
        with self.assertRaisesRegex(ValueError, 'development'):
            structured_analyze('diabetes', 1)

    @patch('banglamedscanner.structured.read_abstracts_by_pmid')
    @patch('banglamedscanner.structured.analyze')
    def test_bad_pubmed_url_rejected(self, analyze_mock, stored_mock):
        data = report()
        data['papers'][0]['url'] = 'https://example.com/'
        analyze_mock.return_value = data
        stored_mock.return_value = {PMID: {'pmid': PMID, 'url': URL,
                                           'split': 'development', 'abstract': ABSTRACT}}
        with self.assertRaisesRegex(ValueError, 'URL'):
            structured_analyze('diabetes', 1)

    def test_bad_limit(self):
        with self.assertRaises(ValueError):
            structured_analyze('diabetes', limit=9)

    @patch('banglamedscanner.structured.structured_analyze')
    def test_private_audit_and_worksheet(self, mocked):
        mocked.return_value = {
            'topic': 'diabetes', 'paper_count': 1,
            'papers': [{'pmid': PMID, 'url': URL,
                        'structured': extract_candidates(ABSTRACT)}],
        }
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            questions = base / 'questions.csv'
            with questions.open('w', encoding='utf-8', newline='') as handle:
                writer = csv.writer(handle)
                writer.writerow(('question_id', 'topic', 'question_bn'))
                writer.writerow(('q01', 'diabetes', 'diabetes treatment'))
            content = audit_seed_questions(str(questions))
            report_path, sheet_path = write_audit(str(base / 'out'), content)
            report_text = report_path.read_text(encoding='utf-8')
            sheet_text = sheet_path.read_text(encoding='utf-8')
            self.assertNotIn(ABSTRACT, report_text + sheet_text)
            self.assertEqual(json.loads(report_text)['heldout_exposure'], 0)
            self.assertIn('reviewer_notes', sheet_text)
            self.assertNotIn('medical_claim_accuracy', report_text)

    def test_existing_directory_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                write_audit(folder, {'audit': {}, 'review_rows': []})


if __name__ == '__main__':
    unittest.main()
