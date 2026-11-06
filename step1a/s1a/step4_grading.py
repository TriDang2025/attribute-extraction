"""wf_v4 task 9: blind grading packets (pure helpers; files are read and written by scripts/packets_v4.py).

A packet = the approved rubric prompt (config/wf_v4_grading_prompt.txt, copied from grading_rubric_v1.md) with its placeholders filled.
Per set 8 candidates: a, b, c2, e, f, d (pipeline outputs), gt (the GT main design as a candidate) and gt_planted (the GT with 3 planted
errors: two tables merged, one foreign key removed, one column moved to a wrong table; chosen by a seeded rng per set).
"""
import copy
import random
import re
from itertools import combinations

KINDS = ("a", "b", "c2", "e", "f", "d", "gt", "gt_planted")
SETS = ("dev50", "dev50b")
JUDGES = ("claude", "chatgpt")
ALTERNATIVES = ("booking columns may be in the place table instead of a separate booking table (train, hotel, restaurant); "
                "then the booking id and link columns are not needed")
QUESTIONS = ["Which train did the user book, and for how many people?",
             "When does that train leave and arrive, and from where to where?",
             "Which hotel did the user book, for which day, for how many nights and for how many people?",
             "Which hotels in a given area have free parking, and how many stars do they have?",
             "What is the reference number of a restaurant booking, and what is that restaurant's phone number?",
             "Which cheap restaurants in the centre serve a given food?",
             "Where does a booked taxi go from and to, and what is its phone number and car type?",
             "What is the address and entrance fee of an attraction?"]
CONSONANTS = "BCDFGHJKLMNPQRSTVWXZ"
_ALT = re.compile(r'\[ALTERNATIVES[^\]]*\]')


def make_codes(n, seed):
    """n distinct random 4-letter codes (consonants only, so no word appears)."""
    rng, out = random.Random(f"{seed}:codes"), []
    while len(out) < n:
        c = "".join(rng.choice(CONSONANTS) for _ in range(4))
        if c not in out:
            out.append(c)
    return out


def strip_sql(sql):
    """SQL without comments (-- and /* */) and without blank runs; nothing else is changed."""
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.S)
    lines = [re.sub(r"\s*--.*$", "", l).rstrip() for l in sql.splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip() + "\n"


def fill_prompt(template, code, gt_sql, candidate_sql, questions=QUESTIONS, alternatives=ALTERNATIVES):
    """The packet text. Fails when a placeholder is missing from the template."""
    for ph in ("[Q1..Q8]", "[GT SQL]", "[CANDIDATE SQL]", "[CODE]"):
        if ph not in template:
            raise ValueError(f"placeholder {ph} missing")
    if not _ALT.search(template):
        raise ValueError("placeholder [ALTERNATIVES ...] missing")
    qs = "\n".join(f"{i}. {q}" for i, q in enumerate(questions, 1))
    text = _ALT.sub(lambda m: alternatives, template)
    for ph, val in (("[Q1..Q8]", qs), ("[GT SQL]", gt_sql.strip()), ("[CANDIDATE SQL]", candidate_sql.strip())):
        text = text.replace(ph, val)
    return text.replace("[CODE]", code)


def plant_errors(canon, seed, tag):
    """(planted canonical copy, [error dicts]) with three errors in this order: merge two place tables (the second is folded into the
    first, foreign keys to it are redirected), remove one foreign key (and its relationship), move one plain column to a table of
    another entity. Deterministic in (seed, tag). Each error has kind, text and keywords (lower case, for the reason check)."""
    rng = random.Random(f"{seed}:plant:{tag}")
    c = copy.deepcopy(canon)
    tabs = {t["name"]: t for t in c["tables"]}
    place = sorted(n for n in tabs if not n.endswith("_booking"))
    a, b = rng.choice(sorted(combinations(place, 2)))
    tabs[a]["columns"] += tabs[b]["columns"]
    tabs[a]["foreign_keys"] += tabs[b]["foreign_keys"]
    c["tables"] = [t for t in c["tables"] if t["name"] != b]
    for t in c["tables"]:
        for f in t["foreign_keys"]:
            if f["ref_table"] == b:
                f["ref_table"] = a
    rels, seen = [], set()
    for r in c["relationships"]:
        r = {**r, "from": a if r["from"] == b else r["from"], "to": a if r["to"] == b else r["to"]}
        if r["from"] != r["to"] and (r["from"], r["to"]) not in seen:
            seen.add((r["from"], r["to"]))
            rels.append(r)
    c["relationships"] = rels
    tabs = {t["name"]: t for t in c["tables"]}
    errors = [{"kind": "merge", "text": f"tables {a!r} and {b!r} merged into {a!r}", "keywords": [a.lower(), b.lower()]}]
    fks = sorted((t["name"], i) for t in c["tables"] for i in range(len(t["foreign_keys"])))
    tn, i = rng.choice(fks)
    fk = tabs[tn]["foreign_keys"].pop(i)
    c["relationships"] = [r for r in c["relationships"] if (r["from"], r["to"]) != (tn, fk["ref_table"])]
    errors.append({"kind": "fk_removed", "text": f"foreign key {tn}.{fk['columns'][0]} -> {fk['ref_table']} removed",
                   "keywords": [fk["columns"][0].lower(), tn.lower(), fk["ref_table"].lower()]})
    keep = {(t["name"], k) for t in c["tables"] for k in t["primary_key"]}
    keep |= {(t["name"], k) for t in c["tables"] for f in t["foreign_keys"] for k in f["columns"]}
    keep |= {(f["ref_table"], k) for t in c["tables"] for f in t["foreign_keys"] for k in f["ref_columns"]}
    cols = sorted((t["name"], col["name"]) for t in c["tables"] for col in t["columns"] if (t["name"], col["name"]) not in keep)
    src, name = rng.choice(cols)
    dst = rng.choice(sorted(t for t in tabs if t.split("_")[0] != src.split("_")[0]))
    col = next(x for x in tabs[src]["columns"] if x["name"] == name)
    tabs[src]["columns"].remove(col)
    tabs[dst]["columns"].append(col)
    errors.append({"kind": "column_moved", "text": f"column {name!r} moved from {src!r} to {dst!r}", "keywords": [name.lower()]})
    return c, errors


def assign(entries, seed):
    """entries: [(set, kind)] -> {(set, kind): code}, codes distinct, order shuffled by the seed."""
    order = list(entries)
    random.Random(f"{seed}:assign").shuffle(order)
    return dict(zip(order, make_codes(len(order), seed)))


def pick_repeats(codes, seed, per_judge=3):
    """{judge: [(set, kind)]}: 3 packets per judge to answer twice. Sets alternate (claude: dev50, dev50b, dev50; chatgpt: dev50b,
    dev50, dev50b), the kind is the first of a seeded shuffle not taken yet, so the two judges repeat different packets."""
    taken, out = set(), {}
    for j, judge in enumerate(JUDGES):
        rng = random.Random(f"{seed}:repeat:{judge}")
        out[judge] = []
        for i in range(per_judge):
            s = SETS[(i + j) % len(SETS)]
            kinds = sorted(k for (ss, k) in codes if ss == s and (ss, k) not in taken)
            rng.shuffle(kinds)
            taken.add((s, kinds[0]))
            out[judge].append((s, kinds[0]))
    return out


def checklist(codes, repeats):
    """Rows (judge, code, set, answer file, repeat) of all answers to save: every packet once per judge + the repeats."""
    rows = []
    for judge in JUDGES:
        for (s, k), code in sorted(codes.items(), key=lambda kv: (kv[0][0], kv[1])):
            rows.append({"judge": judge, "code": code, "set": s, "file": f"{judge}_{code}.json", "repeat": False})
        for s, k in repeats[judge]:
            code = codes[(s, k)]
            rows.append({"judge": judge, "code": code, "set": s, "file": f"{judge}_{code}_r2.json", "repeat": True})
    return rows


def readme(rows):
    """README.md text: how to grade and the checklist of every answer to save (no candidate names)."""
    head = f"""# wf_v4 blind grading (task 9)

Each file in `packets/` is one complete prompt. Grade it with a judge model (Claude, ChatGPT) and save its JSON answer.

## How to grade
1. For every packet, open a **new temporary chat** (memory off, no earlier messages, no files attached). Paste the whole packet file as the first and only message.
2. Write down the model name and version shown by the app (put it in the answer file as an extra top-level field `"model": "..."`, the reader keeps it).
3. The judge must answer with JSON only. Save the JSON as `answers/<judge>_<code>.json` (judge = `claude` or `chatgpt`; code = the 4 letters in the packet file name). If the JSON is wrapped in a code fence, that is fine; the reader strips it.
4. Repeats: the rows marked "repeat" below are graded a second time in another new chat; save them as `answers/<judge>_<code>_r2.json`.
5. Do not open `key.json` before all {len(rows)} answers are saved. Then run `python scripts/read_grades_v4.py` (writes `grades.csv` and `task11.md`).

## Checklist ({len(rows)} answers: 16 x claude, 16 x chatgpt, 3 repeats each)
| done | judge | code | set | save as | repeat |
|---|---|---|---|---|---|
"""
    body = "".join(f"| [ ] | {r['judge']} | {r['code']} | {r['set']} | answers/{r['file']} | {'yes' if r['repeat'] else ''} |\n" for r in rows)
    return head + body
