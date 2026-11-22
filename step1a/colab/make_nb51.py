"""python colab/make_nb51.py .  (from step1a/). Builds colab/S1A_wf51_colab.ipynb (wf_v5.1 R5) from the wf_v5.0 notebook: the same GPU check and setup
cells (branch wf-v5.1, batch-invariant vLLM, Llama-3.1-8B setting llama8b, engine seed 0), then scripts/gpu_v51.py: guided smoke test, Step 3 with
the R3 + R4 switches, context split + rename + column clash, loop-2 replay (CPU), Step 4 v5.0 variant ARMg seeds 0-2, push, settings.json."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nbtools import cell, read_cells, swap, text, write_notebook  # noqa: E402

step1a = Path(sys.argv[1])
src = step1a / "colab" / "S1A_wf50_colab.ipynb"
v50 = read_cells(src)

intro = """# wf_v5.1 GPU session (diary Nov 24, task R5): the full rerun with the adopted switches
Code: GitHub `TriDang2025/attribute-extraction`, branch `wf-v5.1`, folder `step1a/`. **wf-v5.1 must be pushed before this run** (cell 1 clones it;
only after the user's OK, Claude does not push). Results in `results/wf_v51/r5/` (new folders only).

Model: Llama-3.1-8B-Instruct, bf16, vLLM, temperature 0, guided JSON (setting `llama8b`), batch-invariant mode on, engine seed 0 (as wf_v5.0).
Runtime: **A100 (40 GB or more)**; cell 0 checks it. One GPU session, model load about 5 min, then about 10 min of model time (estimate).

Per set (dev50, dev50b), everything guided; a guided call with `finish_reason` "error" or a row that is not guided stops the cell (no unguided fallback):
- **Cell 7 smoke test:** one tiny guided call. If it fails, stop, copy the output and tell Claude (do not run the next cells).
- **Cell 10 Step 3** (about 550 + 475 calls): the frozen v4.4 Step 3 with **R4** (3 context snippets per cluster in the naming prompt) and **R3**
  (closed question for same-named clusters) on, from the loop-1 entities and frozen A prompts of v4.6 (in git). Stops at MAX_CALLS 900 per set.
- **Cell 11 rename:** context split big40 (v5.0) on the new columns, a G4-style rename of the changed columns (with R4 snippets), then the R3 clash
  question on columns that share a name (v5.0 named both train time parts "departure time").
- **Cell 12 loop 2 (CPU):** **replayed, not re-asked**: the wf_v4.8 W2 replay of the cached v4.7 z4 run-1 loop-2 files on the new loop-1 columns,
  with the laptop bge-m3 vectors (`results/wf_v51/r5/<set>/vectors.npz`; a text without a laptop vector goes to the GPU bge-m3 and is counted).
- **Cell 13 Step 4:** v5.0 frozen = variant **ARMg** (A + re-ask r1 + r2 + same-entity merge), seeds 0-2 -> `results/wf_v51/r5/<set>/step4_ARMg/`.
- **Cell 14:** `results/wf_v51/r5/settings.json` (vLLM settings, session time, calls, tokens, finish reasons, guided share) and
  `calls.csv`; then **Runtime > Disconnect and delete runtime**, and tell Claude "GPU done".
- Cells 1-6: setup, as in wf_v5.0. Cell 2 installs, then restart the session, rerun cells 0-1 and skip cell 2.
  Cell 3 (models) must run before any other cell imports `s1a`.
- After a crash: rerun cells 0-1, 3-9 and the cell that failed (answered calls are cached per folder).
- Colab Secrets `HF_TOKEN` and `GH_TOKEN`, notebook access on. Never put a token in a cell.
"""
clone = swap(text(v50[2]), [("wf-v5.0", "wf-v5.1")], "clone cell")
load = swap(text(v50[7]), [("results/wf_v50/model_load.json", "results/wf_v51/r5/model_load.json")], "model load cell")
smoke = """#@title 7. Guided smoke test (must print finish stop and {"a": "x"} or {"a": "y"}); stops the session if guided decoding fails
import sys
sys.path.insert(0, "/content/attribute-extraction/step1a/scripts")
import gpu_v51 as G
fin, txt = G.smoke_test(llm, sampling, backend.chat)
print("finish:", fin, "| text:", txt)
"""
data = """#@title 8. Data check: inputs from git (loop-1 entities and A prompts, loop-2 files, Step 1a-2 folders, laptop vectors, configs)
missing = G.need()
print("missing:", missing or "none")
assert not missing, "files missing: stop and tell Claude"
print({"switches": G.SWITCHES, "context split": G.CTX, "step 4": G.G48.config(G.VARIANT), "limits": G.LIMITS})
"""
enc = """#@title 9. Encoders: bge-m3 for the Step 3 names (merge booster) and for texts without a laptop vector; laptop vectors first
from s1a import step3_v44 as S3
from run import encoder
enc3 = S3.bge_m3_encoder()
enc_1a = encoder()
vec_enc = G.G50.CachedEnc(G.R5, "vectors.npz", fallback=enc_1a)
print("encoders ready")
"""
step3 = """#@title 10. Step 3 with R3 + R4 on (names, split, R3 clash, reconcile, dupcheck) -> results/wf_v51/r5/<set>/step3
MAX_CALLS = 900  #@param {type:"integer"}
import subprocess
res3 = G.step3_stage(backend, enc3, max_calls=MAX_CALLS)
p = subprocess.run(["bash", "colab/sync.sh", "push-results", "wf_v51 R5 Step 3", "wf_v51"], capture_output=True, text=True)
print(p.stdout.strip() or p.stderr[-500:])
"""
rename = """#@title 11. Context split big40, G4-style rename (R4 snippets), column clash check -> results/wf_v51/r5/rename/<set>
MAX_CALLS = 60  #@param {type:"integer"}
import subprocess
res_rename = G.rename_stage(backend, vec_enc, max_calls=MAX_CALLS)
for dev, r in res_rename.items():
    print(dev, "renamed:", [(x["entity"], x["cid"], x["old"], "->", x["new"]) for x in r["renamed"] if x["renamed"]])
    print(dev, "clash renames:", [(x["entity"], x["cid"], x["old"], "->", x["new"]) for x in r["clash"]])
p = subprocess.run(["bash", "colab/sync.sh", "push-results", "wf_v51 R5 rename and clash", "wf_v51"], capture_output=True, text=True)
print(p.stdout.strip() or p.stderr[-500:])
"""
loop2 = """#@title 12. Loop 2 (frozen; replayed on CPU, not re-asked) and the Step 4 input -> results/wf_v51/r5/<set>/input
import json
paths = G.loop2_stage(vec_enc)
for dev, p in paths.items():
    print(dev, p, len(json.loads(p.read_text(encoding="utf-8"))), "columns")
print("texts without a laptop vector (GPU bge-m3):", vec_enc.fallback_texts)
"""
step4 = """#@title 13. Step 4 v5.0 frozen (variant ARMg), seeds 0-2, dev50 and dev50b -> results/wf_v51/r5/<set>/step4_ARMg
MAX_CALLS = 140  #@param {type:"integer"}
import subprocess
res4 = G.step4_stage(backend, max_calls=MAX_CALLS)
for (var, dev), rows in res4.items():
    print(var, dev, [(x["seed"], x["ok"], x["tables"], x["error"]) for x in rows])
p = subprocess.run(["bash", "colab/sync.sh", "push-results", "wf_v51 R5 Step 4 variant ARMg", "wf_v51"], capture_output=True, text=True)
print(p.stdout.strip() or p.stderr[-500:])
"""
end = """#@title 14. vLLM settings, call counts, GPU session time -> results/wf_v51/r5/settings.json, then disconnect
import json, os, time, subprocess
def _seed():
    try:
        return llm.llm_engine.model_config.seed
    except Exception as e:
        return f"not readable: {type(e).__name__}"
cost = G.cost_report()
info = {"vllm": vllm.__version__, "batch": BATCH, "batch_invariant_env": os.environ.get("VLLM_BATCH_INVARIANT"), "engine_seed": _seed(),
        "temperature": 0, "model": MODEL, "revision": REVISION, "smoke": [fin, txt], "switches": G.SWITCHES, "context_split": G.CTX,
        "step4_variant": G.VARIANT, "loop2": "replayed on CPU (W2 replay of the cached v4.7 z4 run-1 loop-2 files), not re-asked",
        "chains": {f"{v} {d}": [(x["run"], x["ok"], x["tables"]) for x in rows] for (v, d), rows in res4.items()},
        "calls": cost, "total_calls": {s: sum(x["calls"] for x in d.values()) for s, d in cost.items()},
        "total_tokens_in": sum(x["prompt_tokens"] for d in cost.values() for x in d.values()),
        "total_tokens_out": sum(x["output_tokens"] for d in cost.values() for x in d.values()),
        "guided_share": {s: {dev: (x["guided"] / x["calls"] if x["calls"] else None) for dev, x in d.items()} for s, d in cost.items()},
        "unguided_rows": {f"{s} {d}": len(G.G50.unguided_rows(f(G.R5, d))) for s, f in G.STAGES for d in G.SETS},
        "laptop_vector_fallback_texts": vec_enc.fallback_texts,
        "gpu_session_seconds": round(time.time() - _T_SESSION, 1), "model_load_seconds": L44.load_time("results/wf_v51/r5/model_load.json")}
open("results/wf_v51/r5/settings.json", "w").write(json.dumps(info, indent=1, default=str) + "\\n")
print(json.dumps(info, indent=1, default=str))
assert not any(info["unguided_rows"].values()), "some rows are not guided: tell Claude"
p = subprocess.run(["bash", "colab/sync.sh", "push-results", "wf_v51 R5 settings and session time", "wf_v51"], capture_output=True, text=True)
print(p.stdout.strip() or p.stderr[-500:])
print("Done: Runtime > Disconnect and delete runtime, then tell Claude 'GPU done'")
"""
cells = [cell("markdown", intro), v50[1], cell("code", clone), *v50[3:7], cell("code", load), v50[8], cell("code", smoke), cell("code", data),
         cell("code", enc), cell("code", step3), cell("code", rename), cell("code", loop2), cell("code", step4), cell("code", end)]
out = step1a / "colab" / "S1A_wf51_colab.ipynb"
write_notebook(src, cells, out)
print("wrote", out, len(cells), "cells")
