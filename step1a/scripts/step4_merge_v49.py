"""wf_v4.9 B+M (no model calls): the cached v4.8 variant B (results/wf_v48/w3/<set>/step4_B, read only) with the same-entity tables joined
(s1a/step4_merge_v49.py, applied by step4_v44.assemble_all) -> results/wf_v49/v3/<set>/step4_BM/ with the layout of step4_B (final/, score_map/,
chains.json, responses/ copied so the token counts are those of B, manifests/, prompts/). final/status.json rows get `merged`; final/<chain>/merges.json
= that chain's merges. Run: python scripts/step4_merge_v49.py   (prints tables before / after per chain)."""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import gpu_v48 as G48  # noqa: E402
from s1a import batch_v4 as B  # noqa: E402
from s1a import step4_v44 as S4  # noqa: E402

OUT = ROOT / "results" / "wf_v49" / "v3"


def merge_variant(src, dst, root=ROOT):
    """Copy the Step 4 folder `src` to `dst` (without final/) and rebuild final/ with merge_same_entity on. Returns the status rows."""
    src, dst = Path(src), Path(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("final"), dirs_exist_ok=True)
    chains = [{**c, "merge_same_entity": True} for c in B.read_json(src / "chains.json")]
    B.write_json(dst / "chains.json", chains)
    status = S4.assemble_all(dst, chains, root)
    for r in status:
        B.write_json(dst / "final" / r["run"] / "merges.json", r.get("merged", []))
    return status


def main():
    for dev in G48.SETS:
        before = {r["run"]: r for r in B.read_json(G48.OUT / dev / "step4_B" / "final" / "status.json")}
        for r in merge_variant(G48.OUT / dev / "step4_B", OUT / dev / "step4_BM"):
            print(dev, r["run"], f"tables {before[r['run']]['tables']} -> {r['tables']}", r.get("merged"))


if __name__ == "__main__":
    main()
