"""Offline tests for terms_check.py and draft_diff.py."""
from pathlib import Path
import json
import re
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import terms_check as tc
import draft_diff as dd


class InflectionTests(unittest.TestCase):
    def match(self, key, text):
        return bool(re.search(tc.key_regex(key), text, re.I))

    def test_verb_forms_match_the_base_key(self):
        for form in ("take", "takes", "took", "taken", "taking"):
            self.assertTrue(self.match("take", "the target %s damage" % form), form)

    def test_no_substring_hits(self):
        self.assertFalse(self.match("take", "mistake and intake"))
        self.assertFalse(self.match("Hide", "fiend hidden"), "hidden is not hide")

    def test_multiword_key_inflects_last_word_only(self):
        self.assertTrue(self.match("Opportunity Attack", "provoke opportunity attacks"))
        self.assertTrue(self.match("immediately after", "Immediately after casting"))

    def test_capitalised_single_word_keys_are_case_sensitive(self):
        rx = re.compile(tc.key_regex("Sphere"))
        self.assertIsNone(rx.search("an armillary sphere"))
        self.assertIsNotNone(rx.search("a 20-foot Sphere"))

    def test_apostrophe_variants(self):
        self.assertTrue(self.match("Leomund's Tiny Hut", "Leomund’s tiny hut"))


class ZhCountTests(unittest.TestCase):
    def test_ellipsis_term_needs_both_parts_in_order(self):
        self.assertEqual(tc.zh_count("緊接在施放該法術後立即傳送", "緊接在…後"), 1)
        self.assertEqual(tc.zh_count("在施放該法術後，立即傳送", "緊接在…後"), 0)

    def test_counts_repeated_terms(self):
        self.assertEqual(tc.zh_count("承受傷害與承受傷害", "承受"), 2)


class DraftDiffTests(unittest.TestCase):
    def test_reordered_sentences_still_find_their_source(self):
        src = ["甲句一。乙句二是這樣。", "丙句三。"]
        best = dd.best_match("乙句二是這樣。", src)
        self.assertGreater(best[0], 0.95)
        self.assertEqual(best[1], 1)

    def test_from_scratch_paragraph_has_low_ratio(self):
        src = ["這本沾有汙漬的書卷散發著刺鼻氣味。"]
        self.assertLess(dd.best_match("完全不同的另一段文字內容在這裡。", src)[0], 0.45)


if __name__ == "__main__":
    unittest.main()
