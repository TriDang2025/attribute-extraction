"""python colab/make_nb46.py .  (from step1a/). Builds colab/S1A_wf46_colab.ipynb (wf_v4.6, diary Nov 16): the wf_v4.5 notebook's setup cells
(branch wf-v4.6, GPU_UTIL 0.6 so bge-m3 and GLiNER fit next to vLLM, load time to results/wf_v46/model_load.json) plus the Nov 16 notebook's
model cell (GLiNER, deberta-v3-base, bge-m3, pinned revisions). Run cells: scripts/gpu_v46.py y3 -> y56 -> y8, one model load."""
import json
import sys
from pathlib import Path

step1a = Path(sys.argv[1])
v45 = json.loads((step1a / "colab" / "S1A_wf45_colab.ipynb").read_text(encoding="utf-8"))["cells"]
v41 = json.loads((step1a / "colab" / "S1A_nov16_v41_colab.ipynb").read_text(encoding="utf-8"))["cells"]


def text(c):
    return "".join(c["source"])


def cell(kind, s):
    c = {"cell_type": kind, "metadata": {}, "source": s.splitlines(keepends=True)}
    if kind == "code":
        c.update(execution_count=None, outputs=[])
    return c


def swap(s, pairs, what):
    for a, b in pairs:
        if a not in s:
            raise SystemExit(f"{what}: '{a}' not found; the source notebook changed, update make_nb46.py")
        s = s.replace(a, b)
    return s


intro = """# wf_v4.6 GPU session (diary Nov 16): loop 1 with LLM entity names, then loop 2 with Llama
Code: GitHub `TriDang2025/attribute-extraction`, branch `wf-v4.6`, folder `step1a/`. Results in `results/wf_v46/`.

Model: Llama-3.1-8B-Instruct, bf16, vLLM, temperature 0, guided JSON (setting `llama8b`). Runtime: **A100 (40 GB or more)**.
**One GPU session only**: the model loads once (about 4 min), then every job runs back to back. Expected model time under 10 min.

- Cells 1-8: setup. Cell 2 installs, then restart the session, rerun cell 1 and skip cell 2.
- Cell 3: GLiNER, deberta-v3-base and bge-m3 (loop-2 evidence check). It must run before any other cell imports `s1a`: the model paths are read at import.
- Cell 5: loads Llama with `gpu_memory_utilization=0.6`, so bge-m3 and GLiNER fit next to it.
- Cell 9: **Y3** loop 1 with LLM entity names on raw dev50 and dev50b (Step 1a-2 from git; Step 3 v4.4, 3 orders; Step 4 v4.3 seed 0). About 450-600 calls per set.
- Cell 10: **Y5 + Y6** loop 2 on the Y3 output (Step 1b 3 orders + vote, evidence check, Step 3 naming). About 30-60 calls per set.
- Cell 11: **Y8** (only if time is left) Step 4 v4.3 with pass 2 in batches of 20, seed 0. About 10-20 calls per set.
- Cell 12: total GPU session time, then **Runtime > Disconnect and delete runtime**.
- Each run cell pushes its results to git. After a crash: rerun cells 1, 3-8 and the cell you were on (answered calls are cached).
- Stop rule: a cell stops by itself if a set needs more than MAX_CALLS calls; then tell Claude before going on.
- Colab Secrets `HF_TOKEN` and `GH_TOKEN`, notebook access on. Never put a token in a cell.
"""
c1 = swap(text(v45[1]), [("wf-v4.5", "wf-v4.6")], "clone cell")
setting = swap(text(v45[4]), [("#@title 3. Model setting", "#@title 4. Model setting")], "setting cell")
models = swap(text(v41[5]), [("#@title 4. Data and", "#@title 3. Data and")], "models cell")   # before any s1a import: spans / chk.config read CHK_MODELS at import
load = swap(text(v45[5]), [("GPU_UTIL = 0.80", "GPU_UTIL = 0.6"), ("results/wf_v45/model_load.json", "results/wf_v46/model_load.json"), ("#@title 4. Load", "#@title 5. Load"),
                           ("import time\n_t0 = time.time()", "import time\n_t0 = _T_SESSION = time.time()   # the GPU session clock starts with the model load")],
            "model load cell")
backend = swap(text(v45[6]), [("#@title 5. Backend", "#@title 6. Backend")], "backend cell")
data = """#@title 7. Data check: the Step 1a-2 folders of the raw dev sets (from git)
import sys
sys.path.insert(0, "/content/attribute-extraction/step1a/scripts")
import gpu_v46 as G
missing = G.need()
print("missing:", missing or "none")
assert not missing, "files missing: stop and tell Claude"
"""
enc = """#@title 8. Encoders and the GLiNER loader (bge-m3 for the Step 3 names; bge-m3 + GLiNER on the GPU for the loop-2 evidence check)
from s1a import step3_v44 as S3, corpus_v45 as CO
from run import encoder
enc3 = S3.bge_m3_encoder()
enc_1a = encoder()
gliner_loader = CO._gliner_on_gpu()[2]
print("encoders ready")
"""


def run_cell(title, call, msg, extra=""):
    return f"""#@title {title}
MAX_CALLS = 1500  #@param {{type:"integer"}}
import json, subprocess
res = {call}
{extra}p = subprocess.run(["bash", "colab/sync.sh", "push-results", "{msg}", "wf_v46"], capture_output=True, text=True)
print(p.stdout.strip() or p.stderr[-500:])
"""


y3 = run_cell("9. Y3: loop 1 with LLM entity names (dev50, dev50b) -> results/wf_v46/y3/<set>",
              "{}\nfor dev in G.SETS:\n    res[dev] = G.y3(backend, enc3, enc_1a, {dev: G.SETS[dev]}, load_seconds=L44.load_time(\"results/wf_v46/model_load.json\"))[dev]\n"
              "    print(dev, json.dumps({k: res[dev][k] for k in ('total_llm', 'entity_names', 'step4_chains_finished')}))\n"
              "    names = json.load(open(G.out_dir(dev) / 'entity_names.json'))\n    print('  names:', names['names'], '| groups:', names['groups'])\n"
              "    assert res[dev]['total_llm']['calls'] <= MAX_CALLS, f'{dev}: more calls than MAX_CALLS: stop and tell Claude'",
              "wf_v46 Y3 loop 1 with LLM entity names")
y56 = run_cell("10. Y5 + Y6: loop 2 on the Y3 output -> results/wf_v46/y3/<set>/loop2",
               "G.y56(backend, enc_1a, gliner_loader)",
               "wf_v46 Y5 Y6 loop 2",
               "for dev, r in res.items():\n    print(dev, (G.out_dir(dev) / 'loop2' / 'report.md').read_text(encoding='utf-8')[:3000])\n")
y8 = run_cell("11. Y8 (only if time is left): Step 4 v4.3, pass 2 in batches of 20, seed 0 -> results/wf_v46/y3/<set>/step4_p2b20",
              "G.y8(backend)", "wf_v46 Y8 step 4 pass 2 batches of 20")
end = """#@title 12. GPU session time -> results/wf_v46/gpu_session.json, then disconnect
import json, time, subprocess
info = {"gpu_session_seconds": round(time.time() - _T_SESSION, 1), "model_load_seconds": L44.load_time("results/wf_v46/model_load.json")}
open("results/wf_v46/gpu_session.json", "w").write(json.dumps(info, indent=1) + "\\n")
print(info)
p = subprocess.run(["bash", "colab/sync.sh", "push-results", "wf_v46 GPU session time", "wf_v46"], capture_output=True, text=True)
print(p.stdout.strip() or p.stderr[-500:])
print("Done: Runtime > Disconnect and delete runtime, then tell Claude 'GPU done'")
"""
nb = json.loads((step1a / "colab" / "S1A_wf45_colab.ipynb").read_text(encoding="utf-8"))
nb["cells"] = [cell("markdown", intro), cell("code", c1), v45[2], v45[3], cell("code", models), cell("code", setting), cell("code", load),
               cell("code", backend), cell("code", data), cell("code", enc), cell("code", y3), cell("code", y56), cell("code", y8), cell("code", end)]
out = step1a / "colab" / "S1A_wf46_colab.ipynb"
out.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print("wrote", out, len(nb["cells"]), "cells")
