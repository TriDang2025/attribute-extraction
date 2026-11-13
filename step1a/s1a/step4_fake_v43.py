"""wf_v4.3 U3: the no-GPU stand-in for the Step 4 v4.3 calls (s1a/step4_v43.py). Same job interface as nov16_v41.FakeLLM (run(out, jobs)); each
answer is built from the job's prompt and guided schema only, so it is always valid for the schema.

p1: one table name per heading of the column block, plus "extra" when there are two or more headings (so the pair calls see k + 1 tables);
p2: each column to the table named like its heading (else the first table), every 5th to "extra"; every 7th column "unused" (exercises the unused path);
pair: option chosen by a checksum of the table pair (covers none, both directions and many_to_many);
key: the first column id, or "new" with a made-up name on even checksums; each reference "new".
"""
import json
import re

from . import nov16_v41 as NV
from .step4_v43 import NEW, UNUSED


def _sum(text):
    return sum(ord(c) for c in text)


class FakeV43(NV.FakeLLM):
    def respond(self, job, prompt, schema):
        self.n_made += 1
        fmt, props = job["format"], schema.get("properties", {})
        if fmt == "s43_p1":
            heads = list(dict.fromkeys(re.findall(r"^== (\S+) ==$", prompt, re.M)))
            names = [re.sub(r"[^a-z0-9_]", "_", h.lower()) for h in heads] + (["extra"] if len(heads) > 1 else [])
            return json.dumps({"tables": names[:props["tables"]["maxItems"]]})
        if fmt == "s43_p2":
            enum = next(iter(props.values()))["enum"]
            ent = {}
            for h, block in re.findall(r"^== (\S+) ==$\n((?:(?!^== ).*\n?)*)", prompt, re.M):
                for cid in re.findall(r"^\[(\S+)\]", block, re.M):
                    ent[cid] = h.lower()
            out = {}
            for n, cid in enumerate(props):
                if n % 7 == 6:
                    out[cid] = UNUSED
                elif n % 5 == 4 and "extra" in enum:
                    out[cid] = "extra"
                else:
                    out[cid] = ent.get(cid) if ent.get(cid) in enum else enum[0]
            return json.dumps(out)
        if fmt == "s43_pair":
            opts = props["link"]["enum"]
            return json.dumps({"link": opts[_sum("".join(opts)) % len(opts)]})
        if fmt == "s43_key":
            ids = props["primary_key"]["enum"]
            even = _sum(ids[0]) % 2 == 0
            ans = {"primary_key": NEW if even else ids[0], "new_id_name": "made up key" if even else ""}
            if "foreign_keys" in props:
                ans["foreign_keys"] = {r: NEW for r in props["foreign_keys"]["properties"]}
            return json.dumps(ans)
        raise ValueError(f"unknown format {fmt!r}")
