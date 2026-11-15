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
- Cell 8: **W2** the one command (`s1a/pipeline_v45.py`) on raw dev50 (corpus n50): Steps 3-4 on GPU (Step 1a-2 output `results/graph_v22_c_n50` comes from the laptop), then the dev50 check. Set STEP4 to the W1 freeze. About 450 calls, 30-40 min (estimate).
- Cell 9: **W4** cost runs per corpus size, after the Step 1a notebook (`colab/S1A_wf45_step1a_colab.ipynb`) has uploaded the Step 1a-2 folders
  to HF. One seed of the command per size, smallest first, push after each size. Calls grow with the clusters: roughly 450 (n50) to a few
  thousand (n1000); total 2-5 h on an A100 (rough estimate; set SIZES to fewer sizes to stop early).
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
w2 = """#@title 8. W2: one command on raw dev50 (n50 corpus; Step 1a-2 output from the laptop) -> results/wf_v45/w2/n50, dev50 check
STEP4 = "v44_other_off"  #@param ["v44_other_off", "v43"]
import sys, json, subprocess
from pathlib import Path
sys.path.insert(0, "/content/attribute-extraction/step1a/scripts")
from s1a import pipeline_v45 as PL, step3_v44 as S3
OUT = Path("results/wf_v45/w2/n50")
enc3 = S3.bge_m3_encoder()
c = PL.run_pipeline("data/wf_v45_corpora/n50.jsonl", OUT, "c_n50", backend, enc3, None, PL.step4_config(STEP4),
                    load_seconds=L44.load_time("results/wf_v45/model_load.json"), skip_1a=True)   # the corpus file is not read with skip_1a
print(json.dumps(c, indent=1))
rows = PL.compare_step3(OUT, "c_n50")
d = PL.score_step4_as(OUT, "c_n50")
(OUT / "dev50_check.md").write_text("# W2 dev50 check\\n\\nStep 4: " + STEP4 + "\\n\\n## Step 3 final columns vs frozen wf_v4.4 T4\\n\\n" + "\\n".join(rows)
                                     + "\\n\\n## Step 4 scored as dev50\\n\\n" + (d / "summary.md").read_text(encoding="utf-8"), encoding="utf-8")
print((OUT / "dev50_check.md").read_text(encoding="utf-8")[:5000])
p = subprocess.run(["bash", "colab/sync.sh", "push-results", "wf_v45 W2 n50 end to end", "wf_v45/w2"], capture_output=True, text=True)
print(p.stdout.strip() or p.stderr[-500:])
print("W2 done: disconnect the runtime, then tell Claude 'W2 done'")
"""
w4 = """#@title 9. W4: cost runs, one seed of the W2 command per corpus size (Step 1a-2 from the Step 1a notebook, via HF), smallest first
STEP4 = "v44_other_off"  #@param ["v44_other_off", "v43"]
SIZES = "50,100,200,300,500,1000"  #@param {type:"string"}
import sys, json, subprocess
from pathlib import Path
sys.path.insert(0, "/content/attribute-extraction/step1a/scripts")
from s1a import pipeline_v45 as PL, step3_v44 as S3
import w4_step1a_v45 as W
sizes = [int(x) for x in SIZES.split(",")]
W.download(sizes)
tok = llm.get_tokenizer()
times = W.times()
if "enc3" not in globals():
    enc3 = S3.bge_m3_encoder()
for n in sizes:
    texts = [json.loads(l)["text"] for l in open(W.CORPORA / f"n{n}.jsonl", encoding="utf-8")] if (W.CORPORA / f"n{n}.jsonl").exists() else \\
            [json.loads(l)["text"] for l in open(PL.CO.run_dir(W.set_name(n)) / "docs.jsonl", encoding="utf-8")]
    corpus_tokens = sum(len(tok.encode(t, add_special_tokens=False)) for t in texts)
    out = W.OUT / f"n{n}"
    c = PL.run_pipeline(None, out, W.set_name(n), backend, enc3, None, PL.step4_config(STEP4), load_seconds=L44.load_time("results/wf_v45/model_load.json"),
                        skip_1a=True)
    c.update(dialogues=len(texts), corpus_tokens=corpus_tokens, step1a_2=times.get(n), step4_choice=STEP4)
    (out / "cost.json").write_text(json.dumps(c, indent=1) + "\\n", encoding="utf-8")
    print(n, "dialogues:", c["total_llm"], "| step 1a s:", (times.get(n) or {}).get("seconds"))
    p = subprocess.run(["bash", "colab/sync.sh", "push-results", f"wf_v45 W4 n{n}", "wf_v45/w4"], capture_output=True, text=True)
    print(p.stdout.strip() or p.stderr[-500:])
print("W4 done: disconnect the runtime, then tell Claude 'W4 done'")
"""
nb = dict(src)
nb["cells"] = [cell("markdown", intro), cell("code", c1), cells[2], cells[3], cells[4], cell("code", c4), cells[6], cell("code", data), cell("code", w1),
               cell("code", w2), cell("code", w4)]
out = step1a / "colab" / "S1A_wf45_colab.ipynb"
out.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print("wrote", out, len(nb["cells"]), "cells")
