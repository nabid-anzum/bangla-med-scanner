import unittest
from unittest.mock import patch

from banglamedscanner.pubmed import search_pubmed


class PubMedClientTests(unittest.TestCase):

    def test_missing_query_is_rejected(self):
        with self.assertRaises(ValueError):
            search_pubmed("  ")

    @patch("banglamedscanner.pubmed._get_json")
    def test_no_results(self, fetch):
        fetch.return_value = {
            "esearchresult": {"idlist": []}
        }

        self.assertEqual(
            search_pubmed("unlikely search"), []
        )
        self.assertEqual(fetch.call_count, 1)

    @patch("banglamedscanner.pubmed._get_json")
    def test_metadata_extraction(self, fetch):
        fetch.side_effect = [
            {
                "esearchresult": {
                    "idlist": ["12345"]
                }
            },
            {
                "result": {
                    "12345": {
                        "title": "Example Trial",
                        "fulljournalname":
                            "Example Journal",
                        "pubdate": "2026",
                        "articleids": [
                            {
                                "idtype": "doi",
                                "value": "10.1000/example"
                            }
                        ],
                    }
                }
            },
        ]

        results = search_pubmed("diabetes trial")

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["pmid"], "12345"
        )
        self.assertEqual(
            results[0]["doi"], "10.1000/example"
        )
        self.assertIn(
            "12345", results[0]["url"]
        )
        self.assertEqual(fetch.call_count, 2)


if __name__ == "__main__":
    unittest.main()
