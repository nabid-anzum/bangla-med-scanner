import unittest

from banglamedscanner.query import interpret


class QueryInterpretationTests(unittest.TestCase):

    def test_diabetes_bangla_treatment(self):
        result = interpret(
            "ডায়াবেটিসের চিকিৎসায় নতুন গবেষণা কী বলছে?"
        )
        self.assertEqual(result["topic"], "diabetes")
        self.assertEqual(
            result["detected_language"], "bn"
        )
        self.assertEqual(
            result["english_search_query"],
            "type 2 diabetes treatment",
        )
        self.assertTrue(result["recent_requested"])

    def test_hypertension(self):
        result = interpret("উচ্চ রক্তচাপের ঝুঁকি")
        self.assertEqual(
            result["english_search_query"],
            "hypertension risk",
        )

    def test_asthma(self):
        result = interpret("হাঁপানি প্রতিরোধ")
        self.assertEqual(
            result["english_search_query"],
            "asthma prevention",
        )

    def test_depression(self):
        result = interpret("বিষণ্নতার চিকিৎসা")
        self.assertEqual(result["topic"], "depression")

    def test_copd(self):
        result = interpret("সিওপিডি গবেষণা")
        self.assertEqual(result["topic"], "copd")

    def test_english(self):
        result = interpret("diabetes treatment")
        self.assertEqual(
            result["detected_language"], "en"
        )

    def test_unsupported(self):
        with self.assertRaisesRegex(
            ValueError, "No supported"
        ):
            interpret("ক্যান্সারের চিকিৎসা")

    def test_multiple_topics(self):
        with self.assertRaisesRegex(
            ValueError, "Multiple"
        ):
            interpret("ডায়াবেটিস ও হাঁপানি")

    def test_empty(self):
        with self.assertRaises(ValueError):
            interpret("   ")
