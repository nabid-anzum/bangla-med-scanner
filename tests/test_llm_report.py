import os
import unittest
from unittest.mock import patch
from banglamedscanner.llm_report import LLMMissingConfiguration, LLMResponseError, _check_response, generate_bangla_report, is_configured
from banglamedscanner.ui_evidence import enhance

class LLMTests(unittest.TestCase):
    def test_credential_required(self):
        with patch.dict(os.environ,{},clear=True):
            self.assertFalse(is_configured())
            with self.assertRaises(LLMMissingConfiguration):
                generate_bangla_report('question',[{'pmid':'101','evidence':[]}])

    def test_unknown_pmid_rejected(self):
        with self.assertRaises(LLMResponseError):
            _check_response({'summary_bn':'এই গবেষণায় পর্যাপ্ত তথ্য পাওয়া যায়নি।','paper_explanations':[{'pmid':'999','explanation_bn':'এই তথ্য পাওয়া গেছে।'}]}, {'101'})

    def test_valid_pmid_accepted(self):
        report=_check_response({'summary_bn':'এই গবেষণায় পর্যাপ্ত তথ্য পাওয়া যায়নি।','paper_explanations':[{'pmid':'101','explanation_bn':'এই তথ্য পাওয়া গেছে।'}]}, {'101'})
        self.assertEqual(report['paper_explanations'][0]['pmid'],'101')

    def test_ui_enhancement(self):
        output=enhance('<main></main><script>old()</script></body></html>')
        self.assertIn('evidence-run',output)
        self.assertIn('/api/evidence',output)

if __name__=='__main__': unittest.main()
