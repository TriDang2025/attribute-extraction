"""wf_v4.4 (diary Nov 14) T2: keyed "exactly once" split pass on Llama (s1a/split_v44.py). v4.3: 41/54 frozen split answers did not parse.

python scripts/t2_split_v44.py --build [--out DIR]   -> DIR (default results/wf_v44/t2): the 54 keyed split prompts + schemas
                                                        (manifest_split44.json; the frozen v4.3 split jobs are copied in as the sources)
python scripts/t2_split_v44.py --fake  [--out DIR]   -> run with the fake model (laptop plumbing test only)
python scripts/t2_split_v44.py --report [--out DIR]  -> DIR/split_report.json + split_report.md from the saved answers
Notebook: `build(out)`, then `run(out, backend)` with log_v44.VllmBackend44, then `report(out)`; target: parse errors <= 5 of 54.
The split prompts do not depend on the names (they are the v4.3 split jobs), so this is the v4.3 split set with the keyed schema.
The assembled frozen-format answers are written to DIR/responses/<ent>_<run>_split_<cid>_r1.jsonl (what reconcile / dupcheck read).
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from s1a import batch_v4 as B  # noqa: E402
from s1a import log_v44 as LOG  # noqa: E402
from s1a import split_v44 as SP  # noqa: E402
from s1a import step3_post_v43 as PP  # noqa: E402
from s1a import step3_v44 as S  # noqa: E402

OUT = S.RES / "t2"


def build(out):
    """Copy the 54 frozen split jobs (the sources) and write the keyed jobs; returns the keyed job rows."""
    out = Path(out)
    frozen = []
    for s in PP.SETS:
        rows, _ = PP.copy_split_jobs(out, s)
        frozen += rows
    return SP.split_jobs(out, frozen)


def run(out, backend):
    """Run the keyed split jobs on `backend` and assemble the frozen-format answers; returns {"backend": info, "split": summary}."""
    info = backend.run(out, SP.read_split_jobs(out))
    return {"backend": info, "split": SP.summary(SP.assemble_split(out))}


def report(out):
    """Parse errors, retries, calls and tokens; writes split_report.{json,md}; returns the dict."""
    out = Path(out)
    res = SP.assemble_split(out)
    rows = [r for r in LOG.call_rows(out) if "_splitk_" in r["job"]]
    doc = {"jobs": res["jobs"], "answered": res["answered"], "parse_errors": res["parse_errors"], "target": "<= 5 of 54",
           "errors": res["errors"], "calls": LOG.call_totals(rows) if rows else {}, "v43_parse_errors": "41/54"}
    B.write_json(out / "split_report.json", doc)
    (out / "split_report.md").write_text(
        f"# wf_v4.4 T2: keyed split pass\n\nParse errors {doc['parse_errors']}/{doc['jobs']} (target <= 5/54; v4.3 frozen schema 41/54). "
        f"Answered {doc['answered']}. Calls {doc['calls']}.\n", encoding="utf-8", newline="\n")
    return doc


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    for k in ("build", "fake", "report"):
        g.add_argument(f"--{k}", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    if a.build:
        print(f"{len(build(a.out))} keyed split jobs in {a.out}")
    elif a.fake:
        build(a.out)
        print(run(a.out, S.FakeStep44()))
    else:
        print(report(a.out))


if __name__ == "__main__":
    main()
