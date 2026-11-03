"""Export the current attribute ground truth (L1 TEAR gold, L2 MultiWOZ 2.2 slots, L3 MultiWOZ 2.4 DB columns) to one
plain-text file, readable without code (diary 2 Nov 2026, task 0). No LLM, no models.

python scripts/export_attribute_gt.py --mwoz C:/Users/nguye/data/MultiWOZ_2.2
Reads the GT level tables written by gt_v35.py; the pure formatting / counting functions at the top are tested in
tests/test_export_attribute_gt.py.
"""

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from s1a import gt_ext as GT  # noqa: E402
from s1a import mentions as MN  # noqa: E402
from s1a import pilot_input as PIN  # noqa: E402
from s1a import value_types as VT  # noqa: E402
from s1a.v34_data import read_gt_levels  # noqa: E402

DB_ZIP = ROOT.parent / "chunking" / "data" / "MULTIWOZ2.4.zip"
LEVELS_JSON = ROOT.parent / "tear" / "data" / "conversation" / "levels.json"
REPORTS = Path("C:/Users/nguye/OneDrive/Desktop/Work/TEAR/report/3_main")
ENTITIES = ("train", "hotel", "restaurant", "taxi", "attraction")
SETS = ("dev50", "dev50b")
DB_DOMAINS = ("train", "hotel", "restaurant")  # the domains GT_ext.load_db reads (L3)
SHORT_VALUES = 8  # possible values listed when the slot has at most this many
OWN_DESCRIPTION = {  # attributes without a schema.json description (marked "own" in the file)
    "Hotel confirmed name": "name of the hotel the system confirmed in a booking",
    "Restaurant confirmed name": "name of the restaurant the system confirmed in a booking",
}


# ---------- pure functions (tested) ----------

def split_labels(s):
    """"A;B" -> ["A", "B"]; "" -> []."""
    return [x for x in str(s).split(";") if x]


def attr_counts(df, label_col="gt_L3"):
    """{attr: Counter(user=, system=)}: mentions per label and speaker (one count per label of a multi-label mention)."""
    out = {}
    for lab, sp in zip(df[label_col], df["speaker"]):
        for a in split_labels(lab):
            out.setdefault(a, Counter())[sp] += 1
    return out


def majority(items):
    """(most common item, its count, total); ("", 0, 0) when empty. Ties: the first seen."""
    c = Counter(items)
    if not c:
        return "", 0, 0
    top, n = c.most_common(1)[0]
    return top, n, sum(c.values())


def top_values(values, k=5):
    """Most frequent distinct values: [(value, count)], ties in first-seen order, empty values skipped."""
    return Counter(v for v in values if v).most_common(k)


def level_of(name, tear_names, slot):
    """Lowest level that has the attribute: L1 = TEAR gold attribute, L2 = MultiWOZ 2.2 schema slot, else L3 (DB column)."""
    if name in tear_names:
        return "L1"
    return "L2" if slot else "L3"


def role_partner(name, pairs):
    """The attribute that names the same value type in the other role ("Train departure" -> "Train destination"), or ""."""
    ent, _, rest = name.partition(" ")
    for p in pairs:
        if ent.lower() in p["entities"] and rest in p["slots"]:
            other = [s for s in p["slots"] if s != rest][0]
            return f"{ent} {other}"
    return ""


def fmt_counts(c):
    """Counter(user=, system=) -> "user 3, system 5 (total 8)"."""
    u, s = c.get("user", 0), c.get("system", 0)
    return f"user {u}, system {s} (total {u + s})"


def format_block(d):
    """One attribute block: a title line, then aligned "key: value" lines (d["fields"] = [(key, value)])."""
    width = max(len(k) for k, _ in d["fields"])
    return "\n".join([d["name"]] + [f"  {k.ljust(width)} : {v}" for k, v in d["fields"]])


def md_rows(text):
    """Rows of the first markdown table in `text` as lists of cells (header and separator dropped)."""
    rows = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in text.splitlines() if ln.startswith("|")]
    return [r for r in rows[2:]]


def quote_lines(path, needles):
    """Lines of the text file `path` that contain any of `needles` (stripped, markdown ** and ` removed); [] when the
    file is missing."""
    p = Path(path)
    if not p.exists():
        return []
    return [ln.strip().replace("**", "").replace("`", "") for ln in p.read_text(encoding="utf-8").splitlines()
            if any(n in ln for n in needles)]


# ---------- IO ----------

def git_state(repo):
    head = subprocess.run(["git", "-C", str(repo), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=no"],
                           capture_output=True, text=True).stdout.strip()
    return head + (" with uncommitted scoring changes" if dirty else "")


def load_set(run, gt_dir, ids_from=None):
    """(mentions with speaker + gt level columns, match table) of one set. `run` = results/graph_* dir."""
    ment = pd.read_csv(run / "spans" / "mentions.csv", keep_default_na=False)
    ment["mention_id"] = ment["mention_id"].astype(int)
    docs, _gv, _attrs = MN.load_shared(run)
    ment["speaker"] = [PIN._speaker(docs[d], int(t)) for d, t in zip(ment["dialogue_id"], ment["turn"])]
    gt = read_gt_levels(gt_dir / "gt_levels.csv")
    gt["mention_id"] = gt["mention_id"].astype(int)
    ment = ment.merge(gt, on="mention_id", how="left")
    match = pd.read_csv(gt_dir / "mwoz_match.csv", keep_default_na=False)
    return ment, match


def build_universe(tear_names, tear_map, schema, seen):
    """{attribute name: dict(entity, tear, slot, column, description, categorical)} for the entities."""
    u = {}

    def add(name, **kw):
        d = u.setdefault(name, {"entity": name.split()[0].lower(), "tear": "", "slot": "", "desc": "", "cat": ""})
        d.update({k: v for k, v in kw.items() if v})

    for n in tear_names:
        add(n, tear=n, slot=tear_map.get(n, ""))
    for slot, info in schema.items():
        dom, _, rest = slot.partition("-")
        if dom in ENTITIES:
            cat = ""
            if info.get("is_categorical") and 0 < len(info.get("possible_values", [])) <= SHORT_VALUES:
                cat = "categorical: " + ", ".join(info["possible_values"])
            add(GT.slot_name(dom, rest, tear_map), slot=slot, desc=info.get("description", ""), cat=cat)
    for n in seen:
        add(n)
    return u


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mwoz", required=True)
    ap.add_argument("--dev50", default=str(ROOT / "results" / "graph_v22_dev50"))
    ap.add_argument("--dev50-gt", default=str(ROOT / "results" / "loop1_v35"))
    ap.add_argument("--dev50b", default=str(ROOT / "results" / "graph_v22_dev50b"))
    ap.add_argument("--dev50b-gt", default=str(ROOT / "results" / "loop1_v37" / "dev50b" / "gt"))
    ap.add_argument("--out", default=str(ROOT / "gt" / "attribute_gt_2026-11-02.txt"))
    ap.add_argument("--date", default="2026-11-02")
    a = ap.parse_args()

    runs = {"dev50": (Path(a.dev50), Path(a.dev50_gt)), "dev50b": (Path(a.dev50b), Path(a.dev50b_gt))}
    data = {s: load_set(*runs[s]) for s in SETS}
    tear_map = json.loads((ROOT / "config" / "tear_to_mwoz.json").read_text(encoding="utf-8"))
    pairs = json.loads((ROOT / "config" / "role_pairs.json").read_text(encoding="utf-8"))["pairs"]
    tear_names = json.loads(LEVELS_JSON.read_text(encoding="utf-8"))["full_schema"]
    schema_path = Path(a.mwoz) / "schema.json"
    schema = {s["name"]: s for svc in json.loads(schema_path.read_text(encoding="utf-8")) for s in svc["slots"]}
    db = GT.load_db(DB_ZIP)
    db_cols = {d: sorted({c for r in rows for c in r}) for d, rows in db.items()}

    counts = {s: attr_counts(data[s][0]) for s in SETS}
    seen = sorted({n for s in SETS for n in counts[s]})
    universe = build_universe(tear_names, tear_map, schema, seen)
    # entities that appear: the always-listed four, attraction only if some dev label is an attraction attribute
    ents = [e for e in ENTITIES if e != "attraction" or any(n.startswith("Attraction") for n in seen)]
    col_of = {GT.column_name(d, c, tear_map): c for d, cols in db_cols.items() for c in cols}
    all_m = pd.concat([data[s][0] for s in SETS])
    labelled = all_m[all_m["gt_L3"] != ""]
    by_attr = {}
    for text, nv, lab in zip(labelled["text"], labelled["norm_value"], labelled["gt_L3"]):
        for x in split_labels(lab):
            by_attr.setdefault(x, []).append((text, nv))

    lines = [f"Attribute ground truth (GT), exported {a.date}", f"git commit: {git_state(ROOT)}",
             "scoring rules: v1.1 (RULES_V1_1.md)", "",
             "Levels: L1 = TEAR gold (user goal); L2 = L1 + MultiWOZ 2.2 schema slots (span labels); "
             "L3 = L2 + MultiWOZ 2.4 database columns (exact value match, same domain, not id-like, value in <= 30% of rows).",
             "Counts: mentions of dev50 (50 dialogues) and dev50b (50 dialogues) per attribute, by the final (L3) label of the "
             "mention, split by who said it. A mention with a multi-attribute label counts once for each attribute.",
             "Level of an attribute: the lowest level that has it (L1 = TEAR attribute, L2 = schema slot, L3 = database column only).",
             "", "Source files:"]
    src = [f"  TEAR levels (full schema): {LEVELS_JSON.resolve()}",
           f"  TEAR to MultiWOZ map: {ROOT / 'config' / 'tear_to_mwoz.json'}",
           f"  role pairs: {ROOT / 'config' / 'role_pairs.json'}",
           f"  MultiWOZ 2.2 schema: {schema_path}",
           f"  MultiWOZ 2.2 dialogues and acts: {Path(a.mwoz)} (train/dev/test dialogues_*.json, dialog_acts.json)",
           f"  MultiWOZ 2.4 databases (read in place): {DB_ZIP.resolve()} (MULTIWOZ2.4/<domain>_db.json)"]
    for s in SETS:
        run, gt = runs[s]
        src += [f"  {s} mentions: {run / 'spans' / 'mentions.csv'}", f"  {s} turns (speaker): {run / 'docs.jsonl'}",
                f"  {s} GT levels: {gt / 'gt_levels.csv'}", f"  {s} MultiWOZ match: {gt / 'mwoz_match.csv'}",
                f"  {s} match failures: {gt / 'match_failures.csv'}"]
    lines += src + [""]

    block_count = {}
    for ent in ents:
        names = sorted((n for n, d in universe.items() if d["entity"] == ent),
                       key=lambda n: ("L1L2L3".index(level_of(n, tear_names, universe[n]["slot"])), n))
        block_count[ent] = len(names)
        lines += ["=" * 78, f"ENTITY: {ent} ({len(names)} attributes)", "=" * 78, ""]
        for n in names:
            d = universe[n]
            vals = by_attr.get(n, [])
            vt, k, tot = majority([VT.value_type_v35(t) for t, _ in vals])
            vtype = f"{vt} ({k} of {tot} mentions)" if tot else "unknown (no dev mention)"
            if d["cat"]:
                vtype += "; " + d["cat"]
            col = col_of.get(n, "")
            if ent not in DB_DOMAINS:
                dbc = "n/a (domain not in the L3 database)"
            else:
                dbc = f"yes (column {col})" if col else "no"
            if d["desc"]:
                desc = d["desc"]
            elif n in OWN_DESCRIPTION:
                desc = OWN_DESCRIPTION[n] + " (own description, no schema description)"
            else:
                desc = f"{col or 'database'} column of the {ent} database, not a schema slot (own description, no schema description)"
            lvl = level_of(n, tear_names, d["slot"])
            fields = [("TEAR name", d["tear"] or "none"),
                      ("MultiWOZ 2.2 slot", d["slot"] or "none (no schema slot)"),
                      ("level", lvl), ("description", desc), ("value type", vtype),
                      ("role partner", role_partner(n, pairs) or "none"), ("database column", dbc)]
            fields += [(f"mentions {s}", fmt_counts(counts[s].get(n, Counter()))) for s in SETS]
            ex = top_values([nv for _, nv in vals])
            fields.append(("examples", "; ".join(f"{v} ({c})" for v, c in ex) if ex else "none"))
            lines += [format_block({"name": n, "fields": fields}), ""]

    # section 1
    lines += ["=" * 78, "SECTION 1: TEAR to MultiWOZ map (config/tear_to_mwoz.json)", "=" * 78, ""]
    lines += [f"{k}: {v}" for k, v in tear_map.items() if not k.startswith("_")]
    lines += ["", "Reason (_notes): " + tear_map.get("_notes", "(missing)"), ""]
    unmapped = [n for n in tear_names if n not in tear_map]
    lines += ["TEAR attributes (levels.json full schema) with no map row: " + (", ".join(unmapped) or "none"), ""]

    # section 2
    lines += ["=" * 78, "SECTION 2: database columns that are not schema slots", "=" * 78, "",
              "Columns of MultiWOZ 2.4 <domain>_db.json with no schema.json slot; 'dev mentions' = mentions of dev50 + dev50b "
              "with that L3 label. id and location columns are id-like and never used."]
    for dom in DB_DOMAINS:
        lines += ["", f"{dom}:"]
        for c in db_cols[dom]:
            if c.lower() in GT.SKIP_COLUMNS or universe.get(GT.column_name(dom, c, tear_map), {}).get("slot"):
                continue
            n = GT.column_name(dom, c, tear_map)
            tot = sum(sum(counts[s].get(n, Counter()).values()) for s in SETS)
            lines.append(f"  {c}: label '{n}', {tot} dev mentions" + (" (dict of room prices, never matched)" if c == "price" and dom == "hotel" else ""))
    lines += [""]

    # section 3 and 4 need act rows of both sets
    ids = {s: set(data[s][0]["dialogue_id"]) for s in SETS}
    dialogues, acts = GT.load_mwoz(a.mwoz, ids["dev50"] | ids["dev50b"])
    sp = GT.span_table(dialogues, acts)
    lines += ["=" * 78, "SECTION 3: slots used as GT for attribute_cue (request acts, MultiWOZ '*-Request')", "=" * 78, "",
              "acts = turns with a request act for the slot (from dialog_acts.json); mentions = dev mentions in such a turn "
              "that are the question phrase (is_request in gt_levels.csv). Booking requests belong to the dialogue's entity."]
    req = sp[sp["act"] == "request"]
    keys = sorted(set(req["domain"] + "-" + req["slot"]) | {x for s in SETS for x in data[s][0]["request_slot"] if x})
    rows = []
    for k in keys:
        parts = []
        tot = 0
        for s in SETS:
            r = req[(req["dialogue_id"].isin(ids[s])) & (req["domain"] + "-" + req["slot"] == k)]
            m = data[s][0]
            nm = int((m["request_slot"] == k).sum())
            tot += len(r) + nm
            parts.append(f"{s} acts {len(r)} (user {int((r['speaker'] == 'user').sum())}, system {int((r['speaker'] == 'system').sum())}), mentions {nm}")
        rows.append((tot, f"{k}: " + "; ".join(parts)))
    lines += [t for _, t in sorted(rows, key=lambda x: (-x[0], x[1]))] + [""]

    lines += ["=" * 78, "SECTION 4: 'choice' as noise", "=" * 78, ""]
    lines += quote_lines(ROOT / "RULES_V1.md", ["**choice**"]) or ["(RULES_V1.md not found)"]
    for s in SETS:
        m = data[s][0]
        c = m[m["is_choice"] == True]  # noqa: E712
        lab = ", ".join(f"L{i} {int((c[f'gt_L{i}'] != '').sum())}" for i in (1, 2, 3))
        lines.append(f"{s}: {len(c)} choice mentions (user {int((c['speaker'] == 'user').sum())}, system {int((c['speaker'] == 'system').sum())}) "
                     f"of {len(m)} mentions; of these with a non-empty label: {lab} (a TEAR gold label can sit on a choice mention)")
    lines += [""]

    lines += ["=" * 78, "SECTION 5: known gaps", "=" * 78, ""]
    for s in SETS:
        m, match = data[s]
        run, gt = runs[s]
        none = match[match["match"] == "none"]
        sp_of = m.set_index("mention_id")["speaker"]
        spk = Counter(sp_of.reindex(none["mention_id"].astype(int)).fillna("unknown"))
        fails = pd.read_csv(gt / "match_failures.csv", keep_default_na=False)
        lines += [f"{s}: unmatched mentions (match == none): {GT.fmt_count(len(none), len(match))}; "
                  f"user {spk.get('user', 0)}, system {spk.get('system', 0)}",
                  f"  match failures file (turn text not matched): {gt / 'match_failures.csv'}, {len(fails)} rows"]
    kinds = ROOT / "results" / "loop1_v36" / "unmatched_kinds.md"
    lines += ["", f"Unmatched dev50 mentions by kind ({kinds}), kind: n (share):"]
    rows = md_rows(kinds.read_text(encoding="utf-8")) if kinds.exists() else []
    lines += [f"  {r[0]}: {r[1]} ({r[2]})" for r in rows] or ["  file not found"]
    lines += ["  not computed for dev50b."]
    r35 = REPORTS / "wf_v3.5" / "wf_v3.5_report.md"
    r36 = REPORTS / "wf_v3.6" / "wf_v3.6_report.md"
    lines += ["", f"Label errors found in earlier checks (quoted from {r35}):"]
    lines += [f"  {x}" for x in quote_lines(r35, ["Label check (T7)", "Cases where the GT looks wrong"])] or ["  not found"]
    lines += [f"Unmatched mentions, v3.6 (quoted from {r36}):"]
    lines += [f"  {x}" for x in quote_lines(r36, ["A Haiku pass splits the 59"])] or ["  not found"]
    lines += [f"Label check sheet: {ROOT / 'results' / 'loop1_v35' / 'label_check.csv'}", ""]

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"wrote {out}")
    for ent in ents:
        print(f"{ent}: {block_count[ent]} attribute blocks")


if __name__ == "__main__":
    main()
