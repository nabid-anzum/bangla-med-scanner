import sqlite3
import tempfile
import unittest
from pathlib import Path
from banglamedscanner.evidence import analyze, extract_abstract_evidence, _verify_quote, read_abstracts_by_pmid

class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db=Path(self.tmp.name)/'fixture.sqlite3'
        with sqlite3.connect(self.db) as db:
            db.execute('CREATE TABLE papers (pmid TEXT PRIMARY KEY, topic TEXT, title TEXT, journal TEXT, year INTEGER, doi TEXT, pmcid TEXT, study_type TEXT, url TEXT, abstract TEXT, split TEXT)')
            db.execute('CREATE VIRTUAL TABLE papers_fts USING fts5(title,abstract)')
            for pmid,split in [('1001','development'),('1002','evaluation_candidate')]:
                abstract='METHODS: Diabetes treatment was studied in adults.\nRESULTS: Diabetes treatment outcomes were compared across trial groups.\nCONCLUSIONS: Further studies are required.'
                cur=db.execute('INSERT INTO papers VALUES (?,?,?,?,?,?,?,?,?,?,?)',(pmid,'diabetes','Diabetes treatment trial','Clinical J',2025,'','', 'Randomized Controlled Trial',f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/',abstract,split))
                db.execute('INSERT INTO papers_fts(rowid,title,abstract) VALUES (?,?,?)',(cur.lastrowid,'Diabetes treatment trial',abstract))

    def test_structured_evidence_and_citations(self):
        answer=analyze('ডায়াবেটিসের চিকিৎসা',db_path=self.db)
        self.assertEqual(answer['paper_count'],1)
        self.assertEqual(answer['papers'][0]['pmid'],'1001')
        self.assertEqual(answer['evidence_count'],2)
        self.assertEqual(answer['papers'][0]['evidence'][0]['section'],'results')
        self.assertTrue(answer['agent_trace'])
        self.assertEqual(answer['bangla_report_type'],'deterministic_metadata_only')

    def test_evaluation_subset_is_never_loaded(self):
        found=read_abstracts_by_pmid(['1001','1002'],self.db)
        self.assertEqual(set(found),{'1001'})
        self.assertNotIn('1002',repr(analyze('diabetes',db_path=self.db)))

    def test_unsupported_disease_is_rejected(self):
        with self.assertRaises(ValueError):analyze('ক্যান্সারের চিকিৎসা',db_path=self.db)

    def test_tampered_quote_fails_check(self):
        self.assertFalse(_verify_quote('The treatment was 100% effective','RESULTS: No measured difference.'))

    def test_unstructured_quote_cannot_be_called_a_conclusion(self):
        x=extract_abstract_evidence('We examined this disease and the treatment outcomes.','321','https://pubmed.ncbi.nlm.nih.gov/321/')
        self.assertEqual(x[0]['section'],'unstructured_abstract')

    def test_no_remote_llm_call_by_default(self):
        result=analyze('diabetes',db_path=self.db,ai_summary=False)
        self.assertNotIn('ai_report',result)

if __name__=='__main__': unittest.main()
