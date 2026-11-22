"""wf_v4.9 V2: recount the wf_v4.8 W1 main claim with the confirmed human-check -> gold mapping (scoring only, never fed back).

python scripts/mainclaim_v49.py  -> results/wf_v49/v2/{v2.md, v2.csv}
Input: results/wf_v48/w1/<set>/{compare.md, human_check_sheet.csv, human_check_key.csv} (written by scripts/mainclaim_v48.py)
       results/wf_v49/v2/mapping_draft.csv (set,row_id,...,gold_L2,confirm; confirmed by the user 2026-11-22)
A mapped "yes" row counts as a found gold attribute (span + human check) and gets that gold name as its name_match, so it is no longer
"beyond gold" in human_groups_v48.summary.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import pandas as pd  # noqa: E402

import mainclaim_v48 as M48  # noqa: E402
from s1a import human_groups_v48 as H  # noqa: E402
from s1a.mainclaim_v41 import parse_real  # noqa: E402

W1 = M48.OUT
OUT = ROOT / "results" / "wf_v49" / "v2"
MAPPING = OUT / "mapping_draft.csv"


def found_marks(set_name):
    """{source: {gold attribute: entity}} found by span or span + human check, read from the 'Gold attributes found by source' table
    of W1 compare.md (mainclaim_v41 writes it; compare.csv has no per-attribute rows)."""
    lines = (W1 / set_name / "compare.md").read_text(encoding="utf-8").splitlines()
    start = lines.index("## Gold attributes found by source")
    head = next(i for i in range(start, len(lines)) if lines[i].startswith("| entity |"))
    srcs = [c.strip() for c in lines[head].strip("|").split("|")][2:]
    out = {s: {} for s in srcs}
    gold = {}
    for ln in lines[head + 2:]:
        if not ln.startswith("|"):
            break
        cells = [c.strip() for c in ln.strip("|").split("|")]
        ent, attr, marks = cells[0], cells[1], cells[2:]
        gold[attr] = ent
        for s, m in zip(srcs, marks):
            if m in ("yes", "check"):
                out[s][attr] = ent
    return out, gold


def recount(set_name, mapping):
    """Rows (one per source) of found k/n and beyond-gold groups before and after the mapping."""
    found, gold = found_marks(set_name)
    sheet = pd.read_csv(W1 / set_name / "human_check_sheet.csv", dtype=str, keep_default_na=False)
    key = pd.read_csv(W1 / set_name / "human_check_key.csv", dtype=str, keep_default_na=False)
    merged = sheet.merge(key[["id", "source", "item_id", "name_match"]], on="id")
    gmap = mapping[mapping["set"] == set_name].set_index("row_id")["gold_L2"].to_dict()
    unknown = set(gmap.values()) - set(gold)
    if unknown:
        raise ValueError(f"{set_name}: mapped names not in the gold L2 list: {sorted(unknown)}")
    mapped = merged.assign(name_match=[gmap.get(i, nm) for i, nm in zip(merged["id"], merged["name_match"])])
    rows = []
    for src, keep in M48.SOURCES.items():
        part = mapped[mapped["source"].isin(keep)]
        add = {gmap[i] for i, r in zip(part["id"], part["real"]) if i in gmap and parse_real(r)}
        before = H.summary(merged[merged["source"].isin(keep)].to_dict("records"))
        after = H.summary(part.to_dict("records"))
        rows.append({"set": set_name, "source": src, "gold_n": len(gold),
                     "found_human_k_v48": len(found[src]), "found_human_k_v49": len(set(found[src]) | add),
                     "newly_found": "; ".join(sorted(add - set(found[src]))),
                     "beyond_gold_v48": before["new_not_gold"], "beyond_gold_v49": after["new_not_gold"]})
    return rows


def main():
    mapping = pd.read_csv(MAPPING, dtype=str, keep_default_na=False)
    if not mapping["confirm"].str.startswith("yes").all():
        raise ValueError("every mapping row must be confirmed (confirm = yes...) before recounting")
    df = pd.DataFrame([r for s in ("dev50", "dev50b") for r in recount(s, mapping)])
    df.to_csv(OUT / "v2.csv", index=False, encoding="utf-8", lineterminator="\n")
    (OUT / "v2.md").write_text("# wf_v4.9 V2: human-check rows mapped to gold by meaning\n\n" + df.to_markdown(index=False) + "\n",
                               encoding="utf-8", newline="\n")
    print(df.to_string())


if __name__ == "__main__":
    main()
