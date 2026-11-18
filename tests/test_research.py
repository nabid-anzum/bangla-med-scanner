import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from banglamedscanner.research import research, excerpt

class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / 'test.sqlite3'
        with sqlite3.connect(self.db) as c:
            c.execute('CREATE TABLE papers (pmid TEXT, topic TEXT, title TEXT, journal TEXT, year INTEGER, doi TEXT, pmcid TEXT, study_type TEXT, url TEXT, abstract TEXT, split TEXT)')
            c.execute('CREATE VIRTUAL TABLE papers_fts USING fts5(title,abstract)')
            for pmid, topic, split in [('123','diabetes','development'),('456','diabetes','evaluation_candidate'),('789','asthma','development')]:
                title = ('Diabetes' if topic=='diabetes' else 'Asthma')+' clinical study'
                abstract = 'RESULTS: Diabetes treatment was investigated in a trial. The full findings must be checked.'
                cur=c.execute('INSERT INTO papers VALUES (?,?,?,?,?,?,?,?,?,?,?)',(pmid,topic,title,'Journal',2025,'','','Randomized Controlled Trial',f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/',abstract,split))
                c.execute('INSERT INTO papers_fts(rowid,title,abstract) VALUES (?,?,?)',(cur.lastrowid,title,abstract))

    def test_bangla_local_search(self):
        result=research('ডায়াবেটিসের চিকিৎসা',db_path=self.db)
        self.assertEqual(result['count'],1)
        self.assertEqual(result['papers'][0]['pmid'],'123')
        self.assertEqual(result['papers'][0]['corpus_split'],'development')
        self.assertEqual(result['interpretation']['english_search_query'],'type 2 diabetes treatment')

    def test_no_eval_leak(self):
        result=research('diabetes',db_path=self.db)
        self.assertNotIn('456',[p['pmid'] for p in result['papers']])

    def test_topic_filter(self):
        result=research('হাঁপানি গবেষণা',db_path=self.db)
        self.assertEqual(result['papers'][0]['pmid'],'789')

    @patch('banglamedscanner.research.search_pubmed')
    def test_live_search(self, mock_search):
        mock_search.return_value=[{'pmid':'42','title':'Paper','journal':'J','date':'2025','doi':'','url':'https://pubmed.ncbi.nlm.nih.gov/42/'}]
        result=research('ডায়াবেটিস',source='live')
        self.assertEqual(result['count'],1)
        self.assertIsNone(result['papers'][0]['abstract_excerpt_en'])
        mock_search.assert_called_once()

    def test_invalid_source(self):
        with self.assertRaises(ValueError):
            research('ডায়াবেটিস',source='invalid')

    def test_excerpt_length(self):
        self.assertLessEqual(len(excerpt('RESULTS: ' + 'word ' * 60).split()),23)

if __name__=='__main__': unittest.main()
