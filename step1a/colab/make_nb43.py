"""python colab/make_nb43.py .  (from step1a/). Builds colab/S1A_wf43_colab.ipynb (wf_v4.3, diary Nov 13: U0, U2, U4 with Llama-3.1-8B) from the
Nov 16 notebook's setup cells (same install, model load and backend), like make_nb42.py."""
import json
import sys
from pathlib import Path

step1a = Path(sys.argv[1])
src = json.loads((step1a / "colab" / "S1A_nov16_v41_colab.ipynb").read_text(encoding="utf-8"))
cells = src["cells"]


def text(c):
    return "".join(c["source"])


def cell(kind, s):
    c = {"cell_type": kind, "metadata": {}, "source": s.splitlines(keepends=True)}
    if kind == "code":
        c.update(execution_count=None, outputs=[])
    return c


intro = """# wf_v4.3 real runs with Llama (diary Nov 13): the 8B design
Code: GitHub `TriDang2025/attribute-extraction`, branch `wf-v4.3` (from `wf-v4.2-llama`), folder `step1a/`. Results in `results/wf_v43/`.

Model: Llama-3.1-8B-Instruct, bf16, vLLM, temperature 0, guided JSON from each job's schema (setting `llama8b`). Runtime: **A100 (40 GB or more)**.
Idea: Llama gets small, closed questions; code does the bookkeeping. Prompts of U0 and U2 were built on the laptop and are in the branch.

- Cells 1-5: setup (as the Nov 16 / wf_v4.2 notebooks).
- Cell 6: data check (bge-m3 vectors and GT files the post steps need).
- Cell 7: **U0** baseline: frozen split pass -> reconcile -> duplicate check on the wf_v4.2 option B A answers, then the L2 score. About 160 calls, about 5 min (estimate).
- Cell 8: **U2** Step 3 v4.3: one name per cluster, batches of 5, 3 orders + vote, worked examples, then the same post steps; writes the Step 4 input `a_llama43`. About 300 calls, about 10-15 min (estimate).
- Cell 9: **U4** Step 4 v4.3 on inputs a, c1 and a_llama43 (dev50 + dev50b, seeds 0-2, 18 chains; at most 38 short calls per chain), then assemble and score. About 20-30 min (estimate).
- Each cell commits and pushes its results folder. If time runs short, the order of priority is cell 7, 8, then 9.
- After a crash or disconnect: rerun cells 1, 3, 4, 5 and then the cell you were on. Answered calls are read from the cache.
- Colab Secrets `HF_TOKEN` and `GH_TOKEN`, notebook access on. Never put a token in a cell.
- When the GPU work is done: **Runtime > Disconnect and delete runtime**, so the paid GPU stops.
"""
c1 = text(cells[1]).replace('BRANCH = "wf-v4.1"', 'BRANCH = "wf-v4.3"').replace("clone/pull wf-v4.1", "clone/pull wf-v4.3")
c3 = text(cells[4]).replace('SETTING = "qwen32b"  #@param ["qwen32b", "llama8b"]', 'SETTING = "llama8b"  #@param ["llama8b"]')
c5 = text(cells[6]).replace(" (gpu_memory_utilization leaves room for GLiNER and bge-m3 of loop 2)", " (gpu_memory_utilization leaves room for GLiNER and bge-m3 of loop 2, T6)") \
    .replace("TAG = SETTING   # run folder results/wf_v41/nov16/<TAG>\n", "").replace("#@title 5. Load", "#@title 4. Load")
assert c1 != text(cells[1]) and c3 != text(cells[4]), "Nov 16 notebook cells changed: update this generator"
push = """p = subprocess.run(["bash", "colab/sync.sh", "push-results", "{msg}", "{sub}"], capture_output=True, text=True)
print(p.stdout.strip() or p.stderr[-500:])
"""
data = """#@title 6. Data check: bge-m3 vectors (reconcile) and GT levels (score)
from pathlib import Path
need = ["results/graph_v22_dev50/spans/vectors.npz", "results/graph_v22_dev50b/spans/vectors.npz",
        "results/loop1_v35/gt_levels.csv", "results/loop1_v37/dev50b/gt/gt_levels.csv",
        "results/wf_v43/u0/manifest.json", "results/wf_v43/u2/manifest.json"]
missing = [p for p in need if not Path(p).exists()]
print("missing:", missing or "none")
assert not missing, "files missing: stop and tell Claude"
"""
u0 = """#@title 7. U0: frozen Step 3 post steps on Llama option B answers (split -> reconcile -> dupcheck), then the L2 score
import sys, subprocess
sys.path.insert(0, "/content/attribute-extraction/step1a/scripts")
import u0_step3_post_v43 as U0
print(U0.run(U0.OUT, backend))
!python scripts/u0_step3_post_v43.py --score
""" + push.format(msg="wf_v43 U0 step3 post", sub="wf_v43/u0") + """print("U0 done")
"""
u2 = """#@title 8. U2: Step 3 v4.3 (names in batches of 5, 3 orders + vote, examples, post steps); writes a_llama43
import sys, subprocess
sys.path.insert(0, "/content/attribute-extraction/step1a/scripts")
import u2_step3_v43 as U2
print(U2.run(U2.OUT, backend))
res, sizes = U2.score_all(U2.OUT)
print("a_llama43:", sizes)
print((U2.OUT / "scores" / "summary.md").read_text(encoding="utf-8")[:3000])
""" + push.format(msg="wf_v43 U2 step3 v43", sub="wf_v43/u2") + """print("U2 done")
"""
u4 = """#@title 9. U4: Step 4 v4.3 on a, c1, a_llama43 (18 chains), assemble all, score
import subprocess
from pathlib import Path
from s1a import step4_v43 as S
for inp in S.INPUTS:                      # a, c1, a_llama43 (priority order); a_llama43 needs cell 8
    print(inp, S.run(S.OUT, backend, inputs=(inp,)))
    p = subprocess.run(["bash", "colab/sync.sh", "push-results", f"wf_v43 U4 step4 v43 {inp}", "wf_v43/u4"], capture_output=True, text=True)
    print(p.stdout.strip() or p.stderr[-500:])
S.assemble_all(S.OUT, S.make_chains(S.INPUTS), S.ROOT)     # final/ and repairs.json over all 18 chains
r = subprocess.run(["python", "scripts/u4_step4_v43.py", "--score", "--out", "results/wf_v43/u4"], capture_output=True, text=True)
print(r.stdout[-3000:] or r.stderr[-1500:])
""" + push.format(msg="wf_v43 U4 scores", sub="wf_v43/u4") + """print("U4 done: tell Claude 'wf_v4.3 run done'")
"""
nb = dict(src)
nb["cells"] = [cell("markdown", intro), cell("code", c1), cells[2], cells[3], cell("code", c3), cell("code", c5),
               cell("code", text(cells[7]).replace("#@title 6. Backend", "#@title 5. Backend")),
               cell("code", data), cell("code", u0), cell("code", u2), cell("code", u4)]
out = step1a / "colab" / "S1A_wf43_colab.ipynb"
out.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print("wrote", out, len(nb["cells"]), "cells")
