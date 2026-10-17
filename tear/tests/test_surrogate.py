"""Checks the surrogate serialization (TEAR Section 4.2.1) and data helpers."""

import json
import random
import tempfile
import unittest
from pathlib import Path

from surrogate.data import drop_hidden, from_model_text, length_batches, load_hidden, to_model_text
from surrogate.serialize import (
    CELL_SEP,
    ROW_SEP,
    SPAN_SEP,
    parse_table_sequence,
    preview_for_schema,
    probe_sequence,
    serialize_table,
)

TABLE = {
    "headers": ["Victim name", "Victim status", "City"],
    "rows": [
        [["John Doe"], "Injured", "Memphis"],
        [["Jane Smith", "J. Smith"], ["Deceased"], []],
    ],
}


class SerializeTest(unittest.TestCase):
    def test_tokens(self):
        self.assertEqual((SPAN_SEP, CELL_SEP, ROW_SEP), ("⟨m⟩", "⟨s⟩", "⟨n⟩"))

    def test_serialize_format(self):
        self.assertEqual(
            serialize_table(TABLE),
            "Victim name⟨s⟩Victim status⟨s⟩City"
            "⟨n⟩John Doe⟨s⟩Injured⟨s⟩Memphis"
            "⟨n⟩Jane Smith⟨m⟩J. Smith⟨s⟩Deceased⟨s⟩",
        )

    def test_round_trip(self):
        parsed = parse_table_sequence(serialize_table(TABLE))
        self.assertEqual(parsed["headers"], TABLE["headers"])
        self.assertEqual(parsed["rows"], [
            [["John Doe"], ["Injured"], ["Memphis"]],
            [["Jane Smith", "J. Smith"], ["Deceased"], []],
        ])
        self.assertEqual(serialize_table(parsed), serialize_table(TABLE))

    def test_header_only(self):
        seq = serialize_table({"headers": ["A", "B"], "rows": []})
        self.assertEqual(seq, "A⟨s⟩B")
        self.assertEqual(parse_table_sequence(seq), {"headers": ["A", "B"], "rows": []})

    def test_model_text_round_trip(self):
        seq = serialize_table(TABLE)
        spaced = to_model_text(seq)
        self.assertIn("⟨s⟩ Victim status", spaced)
        self.assertEqual(from_model_text(spaced), seq)
        self.assertEqual(from_model_text(" Victim name ⟨s⟩  City ⟨n⟩ x "), "Victim name⟨s⟩City⟨n⟩x")


class ProbeTest(unittest.TestCase):
    def test_probe_hand_written(self):
        seq = "<s>Victim name⟨s⟩Victim status⟨n⟩John Doe⟨s⟩Injured⟨n⟩Jane Smith⟨m⟩J. Smith⟨s⟩ ⟨n⟩</s>"
        headers, values = probe_sequence(seq)
        self.assertEqual(headers, ["Victim name", "Victim status"])
        self.assertEqual(values, ["John Doe", "Injured", "Jane Smith", "J. Smith"])

    def test_probe_header_only(self):
        self.assertEqual(probe_sequence("Period⟨s⟩High temperature"), (["Period", "High temperature"], []))

    def test_probe_keeps_angle_brackets_in_text(self):
        _, values = probe_sequence("Wind⟨n⟩gusts <30 mph> later")
        self.assertEqual(values, ["gusts <30 mph> later"])


class PreviewForSchemaTest(unittest.TestCase):
    SCHEMA = ["Victim name", "Victim status", "City"]

    def test_filters_headers_and_their_values(self):
        seq = ("victim  NAME⟨s⟩Weapon⟨s⟩Victim status"
               "⟨n⟩John Doe⟨s⟩handgun⟨s⟩Injured"
               "⟨n⟩Jane Smith⟨m⟩J. Smith⟨s⟩rifle⟨s⟩")
        headers, values = preview_for_schema(seq, self.SCHEMA)
        self.assertEqual(headers, ["Victim name", "Victim status"])
        self.assertEqual(values, ["John Doe", "Injured", "Jane Smith", "J. Smith"])

    def test_cells_without_header_and_empty_header_dropped(self):
        seq = "⟨s⟩City⟨n⟩junk⟨s⟩Tulsa⟨s⟩extra"
        self.assertEqual(preview_for_schema(seq, self.SCHEMA), (["City"], ["Tulsa"]))

    def test_no_schema_match(self):
        self.assertEqual(preview_for_schema("Weapon⟨n⟩rifle", self.SCHEMA), ([], []))

    def test_duplicate_headers_once(self):
        headers, values = preview_for_schema("City⟨s⟩city⟨n⟩Tulsa⟨s⟩Tulsa", self.SCHEMA)
        self.assertEqual(headers, ["City"])
        self.assertEqual(values, ["Tulsa", "Tulsa"])


class MissingRowSeparatorTest(unittest.TestCase):
    def test_header_row_recovered_from_attribute_names(self):
        seq = "Hotel name⟨s⟩Taxi type⟨s⟩Acorn⟨s⟩blue"
        vocab = ["Hotel name", "Taxi type", "Hotel area"]
        # Taxi type is hidden at this level: its value is filtered out with it.
        self.assertEqual(preview_for_schema(seq, ["Hotel name", "Hotel area"], vocab),
                         (["Hotel name"], ["Acorn"]))
        self.assertEqual(preview_for_schema(seq, ["Hotel name"]), (["Hotel name"], []))


class DataTest(unittest.TestCase):
    def test_drop_hidden(self):
        table = drop_hidden(TABLE, {"victim status", "city"})
        self.assertEqual(table, {"headers": ["Victim name"],
                                 "rows": [[["John Doe"]], [["Jane Smith", "J. Smith"]]]})
        only_status = drop_hidden({"headers": ["A", "B"], "rows": [["x", ""], ["", "y"]]}, {"b"})
        self.assertEqual(only_status["rows"], [["x"]])

    def test_load_hidden_layouts(self):
        with tempfile.TemporaryDirectory() as d:
            for i, data in enumerate([
                {"1": ["City"], "2": ["City", "Hospital"]},
                {"levels": {"2": {"hidden": ["city", "HOSPITAL"]}}},
                [{"level": 2, "hidden": ["City", "Hospital"]}],
            ]):
                path = Path(d) / f"levels{i}.json"
                path.write_text(json.dumps(data), encoding="utf8")
                self.assertEqual(load_hidden(path, 2), {"city", "hospital"})

    def test_length_batches(self):
        lengths = [5, 1, 4, 2, 3, 6, 7]
        self.assertEqual(length_batches(lengths, 3), [[1, 3, 4], [2, 0, 5], [6]])
        batches = length_batches(lengths, 2, random.Random(0))
        self.assertEqual(sorted(i for b in batches for i in b), list(range(7)))


if __name__ == "__main__":
    unittest.main()
