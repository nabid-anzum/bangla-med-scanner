"""Security, accessibility and route tests for the unified report UI.

No paid model call, network request or dataset mutation is performed.
"""
import unittest
from html.parser import HTMLParser

from banglamedscanner.ui_unified import PAGE


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.attrs = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.attrs.append((tag, dict(attrs)))


class UnifiedUITests(unittest.TestCase):
    def test_one_search_form_one_question(self):
        t = Tags()
        t.feed(PAGE)
        self.assertEqual(t.tags.count('form'), 1)
        self.assertEqual(t.tags.count('textarea'), 1)

    def test_all_legacy_page_handlers_use_one_workspace(self):
        from banglamedscanner.web import home, structured_home, workflow_home
        for handler in (home, structured_home, workflow_home):
            result = handler()
            content = result.body.decode('utf-8')
            self.assertIn('data-bms-unified="v1"', content)
            self.assertIn('id="research-form"', content)
            self.assertEqual(content.count('<textarea'), 1)

    def test_one_corpus_api_call_drives_all_tabs(self):
        self.assertIn("'/api/orchestrate'", PAGE)
        self.assertIn('case \'pico\'', PAGE)
        self.assertIn('case \'trace\'', PAGE)
        self.assertIn('case \'papers\'', PAGE)
        self.assertIn('renderOverview', PAGE)

    def test_live_pubmed_metadata_is_explicit(self):
        self.assertIn("'/api/research'", PAGE)
        self.assertIn("source:'live'", PAGE)
        self.assertIn('bibliographic metadata only', PAGE)

    def test_admin_ai_keeps_token_private(self):
        self.assertIn('X-BMS-AI-Token', PAGE)
        self.assertIn("'/api/ai/jobs'", PAGE)
        self.assertIn("input.type='password'", PAGE)
        self.assertNotIn('localStorage', PAGE)
        self.assertNotIn('sessionStorage', PAGE)
        self.assertNotIn('innerHTML', PAGE)

    def test_no_tracker_or_remote_assets(self):
        self.assertEqual(PAGE.count('<script'), 1)
        self.assertNotIn('src="https:', PAGE)
        self.assertNotIn('href="https://fonts.', PAGE)
        self.assertNotIn('googletagmanager', PAGE)

    def test_keyboard_and_screenreader_support(self):
        self.assertIn('role="tablist"', PAGE)
        self.assertIn('role="tabpanel"', PAGE)
        self.assertIn('aria-live="polite"', PAGE)
        self.assertIn("event.key==='ArrowRight'", PAGE)
        self.assertIn('prefers-reduced-motion', PAGE)

    def test_links_are_canonical_pubmed_ids(self):
        self.assertIn("/^\\d{1,10}$/", PAGE)
        self.assertIn("'https://pubmed.ncbi.nlm.nih.gov/'+pmid+'/'", PAGE)
        self.assertIn('noopener noreferrer', PAGE)

    def test_preserves_server_routes_and_authorization(self):
        from banglamedscanner.web import app
        paths = {r.path for r in app.routes}
        for path in ('/','/structured','/workflow','/api/research',
                     '/api/structured','/api/orchestrate','/api/ai/jobs',
                     '/api/ai/jobs/{job_id}'):
            self.assertIn(path, paths)


if __name__ == '__main__':
    unittest.main()
