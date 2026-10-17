"""Checks the paper-faithful pipeline pieces with a scripted fake model."""

import json
import unittest

from tear_reproduction.integration import HybridIntegrator, diversity_threshold, low_diversity_sets, vendi_score
from tear_reproduction.pipeline import TearPipeline
from tear_reproduction.prompts import extraction_prompt, schema_prefix
from tear_reproduction.schema import full_schema, json_to_table, project, table_to_json

POOL = [
    {"text": "A 24-year-old man was shot and killed in Dayton.",
     "table": json_to_table({"Accident": {"0": {"Accident address": ["Dayton"]}},
                             "Victim": {"0": {"Victim age": ["24-year-old"], "Victim gender": ["man"], "Victim status": ["killed"]}}},
                            "Incidents")},
    {"text": "Maria Lopez, 45, was injured in Phoenix.",
     "table": json_to_table({"Victim": {"0": {"Victim name": ["Maria Lopez"], "Victim age": ["45"], "Victim status": ["injured"]}}},
                            "Incidents")},
]
SCHEMA = ["Victim age", "Victim gender", "Victim status", "Victim name", "Accident address"]


class FakeClient:
    def __init__(self, replies):
        self.replies, self.prompts = list(replies), []

    def chat(self, system, user, **kwargs):
        self.prompts.append(user)
        return self.replies.pop(0)


class SchemaTests(unittest.TestCase):
    def test_entity_json_round_trip_and_single_record(self):
        table = POOL[0]["table"]
        self.assertEqual(json_to_table(table_to_json(table, "Incidents"), "Incidents"), table)
        merged = json_to_table({"Hotel": {"0": {"Hotel area": ["north"]}}, "Train": {"0": {"Train day": ["friday"]}}},
                               "Conversation")
        self.assertEqual(len(merged["rows"]), 1)
        self.assertEqual(len(full_schema("Conversation")), 35)

    def test_project_hides_attributes_and_drops_empty_records(self):
        projected = project(POOL[0]["table"], ["Victim age"])
        self.assertEqual(projected, {"headers": ["Victim age"], "rows": [[["24-year-old"]]]})

    def test_extraction_prompt_follows_appendix(self):
        prompt = extraction_prompt("text", SCHEMA, "Incidents", POOL, ["Victim age"], ["24"])
        self.assertIn("If an attribute is not present or cannot be determined, do not include the attribute", prompt)
        self.assertIn("The above text is most likely to contain the attributes: [\"Victim age\"]", prompt)
        self.assertNotIn("Here are some hints", extraction_prompt("text", SCHEMA, "Incidents", POOL))
        self.assertTrue(schema_prefix("Incidents", ["A", "B"]).endswith("A, B,"))


class PipelineTests(unittest.TestCase):
    def test_tear_extraction_parses_entity_json(self):
        reply = json.dumps({"Victim": {"0": {"Victim age": ["19-year-old"], "Victim gender": ["woman"]}}})
        client = FakeClient([reply])
        pipe = TearPipeline(client, POOL, "Incidents", SCHEMA, shots=1)
        result = pipe.extract("A 19-year-old woman was shot.", ["Victim age", "Weather"], ["19-year-old"])
        self.assertEqual(result["table"]["headers"], ["Victim age", "Victim gender"])
        self.assertEqual(result["preview"]["headers"], ["Victim age"])  # H_p is kept within S
        self.assertIn("Here are some hints", client.prompts[0])

    def test_rag_uses_no_previews_and_retries_invalid_json(self):
        client = FakeClient(["not json", json.dumps({"Victim": {"0": {"Victim age": ["45"]}}})])
        pipe = TearPipeline(client, POOL, "Incidents", SCHEMA, shots=1, retrieval="rag")
        result = pipe.extract("Someone, 45, was hurt.")
        self.assertEqual(len(result["demonstration_indices"]), 1)
        self.assertNotIn("Here are some hints", client.prompts[-1])
        self.assertEqual(pipe.calls[-1]["attempts"], 2)

    def test_hidden_attributes_leave_the_pool(self):
        pipe = TearPipeline(FakeClient([]), POOL, "Incidents", ["Victim age"], shots=1)
        self.assertEqual(pipe.pool[0]["table"]["headers"], ["Victim age"])

    def test_discovery_returns_only_new_attributes(self):
        reply = json.dumps({"Victim": {"0": {"Victim age": ["45"], "Victim weapon wound": ["leg"]}}})
        pipe = TearPipeline(FakeClient([reply]), POOL, "Incidents", ["Victim age", "Victim status"], shots=1)
        table = {"headers": ["Victim age"], "rows": [[["45"]]]}
        result = pipe.discover("Someone, 45, was shot in the leg.", table)
        self.assertEqual(result["proposals"], [{"name": "Victim weapon wound", "values": ["leg"]}])


class PlaceholderTests(unittest.TestCase):
    def test_placeholder_names_are_retried(self):
        bad = json.dumps({"Victim": {"0": {"<new attribute 1>": ["leg"]}}})
        good = json.dumps({"Victim": {"0": {"Victim wound": ["leg"]}}})
        client = FakeClient([bad, good])
        pipe = TearPipeline(client, POOL, "Incidents", ["Victim age"], shots=1)
        result = pipe.discover("Someone was shot in the leg.", {"headers": [], "rows": []})
        self.assertEqual(result["proposals"], [{"name": "Victim wound", "values": ["leg"]}])
        self.assertIn("placeholder", client.prompts[1])


class IntegrationTests(unittest.TestCase):
    def test_vendi_score_bounds(self):
        self.assertAlmostEqual(vendi_score(["a", "a"], lambda x, y: 1.0), 1.0)
        self.assertAlmostEqual(vendi_score(["a", "b"], lambda x, y: float(x == y)), 2.0)

    def test_low_diversity_sets_and_greedy_iteration(self):
        schema = ["Victim age", "Victim name"]  # close names: low threshold 1 + delta
        threshold = diversity_threshold(schema)
        sets = low_diversity_sets(["Hospital name", "Hospital names", "Weapon type"] + schema, threshold)
        self.assertEqual(sets, [frozenset({"Hospital name", "Hospital names"})])
        client = FakeClient(['{"Hospital name": "d1"}', '{"Hospital names": "d2"}', "One"])
        integrator = HybridIntegrator(client, "Incidents", schema, {"Hospital name": 0.5, "Hospital names": 0.1})
        contexts = {"Hospital name": [{"text": "t", "values": ["X"]}], "Hospital names": [{"text": "t", "values": ["Y"]}]}
        result = integrator.integrate(["Hospital name", "Hospital names", "Weapon type"], contexts)
        self.assertEqual(sorted(result["candidates"]), ["Hospital name", "Weapon type"])


if __name__ == "__main__":
    unittest.main()
