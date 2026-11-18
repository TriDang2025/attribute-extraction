"""python colab/make_nb47.py .  (from step1a/). Builds colab/S1A_wf47_colab.ipynb (wf_v4.7 Z4, diary Nov 17) from the wf_v4.6 notebook:
same setup cells (branch wf-v4.7, results/wf_v47/), an optional batch-invariant vLLM mode (VLLM_BATCH_INVARIANT, set before vllm is
imported), then scripts/gpu_v47.py z4 = loop 2 v4.7 three times on dev50 and dev50b, one model load, a push after each run."""
import json
import sys
from pathlib import Path

step1a = Path(sys.argv[1])
v46 = json.loads((step1a / "colab" / "S1A_wf46_colab.ipynb").read_text(encoding="utf-8"))["cells"]


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
            raise SystemExit(f"{what}: '{a}' not found; the source notebook changed, update make_nb47.py")
        s = s.replace(a, b)
    return s


intro = """# wf_v4.7 GPU session (diary Nov 17, task Z4): loop 2 v4.7, three runs
Code: GitHub `TriDang2025/attribute-extraction`, branch `wf-v4.7`, folder `step1a/`. Results in `results/wf_v47/z4/run<1-3>/<set>/`.

Model: Llama-3.1-8B-Instruct, bf16, vLLM, temperature 0, guided JSON (setting `llama8b`). Runtime: **A100 (40 GB or more)**.
**One GPU session only**: the model loads once (about 4 min), then the three runs go back to back. Expected model time about 5 min;
if a run looks much bigger (the stop rule fires), stop and tell Claude.

- Cells 1-8: setup, as in wf_v4.6. Cell 2 installs, then restart the session, rerun cell 1 and skip cell 2.
- Cell 3 (models) must run before any other cell imports `s1a`: the model paths are read at import.
- Cell 5: `BATCH_INVARIANT` on = vLLM batch-invariant kernels (VLLM_BATCH_INVARIANT=1), so an answer should not depend on which other
  prompts share its batch (in v4.6, 18% of identical prompts got another answer). If the model load fails with it, set it off, restart
  the session and go on; cell 10 records which mode ran.
- Cell 9: **Z4** loop 2 v4.7 (config/wf_v47_loop2.json) on the v4.6 Y3 loop-1 output, runs 1, 2, 3; each run pushes its results.
- Cell 10: run agreement (same raw answer in all 3 runs) + the vLLM settings -> results/wf_v47/z4/settings.json; GPU session time.
  Then **Runtime > Disconnect and delete runtime**.
- After a crash: rerun cells 1, 3-8 and cell 9 (answered calls are cached per run folder).
- Colab Secrets `HF_TOKEN` and `GH_TOKEN`, notebook access on. Never put a token in a cell.
"""
clone = swap(text(v46[1]), [("wf-v4.6", "wf-v4.7")], "clone cell")
load = swap(text(v46[6]), [("GPU_UTIL = 0.6  #@param {type:\"number\"}", "GPU_UTIL = 0.6  #@param {type:\"number\"}\n"
                            "BATCH_INVARIANT = True  #@param {type:\"boolean\"}\nimport os\n"
                            "os.environ[\"VLLM_BATCH_INVARIANT\"] = \"1\" if BATCH_INVARIANT else \"0\"   # read when vllm is imported"),
                           ("results/wf_v46/model_load.json", "results/wf_v47/model_load.json")], "model load cell")
data = """#@title 7. Data check: Step 1a-2 folders (git) and the v4.6 Y3 loop-1 output (git)
import sys
sys.path.insert(0, "/content/attribute-extraction/step1a/scripts")
import gpu_v47 as G
missing = G.G46.need() + [str(G.SRC / d / "step3/scores/final_columns.json") for d in G.SETS
                          if not (G.SRC / d / "step3/scores/final_columns.json").exists()]
print("missing:", missing or "none")
assert not missing, "files missing: stop and tell Claude"
"""
enc = """#@title 8. bge-m3 and the GLiNER loader on the GPU (loop-2 evidence check)
from s1a import corpus_v45 as CO
from run import encoder
enc_1a = encoder()
gliner_loader = CO._gliner_on_gpu()[2]
print("encoders ready")
"""
z4 = """#@title 9. Z4: loop 2 v4.7, runs 1-3, dev50 and dev50b -> results/wf_v47/z4/run<r>/<set>
MAX_CALLS = 300  #@param {type:"integer"}
import json, subprocess
res = {}
for r in G.RUNS:
    res[r] = G.z4(backend, enc_1a, gliner_loader, runs=(r,))[r]
    for dev, info in res[r].items():
        print("run", r, dev, json.dumps({k: info[k] for k in ("suggested", "voted", "evidence_kept", "new_columns", "duplicates")}),
              "| calls", info["cost"]["total"])
        assert info["cost"]["total"]["calls"] <= MAX_CALLS, f"run {r} {dev}: more calls than MAX_CALLS: stop and tell Claude"
    p = subprocess.run(["bash", "colab/sync.sh", "push-results", f"wf_v47 Z4 loop 2 run {r}", "wf_v47"], capture_output=True, text=True)
    print(p.stdout.strip() or p.stderr[-500:])
"""
end = """#@title 10. Run agreement, vLLM settings, GPU session time -> results/wf_v47/z4/settings.json, then disconnect
import json, time, subprocess
def _seed():
    try:
        return llm.llm_engine.model_config.seed
    except Exception as e:
        return f"not readable: {type(e).__name__}"
info = {"agreement": {d: {s: list(v) for s, v in st.items()} for d, st in G.agreement().items()},
        "vllm": vllm.__version__, "batch": BATCH, "batch_invariant_env": os.environ.get("VLLM_BATCH_INVARIANT"), "engine_seed": _seed(),
        "temperature": 0, "gpu_session_seconds": round(time.time() - _T_SESSION, 1),
        "model_load_seconds": L44.load_time("results/wf_v47/model_load.json")}
open("results/wf_v47/z4/settings.json", "w").write(json.dumps(info, indent=1, default=str) + "\\n")
print(json.dumps(info, indent=1, default=str))
p = subprocess.run(["bash", "colab/sync.sh", "push-results", "wf_v47 Z4 settings and session time", "wf_v47"], capture_output=True, text=True)
print(p.stdout.strip() or p.stderr[-500:])
print("Done: Runtime > Disconnect and delete runtime, then tell Claude 'GPU done'")
"""
nb = json.loads((step1a / "colab" / "S1A_wf46_colab.ipynb").read_text(encoding="utf-8"))
nb["cells"] = [cell("markdown", intro), cell("code", clone), v46[2], v46[3], v46[4], v46[5], cell("code", load), v46[7],
               cell("code", data), cell("code", enc), cell("code", z4), cell("code", end)]
out = step1a / "colab" / "S1A_wf47_colab.ipynb"
out.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print("wrote", out, len(nb["cells"]), "cells")
