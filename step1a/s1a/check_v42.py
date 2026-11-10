"""wf_v4.2 (diary Nov 10): check of a job folder answered on Colab (T0 smoke test, T1 Step 3 rerun). Reads only; no LLM.

check_rows(out): one row per manifest job of <out>: parse errors, guided, finish reason, tokens, seconds, and for Step 3 A answers
(format v2) the cluster rows written vs expected and the most repeated cluster id (the T0 failure: one id written until max_tokens).
"""
import collections
import json
import re
from pathlib import Path

from . import batch_v4 as B

COLS = ["job", "answered", "parse_errors", "guided", "retried", "finish", "prompt_tokens", "output_tokens", "batch_seconds",
        "clusters_expected", "cluster_rows", "distinct_ids", "top_id", "top_id_rows"]
_CLUSTER_ID = re.compile(r'"cluster_id"\s*:\s*"([^"]+)"')


def a_stats(raw, schema):
    """Cluster rows of a Step 3 A answer (raw text, so a cut-off answer counts too) against the schema's cluster ids."""
    ids = _CLUSTER_ID.findall(raw)
    top = collections.Counter(ids).most_common(1)
    expected = schema["properties"]["clusters"]["items"]["properties"]["cluster_id"]["enum"]
    return {"clusters_expected": len(expected), "cluster_rows": len(ids), "distinct_ids": len(set(ids)),
            "top_id": top[0][0] if top else "", "top_id_rows": top[0][1] if top else 0}


def check_rows(out):
    out, rows = Path(out), []
    for j in B.read_json(out / "manifest.json")["jobs"]:
        r = B.last_row(out / "responses" / f"{j['job']}.jsonl")
        row = dict.fromkeys(COLS, "")
        row.update(job=j["job"], answered=r is not None)
        if r is not None:
            row.update(parse_errors=len(r["errors"]), guided=r.get("guided"), retried=bool(r.get("retried")), finish=r.get("finish_reason"),
                       prompt_tokens=r.get("prompt_tokens"), output_tokens=r.get("output_tokens"), batch_seconds=r.get("batch_seconds"))
            if j["format"] == "v2":
                row.update(a_stats(r["raw"], json.loads((out / j["schema"]).read_text(encoding="utf-8"))))
        rows.append(row)
    return rows


def ok(row):
    return row["answered"] and row["parse_errors"] == 0


def check_md(title, rows):
    n_ok = sum(map(ok, rows))
    lines = [f"# {title}", "", f"Parsed without errors: **{n_ok}/{len(rows)}**", "",
             "| " + " | ".join(COLS) + " |", "|" + "---|" * len(COLS)]
    lines += ["| " + " | ".join(str(r[c]) for c in COLS) + " |" for r in rows]
    return "\n".join(lines) + "\n"


def write_check(out, title):
    """Writes <out>/check.md and check.csv; returns (rows, all ok)."""
    rows = check_rows(out)
    B.write(Path(out) / "check.md", check_md(title, rows))
    B.write(Path(out) / "check.csv", ",".join(COLS) + "\n" + "".join(",".join(str(r[c]) for c in COLS) + "\n" for r in rows))
    return rows, all(map(ok, rows))
