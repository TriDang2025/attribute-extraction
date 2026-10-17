"""Checks the retrieval module against TEAR equations 7-11, 13 and 20."""

import json
import math
import unittest
from pathlib import Path

from eval.metrics import chrf, extract_match
from tear_reproduction.retrieval import (
    cosine_similarity,
    discovery_examples,
    header_utility,
    rank_examples,
    soft_f1,
    split_table,
    table_values,
    value_utility,
)

POOL = [
    json.loads(line)
    for line in (Path(__file__).resolve().parents[1] / "data/samples/labeled_pool.jsonl").read_text(encoding="utf8").splitlines()
    if line.strip()
]


class FakeEmbedder:
    def embed(self, texts):
        # Bag of letters, enough for a deterministic dense vector.
        return [[t.lower().count(c) for c in "abcdefghijklmnopqrstuvwxyz"] for t in texts]


class RetrievalEquationTests(unittest.TestCase):
    def test_eq20_matches_paper_example_5_1(self):
        predicted = ["Victim gender", "Victim age", "Victim status"]
        gold = ["Victim age", "Victim status"]
        self.assertAlmostEqual(soft_f1(predicted, gold, extract_match), 0.8)

    def test_eq20_is_max_based_not_one_to_one(self):
        # Two predictions may both match the same gold item: P = 1, R = 1/2.
        self.assertAlmostEqual(soft_f1(["a", "a"], ["a", "b"], extract_match), 2 / 3)

    def test_eq7_header_utility(self):
        self.assertAlmostEqual(header_utility(["A", "B"], ["a", "C", "D"], 4), 1 + 2 / 5)
        # Empty preview reduces to |H_l| / (|S| + 1).
        self.assertAlmostEqual(header_utility([], ["A", "C", "D"], 4), 3 / 5)
        # The tie-break term stays below 1 whenever H_l is a subset of S.
        self.assertLess(header_utility([], ["A", "B", "C", "D"], 4), 1)

    def test_eq8_value_utility_and_text_fallback(self):
        table = {"headers": ["x", "y"], "rows": [["Alex", ["12 Oak St", "Oak St"]]]}
        self.assertEqual(table_values(table), ["Alex", "12 Oak St", "Oak St"])
        self.assertAlmostEqual(
            value_utility(["Alex"], "ignored", table), soft_f1(["Alex"], table_values(table), chrf)
        )
        text = "Alex was hurt at 12 Oak St"
        self.assertAlmostEqual(value_utility([], text, table), soft_f1([text], table_values(table), chrf))

    def test_eq9_chrf_beta_two(self):
        self.assertAlmostEqual(chrf("Victim name", "Victim name"), 1.0)
        # beta = 2 weights recall: a short prediction inside a longer reference scores lower
        # than the reverse.
        self.assertLess(chrf("Victim", "Victim name"), chrf("Victim name", "Victim"))

    def test_eq10_cosine_equals_dot_of_normalized_vectors(self):
        u, v = [3.0, 4.0, 0.0], [1.0, 2.0, 2.0]
        nu = [x / 5 for x in u]
        nv = [x / 3 for x in v]
        self.assertAlmostEqual(cosine_similarity(u, v), sum(a * b for a, b in zip(nu, nv)))

    def test_eq11_union_matches_brute_force(self):
        text = "A 19-year-old woman was shot near Main Street in Chicago on Friday."
        schema = ["Victim age", "Victim gender", "City"]
        hp, vp = ["Victim age", "City"], ["19-year-old", "Chicago"]
        embedder = FakeEmbedder()
        for k in (1, 2, 3):
            vecs = embedder.embed([text] + [e["text"] for e in POOL])
            scores = {
                "header": [header_utility(hp, e["table"]["headers"], len(schema)) for e in POOL],
                "value": [soft_f1(vp, table_values(e["table"]), chrf) for e in POOL],
                "semantic": [
                    sum(a * b for a, b in zip(vecs[0], w))
                    / (math.sqrt(sum(a * a for a in vecs[0])) * math.sqrt(sum(b * b for b in w)))
                    for w in vecs[1:]
                ],
            }
            expected = set()
            for s in scores.values():
                expected |= set(sorted(range(len(POOL)), key=lambda i: (-s[i], i))[:k])
            got = rank_examples(text, hp, vp, POOL, k, embedder, schema)
            self.assertEqual([g["index"] for g in got], sorted(expected))
            self.assertTrue(k <= len(got) <= 3 * k)
            for g in got:
                for name, value in g["utilities"].items():
                    self.assertAlmostEqual(value, scores[name][g["index"]])

    def test_example_4_1_split(self):
        table = {"headers": ["Victim name", "Victim status"], "rows": [["Alex", "Injured"]]}
        parts = split_table(table, ["Victim name"])
        self.assertEqual(parts["known_table"], {"headers": ["Victim name"], "rows": [["Alex"]]})
        self.assertEqual(parts["new_table"], {"headers": ["Victim status"], "rows": [["Injured"]]})

    def test_eq13_uses_extracted_table_as_previews(self):
        text = "A 24-year-old man was shot in Dayton."
        du = {"headers": ["Victim age", "City"], "rows": [["24", "Dayton"]]}
        demos = discovery_examples(text, ["Victim age", "City"], du, POOL, 2)
        self.assertTrue(demos)
        for d in demos:
            known = {h.lower() for h in d["known_table"]["headers"]}
            self.assertTrue(known <= {"victim age", "city"})
            self.assertFalse({h.lower() for h in d["new_table"]["headers"]} & {"victim age", "city"})


if __name__ == "__main__":
    unittest.main()
