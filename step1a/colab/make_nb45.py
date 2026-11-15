"""python colab/make_nb45.py .  (from step1a/). Builds colab/S1A_wf45_colab.ipynb (wf_v4.5, diary Nov 15) from the wf_v4.4 notebook's setup
cells (same install, model load, backend; branch wf-v4.5, load time to results/wf_v45/model_load.json). Run cells: W1 Step 4 confirm run."""
import json
import sys
from pathlib import Path

step1a = Path(sys.argv[1])
src = json.loads((step1a / "colab" / "S1A_wf44_colab.ipynb").read_text(encoding="utf-8"))
cells = src["cells"]


def text(c):
    return "".join(c["source"])


def cell(kind, s):
    c = {"cell_type": kind, "metadata": {}, "source": s.splitlines(keepends=True)}
    if kind == "code":
        c.update(execution_count=None, outputs=[])
    return c


intro = """# wf_v4.5 runs with Llama (diary Nov 15): freeze, end to end, cost test
Code: GitHub `TriDang2025/attribute-extraction`, branch `wf-v4.5` (from `wf-v4.4`), folder `step1a/`. Results in `results/wf_v45/`.

Model: Llama-3.1-8B-Instruct, bf16, vLLM, temperature 0, guided JSON (setting `llama8b`). Runtime: **A100 (40 GB or more)**.

- Cells 1-5: setup (as the wf_v4.4 notebook; cell 4 logs the loading time to `results/wf_v45/model_load.json`).
- Cell 6: data check.
- Cell 7: **W1** Step 4 v4.4 with "other" off on a_llama44 then c1 (dev50 + dev50b, seeds 0-2 + vote), score, freeze check. About 70 calls, 10-20 min (estimate).
- After a crash or disconnect: rerun cells 1, 3, 4, 5 and then the cell you were on. Answered calls are read from the cache.
- Colab Secrets `HF_TOKEN` and `GH_TOKEN`, notebook access on. Never put a token in a cell.
- When the GPU work is done: **Runtime > Disconnect and delete runtime**, so the paid GPU stops.
"""
c1 = text(cells[1]).replace("wf-v4.4", "wf-v4.5")
c4 = text(cells[5]).replace("results/wf_v44/model_load.json", "results/wf_v45/model_load.json").replace(" of T4", "")
assert c1 != text(cells[1]) and c4 != text(cells[5]), "wf_v4.4 notebook cells changed: update this generator"
data = text(cells[7]).replace('"results/wf_v42/t1b_step3_keyed/manifest.json", "results/wf_v43/u2/manifest.json",',
                              '"results/wf_v44/t4/a_llama44/dev50/a.columns.json", "results/wf_v44/t4/a_llama44/dev50b/a.columns.json",')
assert data != text(cells[7]), "wf_v4.4 data cell changed: update this generator"
w1 = """#@title 7. W1: Step 4 v4.4 with "other" off (a_llama44, c1), score, freeze check -> results/wf_v45/w1
import sys, subprocess
sys.path.insert(0, "/content/attribute-extraction/step1a/scripts")
import w1_step4_v45 as W1
for inp in W1.INPUTS:
    print(inp, W1.run(backend, inputs=(inp,))[inp])
    p = subprocess.run(["bash", "colab/sync.sh", "push-results", f"wf_v45 W1 step4 other off {inp}", "wf_v45/w1"], capture_output=True, text=True)
    print(p.stdout.strip() or p.stderr[-500:])
W1.T6.score(W1.OUT)
print(W1.write_freeze(W1.OUT))
p = subprocess.run(["bash", "colab/sync.sh", "push-results", "wf_v45 W1 scores", "wf_v45"], capture_output=True, text=True)
print(p.stdout.strip() or p.stderr[-500:])
print("W1 done: disconnect the runtime, then tell Claude 'W1 done'")
"""
nb = dict(src)
nb["cells"] = [cell("markdown", intro), cell("code", c1), cells[2], cells[3], cells[4], cell("code", c4), cells[6], cell("code", data), cell("code", w1)]
out = step1a / "colab" / "S1A_wf45_colab.ipynb"
out.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print("wrote", out, len(nb["cells"]), "cells")
