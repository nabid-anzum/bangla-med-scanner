import tempfile
from pathlib import Path
import sqlite3
import unittest
from banglamedscanner.corpus import parse_articles, local_search, stats

class CorpusTests(unittest.TestCase):
    def test_structured_abstract(self):
        doc = b'''<PubmedArticleSet><PubmedArticle><MedlineCitation>
        <PMID>123456</PMID><Article><ArticleTitle>Diabetes <i>trial</i></ArticleTitle>
        <Journal><JournalIssue><PubDate><Year>2025</Year></PubDate></JournalIssue><Title>Medical Journal</Title></Journal>
        <Language>eng</Language><Abstract><AbstractText Label="BACKGROUND">''' + b"Studies of diabetes control with randomized trials show results. "*3 + b'''</AbstractText></Abstract>
        <PublicationTypeList><PublicationType>Randomized Controlled Trial</PublicationType></PublicationTypeList>
        </Article></MedlineCitation><PubmedData><ArticleIdList><ArticleId IdType="doi">10.1000/test</ArticleId></ArticleIdList></PubmedData></PubmedArticle></PubmedArticleSet>'''
        papers = parse_articles(doc)
        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0]['title'], 'Diabetes trial')
        self.assertEqual(papers[0]['doi'], '10.1000/test')
        self.assertIn('BACKGROUND:', papers[0]['abstract'])

    def test_fts_search(self):
        with tempfile.TemporaryDirectory() as tmp:
            dbfile = Path(tmp) / 'corpus.sqlite3'
            with sqlite3.connect(dbfile) as db:
                db.execute('''CREATE TABLE papers (pmid TEXT PRIMARY KEY, topic TEXT, title TEXT, abstract TEXT, journal TEXT, year INTEGER, doi TEXT, pmcid TEXT, study_type TEXT, url TEXT, split TEXT, retrieved_at_utc TEXT)''')
                db.execute('CREATE VIRTUAL TABLE papers_fts USING fts5(title, abstract)')
                db.execute("INSERT INTO papers (pmid, title, abstract, topic, split) VALUES ('12345', 'Diabetes study', 'Randomized study', 'diabetes', 'development')")
                db.execute('INSERT INTO papers_fts(rowid,title,abstract) VALUES (1,\'Diabetes study\',\'Randomized study\')')
            self.assertEqual(stats(dbfile)['total'], 1)
            self.assertEqual(local_search('diabetes', db_path=dbfile)[0]['pmid'], '12345')
            self.assertEqual(local_search('"*', db_path=dbfile), [])

if __name__ == '__main__':
    unittest.main()

