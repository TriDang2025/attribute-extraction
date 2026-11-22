"""python colab/make_nb50b.py .  (from step1a/). Builds colab/S1A_wf50b_colab.ipynb: the wf_v5.0 G5 rerun only. The first run (step4_ARM) used the
unguided fallback on every Step 4 call (guided finish_reason "error"), so it is not comparable with v4.9. Same setup cells as S1A_wf50_colab.ipynb,
then a guided smoke test (stops the session if guided decoding fails), G5 variant ARMg (= ARM) into results/wf_v50/g5/<set>/step4_ARMg on the G4 inputs
already in git, a check that every cached row is guided, push, settings_g5b.json. No G4 and no input build."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nbtools import cell, read_cells, swap, text, write_notebook  # noqa: E402

step1a = Path(sys.argv[1])
src = step1a / "colab" / "S1A_wf50_colab.ipynb"
v50 = read_cells(src)

intro = """# wf_v5.0 GPU session 2: G5 rerun (Step 4 variant ARM, guided)
The first G5 run got finish_reason "error" on every guided Step 4 call and used the unguided fallback, so it is not comparable with v4.9.
This session runs only G5 again, into `results/wf_v50/g5/<set>/step4_ARMg/`, on the Step 4 inputs from session 1 (in git). Branch `wf-v5.0`.

- Cells 0-6: setup as in session 1 (cell 2 installs, then restart the session, rerun cells 0-1 and skip cell 2; cell 3 before any `s1a` import).
- Cell 7: data check. **Cell 8: guided smoke test**: if it fails, stop, copy its output and tell Claude (do not run cell 9).
- Cell 9: G5 (6 chains); it stops if any call ran unguided. Cell 10: settings, then **Runtime > Disconnect and delete runtime**, tell Claude "GPU done".
- Run on a **fresh runtime** (not the session-1 runtime).
"""
data = """#@title 7. Data check: the G5 inputs from session 1 (git)
import sys
sys.path.insert(0, "/content/attribute-extraction/step1a/scripts")
import gpu_v50 as G
need = [G.G48.input_dir(d, G.G5) / r / "a.columns.json" for d, r in G.SETS.items()]
need += [G.Y3 / d / f for d in G.SETS for f in ("entities.json", "a_prompts")]
missing = [str(p) for p in need if not p.exists()]
print("missing:", missing or "none")
assert not missing, "files missing: stop and tell Claude"
print(G.G48.config("ARMg"))
"""
smoke = """#@title 8. Guided smoke test (must print finish stop and {"a": "x"} or {"a": "y"})
fin, txt = G.guided_smoke(llm, sampling, backend.chat)
print("finish:", fin, "| text:", txt)
assert fin == "stop" and txt.strip().startswith("{"), "guided decoding is broken in this session: stop and tell Claude (copy this output)"
"""
g5 = """#@title 9. G5 rerun: Step 4 variant ARMg, seeds 0-2, dev50 and dev50b -> results/wf_v50/g5/<set>/step4_ARMg
MAX_CALLS = 140  #@param {type:"integer"}
import subprocess
from s1a import log_v44 as L44
res = G.g5(backend)
for (var, dev), rows in res.items():
    folder = G.G5 / dev / f"step4_{var}"
    calls = len(L44.call_rows(folder))
    kinds = {k: sum(x["repair_kinds"].get(k, 0) for x in rows) for k in ("p2_reask", "p2_reask2", "p2_missing_column", "p2_unknown_column")}
    bad = G.unguided_rows(folder)
    print(var, dev, [(x["seed"], x["ok"], x["tables"], x["error"]) for x in rows], "| calls", calls, "| unguided", len(bad), "|", kinds)
    assert calls <= MAX_CALLS, f"{var} {dev}: more calls than MAX_CALLS: stop and tell Claude"
p = subprocess.run(["bash", "colab/sync.sh", "push-results", "wf_v50 G5 rerun ARMg", "wf_v50"], capture_output=True, text=True)
print(p.stdout.strip() or p.stderr[-500:])
assert not any(G.unguided_rows(G.G5 / d / "step4_ARMg") for d in G.SETS), "some calls ran unguided: tell Claude"
"""
load = swap(text(v50[7]), [("results/wf_v50/model_load.json", "results/wf_v50/model_load_g5b.json")], "model load cell")
end = """#@title 10. vLLM settings, GPU session time -> results/wf_v50/settings_g5b.json, then disconnect
import json, os, time, subprocess
def _seed():
    try:
        return llm.llm_engine.model_config.seed
    except Exception as e:
        return f"not readable: {type(e).__name__}"
info = {"chains": {f"{v} {d}": [(x["run"], x["ok"], x["tables"]) for x in rows] for (v, d), rows in res.items()},
        "vllm": vllm.__version__, "batch": BATCH, "batch_invariant_env": os.environ.get("VLLM_BATCH_INVARIANT"), "engine_seed": _seed(),
        "temperature": 0, "model": MODEL, "revision": REVISION, "smoke": [fin, txt],
        "unguided": {d: len(G.unguided_rows(G.G5 / d / "step4_ARMg")) for d in G.SETS},
        "gpu_session_seconds": round(time.time() - _T_SESSION, 1), "model_load_seconds": L44.load_time("results/wf_v50/model_load_g5b.json")}
open("results/wf_v50/settings_g5b.json", "w").write(json.dumps(info, indent=1, default=str) + "\n")
print(json.dumps(info, indent=1, default=str))
p = subprocess.run(["bash", "colab/sync.sh", "push-results", "wf_v50 G5 rerun settings", "wf_v50"], capture_output=True, text=True)
print(p.stdout.strip() or p.stderr[-500:])
print("Done: Runtime > Disconnect and delete runtime, then tell Claude 'GPU done'")
"""
cells = [cell("markdown", intro), *v50[1:7], cell("code", load), v50[8], cell("code", data), cell("code", smoke), cell("code", g5), cell("code", end)]
out = step1a / "colab" / "S1A_wf50b_colab.ipynb"
write_notebook(src, cells, out)
print("wrote", out, len(cells), "cells")
