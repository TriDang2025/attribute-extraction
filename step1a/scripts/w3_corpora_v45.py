"""wf_v4.5 (diary Nov 15) W3: nested test corpora for the cost test (no labels).

python scripts/w3_corpora_v45.py [--mwoz C:/Users/nguye/data/MultiWOZ_2.2] [--seed 0]
-> data/wf_v45_corpora/n<size>.jsonl ({"id", "text"} per line; gitignored, rebuildable) and results/wf_v45/w3/{ids.json, data_card.md}

Sizes 50-300 = the TEAR non-test pool in its own order (so n50 = dev50, n100 = dev50 + dev50b). Sizes 500 and 1000 = n300 plus raw
MultiWOZ 2.2 dialogues (all splits, seeded shuffle) that are not in TEAR's test set and not in the pool, checked by dialogue id and by a
text hash (lowercase letters and digits only, so TEAR's spacing clean-up does not hide a copy). Extra texts use TEAR's format
("User: ..." / "System: ..." lines) with the space before . , ! ? removed as TEAR does.
"""
import argparse
import glob
import hashlib
import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEAR = ROOT.parent / "tear" / "data" / "conversation"
OUT_DATA = ROOT / "data" / "wf_v45_corpora"
OUT = ROOT / "results" / "wf_v45" / "w3"
SIZES = (50, 100, 200, 300, 500, 1000)


def read_jsonl(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def text_hash(t):
    return hashlib.sha1(re.sub(r"[^a-z0-9]", "", t.lower()).encode()).hexdigest()


def mwoz_text(d):
    t = "\n".join(("User: " if u["speaker"] == "USER" else "System: ") + u["utterance"] for u in d["turns"])
    return re.sub(r" +([.,!?])", r"\1", t)


def load_mwoz(root):
    out = {}
    for f in sorted(glob.glob(str(Path(root) / "*" / "dialogues_*.json"))):
        for d in json.load(open(f, encoding="utf-8")):
            out[d["dialogue_id"].removesuffix(".json")] = mwoz_text(d)
    return out


def build(mwoz_root, seed=0):
    pool, test = read_jsonl(TEAR / "pool.jsonl"), read_jsonl(TEAR / "test.jsonl")
    mwoz = load_mwoz(mwoz_root)
    used_ids = {r["id"] for r in pool} | {r["id"] for r in test}
    used_hash = {text_hash(r["text"]) for r in pool + test}
    cand = sorted(mwoz)
    by_id = [i for i in cand if i not in used_ids]
    kept = [i for i in by_id if text_hash(mwoz[i]) not in used_hash]
    random.Random(seed).shuffle(kept)
    rows = [{"id": r["id"], "text": r["text"], "source": "tear_pool"} for r in pool]
    rows += [{"id": i, "text": mwoz[i], "source": "multiwoz22"} for i in kept[:max(SIZES) - len(pool)]]
    seen = set()
    for r in rows:  # no duplicate text inside the corpus either
        h = text_hash(r["text"])
        assert h not in seen, f"duplicate text {r['id']}"
        seen.add(h)
    counts = {"multiwoz_dialogues": len(cand), "removed_by_id": len(cand) - len(by_id), "removed_by_text_hash": len(by_id) - len(kept),
              "kept_candidates": len(kept), "extra_used": len(rows) - len(pool), "tear_test_ids_in_mwoz": len({r["id"] for r in test} & set(mwoz)),
              "pool_format_match": sum(mwoz.get(r["id"]) == r["text"] for r in pool)}
    return rows, counts


def write(rows, counts, seed, mwoz_root):
    OUT_DATA.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    for n in SIZES:
        with open(OUT_DATA / f"n{n}.jsonl", "w", encoding="utf-8", newline="\n") as f:
            for r in rows[:n]:
                f.write(json.dumps({"id": r["id"], "text": r["text"]}, ensure_ascii=False) + "\n")
    ids = {f"n{n}": [r["id"] for r in rows[:n]] for n in SIZES}
    (OUT / "ids.json").write_text(json.dumps({"seed": seed, "counts": counts, "ids": ids}, indent=1) + "\n", encoding="utf-8", newline="\n")
    chars = {n: sum(len(r["text"]) for r in rows[:n]) for n in SIZES}
    lines = ["# wf_v4.5 W3: cost-test corpora (data card)", "",
             "- **Use:** cost test only (no labels, nothing tuned on them).",
             "- **Sizes:** " + ", ".join(map(str, SIZES)) + "; each smaller set is the start of the bigger one.",
             "- **50-300:** TEAR's non-test pool (`tear/data/conversation/pool.jsonl`) in its own order: n50 = dev50, n100 = dev50 + dev50b.",
             f"- **500, 1000:** n300 plus raw MultiWOZ 2.2 dialogues (`{Path(mwoz_root).as_posix()}`, train + dev + test files), "
             f"shuffled with seed {seed}. Text built as TEAR does: `User:` / `System:` lines, space before . , ! ? removed.",
             "- **Overlap check** against TEAR's test set (700) and the pool (300), by dialogue id and by text hash (sha1 of lowercase letters and digits):", "",
             "| count | value |", "|---|---|"]
    lines += [f"| {k.replace('_', ' ')} | {v} |" for k, v in counts.items()]
    lines += ["", f"Format check: rebuilding the pool from MultiWOZ this way gives TEAR's exact text for {counts['pool_format_match']}/300 "
              "dialogues; the rest differ only in TEAR's other small clean-ups, so the extra texts are close to, not identical with, TEAR's format."]
    lines += ["", "| corpus | dialogues | from pool | from MultiWOZ | characters |", "|---|---|---|---|---|"]
    lines += [f"| n{n} | {n} | {min(n, 300)} | {max(0, n - 300)} | {chars[n]:,} |" for n in SIZES]
    lines += ["", "Files: `data/wf_v45_corpora/n<size>.jsonl` (gitignored; rebuild with `python scripts/w3_corpora_v45.py`), ids in `results/wf_v45/w3/ids.json`."]
    (OUT / "data_card.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mwoz", default="C:/Users/nguye/data/MultiWOZ_2.2")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    rows, counts = build(a.mwoz, a.seed)
    print(write(rows, counts, a.seed, a.mwoz))


if __name__ == "__main__":
    main()
