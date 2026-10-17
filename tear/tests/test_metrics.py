"""Checks the metrics against Section 5.2 of the paper (Examples 5.1, 5.2 and Figure 3)."""

import unittest
from unittest.mock import patch

from eval.metrics import (
    bertscore,
    chrf,
    dictionary_f1,
    extract_match,
    header_f1,
    recall_auc,
    recall_curve,
    structured_f1,
    table_headers,
)

# Figure 3: f_k between predicted headers (rows) and gold headers (columns).
F_K = {
    ("Victim gender", "Victim age"): 0.1, ("Victim age", "Victim age"): 1.0,
    ("Victim status", "Victim age"): 0.1, ("Victim gender", "Victim status"): 0.2,
    ("Victim age", "Victim status"): 0.1, ("Victim status", "Victim status"): 1.0,
}


def f_k(pred, gold):
    return F_K.get((pred, gold), 0.0)


def f_v(pred, gold):
    # Figure 3 (3): "badly injured" vs "life-threatening" is 0.1, equal values are 1.
    if pred == gold:
        return 1.0
    return 0.1 if (pred, gold) == ("badly injured", "life-threatening") else 0.0


GOLD = {"headers": ["Victim age", "Victim status"],
        "rows": [[["15-year-old"], ["injured"]], [["eighteen"], ["life-threatening"]]]}
PRED = {"headers": ["Victim gender", "Victim age", "Victim status"],
        "rows": [[["male"], ["eighteen"], ["life-threatening"]],
                 [[], ["15-year-old"], ["injured"]],
                 [["female"], ["eighteen"], ["badly injured"]]]}


def record(table, i):
    return dict(zip(table["headers"], table["rows"][i]))


class MetricTests(unittest.TestCase):
    def test_header_f1_example_5_1(self):
        pred = ["Victim gender", "Victim age", "Victim status"]
        gold = ["Victim age", "Victim status"]
        self.assertAlmostEqual(header_f1(pred, gold), 0.8)

    def test_df1_empty_value_is_ignored(self):
        # Example 5.2 (2): DF1(R2, R^1) = 1 because R2's empty gender is ignored.
        self.assertAlmostEqual(dictionary_f1(record(PRED, 1), record(GOLD, 0), f_k, f_v), 1.0)

    def test_df1_argmax_alignment(self):
        # Example 5.2 (3): DP = (0+1+0.1)/3, DR = (1+0.1)/2. The paper prints 0.42;
        # 2PR/(P+R) with these values is 0.44.
        self.assertAlmostEqual(dictionary_f1(record(PRED, 2), record(GOLD, 1), f_k, f_v), 0.44, places=2)
        # Figure 3 pairwise DF1(R1, R^2) = 0.8: gender aligns to status (0.2 > 0.1).
        self.assertAlmostEqual(dictionary_f1(record(PRED, 0), record(GOLD, 1), f_k, f_v), 0.8)

    def test_df1_many_to_one(self):
        # Two predicted headers may align to the same gold header.
        self.assertAlmostEqual(
            dictionary_f1({"Victim": "Sarah", "Person": "Sarah"}, {"Person": "Sarah"}, extract_match, extract_match), 1.0)

    def test_structured_f1_figure_3(self):
        # Precision matches the paper: (0.8 + 1 + 0.44) / 3 = 0.747. The paper's recall
        # (1 + 0.42) / 2 conflicts with its own matrix, where R^2's best match is 0.8, so
        # Equation 20 gives (1 + 0.8) / 2 = 0.9.
        p, r = (0.8 + 1 + 0.44) / 3, 0.9
        self.assertAlmostEqual(structured_f1(PRED, GOLD, f_k, f_v), 2 * p * r / (p + r), places=2)

    def test_empty_columns_and_rows_are_not_part_of_the_table(self):
        table = {"headers": ["A", "B"], "rows": [["x", ""], ["", ""]]}
        self.assertEqual(table_headers(table), ["A"])
        self.assertAlmostEqual(structured_f1(table, {"headers": ["A"], "rows": [["x"]]}, extract_match, extract_match), 1.0)

    def test_chrf_is_standard(self):
        self.assertAlmostEqual(chrf("Victim name", "Victim name"), 1.0)
        self.assertAlmostEqual(chrf("25", "25"), 1.0)
        self.assertAlmostEqual(chrf("a b", "ab"), 1.0)  # whitespace is ignored
        self.assertLess(chrf("female", "Female"), 1.0)  # case-sensitive
        self.assertLess(chrf("the quick brown fox", "completely different text"), 0.5)

    def test_recall_curve_and_auc(self):
        ranked = ["Gender", "Status", "Location", "Weapon", "Weather", "Occupation"]
        hidden = ["Gender", "Location", "Weapon"]
        self.assertEqual(recall_curve(ranked, hidden, extract_match), [1/3, 1/3, 2/3, 1, 1, 1])
        self.assertAlmostEqual(recall_auc(ranked, hidden, extract_match), (1/3 + 1/2 + 5/6 + 1 + 1) / 5)
        # Padding a short curve with its final value.
        self.assertAlmostEqual(recall_auc(["Gender"], hidden, extract_match, pad_to=3), 1/3)

    def test_bertscore_does_not_fallback_to_chrf(self):
        with patch("eval.metrics._bert_scorer", side_effect=RuntimeError("missing optional metric")):
            with self.assertRaisesRegex(RuntimeError, "missing optional metric"):
                bertscore("different text A", "different text B")


if __name__ == "__main__":
    unittest.main()
