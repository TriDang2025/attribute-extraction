"""dev50 input builder and the demonstration-pool exclusion (wf_v3.6)."""

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import eval.reproduce as R
from data_build import dev50


def _dialogue(city):
    log = [{"text": f"I need a train to {city}.", "metadata": {}},
           {"text": "Which day?", "metadata": {"train": {"semi": {"destination": city, "day": "friday"}}}}]
    return {"log": log}


DATA = {"A1.json": _dialogue("ely"), "B2.json": _dialogue("bath"), "C3.json": _dialogue("york")}


class Dev50Tests(unittest.TestCase):
    def test_rows_use_the_multiwoz_builder(self):
        rows = dev50.build_rows(DATA, ["B2", "A1"])
        self.assertEqual([r["id"] for r in rows], ["B2", "A1"])
        self.assertEqual(rows[0]["text"], "User: I need a train to bath.\nSystem: Which day?")
        self.assertEqual(rows[0]["table"]["headers"], ["Train destination", "Train day"])
        self.assertEqual(rows[0]["table"]["rows"], [[["bath"], ["friday"]]])
        self.assertEqual(len(rows[0]["schema"]), 35)

    def test_empty_table_is_an_error(self):
        with self.assertRaises(ValueError):
            dev50.build_rows({"X.json": {"log": [{"text": "hi"}, {"text": "bye", "metadata": {}}]}}, ["X"])

    def test_pool_check_and_exclusion(self):
        rows = dev50.build_rows(DATA, ["A1", "B2"])
        pool = [dict(r) for r in rows] + [{"id": "C3", "text": "t", "table": rows[0]["table"]}]
        self.assertEqual(dev50.check_against_pool(rows, pool), [])
        pool[1]["text"] = "changed"
        self.assertEqual(dev50.check_against_pool(rows, pool), ["B2"])
        self.assertEqual([r["id"] for r in dev50.pool_without(pool, ["A1", "B2"])], ["C3"])
        self.assertEqual(len(pool), 3)  # the pool is not edited

    def test_pipeline_pool_drops_held_out_ids_only_for_dev50(self):
        rows = dev50.build_rows(DATA, ["A1", "B2", "C3"])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pool.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
            test = root / "dev.jsonl"
            test.write_text("".join(json.dumps(r) + "\n" for r in rows[:2]), encoding="utf-8")
            args = SimpleNamespace(max_attempts=1)
            with patch.dict(R.DATA, {"conversation_dev50": ("Conversation", root), "conversation": ("Conversation", root)}), \
                    patch.dict(R.HELD_OUT, {"conversation_dev50": {"test": test, "previews": root / "p.jsonl"}}), \
                    patch.object(R, "_client", return_value=None), patch.object(R, "_embedder", return_value=None):
                held = R._pipeline(args, "conversation_dev50", "full", "tear", 0)
                normal = R._pipeline(args, "conversation", "full", "tear", 0)
                self.assertEqual([r["text"] for r in held.pool], [rows[2]["text"]])
                self.assertEqual(len(normal.pool), 3)
                self.assertEqual([r["id"] for r in R._tests("conversation_dev50", None)], ["A1", "B2"])

    def test_read_ids_start_gives_dev50b(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "ids.txt"
            p.write_text("\n".join(f"D{i}" for i in range(120)) + "\n", encoding="utf-8")
            self.assertEqual(dev50.read_ids(p), [f"D{i}" for i in range(50)])
            self.assertEqual(dev50.read_ids(p, 50, 50), [f"D{i}" for i in range(50, 100)])
            with self.assertRaises(ValueError):
                dev50.read_ids(p, 50, 100)

    def test_dev50b_is_a_held_out_dataset_with_its_own_files(self):
        self.assertEqual(R.DATA["conversation_dev50b"], R.DATA["conversation_dev50"])     # same pool and embeddings
        self.assertEqual(R.HELD_OUT["conversation_dev50b"]["test"].name, "conversation_dev50b.jsonl")
        self.assertEqual(R.HELD_OUT["conversation_dev50b"]["previews"].name, "previews_dev50b.jsonl")
        self.assertEqual(R.HELD_OUT["conversation_dev50"]["test"].name, "conversation_dev50.jsonl")   # unchanged

    def test_run_all_sets_of_tear_dev50(self):
        import tools.run_all as RA
        self.assertEqual(RA.held_out_sets("1"), ("dev50",))
        self.assertEqual(RA.held_out_sets("both"), ("dev50", "dev50b"))
        self.assertEqual(RA.held_out_sets("dev50b"), ("dev50b",))
        with self.assertRaises(ValueError):
            RA.held_out_sets("dev50c")


if __name__ == "__main__":
    unittest.main()
