"""Build the TEAR "Conversation" benchmark from MultiWOZ 2.4.

Usage (from the project root; standard library only):
    python -I data_build/multiwoz.py [--zip PATH] [--out DIR]

Reads MULTIWOZ2.4/data.json from the zip with zipfile/json only, samples 1000
dialogues with random.Random(0), maps the final dialogue state (metadata of the
last system turn) to the 35 attributes of the paper's Table 6, and writes
pool.jsonl, test.jsonl, input.jsonl, levels.json and README.md.
"""

import argparse
import collections
import json
import random
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ZIP = ROOT / "downloads" / "multiwoz" / "MULTIWOZ2.4.zip"
DEFAULT_OUT = ROOT / "data" / "conversation"
DATA_MEMBER = "MULTIWOZ2.4/data.json"

N_TEXTS = 1000
N_TRAIN, N_VAL = 200, 100
LOW_FREQ = 0.15
HIDDEN = {"1": 7, "2": 12, "3": 17}

# (attribute, domain, source, key); source is "semi", "book" or "booked".
MAPPING = [
    ("Attraction name", "attraction", "semi", "name"),
    ("Attraction area", "attraction", "semi", "area"),
    ("Attraction type", "attraction", "semi", "type"),
    ("Hotel name", "hotel", "semi", "name"),
    ("Hotel area", "hotel", "semi", "area"),
    ("Hotel type", "hotel", "semi", "type"),
    ("Hotel parking", "hotel", "semi", "parking"),
    ("Hotel price range", "hotel", "semi", "pricerange"),
    ("Hotel internet", "hotel", "semi", "internet"),
    ("Hotel stars", "hotel", "semi", "stars"),
    ("Hotel requested day", "hotel", "book", "day"),
    ("Hotel requested people", "hotel", "book", "people"),
    ("Hotel requested stay", "hotel", "book", "stay"),
    ("Hotel confirmed name", "hotel", "booked", "name"),
    ("Hotel confirmed reference", "hotel", "booked", "reference"),
    ("Restaurant name", "restaurant", "semi", "name"),
    ("Restaurant area", "restaurant", "semi", "area"),
    ("Restaurant food", "restaurant", "semi", "food"),
    ("Restaurant price range", "restaurant", "semi", "pricerange"),
    ("Restaurant requested day", "restaurant", "book", "day"),
    ("Restaurant requested people", "restaurant", "book", "people"),
    ("Restaurant requested time", "restaurant", "book", "time"),
    ("Restaurant confirmed name", "restaurant", "booked", "name"),
    ("Restaurant confirmed reference", "restaurant", "booked", "reference"),
    ("Taxi departure", "taxi", "semi", "departure"),
    ("Taxi destination", "taxi", "semi", "destination"),
    ("Taxi leave at", "taxi", "semi", "leaveAt"),
    ("Taxi arrive by", "taxi", "semi", "arriveBy"),
    ("Train departure", "train", "semi", "departure"),
    ("Train destination", "train", "semi", "destination"),
    ("Train day", "train", "semi", "day"),
    ("Train leave at", "train", "semi", "leaveAt"),
    ("Train arrive by", "train", "semi", "arriveBy"),
    ("Train requested people", "train", "book", "people"),
    ("Train confirmed reference", "train", "booked", "reference"),
]
SCHEMA = [m[0] for m in MAPPING]
TIME_ATTRS = {"Restaurant requested time", "Taxi leave at", "Taxi arrive by",
              "Train leave at", "Train arrive by"}
DROP = {"", "not mentioned", "none", "dontcare", "dont care", "don't care"}

NUM_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
             "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
             "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]
TEXT_SUBS = [("centre", "center"), ("center", "centre"),
             ("guesthouse", "guest house"), ("guest house", "guesthouse"),
             (" & ", " and "), (" and ", " & "),
             ("theatre", "theater"), ("theater", "theatre")]

# Boundaries: no letter/digit on either side, and do not start or end inside a
# number such as 12:00 or 2.50.
L = r"(?<![0-9a-z])(?<![0-9][:.])"
R = r"(?![0-9a-z])(?![:.,][0-9])"
SEP = r"[^0-9a-z\n]{0,3}"  # flexible separator: spaces, hyphens, apostrophes
FLAGS = re.IGNORECASE


# ----------------------------------------------------------------- text
def clean_turn(text):
    return re.sub(r"\s+", " ", text).strip()


def dialogue_text(log):
    lines = []
    for i, turn in enumerate(log):
        speaker = "User" if i % 2 == 0 else "System"
        lines.append(f"{speaker}: {clean_turn(turn.get('text', ''))}")
    return "\n".join(lines)


# ----------------------------------------------------------------- values
def raw_values(state, domain, source, key):
    """MultiWOZ values for one slot. '|' separates alternatives (all kept),
    'a>b' marks a value changed from a to b (b kept)."""
    dom = state.get(domain) or {}
    if source == "booked":
        found = [b.get(key) for b in (dom.get("book") or {}).get("booked") or []]
    else:
        found = [(dom.get(source) or {}).get(key)]
    out = []
    for v in found:
        if not isinstance(v, str):
            continue
        for part in v.split("|"):
            part = part.split(">")[-1].strip()
            if part.lower() not in DROP and part.lower() not in {p.lower() for p in out}:
                out.append(part)
    return out


def time_patterns(value):
    m = re.fullmatch(r"(\d{1,2})[:.]?(\d{2})", value.strip())
    if not m:
        return []
    h, mi = int(m.group(1)), int(m.group(2))
    if h > 24 or mi > 59:
        return []
    hh, mm = f"{h:02d}", f"{mi:02d}"
    h12 = h % 12 or 12
    ap = r"\s?{}\.?\s?m\.?".format("a" if h % 24 < 12 else "p")
    pats = [f"{hh}:{mm}", f"{h}:{mm}", f"{hh}{mm}", rf"{hh}\.{mm}", rf"{h}\.{mm}",
            f"{h12}:{mm}{ap}", rf"{h12}\.{mm}{ap}", f"{h12}{mm}{ap}"]
    if mi == 0:
        pats += [f"{h12}{ap}", f"{h12} o['’]clock"]
        if h == 12:
            pats += ["noon", "midday"]
        if h % 24 == 0:
            pats += ["midnight"]
    pats += [f"{h12}:{mm}", rf"{h12}\.{mm}"]  # bare 12-hour clock last
    return list(dict.fromkeys(pats))


def number_patterns(value):
    v = value.strip().lower()
    if v.isdigit() and int(v) < len(NUM_WORDS):
        return [NUM_WORDS[int(v)]]
    if v in NUM_WORDS:
        return [str(NUM_WORDS.index(v))]
    return []


def text_variants(value):
    variants = [value.lower()]
    for a, b in TEXT_SUBS:
        variants += [v.replace(a, b) for v in variants if a in v]
    variants += [v[4:] for v in variants if v.startswith("the ")]
    return list(dict.fromkeys(variants))


def flexible_pattern(variant):
    toks = re.findall(r"[a-z0-9]+", variant.lower())
    if not toks:
        return None
    parts = []
    for t in toks:
        if t.isalpha() and len(t) > 3:  # optional possessive/plural s
            base = t[:-1] if t.endswith("s") else t
            parts.append(re.escape(base) + r"(?:['’]?s)?")
        else:
            parts.append(re.escape(t))
    return SEP.join(parts)


def find_span(value, text, is_time):
    """Return (span, method). The span is a substring of text when found."""
    def search(pat, bounded=True):
        m = re.search(L + pat + R if bounded else pat, text, FLAGS)
        return text[m.start():m.end()] if m else None

    span = search(re.escape(value))
    if span:
        return span, "exact"
    typed = time_patterns(value) if is_time else number_patterns(value)
    for pat in typed:
        span = search(pat)
        if span:
            return span, "time" if is_time else "number"
    variants = text_variants(value)
    for var in variants[1:]:
        span = search(re.escape(var))
        if span:
            return span, "variant"
    for var in variants:
        pat = flexible_pattern(var)
        span = search(pat) if pat else None
        if span:
            return span, "flexible"
    span = search(re.escape(value), bounded=False)
    if span:
        return span, "substring"
    return value, "not_found"


def build_table(state, text, methods):
    headers, cells = [], []
    for attr, domain, source, key in MAPPING:
        cell = []
        for v in raw_values(state, domain, source, key):
            span, how = find_span(v, text, attr in TIME_ATTRS)
            methods[how] += 1
            if span not in cell:
                cell.append(span)
        if cell:
            headers.append(attr)
            cells.append(cell)
    return {"headers": headers, "rows": [cells]} if headers else None


# ----------------------------------------------------------------- survey
def key_survey(data):
    semi, book, booked = (collections.defaultdict(set) for _ in range(3))
    for d in data.values():
        state = d["log"][-1].get("metadata") or {}
        for dom, v in state.items():
            semi[dom].update((v.get("semi") or {}).keys())
            b = v.get("book") or {}
            book[dom].update(k for k in b if k != "booked")
            for e in b.get("booked") or []:
                booked[dom].update(e.keys())
    used = {(m[1], m[2], m[3]) for m in MAPPING}
    lines = []
    for dom in sorted(set(semi) | set(book) | set(booked)):
        for src, keys in (("semi", semi[dom]), ("book", book[dom]), ("booked", booked[dom])):
            if not keys:
                continue
            fmt = [k if (dom, src, k) in used else f"{k}(unmapped)" for k in sorted(keys)]
            lines.append(f"  {dom}.{src}: {', '.join(fmt)}")
    return lines


# ----------------------------------------------------------------- main
def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--zip", type=Path, default=DEFAULT_ZIP)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    with zipfile.ZipFile(args.zip) as z:
        data = json.loads(z.read(DATA_MEMBER).decode("utf-8"))
    print(f"Loaded {len(data)} dialogues from {args.zip.name}")
    print("Final-state keys (metadata of the last system turn):")
    for line in key_survey(data):
        print(line)

    rng = random.Random(0)
    ids = sorted(data)
    methods = collections.Counter()
    records, skipped, used = {}, [], set()
    queue = rng.sample(ids, N_TEXTS)
    while True:
        used.update(queue)
        for did in queue:
            log = data[did]["log"]
            text = dialogue_text(log)
            state = log[-1].get("metadata") or {}
            table = build_table(state, text, methods)
            if table is None:
                skipped.append(did)
            else:
                records[did] = {"id": did.removesuffix(".json"), "text": text, "table": table}
        need = N_TEXTS - len(records)
        if need == 0:
            break
        rest = [i for i in ids if i not in used]
        queue = rng.sample(rest, need)
    recs = [records[k] for k in sorted(records)]

    # Splits: 300 labeled (200 train, 100 val), 700 test in a shuffled order.
    pool_idx = rng.sample(range(N_TEXTS), N_TRAIN + N_VAL)
    pool = [dict(id=recs[i]["id"], split="train" if j < N_TRAIN else "val",
                 text=recs[i]["text"], table=recs[i]["table"])
            for j, i in enumerate(pool_idx)]
    chosen = set(pool_idx)
    test_idx = [i for i in range(N_TEXTS) if i not in chosen]
    rng.shuffle(test_idx)
    test = [recs[i] for i in test_idx]
    inputs = [{"id": r["id"], "text": r["text"], "schema": SCHEMA} for r in test]

    # Exploratory levels.
    counts = collections.Counter(h for r in recs for h in r["table"]["headers"])
    coverage = {a: counts[a] / N_TEXTS for a in SCHEMA}
    low = [a for a in SCHEMA if coverage[a] < LOW_FREQ]
    rng.shuffle(low)
    rest = sorted((a for a in SCHEMA if a not in low), key=lambda a: (coverage[a], SCHEMA.index(a)))
    order = low + rest
    warnings, levels = [], {}
    for lvl, k in HIDDEN.items():
        if k > len(low):
            warnings.append(f"WARNING: level {lvl} hides {k} but only {len(low)} attributes have "
                            f"coverage < {LOW_FREQ:.0%}; filled with {k - len(low)} next-lowest: "
                            f"{', '.join(order[len(low):k])}")
        hidden = set(order[:k])
        levels[lvl] = {"schema": [a for a in SCHEMA if a not in hidden],
                       "hidden": [a for a in SCHEMA if a in hidden]}

    args.out.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out / "pool.jsonl", pool)
    write_jsonl(args.out / "test.jsonl", test)
    write_jsonl(args.out / "input.jsonl", inputs)
    with open(args.out / "levels.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump({"full_schema": SCHEMA, "coverage": {a: round(c, 4) for a, c in coverage.items()},
                   "levels": levels}, f, ensure_ascii=False, indent=1)

    # Summary.
    ws = [len(r["text"].split()) for r in recs]
    wp = [len(re.findall(r"\w+|[^\w\s]", r["text"])) for r in recs]
    cols = [len(r["table"]["headers"]) for r in recs]
    spans = [s for r in recs for cell in r["table"]["rows"][0] for s in cell]
    in_text = sum(s in r["text"] for r in recs for cell in r["table"]["rows"][0] for s in cell)
    multi = sum(len(cell) > 1 for r in recs for cell in r["table"]["rows"][0])
    n_vals = sum(methods.values())
    lines = [
        "# Conversation benchmark (MultiWOZ 2.4)",
        "",
        "Built by `python -I data_build/multiwoz.py` from `downloads/multiwoz/MULTIWOZ2.4.zip`"
        " (`MULTIWOZ2.4/data.json`), seed `random.Random(0)`.",
        "Text: the full dialogue, one `User:` / `System:` line per turn."
        " Gold: the final dialogue state (metadata of the last system turn) mapped to the"
        " 35 Table 6 attributes; one record per text; each cell is a list of spans.",
        "",
        "## Counts",
        f"- Dialogues in data.json: {len(data)}. Sampled texts: {len(recs)}"
        f" (skipped {len(skipped)} with an empty table and drew replacements).",
        f"- pool.jsonl: {len(pool)} ({N_TRAIN} train, {N_VAL} val). test.jsonl and input.jsonl: {len(test)}.",
        f"- Tokens per text (whitespace): avg {sum(ws) / len(ws):.1f}, max {max(ws)}"
        f" (words+punctuation: avg {sum(wp) / len(wp):.1f}, max {max(wp)}). Paper: avg 303, max 938.",
        f"- Columns per table: avg {sum(cols) / len(cols):.2f}, max {max(cols)}, min {min(cols)}."
        f" Paper: avg 8.3, max 24.",
        f"- Values (spans): {len(spans)}; cells with more than one span: {multi}.",
        f"- Values that are exact spans of their text: {in_text}/{len(spans)} = {in_text / len(spans):.1%}.",
        "- Match method per value: " + ", ".join(f"{k} {v} ({v / n_vals:.1%})"
                                                 for k, v in methods.most_common()) + ".",
        "",
        "## Attribute coverage (share of the 1000 texts)",
        "",
        "| Attribute | Coverage | Hidden at level |",
        "|---|---|---|",
    ]
    for a in SCHEMA:
        lv = next((lvl for lvl in HIDDEN if a in levels[lvl]["hidden"]), "")
        lines.append(f"| {a} | {coverage[a]:.3f} | {lv} |")
    lines += ["", f"Low-frequency attributes (coverage < {LOW_FREQ:.0%}): {len(low)}.", ""]
    for lvl, k in HIDDEN.items():
        lines.append(f"- Level {lvl}: hides {k}, schema {len(levels[lvl]['schema'])}:"
                     f" {', '.join(levels[lvl]['hidden'])}.")
    lines += [f"- {w}" for w in warnings]
    lines += ["", "## Files",
              "- `pool.jsonl`: {id, split, text, table}; `split` is train or val.",
              "- `test.jsonl`: {id, text, table}. `input.jsonl`: {id, text, schema} (full 35-attribute schema), same order.",
              "- `levels.json`: {full_schema, coverage, levels: {1|2|3: {schema, hidden}}}.",
              "- Table format: {\"headers\": [...], \"rows\": [[cell, ...]]}, cell = list of strings."]
    summary = "\n".join(lines) + "\n"
    (args.out / "README.md").write_text(summary, encoding="utf-8", newline="\n")
    print()
    print(summary)
    for w in warnings:
        print(w)
    print("Skipped (empty table):", ", ".join(skipped) if skipped else "none")


if __name__ == "__main__":
    main()
