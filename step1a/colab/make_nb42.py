"""python colab/make_nb42.py .  (from step1a/). Builds colab/S1A_wf42_colab.ipynb from the Nov 16 notebook's setup cells (same install, model load and backend)."""
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


intro = """# wf_v4.2 real runs with Llama (diary Nov 10)
Code: GitHub `TriDang2025/attribute-extraction`, branch `wf-v4.2-llama` (from `wf-v4.1`), folder `step1a/`. Results in `results/wf_v42/`.

Model: Llama-3.1-8B-Instruct, bf16, vLLM, temperature 0, guided JSON from each job's schema (setting `llama8b` of `config/wf_v41_models.json`). Runtime: **A100 (40 GB or more)**. Frozen prompts, parsers and scorers.

- Cells 1-5: setup (as the Nov 16 notebook). Cell 6: **T0 smoke test** (1 Step 3 call + 1 Step 4 call); results are committed and pushed.
- Cell 7: **T1** frozen Step 3 A prompt, 18 calls (3 entities x 3 orders x dev50 / dev50b), unchanged (option A of the T0 report). It counts failures; it does not stop on them. Time: about 3 min if all answers stop normally, up to about 45 min if all loop (each looping answer is retried once, unguided, one at a time).
- After a crash or disconnect: rerun cells 1, 3, 4, 5 and then the cell you were on. Answered calls are read from the cache.
- Colab Secrets `HF_TOKEN` and `GH_TOKEN`, notebook access on. The HF account must have accepted the Llama 3.1 license. Never put a token in a cell.
- When the GPU work is done: **Runtime > Disconnect and delete runtime**, so the paid GPU stops.
"""
c1 = text(cells[1]).replace('BRANCH = "wf-v4.1"', 'BRANCH = "wf-v4.2-llama"').replace("clone/pull wf-v4.1", "clone/pull wf-v4.2-llama")
c3 = text(cells[4]).replace('SETTING = "qwen32b"  #@param ["qwen32b", "llama8b"]', 'SETTING = "llama8b"  #@param ["llama8b"]')
c5 = text(cells[6]).replace(" (gpu_memory_utilization leaves room for GLiNER and bge-m3 of loop 2)", " (gpu_memory_utilization leaves room for GLiNER and bge-m3 of loop 2, T6)") \
    .replace("TAG = SETTING   # run folder results/wf_v41/nov16/<TAG>\n", "").replace("#@title 5. Load", "#@title 4. Load")
assert c1 != text(cells[1]) and c3 != text(cells[4]), "Nov 16 notebook cells changed: update this generator"
t0 = """#@title 6. T0 smoke test: 1 Step 3 call (frozen A prompt, hotel dev50b s0) + 1 Step 4 call (v4.1 stage 1, c1 dev50 seed 0)
import subprocess, json
from pathlib import Path
from s1a import batch_v4 as B
OUT = Path("results/wf_v42/t0_smoke")
!python scripts/t0_smoke_v42.py --build
jobs = B.read_json(OUT / "manifest.json")["jobs"]
print(backend.run(OUT, jobs))
r = subprocess.run(["python", "scripts/t0_smoke_v42.py", "--check"], capture_output=True, text=True)
print(r.stdout or r.stderr[-1000:])
p = subprocess.run(["bash", "colab/sync.sh", "push-results", "wf_v42 T0 smoke", "wf_v42/t0_smoke"], capture_output=True, text=True)
print(p.stdout.strip() or p.stderr[-500:])
print("T0", "PASS" if r.returncode == 0 else "FAIL: stop and tell Claude")
"""
t1 = """#@title 7. T1: frozen Step 3 A prompt with Llama, 18 calls (option A: unchanged, count the failures)
import subprocess
from pathlib import Path
from s1a import batch_v4 as B
OUT1 = Path("results/wf_v42/t1_step3")
!python scripts/t1_step3_v42.py --build
print(backend.run(OUT1, B.read_json(OUT1 / "manifest.json")["jobs"]))
!python scripts/t1_step3_v42.py --check
p = subprocess.run(["bash", "colab/sync.sh", "push-results", "wf_v42 T1 step3", "wf_v42/t1_step3"], capture_output=True, text=True)
print(p.stdout.strip() or p.stderr[-500:])
print("T1 done: tell Claude 'T1 done'")
"""
nb = dict(src)
nb["cells"] = [cell("markdown", intro), cell("code", c1), cells[2], cells[3], cell("code", c3), cell("code", c5), cell("code", text(cells[7]).replace("#@title 6. Backend", "#@title 5. Backend")),
               cell("code", t0), cell("code", t1)]
out = step1a / "colab" / "S1A_wf42_colab.ipynb"
out.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print("wrote", out, len(nb["cells"]), "cells")
