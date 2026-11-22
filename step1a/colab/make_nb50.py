"""python colab/make_nb50.py .  (from step1a/). Builds colab/S1A_wf50_colab.ipynb (wf_v5.0 G4 + G5) from the wf_v4.9 notebook: the same GPU check and
setup cells (branch wf-v5.0, results/wf_v50/, batch-invariant vLLM, Llama-3.1-8B setting llama8b, engine seed 0), then scripts/gpu_v50.py:
G4 rename (3 calls), the Step 4 input build (CPU, laptop vectors), G5 Step 4 variant ARM seeds 0-2 on dev50 and dev50b, push, settings.json."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nbtools import cell, read_cells, swap, text, write_notebook  # noqa: E402

step1a = Path(sys.argv[1])
src = step1a / "colab" / "S1A_wf49_colab.ipynb"
v49 = read_cells(src)

intro = """# wf_v5.0 GPU session (diary Nov 23, tasks G4 + G5)
Code: GitHub `TriDang2025/attribute-extraction`, branch `wf-v5.0` (must be pushed before this run), folder `step1a/`. Results in `results/wf_v50/`.

Model: Llama-3.1-8B-Instruct, bf16, vLLM, temperature 0, guided JSON (setting `llama8b`), batch-invariant mode on, engine seed 0 (as wf_v4.9).
Runtime: **A100 (40 GB or more)**; cell 0 checks it. **One short GPU session**: model load about 4 min, then a few minutes of model time.

- **G4** (cell 8): the loop-1 columns that the G3 context split changed get a new name from the frozen Step 3 names prompt (3 calls:
  dev50 train 4 columns, dev50b train 2 + hotel 3). Prompts are in git (`results/wf_v50/g4/<set>/prompts/`).
- **Input build** (cell 9, CPU): the loop-1 Step 4 input and the wf_v4.8 W2 loop-2 replay on the new columns, with the bge-m3 vectors computed on
  the laptop (`g4/<set>/w2_vectors.npz`), so the replay is the laptop one. Writes `results/wf_v50/g5/<set>/input/`.
- **G5** (cell 10): Step 4 variant **ARM** = A (pass 2 in batches of 20) + re-ask r1 (v4.9) + re-ask r2 (a batch whose r1 answer still sends half
  of an entity's columns to "unused" is asked once more with a second note) + same-entity table merge (B+M, code), seeds 0-2, dev50 and dev50b
  = 6 chains -> `results/wf_v50/g5/<set>/step4_ARM/`.
- Cells 1-6: setup, as in wf_v4.9. Cell 2 installs, then restart the session, rerun cells 0-1 and skip cell 2.
  Cell 3 (models) must run before any other cell imports `s1a`.
- Cell 11: vLLM settings + GPU session time, then **Runtime > Disconnect and delete runtime**, and tell Claude "GPU done".
- After a crash: rerun cells 0-1, 3-7 and the cell that failed (answered calls are cached per folder).
- Colab Secrets `HF_TOKEN` and `GH_TOKEN`, notebook access on. Never put a token in a cell.
"""
clone = swap(text(v49[2]), [("wf-v4.9", "wf-v5.0")], "clone cell")
load = swap(text(v49[7]), [("results/wf_v49/model_load.json", "results/wf_v50/model_load.json")], "model load cell")
data = """#@title 7. Data check: G4 jobs, laptop vectors, G3 columns and the loop-1 run files (git)
import sys
sys.path.insert(0, "/content/attribute-extraction/step1a/scripts")
import gpu_v50 as G
need = [G.G4 / d / f for d in G.SETS for f in ("manifest_names.json", "changed.json", "w2_vectors.npz", "prompts")]
need += [G.G3_FINAL / d / "final_columns.json" for d in G.SETS] + [G.LOOP1 / d / "loop2" for d in G.SETS]
need += [G.Y3 / d / f for d in G.SETS for f in ("entities.json", "a_prompts")]
missing = [str(p) for p in need if not p.exists()]
print("missing:", missing or "none")
assert not missing, "files missing: stop and tell Claude"
print({v: G.G48.config(v) for v in ("ARM",)})
"""
g4 = """#@title 8. G4: rename the columns the context split changed (3 calls) -> results/wf_v50/g4/<set>/{responses/, renames.csv}
import subprocess
ren = G.g4(backend)
for dev, rows in ren.items():
    print(dev, [(r["entity"], r["cid"], r["old"], "->", r["new"]) for r in rows])
p = subprocess.run(["bash", "colab/sync.sh", "push-results", "wf_v50 G4 renames", "wf_v50"], capture_output=True, text=True)
print(p.stdout.strip() or p.stderr[-500:])
"""
inputs = """#@title 9. Step 4 input build (CPU, laptop vectors) -> results/wf_v50/g4/w2/<set>/, results/wf_v50/g5/<set>/input/
import json
paths = G.build_inputs(G.CachedEnc())
for dev, p in paths.items():
    cols = json.loads(p.read_text(encoding="utf-8"))
    print(dev, p, len(cols), "columns")
"""
g5 = """#@title 10. G5: Step 4 variant ARM, seeds 0-2, dev50 and dev50b -> results/wf_v50/g5/<set>/step4_ARM
MAX_CALLS = 140  #@param {type:"integer"}
import subprocess
from s1a import log_v44 as L44
res = G.g5(backend)
for (var, dev), rows in res.items():
    folder = G.G5 / dev / f"step4_{var}"
    calls = len(L44.call_rows(folder))
    kinds = {k: sum(x["repair_kinds"].get(k, 0) for x in rows) for k in ("p2_reask", "p2_reask2", "p2_reask_failed", "p2_reask2_failed")}
    print(var, dev, [(x["seed"], x["ok"], x["tables"], x["error"]) for x in rows], "| calls", calls, "| re-asks", kinds)
    assert calls <= MAX_CALLS, f"{var} {dev}: more calls than MAX_CALLS: stop and tell Claude"
p = subprocess.run(["bash", "colab/sync.sh", "push-results", "wf_v50 G5 Step 4 variant ARM", "wf_v50"], capture_output=True, text=True)
print(p.stdout.strip() or p.stderr[-500:])
"""
end = swap(text(v49[11]), [("wf_v49 V3 settings", "wf_v50 G4+G5 settings"), ("results/wf_v49/v3/settings.json", "results/wf_v50/settings.json"),
                           ("results/wf_v49/model_load.json", "results/wf_v50/model_load.json"), ('"wf_v49"]', '"wf_v50"]'),
                           ("#@title 9. vLLM settings", "#@title 11. vLLM settings"),
                           ('"reasks": {f"{d}": sum(x["repair_kinds"].get("p2_reask", 0) for x in rows) for (v, d), rows in res.items()}',
                            '"reasks": {f"{d}": {k: sum(x["repair_kinds"].get(k, 0) for x in rows) for k in ("p2_reask", "p2_reask2")} for (v, d), rows in res.items()}, '
                            '"renamed": {d: sum(r["renamed"] for r in rows) for d, rows in ren.items()}')],
           "settings cell")
cells = [cell("markdown", intro), v49[1], cell("code", clone), *v49[3:7], cell("code", load), v49[8], cell("code", data), cell("code", g4),
         cell("code", inputs), cell("code", g5), cell("code", end)]
out = step1a / "colab" / "S1A_wf50_colab.ipynb"
write_notebook(src, cells, out)
print("wrote", out, len(cells), "cells")
