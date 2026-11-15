"""python colab/make_nb45_s1a.py .  (from step1a/). Builds colab/S1A_wf45_step1a_colab.ipynb: wf_v4.5 W4 part 1, Steps 1a-2 of the cost-test
corpora on a GPU session WITHOUT vLLM (the chunker needs chromadb, which is kept out of the vLLM session). Cell 1 is the wf_v4.4 notebook's
clone cell (branch wf-v4.5); the model cell follows the Nov 16 notebook's loop-2 model cell (same pinned revisions)."""
import json
import sys
from pathlib import Path

step1a = Path(sys.argv[1])
src = json.loads((step1a / "colab" / "S1A_wf44_colab.ipynb").read_text(encoding="utf-8"))
nov16 = json.loads((step1a / "colab" / "S1A_nov16_v41_colab.ipynb").read_text(encoding="utf-8"))


def text(c):
    return "".join(c["source"])


def cell(kind, s):
    c = {"cell_type": kind, "metadata": {}, "source": s.splitlines(keepends=True)}
    if kind == "code":
        c.update(execution_count=None, outputs=[])
    return c


intro = """# wf_v4.5 W4 part 1 (diary Nov 15): Steps 1a-2 of the cost-test corpora (no LLM, no vLLM)
Code: GitHub `TriDang2025/attribute-extraction`, branch `wf-v4.5`, folder `step1a/`. Runtime: **any GPU** (T4 or L4 is enough; no vLLM here).

- Cell 1: tokens, clone/pull wf-v4.5. Cell 2: install (pinned), then **Runtime > Restart session**, rerun cell 1, skip cell 2.
- Cell 3: models (GLiNER medium v2.1, deberta-v3-base config, bge-m3; pinned revisions) and data (TEAR pool/test from HF, MultiWOZ 2.2 from GitHub);
  rebuilds the corpora (`scripts/w3_corpora_v45.py`) and checks the ids against git.
- Cell 4: Steps 1a-2 of n50, n100, n200, n300, n500, n1000, each from empty caches (the time is that size's own); GPU n50 vs laptop n50 check;
  pushes `results/wf_v45/w4/` (times, check). 30-90 min (estimate: the laptop CPU took 18 min for n50, mostly bge-m3).
- Cell 5: uploads the run folders (no caches) to the HF dataset `database-lab/attribute-extraction-data` under `step1a/wf_v45/` and checks
  every file size. Then **Runtime > Disconnect and delete runtime** and tell Claude "W4 step 1a done".
- Colab Secrets `HF_TOKEN` (write access to database-lab) and `GH_TOKEN`. Never put a token in a cell.
"""
c1 = text(src["cells"][1]).replace("wf-v4.4", "wf-v4.5")
assert c1 != text(src["cells"][1]), "wf_v4.4 clone cell changed: update this generator"
install = """#@title 2. Install (pinned; then Runtime > Restart session, rerun cell 1 and skip this cell)
!pip install -q gliner==0.2.29 sentence-transformers==5.6.0 tiktoken==0.14.0 chromadb==1.5.9 openai==3.35.1 anthropic==1.15.0 backoff==2.2.1 \\
    fuzzywuzzy==0.18.0 python-Levenshtein==0.27.5 hdbscan==0.8.44 umap-learn==0.5.12 \\
    "chunking_evaluation @ git+https://github.com/brandonstarxel/chunking_evaluation@e708410d1c61cb76a85cd9d433630ef89b9c6b85"
"""
mc = text(nov16["cells"][5])
cut = mc.index("snapshot_download(\"urchade")
models = ("#@title 3. Models, data, corpora (pinned revisions as the Nov 16 notebook)\nimport json, os, subprocess, sys\nfrom pathlib import Path\n"
          "from huggingface_hub import snapshot_download\nMODELS = Path(\"/content/models\")\n"
          "os.environ[\"CHK_MODELS\"] = str(MODELS)          # read by chunking/chk/config.py and s1a/spans.py at import\n"
          + mc[cut:mc.index("import sys")] + """sys.path.insert(0, "/content/attribute-extraction/step1a"); sys.path.insert(0, "/content/attribute-extraction/step1a/scripts")
subprocess.run([sys.executable, "scripts/get_conversation_data.py"], check=True)
MW = Path("/content/MultiWOZ_2.2")
B = "https://raw.githubusercontent.com/budzianowski/multiwoz/master/data/MultiWOZ_2.2"
files = [f"train/dialogues_{i:03d}.json" for i in range(1, 18)] + [f"{s}/dialogues_{i:03d}.json" for s in ("dev", "test") for i in (1, 2)]
for f in files:
    if not (MW / f).exists():
        (MW / f).parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["curl", "-sSL", "--retry", "5", "-o", str(MW / f), f"{B}/{f}"], check=True)
subprocess.run([sys.executable, "scripts/w3_corpora_v45.py", "--mwoz", str(MW)], check=True, capture_output=True)
same = subprocess.run(["git", "diff", "--quiet", "--", "results/wf_v45/w3/ids.json"]).returncode == 0
subprocess.run(["git", "checkout", "--", "results/wf_v45/w3/"], check=True)   # keep the committed data card (it names the laptop path)
print("corpora ids equal to git:", same)
assert same, "corpus ids differ from the laptop build: stop and tell Claude"
"""
              )
assert "gliner_medium-v2.1" in models and "cfg_path" in models, "Nov 16 model cell changed: update this generator"
run = """#@title 4. Steps 1a-2 per corpus size (fresh caches), GPU n50 vs laptop n50, push the times
import torch, subprocess
assert torch.cuda.is_available(), "no GPU: change the runtime type"
import w4_step1a_v45 as W
from run import encoder
res = W.run_sizes(encoder())
for n, r in res.items():
    print(n, r["docs"], "dialogues", r["mentions"], "mentions", r["clusters"], "clusters", r["seconds"], r["entities"])
print(W.n50_check())
p = subprocess.run(["bash", "colab/sync.sh", "push-results", "wf_v45 W4 step1a times", "wf_v45/w4"], capture_output=True, text=True)
print(p.stdout.strip() or p.stderr[-500:])
"""
up = """#@title 5. Upload the run folders to HF (sizes checked), then disconnect the runtime
import w4_step1a_v45 as W
for n, files in W.upload().items():
    print(n, len(files), "files,", sum(s for _, s in files), "bytes")
print("W4 step 1a done: disconnect the runtime, then tell Claude 'W4 step 1a done'")
"""
nb = {k: v for k, v in src.items() if k != "cells"}
nb["cells"] = [cell("markdown", intro), cell("code", c1), cell("code", install), cell("code", models), cell("code", run), cell("code", up)]
out = step1a / "colab" / "S1A_wf45_step1a_colab.ipynb"
out.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print("wrote", out, len(nb["cells"]), "cells")
