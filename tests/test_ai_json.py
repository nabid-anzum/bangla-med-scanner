"""Regression tests for model-output recovery; no live model use."""
import io
import json
import os
import unittest
from unittest.mock import patch

from banglamedscanner.ai_orchestration import (
    AIWorkflowError, _response_object, _response_schema, _chat,
)


class LocalJSONRecoveryTests(unittest.TestCase):
    def test_planner_schema(self):
        schema = _response_schema('medical query planner')
        self.assertEqual(schema['required'], ['query_en', 'topic_en'])

    def test_pico_schema(self):
        schema = _response_schema('PICO candidate extractor')
        props = schema['properties']['candidates']['items']['properties']
        self.assertIn('population_quote', props)
        self.assertEqual(schema['properties']['candidates']['maxItems'], 2)

    def test_summary_schema(self):
        schema = _response_schema('academic evidence explainer')
        self.assertIn('summary_bn', schema['required'])

    def test_unknown_role_fails_closed(self):
        with self.assertRaises(AIWorkflowError):
            _response_schema('untrusted arbitrary task')

    def test_thinking_stripped_from_final_json(self):
        obj = _response_object('<think>private reasoning</think>```json\\n{"query_en":"diabetes","topic_en":"diabetes"}\\n```'.replace('\\n', '\n'))
        self.assertEqual(obj['query_en'], 'diabetes')

    def test_incomplete_reasoning_is_not_treated_as_final_json(self):
        with self.assertRaises(AIWorkflowError):
            _response_object('<think>{"query_en":"diabetes","topic_en":"diabetes"}')

    def test_no_json_is_rejected(self):
        with self.assertRaises(AIWorkflowError):
            _response_object('Thinking about cancer research without a final object')

    def test_actual_request_is_local_and_has_user_only_and_schema(self):
        expected = {'query_en': 'cancer treatment', 'topic_en': 'cancer'}
        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, *_):
                return json.dumps({'choices': [{'message': {'content':json.dumps(expected)}}]}).encode()
        class FakeOpener:
            def open(self, request, timeout):
                self_request = json.loads(request.data)
                assert request.full_url == 'http://127.0.0.1:18766/v1/chat/completions'
                assert len(self_request['messages']) == 1
                assert self_request['messages'][0]['role'] == 'user'
                assert self_request['max_tokens'] >= 420
                assert self_request['reasoning_effort'] == 'none'
                assert self_request['response_format']['type'] == 'json_schema'
                assert self_request['temperature'] == 0.0
                assert timeout <= 210
                return FakeResponse()
        with patch('banglamedscanner.ai_orchestration.is_configured', return_value=True), \
             patch('banglamedscanner.ai_orchestration._endpoint', return_value='http://127.0.0.1:18766/v1/chat/completions'), \
             patch('banglamedscanner.ai_orchestration.build_opener', return_value=FakeOpener()), \
             patch.dict(os.environ, {'BMS_LLM_MODEL':'local-gguf-model'}):
            self.assertEqual(_chat('medical query planner', {'question': 'cancer'}), expected)

if __name__ == '__main__':
    unittest.main()

class BanglaSynthesisRecoveryTests(unittest.TestCase):
    def _paper(self):
        return {
            'pmid': '12345678',
            'title_en': 'Evidence title',
            'abstract': 'Adults enrolled in a pilot observational study.',
            'evidence': [{'quote_en': 'Adults enrolled in a pilot observational study.'}],
            'pico_ai_candidates': {},
        }

    def test_valid_bangla_once(self):
        from banglamedscanner.ai_orchestration import _model_synthesis
        calls = []
        def model(role, payload, max_tokens):
            calls.append(role)
            return {'summary_bn': 'এই সংক্ষিপ্ত গবেষণা উদ্ধৃতি থেকে চিকিৎসার কার্যকারিতা নিশ্চিতভাবে বলা যায় না।',
                    'paper_explanations': []}
        result = _model_synthesis('বাংলা গবেষণার প্রশ্ন', [self._paper()], model_call=model)
        self.assertEqual(result['synthesis_model_attempts'], 1)
        self.assertEqual(len(calls), 1)

    def test_english_then_valid_bangla(self):
        from banglamedscanner.ai_orchestration import _model_synthesis
        calls = []
        def model(role, payload, max_tokens):
            calls.append(role)
            if len(calls) == 1:
                return {'summary_bn': 'English text; do not publish this answer.',
                        'paper_explanations': []}
            return {'summary_bn': 'এই সংক্ষিপ্ত উদ্ধৃতিগুলো চিকিৎসার ফল সম্পর্কে নির্ভরযোগ্য সিদ্ধান্ত দেয় না।',
                    'paper_explanations': []}
        result = _model_synthesis('বাংলা গবেষণার প্রশ্ন', [self._paper()], model_call=model)
        self.assertEqual(result['synthesis_model_attempts'], 2)
        self.assertEqual(len(calls), 2)

    def test_unknown_pmid_rejected_after_both_attempts(self):
        from banglamedscanner.ai_orchestration import _model_synthesis, AIWorkflowError
        calls = []
        def model(role, payload, max_tokens):
            calls.append(1)
            return {'summary_bn': 'এই গবেষণায় PMID 99999999 থেকে প্রমাণিত ফল পাওয়া গেছে বলে দাবি করা হচ্ছে।',
                    'paper_explanations': []}
        with self.assertRaises(AIWorkflowError):
            _model_synthesis('বাংলা প্রশ্ন', [self._paper()], model_call=model)
        self.assertEqual(len(calls), 2)

    def test_no_english_fallback(self):
        from banglamedscanner.ai_orchestration import _model_synthesis, AIWorkflowError
        def model(role, payload, max_tokens):
            return {'summary_bn': 'English only, no Bengali evidence.', 'paper_explanations': []}
        with self.assertRaises(AIWorkflowError):
            _model_synthesis('বাংলা প্রশ্ন', [self._paper()], model_call=model)
    def test_retry_count_visible_in_full_trace(self):
        from banglamedscanner.ai_orchestration import run_ai_research
        from test_open_ai import fake_search, fake_fetch
        count = [0]
        def model(role, payload, max_tokens):
            if 'query planner' in role:
                return {'query_en':'glioblastoma imaging','topic_en':'glioblastoma'}
            if 'PICO candidate extractor' in role:
                return {'candidates': []}
            count[0] += 1
            if count[0] == 1:
                return {'summary_bn': 'English does not pass language validation.', 'paper_explanations': []}
            return {'summary_bn': 'এই গবেষণার সংক্ষিপ্ত উদ্ধৃতিতে চিকিৎসা সম্পর্কে নিশ্চিত সিদ্ধান্ত দেওয়া যায় না।', 'paper_explanations': []}
        with patch('banglamedscanner.ai_orchestration.is_configured', return_value=True):
            result = run_ai_research('বাংলা প্রশ্ন',1,model_call=model,
                                     search=fake_search,fetch=fake_fetch,heldout=set())
        self.assertEqual(result['model_invocations'],4)
        self.assertEqual(result['agent_trace'][-2]['model_attempts'],2)
        self.assertEqual(sum(bool(x['model_invoked']) for x in result['agent_trace']),3)


class NativeGrammarRecoveryTests(unittest.TestCase):
    def setUp(self):
        from banglamedscanner.ai_orchestration import _MODEL_ATTEMPTS
        _MODEL_ATTEMPTS.set(0)

    def test_invalid_chat_retries_native_schema(self):
        from banglamedscanner.ai_orchestration import _MODEL_ATTEMPTS
        expected={'candidates':[{'pmid':'1234','outcome_quote':'Pilot results'}]}
        urls=[]
        class FakeResponse:
            def __init__(self, obj): self.obj=obj
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self, *a): return json.dumps(self.obj).encode()
        class FakeOpener:
            def open(self, request, timeout):
                urls.append(request.full_url)
                body=json.loads(request.data)
                if request.full_url.endswith('/chat/completions'):
                    self_body=body
                    assert self_body['temperature'] == 0.0
                    return FakeResponse({'choices':[{'finish_reason':'length',
                        'message': {'content':'<think>never completed'}}]})
                assert request.full_url.endswith('/completion')
                assert 'json_schema' in body
                assert body['temperature'] == 0.0
                assert '<think>' not in body['prompt']
                return FakeResponse({'content': json.dumps(expected), 'stop_type':'eos'})
        with patch('banglamedscanner.ai_orchestration.is_configured', return_value=True), \
             patch('banglamedscanner.ai_orchestration._endpoint', return_value='http://127.0.0.1:18766/v1/chat/completions'), \
             patch('banglamedscanner.ai_orchestration.build_opener', return_value=FakeOpener()), \
             patch.dict(os.environ, {'BMS_LLM_MODEL':'local-model'}):
            answer=_chat('PICO candidate extractor', {'question':'question'})
        self.assertEqual(answer, expected)
        self.assertEqual(len(urls),2)
        self.assertEqual(_MODEL_ATTEMPTS.get(),2)

    def test_both_invalid_fails_closed(self):
        from banglamedscanner.ai_orchestration import _MODEL_ATTEMPTS
        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self,*a): return False
            def read(self,*a): return json.dumps({'content':'not valid JSON',
                'choices':[{'message':{'content':'<think>incomplete'}}]}).encode()
        class FakeOpener:
            def open(self,request, timeout): return FakeResponse()
        with patch('banglamedscanner.ai_orchestration.is_configured', return_value=True), \
             patch('banglamedscanner.ai_orchestration._endpoint', return_value='http://127.0.0.1:18766/v1/chat/completions'), \
             patch('banglamedscanner.ai_orchestration.build_opener', return_value=FakeOpener()), \
             patch.dict(os.environ, {'BMS_LLM_MODEL':'local-model'}):
            with self.assertRaises(AIWorkflowError):
                _chat('medical query planner', {'question':'question'})
        self.assertEqual(_MODEL_ATTEMPTS.get(),2)

    def test_unexpected_model_host_rejected_before_network(self):
        with patch('banglamedscanner.ai_orchestration.is_configured', return_value=True), \
             patch('banglamedscanner.ai_orchestration._endpoint', return_value='https://example.com/api'):
            with self.assertRaises(AIWorkflowError):
                _chat('medical query planner', {})

    def test_no_retries_records_one_attempt(self):
        from banglamedscanner.ai_orchestration import _MODEL_ATTEMPTS
        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self,*a): return False
            def read(self,*a): return json.dumps({'choices':[{'message':{'content':
                 '{"query_en":"cancer","topic_en":"cancer"}'}}]}).encode()
        class FakeOpener:
            def open(self,request, timeout):return FakeResponse()
        with patch('banglamedscanner.ai_orchestration.is_configured', return_value=True), \
             patch('banglamedscanner.ai_orchestration._endpoint', return_value='http://127.0.0.1:18766/v1/chat/completions'), \
             patch('banglamedscanner.ai_orchestration.build_opener', return_value=FakeOpener()), \
             patch.dict(os.environ, {'BMS_LLM_MODEL':'local-model'}):
            self.assertEqual(_chat('medical query planner', {'question':'question'})['query_en'], 'cancer')
        self.assertEqual(_MODEL_ATTEMPTS.get(),1)
