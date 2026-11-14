"""python colab/make_nb44.py .  (from step1a/). Builds colab/S1A_wf44_colab.ipynb (wf_v4.4, diary Nov 14: T1, T2, T4, T6, T7 with
Llama-3.1-8B) from the Nov 16 notebook's setup cells (same install, model load and backend), like make_nb43.py. Differences: the backend
is log_v44.VllmBackend44 (keeps the guided raw text on retry, per-job seconds) and the model loading time is logged once."""
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


intro = """# wf_v4.4 real runs with Llama (diary Nov 14): last tuning before the freeze
Code: GitHub `TriDang2025/attribute-extraction`, branch `wf-v4.4` (from `wf-v4.3`), folder `step1a/`. Results in `results/wf_v44/`.

Model: Llama-3.1-8B-Instruct, bf16, vLLM, temperature 0, guided JSON from each job's schema (setting `llama8b`). Runtime: **A100 (40 GB or more)**.
Every call row keeps the guided raw text (also when the unguided retry wins) and its own seconds; the model loading time goes to `results/wf_v44/model_load.json`.

- Cells 1-5: setup (as the wf_v4.3 notebook; cell 4 also logs the loading time).
- Cell 6: data check.
- Cell 7: **T1** guided names probe: 3 jobs per schema variant, picks the first that parses 3/3 -> `t1/choice.json`. About 15 calls, 2-5 min (estimate).
- Cell 8: **T2** keyed split pass on the 54 v4.3 split jobs (target at most 5/54 parse errors). About 54 calls, about 5 min (estimate).
- Cell 9: **T4** Step 3 v4.4 (similar batches, recall rescue, duplicate merge, then split -> reconcile -> dupcheck), L2 score, writes `a_llama44`. About 400-500 calls, 25-35 min (estimate).
- Cell 10: **T6** Step 4 v4.4 on a_llama44 then c1 (dev50 + dev50b, seeds 0-2 + vote), score. 30-40 min (estimate).
- Cell 11: **T7** Step 4 on/off checks (dev50, seed 0, one change off at a time). 15-20 min (estimate).
- Cell 12: Step 3 on/off checks (each booster off, order 0). 15-25 min (estimate).
- Each cell commits and pushes its results folder. If time runs short, the order of priority is cells 7, 8, 9, 10, 11, 12.
- After a crash or disconnect: rerun cells 1, 3, 4, 5 and then the cell you were on. Answered calls are read from the cache.
- Colab Secrets `HF_TOKEN` and `GH_TOKEN`, notebook access on. Never put a token in a cell.
- When the GPU work is done: **Runtime > Disconnect and delete runtime**, so the paid GPU stops.
"""
c1 = text(cells[1]).replace('BRANCH = "wf-v4.1"', 'BRANCH = "wf-v4.4"').replace("clone/pull wf-v4.1", "clone/pull wf-v4.4")
c3 = text(cells[4]).replace('SETTING = "qwen32b"  #@param ["qwen32b", "llama8b"]', 'SETTING = "llama8b"  #@param ["llama8b"]')
c5 = text(cells[6]).replace(" (gpu_memory_utilization leaves room for GLiNER and bge-m3 of loop 2)", " (gpu_memory_utilization leaves room for bge-m3 of T4)") \
    .replace("TAG = SETTING   # run folder results/wf_v41/nov16/<TAG>\n", "").replace("#@title 5. Load", "#@title 4. Load") \
    .replace("llm = LLM(", "import time\n_t0 = time.time()\nllm = LLM(")
c5 = c5.rstrip("\n") + """
from s1a import log_v44 as L44
print("model load:", L44.save_load_time("results/wf_v44/model_load.json", time.time() - _t0, MODEL, REVISION))
"""
c6 = text(cells[7]).replace("#@title 6. Backend", "#@title 5. Backend").replace("s1a/nov16_v41.VllmBackend", "s1a/log_v44.VllmBackend44") \
    .replace("backend = NV.VllmBackend(", "from s1a import log_v44 as L44\nbackend = L44.VllmBackend44(")
assert c1 != text(cells[1]) and c3 != text(cells[4]) and "_t0" in c5 and "VllmBackend44(" in c6, "Nov 16 notebook cells changed: update this generator"
push = """p = subprocess.run(["bash", "colab/sync.sh", "push-results", "{msg}", "{sub}"], capture_output=True, text=True)
print(p.stdout.strip() or p.stderr[-500:])
"""
data = """#@title 6. Data check: bge-m3 vectors, GT levels, frozen prompts, v4.3 split jobs
from pathlib import Path
need = ["results/graph_v22_dev50/spans/vectors.npz", "results/graph_v22_dev50b/spans/vectors.npz",
        "results/loop1_v35/gt_levels.csv", "results/loop1_v37/dev50b/gt/gt_levels.csv",
        "results/wf_v42/t1b_step3_keyed/manifest.json", "results/wf_v43/u2/manifest.json",
        "config/wf_v44_step3.json", "config/wf_v44_step4.json"]
missing = [p for p in need if not Path(p).exists()]
print("missing:", missing or "none")
assert not missing, "files missing: stop and tell Claude"
"""
t1 = """#@title 7. T1: guided names probe (variants v1, v2, v3, v4, v0; 3 jobs each) -> results/wf_v44/t1/choice.json
import subprocess
from s1a import step3_v44 as S3
choice, info = S3.run_probe(S3.OUT_T1, backend)
print("choice:", choice)
print(info)
""" + push.format(msg="wf_v44 T1 names probe", sub="wf_v44/t1") + """print("T1 done")
"""
t2 = """#@title 8. T2: keyed split pass on the 54 v4.3 split jobs (target <= 5/54 parse errors)
import sys, subprocess
sys.path.insert(0, "/content/attribute-extraction/step1a/scripts")
import t2_split_v44 as T2
T2.build(T2.OUT)
print(T2.run(T2.OUT, backend))
print(T2.report(T2.OUT))
""" + push.format(msg="wf_v44 T2 keyed split", sub="wf_v44/t2") + """print("T2 done")
"""
t4 = """#@title 9. T4: Step 3 v4.4 (boosters on) -> L2 score -> a_llama44
import subprocess
from s1a import step3_v44 as S3
encoder = S3.bge_m3_encoder()
info, sizes = S3.full_run(S3.OUT_T4, backend, S3.load_config(), encoder, name_vecs=S3.OUT_T4 / "name_vecs.npz", save_vecs=True)
print(info)
print("a_llama44:", sizes)
for f in ("summary.md", "calls_v44.json", "booster_stats.json"):
    p = S3.OUT_T4 / "scores" / f
    if p.exists():
        print("==", f); print(p.read_text(encoding="utf-8")[:3000])
""" + push.format(msg="wf_v44 T4 step3 v44", sub="wf_v44/t4") + """print("T4 done")
"""
t6 = """#@title 10. T6: Step 4 v4.4 on a_llama44, then c1 (dev50 + dev50b, seeds 0-2 + vote), then score
import sys, subprocess
sys.path.insert(0, "/content/attribute-extraction/step1a/scripts")
import t6_step4_v44 as T6
for inp in ("a_llama44", "c1"):                  # a_llama44 needs cell 9
    print(inp, T6.run(backend, inputs=(inp,)))
    p = subprocess.run(["bash", "colab/sync.sh", "push-results", f"wf_v44 T6 step4 v44 {inp}", "wf_v44/t6"], capture_output=True, text=True)
    print(p.stdout.strip() or p.stderr[-500:])
T6.score()
print((T6.OUT / "summary.md").read_text(encoding="utf-8")[:4000])
""" + push.format(msg="wf_v44 T6 scores", sub="wf_v44/t6") + """print("T6 done")
"""
t7 = """#@title 11. T7: Step 4 on/off checks (dev50, seed 0, input a_llama44; all-on reused from T6)
import sys, subprocess
sys.path.insert(0, "/content/attribute-extraction/step1a/scripts")
import t6_step4_v44 as T6
import t7_ablation_v44 as T7
print(T7.run(backend, all_on_dir=T6.OUT))
print((T7.OUT / "t7_table.md").read_text(encoding="utf-8"))
""" + push.format(msg="wf_v44 T7 step4 on/off", sub="wf_v44/t7") + """print("T7 done")
"""
abl = """#@title 12. Step 3 on/off checks (each booster off, order 0; reads T4's name vectors)
import subprocess
from s1a import step3_v44 as S3
for sw in ("similar_batches", "rescue", "merge"):
    print(sw, S3.ablation(sw, backend, S3.load_config(), encoder))
    p = subprocess.run(["bash", "colab/sync.sh", "push-results", f"wf_v44 step3 off {sw}", "wf_v44/t4_ablate"], capture_output=True, text=True)
    print(p.stdout.strip() or p.stderr[-500:])
p = subprocess.run(["bash", "colab/sync.sh", "push-results", "wf_v44 model load time", "wf_v44"], capture_output=True, text=True)
print(p.stdout.strip() or p.stderr[-500:])
print("all done: disconnect the runtime, then tell Claude 'wf_v4.4 run done'")
"""
nb = dict(src)
nb["cells"] = [cell("markdown", intro), cell("code", c1), cells[2], cells[3], cell("code", c3), cell("code", c5), cell("code", c6),
               cell("code", data), cell("code", t1), cell("code", t2), cell("code", t4), cell("code", t6), cell("code", t7), cell("code", abl)]
out = step1a / "colab" / "S1A_wf44_colab.ipynb"
out.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print("wrote", out, len(nb["cells"]), "cells")
