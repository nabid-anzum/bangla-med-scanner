
"""Tests for request isolation, provenance, concurrency and six-stage execution."""
import unittest
from unittest.mock import patch

from banglamedscanner.orchestrator import (
    AGENTS, MAX_CONCURRENT, OrchestrationBusy, ProvenanceError,
    orchestrate, pubmed_url,
)

PMID = '12345678'
URL = 'https://pubmed.ncbi.nlm.nih.gov/12345678/'
ABSTRACT = (
    'OBJECTIVE: We aimed to investigate patients with diabetes and treatment outcomes.\n'
    'METHODS: We randomized 120 adults with diabetes to a supervised intervention or placebo. '
    'The primary outcome was glycated hemoglobin at 12 weeks.\n'
    'RESULTS: HbA1c decreased compared with placebo (p=0.02) during the study.\n'
    'CONCLUSIONS: Researchers observed a difference, but external review is needed.'
)
CARD = {
    'pmid': PMID, 'title_en': 'Trial in diabetes', 'url': URL,
    'journal': 'Medical Journal', 'year': 2025,
    'study_type': 'Randomized Controlled Trial',
    'corpus_split': 'development',
}
ROW = {'pmid': PMID, 'url': URL, 'abstract': ABSTRACT,
       'split': 'development'}


class AgentFlowTests(unittest.TestCase):
    def execute(self, card=None, row=None):
        with patch('banglamedscanner.orchestrator.search_development',
                   return_value=[card if card is not None else CARD.copy()]):
            with patch('banglamedscanner.orchestrator.read_abstracts_by_pmid',
                       return_value={PMID: row if row is not None else ROW.copy()}):
                return orchestrate('diabetes treatment', limit=1)

    def test_six_explicit_agents(self):
        result = self.execute()
        self.assertEqual(len(AGENTS), 6)
        self.assertEqual(len(result['agent_trace']), 6)
        self.assertTrue(all(t['status'] == 'completed' for t in result['agent_trace']))
        self.assertEqual(result['paper_count'], 1)

    def test_provenance_and_eval_isolation(self):
        result = self.execute()
        paper = result['papers'][0]
        self.assertEqual(paper['split'], 'development')
        self.assertEqual(result['heldout_exposure'], 0)
        self.assertTrue(all(e['pmid'] == PMID for e in paper['evidence']))
        self.assertFalse(result['model_used'])
        self.assertNotIn('abstract', paper)

    def test_false_population_in_objective_filtered(self):
        result = self.execute()
        population = result['papers'][0]['pico']['population']
        self.assertIsNotNone(population)
        self.assertEqual(population['section'], 'methods')
        self.assertNotIn('We aimed to investigate', population['quote_en'])

    def test_heldout_rejected(self):
        row = {**ROW, 'split': 'evaluation_candidate'}
        with self.assertRaises(ProvenanceError):
            self.execute(row=row)

    def test_retrieval_heldout_rejected(self):
        with self.assertRaises(ProvenanceError):
            self.execute(card={**CARD, 'corpus_split':'evaluation_candidate'})

    def test_foreign_or_tampered_source_rejected(self):
        with self.assertRaises(ProvenanceError):
            self.execute(row={**ROW, 'url': 'https://evil.example/12345678/'})
        self.assertFalse(pubmed_url(PMID, 'https://pubmed.ncbi.nlm.nih.gov.evil.test/12345678/'))
        self.assertTrue(pubmed_url(PMID, URL))

    def test_reject_invalid_limits(self):
        for value in [0, 4, True, '3']:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    orchestrate('diabetes treatment', limit=value)

    def test_request_local_id(self):
        first = self.execute()
        second = self.execute()
        self.assertNotEqual(first['request_id'], second['request_id'])
        first['papers'][0]['title_en'] = 'Client modified response'
        self.assertNotEqual(first['papers'][0]['title_en'], second['papers'][0]['title_en'])

    def test_bounded_multiuser(self):
        self.assertEqual(MAX_CONCURRENT, 3)
        class Busy:
            def acquire(self, blocking):
                return False
        with patch('banglamedscanner.orchestrator._SLOTS', Busy()):
            with self.assertRaises(OrchestrationBusy):
                orchestrate('diabetes treatment')

    def test_no_llm_call(self):
        with patch('banglamedscanner.llm_report.generate_bangla_report', side_effect=AssertionError('LLM called')):
            result = self.execute()
            self.assertFalse(result['model_used'])
            self.assertEqual(result['report_type'], 'deterministic_metadata_only')

    def test_ui_uses_safe_dom(self):
        from banglamedscanner.ui_workflow import PAGE
        self.assertIn('/api/orchestrate', PAGE)
        self.assertIn('DeepSeek-R1-Distill-Qwen-1.5B', PAGE)
        self.assertNotIn('innerHTML', PAGE)
        self.assertNotIn('localStorage', PAGE)
        self.assertNotIn('https://cdn.', PAGE)


if __name__ == '__main__':
    unittest.main()
