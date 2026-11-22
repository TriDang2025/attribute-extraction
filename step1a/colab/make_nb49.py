"""python colab/make_nb49.py .  (from step1a/). Builds colab/S1A_wf49_colab.ipynb (wf_v4.9 V3, variant AR) from the wf_v4.8 notebook: a GPU assert cell
first (A100 40 GB or larger), then the same setup cells (branch wf-v4.9, results/wf_v49/, batch-invariant vLLM, Llama-3.1-8B setting llama8b, engine
seed 0), then scripts/gpu_v49.py w3 = Step 4 variant AR (A + p2_reask), seeds 0-2, dev50 and dev50b (6 chains), MAX_CALLS guard, push, settings.json."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nbtools import cell, read_cells, swap, text, write_notebook  # noqa: E402

step1a = Path(sys.argv[1])
src = step1a / "colab" / "S1A_wf48_colab.ipynb"
v48 = read_cells(src)

intro = """# wf_v4.9 GPU session (diary Nov 22, task V3): Step 4 variant AR (A + re-ask)
Code: GitHub `TriDang2025/attribute-extraction`, branch `wf-v4.9` (must be pushed before this run), folder `step1a/`. Results in `results/wf_v49/v3/<set>/step4_AR/`.

Model: Llama-3.1-8B-Instruct, bf16, vLLM, temperature 0, guided JSON (setting `llama8b`), batch-invariant mode on, engine seed 0 (as wf_v4.8).
Runtime: **A100 (40 GB or more)**; cell 0 checks it. **One short GPU session**: model load about 4 min, then a few minutes of model time.

- Step 4 v4.3 on the same loop 1 + 2 input as wf_v4.8 W3 (`results/wf_v49/v3/<set>/input/`, from git), seeds 0-2, dev50 and dev50b = 6 chains.
  **AR** = pass 2 in batches of 20 (variant A) + `p2_reask`: a batch that sends at least half of one entity's columns to "unused" while pass 1 made
  a table for that entity is asked once more (job `<chain>_p2_b<k>_r1`, run_tag `<chain>_r1`); the second answer is kept.
- Cell 0: GPU check. Cells 1-6: setup, as in wf_v4.8. Cell 2 installs, then restart the session, rerun cells 0-1 and skip cell 2.
  Cell 3 (models) must run before any other cell imports `s1a`.
- Cell 7: data check. Cell 8: **AR** (pushes the results). Cell 9: vLLM settings + GPU session time, then
  **Runtime > Disconnect and delete runtime**, and tell Claude "GPU done".
- After a crash: rerun cells 0-1, 3-7 and cell 8 (answered calls are cached per chain folder).
- Colab Secrets `HF_TOKEN` and `GH_TOKEN`, notebook access on. Never put a token in a cell.
"""
gpu = '''#@title 0. GPU check: nvidia-smi, assert an A100 with 40 GB or more
import re, subprocess
smi = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"], capture_output=True, text=True)
print(smi.stdout.strip() or smi.stderr.strip())
assert smi.returncode == 0 and smi.stdout.strip(), "no GPU: set the runtime type to A100"
name, mib = [x.strip() for x in smi.stdout.splitlines()[0].split(",")]
assert re.search(r"A100|H100|H200|B200", name) and int(mib) >= 40000, f"need an A100 with 40 GB or more, got {name} {mib} MiB"
print("GPU ok:", name, mib, "MiB")
'''
clone = swap(text(v48[1]), [("wf-v4.8", "wf-v4.9")], "clone cell")
load = swap(text(v48[6]), [("results/wf_v48/model_load.json", "results/wf_v49/model_load.json")], "model load cell")
data = swap(text(v48[8]), [("W3 inputs", "V3 inputs"), ("gpu_v48", "gpu_v49"), ("G.VARIANTS", '("AR",)')], "data check cell")
w3 = """#@title 8. V3: Step 4 variant AR (A + re-ask), seeds 0-2, dev50 and dev50b -> results/wf_v49/v3/<set>/step4_AR
MAX_CALLS = 120  #@param {type:"integer"}
import json, subprocess
from s1a import log_v44 as L44
res = G.w3(backend)
for (var, dev), rows in res.items():
    folder = G.OUT / dev / f"step4_{var}"
    calls = len(L44.call_rows(folder))
    reasks = sum(x["repair_kinds"].get("p2_reask", 0) for x in rows)
    print(var, dev, [(x["seed"], x["ok"], x["tables"], x["error"]) for x in rows], "| calls", calls, "| re-asks used", reasks)
    assert calls <= MAX_CALLS, f"{var} {dev}: more calls than MAX_CALLS: stop and tell Claude"
p = subprocess.run(["bash", "colab/sync.sh", "push-results", "wf_v49 V3 Step 4 variant AR", "wf_v49"], capture_output=True, text=True)
print(p.stdout.strip() or p.stderr[-500:])
"""
end = swap(text(v48[10]), [("wf_v48", "wf_v49"), ("results/wf_v49/w3/settings.json", "results/wf_v49/v3/settings.json"),
                           ("wf_v49 W3 settings", "wf_v49 V3 settings"),
                           ('"temperature": 0,', '"temperature": 0, "model": MODEL, "revision": REVISION, "reasks": {f"{d}": sum(x["repair_kinds"].get("p2_reask", 0) for x in rows) for (v, d), rows in res.items()},')],
           "settings cell").replace("#@title 9. vLLM settings, GPU session time -> results/wf_v49/w3/settings.json", "#@title 9. vLLM settings, GPU session time -> results/wf_v49/v3/settings.json")
cells = [cell("markdown", intro), cell("code", gpu), cell("code", clone), *v48[2:6], cell("code", load), v48[7], cell("code", data), cell("code", w3),
         cell("code", end)]
out = step1a / "colab" / "S1A_wf49_colab.ipynb"
write_notebook(src, cells, out)
print("wrote", out, len(cells), "cells")
