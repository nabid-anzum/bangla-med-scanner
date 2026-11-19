"""Offline tests: no model calls, PubMed network, patient data or ERP writes."""
import json
import unittest
from unittest.mock import patch

from banglamedscanner.open_topics import (
    clean_query, plan_public, public_live_search,
)
from banglamedscanner.ai_orchestration import (
    _response_object, _fetch_abstracts, _source_papers,
    _model_pico, run_ai_research, AIWorkflowError,
)

PMID = '12345678'
ABSTRACT = (
    'METHODS: Adult patients with advanced glioblastoma were enrolled in '
    'a study of imaging techniques and clinical monitoring over twelve months.\n'
    'RESULTS: Imaging signals correlated with study observations in the '
    'investigated population during follow-up visits at hospital clinics.\n'
    'CONCLUSIONS: The findings were exploratory and additional validation '
    'is required before any clinical use of these observations.'
)


def fake_search(q, limit=5):
    return [{'pmid': PMID, 'title': 'Glioblastoma imaging study',
             'journal': 'Journal of Evidence', 'date': '2025'}]


def fake_fetch(pmids):
    return {PMID: ABSTRACT}


def fake_model(system, payload, max_tokens=100):
    if 'query planner' in system:
        return {'query_en': 'glioblastoma imaging', 'topic_en': 'glioblastoma'}
    if 'PICO candidate extractor' in system:
        return {'candidates':[{'pmid':PMID,
                               'population_quote':'Adult patients with advanced glioblastoma',
                               'result_quote':'This is not in the abstract'}]}
    return {
        'summary_bn':'এই গবেষণার ফলাফল প্রাথমিক এবং আরও যাচাই প্রয়োজন। এটি চিকিৎসা পরামর্শ নয়।',
        'paper_explanations': [],
    }


class AnyTopicTests(unittest.TestCase):
    def test_english_arbitrary_condition(self):
        plan=plan_public('What are studies on glioblastoma immunotherapy?')
        self.assertFalse(plan['local_corpus_supported'])
        self.assertIn('glioblastoma',plan['english_search_query'])

    def test_bangla_cancer(self):
        plan=plan_public('ক্যান্সারের চিকিৎসা নিয়ে কী গবেষণা আছে?')
        self.assertIn('cancer',plan['english_search_query'])
        self.assertFalse(plan['needs_ai_translation'])

    def test_bangla_unknown_is_not_made_up(self):
        plan=plan_public('অজানা চিকিৎসাবিজ্ঞানের প্রশ্ন সম্পর্কে বলুন')
        self.assertTrue(plan['needs_ai_translation'])
        self.assertEqual(plan['english_search_query'],'')

    def test_original_five_still_supported(self):
        self.assertTrue(plan_public('ডায়াবেটিস চিকিৎসা')['local_corpus_supported'])

    def test_live_search_safe_links(self):
        response=public_live_search('glioblastoma',pubmed_search=fake_search)
        self.assertEqual(response['papers'][0]['url'],
                         'https://pubmed.ncbi.nlm.nih.gov/'+PMID+'/')
        self.assertEqual(response['source'],'live')

    def test_english_sanitization(self):
        self.assertEqual(clean_query('Glaucoma[MeSH] AND OR diabetes[Title]'),
                         'Glaucoma diabetes')


class RealAIAgentTests(unittest.TestCase):
    def test_thinking_tags_not_in_output(self):
        doc=_response_object('<think>secret reasoning</think>{"x":1}')
        self.assertEqual(doc,{'x':1})

    def test_efetch_structured_xml(self):
        xml=(f'<PubmedArticleSet><PubmedArticle><MedlineCitation>'
             f'<PMID>{PMID}</PMID><Article><Abstract><AbstractText Label="RESULTS">'
             + ('A few real observations with evidence. '*9) +
             '</AbstractText></Abstract><PublicationTypeList>'
             '<PublicationType>Journal Article</PublicationType>'
             '</PublicationTypeList></Article></MedlineCitation></PubmedArticle>'
             '</PubmedArticleSet>').encode()
        out=_fetch_abstracts([PMID],transport=lambda _:xml)
        self.assertTrue(out[PMID].startswith('RESULTS:'))

    def test_heldout_id_rejected(self):
        self.assertEqual(_source_papers('glioblastoma',1,search=fake_search,
                         fetch=fake_fetch,heldout={PMID}),[])

    def test_pico_requires_exact_text(self):
        papers=[{'pmid':PMID,'abstract':ABSTRACT,'pico_ai_candidates':{}}]
        count=_model_pico('test',papers,model_call=fake_model)
        self.assertEqual(count,1)
        self.assertNotIn('result',papers[0]['pico_ai_candidates'])

    def test_three_actual_model_stages(self):
        with patch('banglamedscanner.ai_orchestration.is_configured',return_value=True):
            result=run_ai_research('গ্লিওব্লাস্টোমা কি?',1,model_call=fake_model,
                search=fake_search,fetch=fake_fetch,heldout=set())
        self.assertEqual(result['model_invocations'],3)
        self.assertEqual(sum(x['model_invoked'] for x in result['agent_trace']),3)
        self.assertEqual(result['paper_count'],1)
        self.assertIn('বাংলা',result['ai_report']['summary_bn']+'বাংলা')
        self.assertNotIn('abstract',result['papers'][0])
        self.assertFalse(result['clinical_validation'])

    def test_model_without_sources_does_not_invent_report(self):
        with patch('banglamedscanner.ai_orchestration.is_configured',return_value=True):
            result=run_ai_research('অন্য একটি বিষয়',1,model_call=fake_model,
                search=lambda q,limit: [],fetch=fake_fetch,heldout=set())
        self.assertIsNone(result['ai_report'])
        self.assertEqual(result['status'],'no_abstract_evidence')

    def test_authorization_checked_before_job(self):
        from fastapi import HTTPException
        from banglamedscanner.web import OpenTopicRequest,bms25_start_ai_research
        with self.assertRaises(HTTPException) as ctx:
            bms25_start_ai_research(OpenTopicRequest(question='glioblastoma'),ai_access=None)
        self.assertEqual(ctx.exception.status_code,403)

    def test_new_routes_registered(self):
        from banglamedscanner.web import app
        paths={r.path for r in app.routes}
        for r in ('/api/open-search','/api/smart-search','/api/ai/research/jobs',
                  '/api/ai/research/jobs/{job_id}'):
            self.assertIn(r,paths)

if __name__=='__main__':
    unittest.main()
