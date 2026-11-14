"""wf_v4.4 T5: the no-GPU stand-in for the Step 4 v4.4 calls (s1a/step4_v44.py). FakeV44 extends step4_fake_v43.FakeV43 (the s43_* formats are answered
as there, so a run with every switch off is the v4.3 fake run); each answer is built from the job's guided schema only, so it is always valid.

s44_p1: one extra table "extra" (when the schema allows at least one name), else an empty list;
s44_p2: hint form (options "keep", "move to ..", third): every column "keep"; every 5th "move to" the first other table; every 7th the third option.
        plain form (enum of table names + "other"): every column to the first table, every 5th to the last table, every 7th "other";
s44_pair: the option "none" for a checksum of the pair that is even, else the first link option (both directions occur over pairs);
s44_key: primary key "none" for an even checksum of the first candidate, else that candidate; a key name; every reference "new".
"""
import json

from . import step4_fake_v43 as F43
from .step4_v43 import NEW


def _sum(text):
    return sum(ord(c) for c in text)


class FakeV44(F43.FakeV43):
    def respond(self, job, prompt, schema):
        fmt, props = job["format"], schema.get("properties", {})
        if not fmt.startswith("s44_"):
            return super().respond(job, prompt, schema)
        self.n_made += 1
        if fmt == "s44_p1":
            return json.dumps({"tables": ["extra"][:props["tables"]["maxItems"]]})
        if fmt == "s44_p2":
            out = {}
            for n, (cid, p) in enumerate(props.items()):
                enum = p["enum"]
                if "keep" in enum:
                    moves = [o for o in enum if o.startswith("move to ")]
                    out[cid] = enum[-1] if n % 7 == 6 else (moves[0] if n % 5 == 4 and moves else "keep")
                else:
                    out[cid] = enum[-1] if n % 7 == 6 else (enum[-2] if n % 5 == 4 else enum[0])
            return json.dumps(out)
        if fmt == "s44_pair":
            opts = props["link"]["enum"]
            return json.dumps({"link": opts[0] if _sum("".join(opts)) % 2 == 0 else opts[1 + _sum(opts[1]) % (len(opts) - 1)]})
        if fmt == "s44_key":
            enum = props["primary_key"]["enum"]
            first = enum[0]
            ans = {"primary_key": "none" if first == "none" or _sum(first) % 2 == 0 else first,
                   "new_id_name": "made up key" if first == "none" or _sum(first) % 2 == 0 else ""}
            if "foreign_keys" in props:
                ans["foreign_keys"] = {r: NEW for r in props["foreign_keys"]["properties"]}
            return json.dumps(ans)
        raise ValueError(f"unknown format {fmt!r}")
