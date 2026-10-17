"""Checks the experiment-runner helpers (elbow for TEAR*, corpus-level proposal pooling)."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import eval.reproduce as R


class ReproduceTests(unittest.TestCase):
    def test_elbow_of_descending_scores(self):
        self.assertEqual(R.elbow([0.9, 0.85, 0.1, 0.08, 0.05]), 3)
        self.assertEqual(R.elbow([0.5]), 1)
        self.assertEqual(R.elbow([0.5, 0.4]), 2)

    def test_proposals_are_pooled_across_texts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data").mkdir()
            tests = [{"id": "a", "text": "t1", "table": {"headers": [], "rows": []}},
                     {"id": "b", "text": "t2", "table": {"headers": [], "rows": []}}]
            (root / "data/test.jsonl").write_text("".join(json.dumps(t) + "\n" for t in tests), encoding="utf8")
            disc = [{"id": "a", "proposals": [{"name": "Hotel phone", "values": ["123"]}]},
                    {"id": "b", "proposals": [{"name": "hotel  phone", "values": ["456"]},
                                              {"name": "Taxi type", "values": ["blue"]}]}]
            (root / "res/x").mkdir(parents=True)
            (root / "res/x/disc_L1_s0.jsonl").write_text("".join(json.dumps(d) + "\n" for d in disc), encoding="utf8")
            with patch.dict(R.DATA, {"x": ("Conversation", root / "data")}), patch.object(R, "RESULTS", root / "res"):
                contexts = R._proposals("x", "1", 0)
        self.assertEqual(sorted(contexts), ["Hotel phone", "Taxi type"])
        self.assertEqual([c["values"] for c in contexts["Hotel phone"]], [["123"], ["456"]])


if __name__ == "__main__":
    unittest.main()
