"""wf_v4.5 (diary Nov 15) W4, part 1: Steps 1a-2 (cheap models, no LLM) of every cost-test corpus, on a Colab GPU session without vLLM.

Colab (notebook colab/S1A_wf45_step1a_colab.ipynb): run_sizes(encoder()) -> results/graph_v22_w4_n<size>/ per size (each from empty caches, so
the time is that size's own), results/wf_v45/w4/step1a_times.json and n50_check.md (the GPU n50 run vs the laptop run results/graph_v22_c_n50);
then upload(): the run folders (without cache/) to the HF dataset database-lab/attribute-extraction-data under step1a/wf_v45/.
LLM session: download(sizes) puts them back into results/ before pipeline_v45.run_pipeline(..., skip_1a=True).
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import pandas as pd  # noqa: E402

from s1a import corpus_v45 as CO  # noqa: E402

SIZES = (50, 100, 200, 300, 500, 1000)
CORPORA = ROOT / "data" / "wf_v45_corpora"
OUT = ROOT / "results" / "wf_v45" / "w4"
HF_REPO, HF_DIR = "database-lab/attribute-extraction-data", "step1a/wf_v45"


def set_name(n):
    return f"w4_n{n}"


def run_sizes(enc, sizes=SIZES, log=print):
    """Step 1a-2 of each corpus size from empty caches; writes and returns {size: info} (step1a_times.json)."""
    OUT.mkdir(parents=True, exist_ok=True)
    res = {}
    for n in sizes:
        res[n] = CO.step1a(CORPORA / f"n{n}.jsonl", set_name(n), enc, fresh=True, log=log)
        (OUT / "step1a_times.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8", newline="\n")
    return res


def n50_check():
    """Markdown: the GPU n50 mentions vs the laptop run (results/graph_v22_c_n50), column by column (share of equal rows)."""
    a = pd.read_csv(CO.run_dir(set_name(50)) / "spans" / "mentions.csv", dtype=str, keep_default_na=False)
    b = pd.read_csv(CO.run_dir("c_n50") / "spans" / "mentions.csv", dtype=str, keep_default_na=False)
    lines = ["# W4 Step 1a: GPU n50 vs laptop n50", "", f"Mentions: GPU {len(a)}, laptop {len(b)}.", ""]
    if len(a) == len(b):
        lines += ["| column | equal rows |", "|---|---|"]
        lines += [f"| {c} | {(a[c].values == b[c].values).mean():.3f} |" for c in ("dialogue_id", "char_start", "text", "cluster_id", "entity")]
    text = "\n".join(lines) + "\n"
    (OUT / "n50_check.md").write_text(text, encoding="utf-8", newline="\n")
    return text


def upload(sizes=SIZES):
    """Upload results/graph_v22_w4_n<size>/ (cache/ left out) to the HF dataset; returns {size: [(path, bytes)]} as uploaded (checked by listing)."""
    from huggingface_hub import HfApi
    api, out = HfApi(), {}
    for n in sizes:
        d = CO.run_dir(set_name(n))
        api.upload_folder(repo_id=HF_REPO, repo_type="dataset", folder_path=str(d), path_in_repo=f"{HF_DIR}/{d.name}",
                          ignore_patterns=["cache/*"], commit_message=f"wf_v45 W4 step1a {d.name}")
        local = {p.relative_to(d).as_posix(): p.stat().st_size for p in d.rglob("*") if p.is_file() and "cache" not in p.relative_to(d).parts}
        remote = {f.path.split(f"{d.name}/", 1)[1]: f.size for f in api.list_repo_tree(HF_REPO, path_in_repo=f"{HF_DIR}/{d.name}", repo_type="dataset",
                                                                                       recursive=True) if hasattr(f, "size")}
        bad = {k: (v, remote.get(k)) for k, v in local.items() if remote.get(k) != v}
        if bad:
            raise RuntimeError(f"{d.name}: upload size mismatch {bad}")
        out[n] = sorted(local.items())
    return out


def download(sizes=SIZES):
    """Put the uploaded run folders back into results/ (LLM session)."""
    from huggingface_hub import snapshot_download
    tmp = ROOT / "data" / "hf_wf_v45"
    snapshot_download(HF_REPO, repo_type="dataset", local_dir=tmp, allow_patterns=[f"{HF_DIR}/graph_v22_{set_name(n)}/*" for n in sizes])
    import shutil
    for n in sizes:
        src, dst = tmp / HF_DIR / f"graph_v22_{set_name(n)}", CO.run_dir(set_name(n))
        shutil.copytree(src, dst, dirs_exist_ok=True)
    return [CO.run_dir(set_name(n)) for n in sizes]


def times():
    p = OUT / "step1a_times.json"
    return {int(k): v for k, v in json.loads(p.read_text(encoding="utf-8")).items()} if p.exists() else {}


if __name__ == "__main__":
    t = time.time()
    from run import encoder
    print(run_sizes(encoder(), tuple(int(x) for x in sys.argv[1:]) or SIZES))
    print(f"{time.time() - t:.0f}s")
