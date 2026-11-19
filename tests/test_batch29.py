"""Batch29 regressions: source provenance, authorization and max-five limits."""
import json
import unittest
from unittest.mock import patch
from banglamedscanner import ai_orchestration as ai
from banglamedscanner import claim_locator as locator
from banglamedscanner import unified_report as report

PMID='12345678'
ABSTRACT=('METHODS: Adults with type 2 diabetes were randomized to metformin or placebo. '
          'RESULTS: Metformin reduced glycated hemoglobin compared with placebo over twelve weeks. '
          'CONCLUSIONS: Further trials are needed to determine long-term cardiovascular outcomes.')
PUBMED_XML=f'''<PubmedArticleSet><PubmedArticle><MedlineCitation>
<PMID>{PMID}</PMID><Article><ArticleTitle>Metformin and metabolic outcomes</ArticleTitle>
<Journal><Title>Medical Research Journal</Title></Journal>
<AuthorList><Author><ForeName>Jane</ForeName><LastName>Smith</LastName></Author>
<Author><ForeName>Ali</ForeName><LastName>Khan</LastName></Author></AuthorList>
<Abstract><AbstractText Label="METHODS">Adults with type 2 diabetes were randomized to metformin or placebo.</AbstractText>
<AbstractText Label="RESULTS">Metformin reduced glycated hemoglobin compared with placebo over twelve weeks.</AbstractText>
<AbstractText Label="CONCLUSIONS">Further trials are needed to determine long-term cardiovascular outcomes.</AbstractText></Abstract>
</Article></MedlineCitation><PubmedData><ArticleIdList>
<ArticleId IdType="pmc">PMC13579</ArticleId></ArticleIdList></PubmedData>
</PubmedArticle></PubmedArticleSet>'''.encode()

class ReportTests(unittest.TestCase):
    def test_live_mode_returns_sourced_pico_and_six_software_steps(self):
        def search(query,limit=5):
            return [{'pmid':PMID,'title':'Metformin and metabolic outcomes','journal':'MRJ','date':'2025'}]
        output=report.run_public_report('epilepsy metformin outcomes', 5, 'auto',
                                        live_search=search, abstract_fetch=lambda ids:{PMID:ABSTRACT},heldout=set())
        self.assertEqual(output['source'],'live')
        self.assertFalse(output['model_used'])
        self.assertEqual(len(output['agent_trace']),6)
        self.assertTrue(output['papers'][0]['pico']['population'])
        self.assertEqual(output['papers'][0]['evidence_scope'],'abstract')
    def test_no_abstract_never_fabricates_pico(self):
        with patch.object(report,'public_live_search',return_value={
                'papers':[{'pmid':PMID,'url':f'https://pubmed.ncbi.nlm.nih.gov/{PMID}/'}],
                'needs_ai_translation':False}):
            out=report.run_public_report('epilepsy science',1,'auto',
                         abstract_fetch=lambda ids:{},heldout=set())
        self.assertEqual(out['pico_candidate_count'],0)
        self.assertTrue(all(v is None for v in out['papers'][0]['pico'].values()))
    def test_up_to_five_and_invalid_source_rejected(self):
        with self.assertRaises(ValueError):
            report.run_public_report('renal cancer',6,'live')
        with self.assertRaises(ValueError):
            report.run_public_report('renal cancer',2,'invalid')

class ClaimSourceTests(unittest.TestCase):
    def test_pubmed_authors_pmcid_from_xml_not_model(self):
        items=locator._parse_pubmed(PUBMED_XML,{PMID})
        self.assertEqual(items[PMID]['authors_display'],'Jane Smith, Ali Khan')
        self.assertEqual(items[PMID]['pmcid'],'PMC13579')
        self.assertIn('Metformin reduced',items[PMID]['abstract'])
        self.assertEqual(items[PMID]['url'],f'https://pubmed.ncbi.nlm.nih.gov/{PMID}/')
    def test_pdf_page_only_on_literal_pdf_page_match(self):
        with patch.object(locator,'_s3_pdf_url',return_value=locator.PMC_S3+'/PMC13579.1/PMC13579.1.pdf'),\
             patch.object(locator,'_url_bytes',return_value=b'%PDF-pseudo'),\
             patch.object(locator,'_pdf_text_pages',return_value=['no metformin outcome','Metformin reduced glycated hemoglobin compared with placebo']):
            n,url=locator._locate_pdf_page('PMC13579','Metformin reduced glycated hemoglobin compared')
            self.assertEqual(n,2)
            missing,_=locator._locate_pdf_page('PMC13579','Metformin reduced mortality')
            self.assertIsNone(missing)
    def test_s3_endpoint_constrained_to_official_pdf(self):
        xml=b'<ListBucketResult><CommonPrefixes><Prefix>PMC13579.1/</Prefix></CommonPrefixes></ListBucketResult>'
        good=b'{"is_retracted":false,"pdf_url":"https://pmc-oa-opendata.s3.amazonaws.com/PMC13579.1/PMC13579.1.pdf"}'
        def transport(url):return xml if 'list-type=2' in url else good
        self.assertEqual(locator._s3_pdf_url('PMC13579',transport=transport),
                         locator.PMC_S3+'/PMC13579.1/PMC13579.1.pdf')
        bad=b'{"pdf_url":"https://evil.invalid/paper.pdf"}'
        self.assertIsNone(locator._s3_pdf_url('PMC13579',transport=lambda url: xml if 'list-type=2' in url else bad))
    def test_fulltext_paragraphs_have_section(self):
        source=b'<article><body><sec><title>Discussion</title><p>Metformin was evaluated in a large group of adults with diabetes, including participants with kidney disease.</p></sec></body></article>'
        got=locator._fulltext_sections('PMC13579',transport=lambda url:source)
        self.assertEqual(got[0]['section'],'Discussion')
        self.assertEqual(got[0]['scope'],'open_access_full_text')
    def test_invalid_pmid_and_external_download_rejected(self):
        with self.assertRaises(ValueError):locator.run_claim_check('hello medical claim',pmid='https://evil.invalid/123')
        with self.assertRaises(locator.ClaimLocatorError):
            locator._url_bytes('https://example.com/private',100)
    def test_paper_limit_and_claim_comparison_source_grounded(self):
        records=locator._parse_pubmed(PUBMED_XML,{PMID})
        def model(system,payload,max_tokens=240):
            if 'query planner' in system:return {'query_en':'metformin glycated hemoglobin','topic_en':'diabetes'}
            if 'claim evidence matcher' in system:
                ids=payload['candidates']
                self.assertTrue(ids)
                return {'matches':[{'id':ids[0]['id'],'pmid':PMID,'relation':'related'}]}
            raise AssertionError(system)
        with patch.object(locator,'is_configured',return_value=True):
            out=locator.run_claim_check('Metformin reduced glycated hemoglobin',
                 pmid=PMID,model_call=model,fetch_records=lambda ids:records,
                 fulltext=lambda p:[],pdf_page_lookup=lambda p,q:(None,None),heldout=set())
        self.assertLessEqual(len(out['papers']),5)
        self.assertEqual(out['paper_count'],1)
        self.assertEqual(out['papers'][0]['authors_display'],'Jane Smith, Ali Khan')
        self.assertIsNone(out['papers'][0]['page_number'])
        self.assertTrue(out['model_used'])
        self.assertEqual(len(out['agent_trace']),6)
        self.assertEqual(sum(x['model_invoked'] for x in out['agent_trace']),2)
    def test_model_cannot_invent_a_paper_or_page(self):
        records=locator._parse_pubmed(PUBMED_XML,{PMID})
        def model(system,payload,max_tokens=240):
            if 'query planner' in system:return {'query_en':'metformin blood sugar','topic_en':'diabetes'}
            return {'matches':[{'id':'E999','pmid':'999999','relation':'direct'}]}
        with patch.object(locator,'is_configured',return_value=True):
            out=locator.run_claim_check('Metformin blood sugar effects',
              pmid=PMID,model_call=model,fetch_records=lambda ids:records,
              fulltext=lambda p:[],pdf_page_lookup=lambda p,q:(999,'https://evil.invalid'),heldout=set())
        self.assertEqual(out['paper_count'],0)
        self.assertEqual(out['status'],'no_verifiable_passage_in_retrieved_material')
    def test_heldout_paper_not_searched(self):
        def model(system,payload,max_tokens=240):return {'query_en':'metformin','topic_en':'diabetes'}
        with patch.object(locator,'is_configured',return_value=True):
            out=locator.run_claim_check('metformin study',pmid=PMID,model_call=model,
                                       heldout={PMID})
        self.assertEqual(out['paper_count'],0)
        self.assertEqual(out['searched_papers'],0)
    def test_schema_is_bounded_and_grammar_local(self):
        schema=ai._response_schema('You are a claim evidence matcher')
        self.assertEqual(schema['properties']['matches']['maxItems'],5)
        self.assertEqual(schema['properties']['matches']['items']['properties']['relation']['enum'],
                         ['direct','related','contradicts','unclear'])

if __name__=='__main__':unittest.main()
