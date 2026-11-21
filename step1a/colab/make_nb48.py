"""python colab/make_nb48.py .  (from step1a/). Builds colab/S1A_wf48_colab.ipynb (wf_v4.8 W3, diary Nov 19) from the wf_v4.7 notebook:
same setup cells (branch wf-v4.8, results/wf_v48/, batch-invariant vLLM on), then scripts/gpu_v48.py w3 = Step 4 variants A and B,
seeds 0-2, dev50 and dev50b (12 chains), one model load, a push after each variant."""
import json
import sys
from pathlib import Path

step1a = Path(sys.argv[1])
v47 = json.loads((step1a / "colab" / "S1A_wf47_colab.ipynb").read_text(encoding="utf-8"))["cells"]


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
            raise SystemExit(f"{what}: '{a}' not found; the source notebook changed, update make_nb48.py")
        s = s.replace(a, b)
    return s


intro = """# wf_v4.8 GPU session (diary Nov 19, task W3): fix the Step 4 collapse
Code: GitHub `TriDang2025/attribute-extraction`, branch `wf-v4.8`, folder `step1a/`. Results in `results/wf_v48/w3/<set>/step4_<A|B>/`.

Model: Llama-3.1-8B-Instruct, bf16, vLLM, temperature 0, guided JSON (setting `llama8b`), batch-invariant mode on, engine seed 0.
Runtime: **A100 (40 GB or more)**. **One short GPU session**: model load about 4 min, then about 3 min of model time.

- Step 4 v4.3 on the loop 1 + 2 attributes after W2 (`results/wf_v48/w3/<set>/input/`, from git), seeds 0-2, two variants:
  **A** = pass 2 in batches of 20; **B** = A + neutral table ids (table_1, table_2, ... with the pass-1 names as a hint; code names the tables).
  2 variants x 2 sets x 3 seeds = 12 chains.
- Cells 1-6: setup, as in wf_v4.7. Cell 2 installs, then restart the session, rerun cell 1 and skip cell 2.
  Cell 3 (models) must run before any other cell imports `s1a`.
- Cell 7: data check. Cell 8: **W3** (pushes after each variant). Cell 9: vLLM settings + GPU session time, then
  **Runtime > Disconnect and delete runtime**, and tell Claude "GPU done".
- After a crash: rerun cells 1, 3-7 and cell 8 (answered calls are cached per chain folder).
- Colab Secrets `HF_TOKEN` and `GH_TOKEN`, notebook access on. Never put a token in a cell.
"""
clone = swap(text(v47[1]), [("wf-v4.7", "wf-v4.8")], "clone cell")
load = swap(text(v47[6]), [("results/wf_v47/model_load.json", "results/wf_v48/model_load.json")], "model load cell")
data = """#@title 7. Data check: W3 inputs and the loop-1 run files (git)
import sys
sys.path.insert(0, "/content/attribute-extraction/step1a/scripts")
import gpu_v48 as G
need = [G.input_dir(d) / r / "a.columns.json" for d, r in G.SETS.items()]
need += [G.Y3 / d / f for d in G.SETS for f in ("entities.json", "a_prompts")]
missing = [str(p) for p in need if not p.exists()]
print("missing:", missing or "none")
assert not missing, "files missing: stop and tell Claude"
print({v: G.config(v) for v in G.VARIANTS})
"""
w3 = """#@title 8. W3: Step 4 variants A and B, seeds 0-2, dev50 and dev50b -> results/wf_v48/w3/<set>/step4_<A|B>
MAX_CALLS = 200  #@param {type:"integer"}
import json, subprocess
from s1a import log_v44 as L44
res = {}
for v in G.VARIANTS:
    r = G.w3(backend, variants=(v,))
    res.update(r)
    for (var, dev), rows in r.items():
        folder = G.OUT / dev / f"step4_{var}"
        calls = len(L44.call_rows(folder))
        print(var, dev, [(x["seed"], x["ok"], x["tables"], x["error"]) for x in rows], "| calls", calls)
        assert calls <= MAX_CALLS, f"{var} {dev}: more calls than MAX_CALLS: stop and tell Claude"
    p = subprocess.run(["bash", "colab/sync.sh", "push-results", f"wf_v48 W3 Step 4 variant {v}", "wf_v48"], capture_output=True, text=True)
    print(p.stdout.strip() or p.stderr[-500:])
"""
end = """#@title 9. vLLM settings, GPU session time -> results/wf_v48/w3/settings.json, then disconnect
import json, time, subprocess
def _seed():
    try:
        return llm.llm_engine.model_config.seed
    except Exception as e:
        return f"not readable: {type(e).__name__}"
info = {"chains": {f"{v} {d}": [(x["run"], x["ok"], x["tables"]) for x in rows] for (v, d), rows in res.items()},
        "vllm": vllm.__version__, "batch": BATCH, "batch_invariant_env": os.environ.get("VLLM_BATCH_INVARIANT"), "engine_seed": _seed(),
        "temperature": 0, "gpu_session_seconds": round(time.time() - _T_SESSION, 1),
        "model_load_seconds": L44.load_time("results/wf_v48/model_load.json")}
open("results/wf_v48/w3/settings.json", "w").write(json.dumps(info, indent=1, default=str) + "\\n")
print(json.dumps(info, indent=1, default=str))
p = subprocess.run(["bash", "colab/sync.sh", "push-results", "wf_v48 W3 settings and session time", "wf_v48"], capture_output=True, text=True)
print(p.stdout.strip() or p.stderr[-500:])
print("Done: Runtime > Disconnect and delete runtime, then tell Claude 'GPU done'")
"""
nb = json.loads((step1a / "colab" / "S1A_wf47_colab.ipynb").read_text(encoding="utf-8"))
nb["cells"] = [cell("markdown", intro), cell("code", clone), v47[2], v47[3], v47[4], v47[5], cell("code", load), v47[7],
               cell("code", data), cell("code", w3), cell("code", end)]
out = step1a / "colab" / "S1A_wf48_colab.ipynb"
out.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print("wrote", out, len(nb["cells"]), "cells")
