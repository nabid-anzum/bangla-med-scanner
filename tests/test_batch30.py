"""BMS30: reject unrelated medicine, expose per-agent work, keep page proof strict."""
import unittest
from unittest.mock import patch

from banglamedscanner import reliable_research as rr
from banglamedscanner import pdf_evidence as pdf
from banglamedscanner import claim_locator as locator

ASTHMA='হাঁপানি চিকিৎসার সাম্প্রতিক গবেষণায় কী নতুন তথ্য এসেছে?'
ASTHMA_ABSTRACT=(
    'METHODS: Adults with persistent asthma were enrolled in a randomized clinical trial '
    'to assess inhaled corticosteroid treatment and biologic therapy. '
    'RESULTS: Asthma symptom control improved after twelve weeks of treatment '
    'with a standardized inhaler regimen compared with usual care. '
    'CONCLUSIONS: Longer follow-up for people with asthma remains necessary.'
)
DENGUE_ABSTRACT=(
    'METHODS: People living in Dhaka were recruited for dengue fever testing '
    'during an urban mosquito surveillance study. '
    'RESULTS: The dengue infection incidence was assessed across rainy seasons '
    'and linked to vector density and neighborhood characteristics. '
    'CONCLUSIONS: Urban mosquito control remained important for dengue management.'
)
PREGNANCY_ABSTRACT=(
    'METHODS: A nationally representative survey of families in Bangladesh examined '
    'unplanned pregnancies using multivariable methods. '
    'RESULTS: Unplanned pregnancy outcomes were associated with demographic factors, '
    'access to contraception and educational attainment. '
    'CONCLUSIONS: The study highlights broader reproductive-health service needs.'
)
RESULTS=[
    {'pmid':'100001','title':'Dengue fever surveillance in Dhaka','journal':'Journal A','date':'2026'},
    {'pmid':'100002','title':'Unplanned pregnancy patterns in Bangladesh','journal':'Journal B','date':'2025'},
    {'pmid':'100003','title':'Randomized asthma treatment comparison','journal':'Journal C','date':'2026'},
]
ABSTRACTS={'100001':DENGUE_ABSTRACT,'100002':PREGNANCY_ABSTRACT,'100003':ASTHMA_ABSTRACT}


def model_mock(system, data, max_tokens=240):
    if 'query planner' in system:
        return {'query_en':'dengue fever unplanned pregnancy Dhaka','topic_en':'dengue pregnancy'}
    if 'PICO candidate extractor' in system:
        return {'candidates':[{'pmid':'100003',
                               'population_quote':'Adults with persistent asthma were enrolled in a randomized clinical trial'}]}
    if 'academic evidence explainer' in system:
        assert all('asthma' in p['title_en'].lower() for p in data['papers']) if 'papers' in data else True
        return {'summary_bn':'হাঁপানি চিকিৎসার গবেষণায় ইনহেলার সংক্রান্ত তথ্য পাওয়া গেছে, তবে এটি চিকিৎসাগত নিশ্চয়তা নয়।',
                'paper_explanations':[]}
    raise AssertionError('Unexpected model role: '+system)


class RelevanceTests(unittest.TestCase):
    def test_original_bangla_asthma_anchor(self):
        self.assertEqual(rr.question_anchors(ASTHMA)[0][0], 'asthma')
        self.assertTrue(rr.question_needs_treatment(ASTHMA))

    def test_wrong_deepseek_query_overridden(self):
        q, core, decision, checked=rr.protected_query(ASTHMA,'dengue pregnancy Bangladesh')
        self.assertEqual(q,'asthma treatment')
        self.assertEqual(core,['asthma'])
        self.assertEqual(decision,'replaced_off_topic_model_query')
        self.assertTrue(checked)

    def test_papers_rejected_before_synthesis(self):
        papers,audit=rr.retrieve_grounded(ASTHMA,'asthma treatment',2,
          search=lambda q,limit:RESULTS, fetch=lambda ids:{i:ABSTRACTS[i] for i in ids}, heldout=set())
        self.assertEqual([x['pmid'] for x in papers],['100003'])
        self.assertEqual(audit['candidates_examined'],3)
        self.assertEqual(audit['rejected_candidates'],2)
        self.assertTrue(any('asthma' in item['reason'] for item in audit['rejected']))

    def test_five_result_pubmed_adapter_is_supported(self):
        def capped(q,limit):
            if limit>5: raise ValueError('max five')
            return RESULTS
        papers,audit=rr.retrieve_grounded(ASTHMA,'asthma treatment',2,
          search=capped,fetch=lambda ids:{i:ABSTRACTS[i] for i in ids},heldout=set())
        self.assertEqual([x['pmid'] for x in papers],['100003'])

    def test_asthma_comorbidity_in_unrelated_dengue_treatment_is_not_evidence(self):
        text=('BACKGROUND: A minority of dengue participants also reported asthma, which was not studied. '
              'METHODS: Adults with dengue fever received a candidate antiviral treatment in Dhaka. '
              'RESULTS: The dengue treatment showed no significant difference from placebo in the trial. '
              'CONCLUSIONS: The authors called for additional dengue studies before clinical implementation.')
        ok,reason,_=rr._paper_relevance(ASTHMA,'asthma treatment',
                                       'Antiviral treatment for dengue fever',text)
        self.assertFalse(ok,reason)

    def test_valid_asthma_rich_agent_trace(self):
        with patch.object(rr,'is_configured',return_value=True):
            out=rr.run_reliable_ai_research(ASTHMA,limit=2,model_call=model_mock,
              search=lambda q,limit:RESULTS,
              fetch=lambda ids:{i:ABSTRACTS[i] for i in ids},heldout=set())
        self.assertEqual(out['paper_count'],1)
        self.assertEqual(out['papers'][0]['pmid'],'100003')
        self.assertEqual(out['english_search_query'],'asthma treatment')
        self.assertEqual(len(out['agent_trace']),6)
        self.assertEqual(out['agent_trace'][1]['papers_rejected'],2)
        rejected=[j for j in out['agent_trace'][1]['jobs'] if j.get('action')=='Reject paper']
        self.assertEqual(len(rejected),2)
        self.assertIn('হাঁপানি',out['ai_report']['summary_bn'])
        self.assertEqual(sum(bool(t['model_invoked']) for t in out['agent_trace']),3)
        self.assertTrue(all(t['jobs'] for t in out['agent_trace']))

    def test_no_relevant_source_fails_closed(self):
        with patch.object(rr,'is_configured',return_value=True):
            out=rr.run_reliable_ai_research(ASTHMA,limit=2,model_call=model_mock,
              search=lambda q,limit:RESULTS[:2],
              fetch=lambda ids:{i:ABSTRACTS[i] for i in ids},heldout=set())
        self.assertEqual(out['paper_count'],0)
        self.assertEqual(out['status'],'no_relevant_evidence')
        self.assertEqual(out['model_invocations'],1)
        self.assertIn('Skipped',out['agent_trace'][4]['method'])

    def test_abstain_when_unknown_query_has_no_subject_overlap(self):
        ok,reason,score=rr._paper_relevance('epilepsy medication','epilepsy medication',
            'Unplanned pregnancy patterns',PREGNANCY_ABSTRACT)
        self.assertFalse(ok)

    def test_heldout_is_not_selected(self):
        found,audit=rr.retrieve_grounded(ASTHMA,'asthma treatment',2,
            search=lambda q,limit:RESULTS,fetch=lambda ids:{i:ABSTRACTS[i] for i in ids},
            heldout={'100003'})
        self.assertFalse(found)


class PageAndClaimsTests(unittest.TestCase):
    def test_pdf_page_requires_real_sequence_not_keywords(self):
        pages=['The first page studies metformin and asthma with related generic words.',
               'Asthma symptoms improved following a carefully controlled inhaled corticosteroid trial in adults over several months of treatment.']
        exact='Asthma symptoms improved following a carefully controlled inhaled corticosteroid trial in adults'
        self.assertEqual(pdf.verified_page_from_text(pages,exact),2)
        self.assertIsNone(pdf.verified_page_from_text(pages,'Corticosteroid treatment was proven to prevent all asthma deaths'))

    def test_page_unavailable_without_licensed_pdf(self):
        with patch.object(locator,'_s3_pdf_url',return_value=None):
            self.assertEqual(pdf.locate_verified_pdf_page('PMC112233','a specific controlled medical study about an outcome'),(None,None))

    def test_claim_relation_not_conflated_with_exact_statement(self):
        records={'890123':{'pmid':'890123','title_en':'Child mortality review in Bangladesh',
          'authors':['Dr A'],'authors_display':'Dr A','abstract':'METHODS: Researchers assessed child mortality in Bangladesh using household surveys across several years. RESULTS: Child mortality declined after changes in primary health care access and vaccination programs, although regional variation persisted. CONCLUSIONS: Continued monitoring remains necessary.',
          'pmcid':None,'url':'https://pubmed.ncbi.nlm.nih.gov/890123/',
          'full_text_url':None,'journal':'Evidence Journal'}}
        def mod(system,data,max_tokens=240):
            if 'query planner' in system:return {'query_en':'child mortality Bangladesh','topic_en':'child mortality'}
            if 'claim evidence matcher' in system:return {'matches':[{'id':'E1','pmid':'890123','relation':'related'}]}
            raise AssertionError(system)
        with patch.object(locator,'is_configured',return_value=True):
            out=locator.run_claim_check('Child death rate Bangladesh has decreased since the year 2020',1,
              pmid='890123',model_call=mod,fetch_records=lambda ids:records,
              fulltext=lambda x:[],pdf_page_lookup=lambda p,q:(None,None),heldout=set())
        self.assertLessEqual(out['paper_count'],1)
        if out['paper_count']:
            p=out['papers'][0]
            self.assertFalse(p['statement_explicitly_present'])
            self.assertNotEqual(p['discussion_assessment'],'Verbatim source statement found')
            self.assertIsNone(p['page_number'])
            self.assertIn('page_verification_status',p)
        self.assertTrue(out['agent_trace'][1]['jobs'])
        self.assertTrue(out['agent_trace'][2]['jobs'])


if __name__ == '__main__':
    unittest.main()
