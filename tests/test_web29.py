import json
import unittest
from unittest.mock import patch
from fastapi import HTTPException
from pydantic import ValidationError
from banglamedscanner import web

class Web29Tests(unittest.TestCase):
    def test_private_claim_routes_deny_unauthenticated_requests(self):
        with self.assertRaises(HTTPException) as cm:
            web.bms29_start_claim(web.StatementLocatorRequest(statement='Metformin lowers HbA1c'),ai_access=None)
        self.assertEqual(cm.exception.status_code,403)
        with self.assertRaises(HTTPException) as cm:
            web.bms29_poll_claim('anyjob',ai_access=None)
        self.assertEqual(cm.exception.status_code,403)
    def test_bad_pmid_rejected_before_model(self):
        with self.assertRaises(ValidationError):
            web.StatementLocatorRequest(statement='Metformin lowers HbA1c',pmid='abc')
    def test_public_unified_endpoint_has_model_free_shape(self):
        result={'paper_count':1,'papers':[{'pmid':'123'}], 'agent_trace':[{'agent':'PubMed'}], 'model_used':False}
        with patch.object(web,'bms29_public_report',return_value=result):
            resp=web.bms29_report_endpoint(web.UnifiedReportRequest(question='epilepsy treatment',source='auto',limit=5))
        self.assertEqual(resp.status_code,200)
        self.assertFalse(json.loads(resp.body)['model_used'])
        self.assertEqual(resp.headers['cache-control'],'no-store')
    def test_source_validation_rejects_unexpected_values(self):
        with self.assertRaises(ValidationError):
            web.UnifiedReportRequest(question='epilepsy',source='file:///etc/passwd')
    def test_all_three_legacy_pages_still_use_single_layout(self):
        for handler in (web.home, web.structured_home, web.workflow_home):
            with self.subTest(handler=handler):
                content=handler().body.decode('utf-8')
                self.assertIn('Find a statement in papers',content)
                self.assertIn('Private DeepSeek administrator token',content)
        paths={r.path for r in web.app.routes}
        for route in ('/api/report/search','/api/ai/claims/jobs','/api/ai/claims/jobs/{job_id}'):
            self.assertIn(route,paths)

if __name__=='__main__':unittest.main()
