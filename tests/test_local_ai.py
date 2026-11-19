"""Network-free tests for isolated DeepSeek integration and AI authorization."""
import json
import os
import time
import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from banglamedscanner.ai_gate import authorized, get_job, start_job, JobBusy
from banglamedscanner.llm_report import (
    LLMMissingConfiguration, LLMResponseError, LOCAL_BASE,
    _endpoint, _parse_model_output, _check_response,
    generate_bangla_report, is_configured,
)
from banglamedscanner.web import EvidenceRequest, evidence_endpoint, start_ai_job, poll_ai_job
from banglamedscanner.ui_evidence import enhance

ENV = {
    'BMS_LOCAL_AI_ENABLED': '1',
    'BMS_LLM_BASE_URL': LOCAL_BASE,
    'BMS_LLM_MODEL': 'local-gguf-model',
    'BMS_AI_ACCESS_TOKEN': 'T'*50,
}


class LocalAITests(unittest.TestCase):
    def test_config_needs_local_model_and_admin_secret(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(is_configured())
            with self.assertRaises(LLMMissingConfiguration):
                generate_bangla_report('কী বলছে?', [])
        with patch.dict(os.environ, ENV, clear=True):
            self.assertTrue(is_configured())
            self.assertEqual(_endpoint(), LOCAL_BASE + '/chat/completions')
        with patch.dict(os.environ, {**ENV, 'BMS_LLM_BASE_URL':'https://outside.invalid/v1'}, clear=True):
            self.assertFalse(is_configured())

    def test_secret_required(self):
        with patch.dict(os.environ, ENV, clear=True):
            self.assertTrue(authorized('T'*50))
            self.assertFalse(authorized(None))
            self.assertFalse(authorized('bad'))

    def test_public_api_refuses_ai_bypass(self):
        with patch('banglamedscanner.web.run_evidence') as worker:
            with self.assertRaises(HTTPException) as exc:
                evidence_endpoint(EvidenceRequest(question='ডায়াবেটিসের চিকিৎসা', ai_summary=True))
            self.assertEqual(exc.exception.status_code, 403)
            worker.assert_not_called()

    def test_public_non_ai_still_operates(self):
        with patch('banglamedscanner.web.run_evidence', return_value={'paper_count':1}) as worker:
            result = evidence_endpoint(EvidenceRequest(question='ডায়াবেটিসের চিকিৎসা', ai_summary=False))
            self.assertEqual(result['paper_count'], 1)
            worker.assert_called_once()

    def test_unauthorized_ai_job_blocked_before_worker(self):
        with patch.dict(os.environ, ENV, clear=True):
            with patch('banglamedscanner.web.start_job') as job:
                with self.assertRaises(HTTPException) as exc:
                    start_ai_job(EvidenceRequest(question='ডায়াবেটিসের চিকিৎসা'), ai_access='wrong')
                self.assertEqual(exc.exception.status_code, 403)
                job.assert_not_called()

    def test_bad_citations_rejected(self):
        with self.assertRaises(LLMResponseError):
            _check_response({'summary_bn':'এখানে পর্যাপ্ত গবেষণার প্রমাণ নেই। PMID 999', 'paper_explanations':[]}, {'123'})
        clean = _check_response({'summary_bn':'এখানে পর্যাপ্ত গবেষণার প্রমাণ নেই।', 'paper_explanations': []}, {'123'})
        self.assertEqual(clean['paper_explanations'], [])

    def test_reasoning_is_never_displayed(self):
        obj = _parse_model_output('<think>private draft</think>{"summary_bn":"অপর্যাপ্ত প্রমাণ পাওয়া গেছে।","paper_explanations":[]}')
        self.assertNotIn('private draft', obj['summary_bn'])
        with self.assertRaises(LLMResponseError):
            _parse_model_output('<think>private incomplete')

    def test_model_call_is_local_and_sends_no_paid_token(self):
        sample = [{'pmid':'123', 'year':2025, 'study_type':'Review',
                   'evidence':[{'section':'results','quote_en':'Short incomplete evidence excerpt.'}]}]
        reply = {'summary_bn':'এই উদ্ধৃতি থেকে পর্যাপ্ত চিকিৎসাগত প্রমাণ পাওয়া যায় না।', 'paper_explanations':[]}
        response = MagicMock()
        response.read.return_value = json.dumps({'choices':[{'message':{'content':json.dumps(reply,ensure_ascii=False)}}]},ensure_ascii=False).encode()
        context = MagicMock()
        context.__enter__.return_value = response
        with patch.dict(os.environ, ENV, clear=True):
            with patch('banglamedscanner.llm_report.urlopen', return_value=context) as call:
                result = generate_bangla_report('ডায়াবেটিসের চিকিৎসা', sample)
        self.assertEqual(result['model_kind'], 'self_hosted_open_weight_1_5b')
        request = call.call_args.args[0]
        self.assertEqual(request.full_url, LOCAL_BASE+'/chat/completions')
        self.assertIsNone(request.get_header('Authorization'))
        payload = json.loads(request.data)
        self.assertIn('response_format', payload)
        self.assertNotIn('T'*50, json.dumps(payload))

    def test_queue_runs_one_at_a_time_and_poll_requires_token(self):
        import threading
        wait = threading.Event()
        def slow_worker(question, limit, ai_summary):
            wait.wait(1)
            return {'paper_count':1}
        with patch.dict(os.environ, ENV, clear=True):
            job_id = start_job('test', 1, slow_worker)
            try:
                with self.assertRaises(JobBusy):
                    start_job('test2', 1, slow_worker)
                with self.assertRaises(HTTPException) as exc:
                    poll_ai_job(job_id, ai_access='invalid')
                self.assertEqual(exc.exception.status_code, 403)
            finally:
                wait.set()
            end=time.monotonic()+2
            while time.monotonic()<end:
                result=get_job(job_id)
                if result['status']=='completed':
                    break
                time.sleep(0.01)
            self.assertEqual(get_job(job_id)['status'], 'completed')
            self.assertEqual(poll_ai_job(job_id, ai_access='T'*50)['result']['paper_count'],1)

    def test_public_ui_uses_background_job_no_storage(self):
        html = enhance('<main></main><script>old()</script></body></html>')
        self.assertIn('ai-access-token',html)
        self.assertIn('/api/ai/jobs',html)
        self.assertNotIn('localStorage',html)
        self.assertNotIn('sessionStorage',html)


if __name__=='__main__':
    unittest.main()
