"""wf_v4 Step 4: data signals for every Step-3 handover column (no LLM, no GT).

Input: the handover columns (id, name, mention_ids per entity) and the Step-1a mention table
(mention_id, dialogue_id, instance_id, norm_value, turn, char_start). Column id = "<entity>:<id>".
An entity instance = an instance_id that holds at least one mention of one of the entity's columns.

Outputs (DataFrames): columns, pairs, fd; plus signal_card(set, column_id), a short text for LLM prompts
(no dataset names, no GT; column names come from the handover).

Choices (also in signals_summary.md):
- values per column and instance: the column's norm_values among that instance's mentions; "main value"
  = most frequent, ties to the alphabetically first.
- name_score = coverage x mean of three parts in [0, 1]: distinct ratio (distinct values / instances, capped
  at 1), 1 - repetition share, share of instances where the column is mentioned first among the entity's
  columns (earliest turn, then char_start); coverage = instances with the column / entity instances
  (so a column seen in one instance cannot win).
- FD X -> Y holds if n >= 3 and share >= 0.9; share = sum over X values of the count of the most common
  Y value / n. "trivial": no X value occurs in 2+ of the n units (X is key-like, FD says nothing).
"""
import json
import math
from collections import Counter, defaultdict
from functools import lru_cache
from itertools import combinations
from pathlib import Path

import pandas as pd

from .graph import _npmi

ENTITIES = ("train", "hotel", "restaurant")
FD_SHARE = 0.9
FD_MIN_N = 3
FIRST_COLS = ("turn", "char_start")


def column_key(entity, col_id):
    return f"{entity}:{col_id}"


# ---------------------------------------------------------------- data prep

def _prep(columns, mentions):
    """columns: {entity: [{"id", "name", "mention_ids"}]}; mentions: DataFrame.
    Returns (cols, long): cols = {key: dict(entity, name)}, long = one row per mention of a column:
    key, entity, dialogue_id, instance_id, norm_value, pos (turn, char_start)."""
    m = mentions.set_index("mention_id")
    cols, rows = {}, []
    for ent, lst in columns.items():
        for c in lst:
            key = column_key(ent, c["id"])
            cols[key] = {"entity": ent, "name": c["name"]}
            sub = m.loc[list(c["mention_ids"])]
            for r in sub.itertuples():
                rows.append((key, ent, r.dialogue_id, r.instance_id, r.norm_value, int(r.turn), int(r.char_start)))
    long = pd.DataFrame(rows, columns=["key", "entity", "dialogue_id", "instance_id", "norm_value", "turn", "char_start"])
    return cols, long


def _mode(values):
    cnt = Counter(values)
    return sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


# ---------------------------------------------------------------- per column

def _column_rows(cols, long):
    inst_of_ent = long.groupby("entity")["instance_id"].nunique()
    # first column per (entity, instance): earliest (turn, char_start), tie by key
    firsts = Counter()
    best = long.sort_values(["entity", "instance_id", "turn", "char_start", "key"]).drop_duplicates(["entity", "instance_id"])
    for k in best["key"]:
        firsts[k] += 1
    rows = []
    for key, info in cols.items():
        g = long[long["key"] == key]
        n_inst = g["instance_id"].nunique()
        per_inst = g.groupby("instance_id")["norm_value"].nunique()
        vi = g.groupby("norm_value")["instance_id"].nunique()
        n_val = len(vi)
        n_rep = int((vi >= 2).sum())
        n_multi = int((per_inst >= 2).sum())
        ent_inst = int(inst_of_ent.get(info["entity"], 0))
        rows.append(dict(
            column_id=key, entity=info["entity"], name=info["name"],
            n_mentions=len(g), n_dialogues=g["dialogue_id"].nunique(), n_instances=n_inst, n_distinct=n_val,
            n_entity_instances=ent_inst,
            values_per_instance_mean=float(per_inst.mean()) if n_inst else float("nan"),
            n_multi_value_instances=n_multi, share_multi_value=n_multi / n_inst if n_inst else float("nan"),
            n_repeated_values=n_rep, share_repeated_values=n_rep / n_val if n_val else float("nan"),
            n_first=firsts.get(key, 0), share_first=firsts.get(key, 0) / n_inst if n_inst else float("nan"),
        ))
    df = pd.DataFrame(rows)
    return df


def name_score(distinct_ratio, repeat_share, first_share, coverage):
    """coverage x mean(distinct ratio capped at 1, 1 - repeated share, first share), in [0, 1]."""
    parts = (min(distinct_ratio, 1.0), 1.0 - repeat_share, first_share)
    return float(min(coverage, 1.0) * sum(parts) / 3)


def _add_name_test(df):
    if df.empty:
        for c in ("distinct_ratio", "coverage", "name_score", "name_rank"):
            df[c] = []
        return df
    df["distinct_ratio"] = df["n_distinct"] / df["n_instances"].where(df["n_instances"] > 0)
    df["coverage"] = df["n_instances"] / df["n_entity_instances"].where(df["n_entity_instances"] > 0)
    df["name_score"] = [name_score(r.distinct_ratio, r.share_repeated_values, r.share_first, r.coverage)
                        if r.n_instances else 0.0 for r in df.itertuples()]  # no mentions: score 0
    # rank within entity: highest score first, ties by more mentions then id
    order = df.sort_values(["entity", "name_score", "n_mentions", "column_id"], ascending=[True, False, False, True])
    order["name_rank"] = order.groupby("entity").cumcount() + 1
    return df.merge(order[["column_id", "name_rank"]], on="column_id")


# ---------------------------------------------------------------- pairs

def _pairs(cols, long):
    rows = []
    n_dlg = long["dialogue_id"].nunique() if len(long) else 0
    # same entity, per instance
    for ent in {c["entity"] for c in cols.values()}:
        g = long[long["entity"] == ent]
        groups = g.groupby("instance_id")["key"].agg(lambda s: sorted(set(s)))
        n = len(groups)
        single, pair = Counter(), Counter()
        for ks in groups:
            single.update(ks)
            pair.update(combinations(ks, 2))
        for (a, b), c in pair.items():
            rows.append(dict(scope="same_entity", col_a=a, col_b=b, count=c, n_a=single[a], n_b=single[b],
                             n_units=n, npmi=_npmi(c, single[a], single[b], n)))
    # different entities, per dialogue (n = all dialogues of the set's mention table)
    groups = long.groupby("dialogue_id")["key"].agg(lambda s: sorted(set(s)))
    single, pair = Counter(), Counter()
    for ks in groups:
        single.update(ks)
        pair.update((a, b) for a, b in combinations(ks, 2) if cols[a]["entity"] != cols[b]["entity"])
    for (a, b), c in pair.items():
        rows.append(dict(scope="cross_entity", col_a=a, col_b=b, count=c, n_a=single[a], n_b=single[b],
                         n_units=n_dlg, npmi=_npmi(c, single[a], single[b], n_dlg)))
    return pd.DataFrame(rows, columns=["scope", "col_a", "col_b", "count", "n_a", "n_b", "n_units", "npmi"])


# ---------------------------------------------------------------- functional dependencies

def fd_check(xs, ys):
    """xs, ys: parallel lists of values (one per unit). Returns dict(n, share, n_x_repeated, status)."""
    n = len(xs)
    by_x = defaultdict(Counter)
    for x, y in zip(xs, ys):
        by_x[x][y] += 1
    agree = sum(max(c.values()) for c in by_x.values())
    n_rep = sum(sum(c.values()) for c in by_x.values() if sum(c.values()) >= 2)
    share = agree / n if n else float("nan")
    if n < FD_MIN_N:
        status = "too_few"
    elif n_rep == 0:
        status = "trivial"
    elif share >= FD_SHARE:
        status = "holds"
    else:
        status = "fails"
    return dict(n=n, share=share, n_agree=agree, n_x_repeated=n_rep, status=status)


def _fds(cols, long):
    main = long.groupby(["key", "instance_id"])["norm_value"].agg(_mode)
    inst_dlg = long.drop_duplicates("instance_id").set_index("instance_id")["dialogue_id"]
    per_col = {k: g.droplevel(0) for k, g in main.groupby(level=0)}
    rows = []
    keys = [k for k in cols if k in per_col]  # a column without mentions has no signals
    for x in keys:
        for y in keys:
            if x == y:
                continue
            if cols[x]["entity"] == cols[y]["entity"]:
                common = per_col[x].index.intersection(per_col[y].index)
                if len(common) == 0:
                    continue
                res = fd_check(list(per_col[x].loc[common]), list(per_col[y].loc[common]))
                scope = "same_entity"
            else:
                # dialogues where each side has exactly one instance with a value
                dx = per_col[x].groupby(inst_dlg.reindex(per_col[x].index).to_numpy()).agg(list)
                dy = per_col[y].groupby(inst_dlg.reindex(per_col[y].index).to_numpy()).agg(list)
                common = [d for d in dx.index.intersection(dy.index) if len(dx[d]) == 1 and len(dy[d]) == 1]
                if not common:
                    continue
                res = fd_check([dx[d][0] for d in common], [dy[d][0] for d in common])
                scope = "cross_entity"
            rows.append(dict(scope=scope, x=x, y=y, **res))
    return pd.DataFrame(rows, columns=["scope", "x", "y", "n", "share", "n_agree", "n_x_repeated", "status"])


def _add_dependants(df, fd):
    for scope, name in (("same_entity", "dependants"), ("cross_entity", "dependants_cross")):
        cnt = fd[(fd["scope"] == scope) & (fd["status"] == "holds")].groupby("x").size()
        df[name] = df["column_id"].map(cnt).fillna(0).astype(int)
    return df


# ---------------------------------------------------------------- cards

def _frac(k, n):
    return f"{k}/{n}"


def card_text(row, partners, fds):
    """Plain-English card (<= 60 words). row: a columns.csv row (Series); partners: pairs rows of this column
    in the same entity, with `other` = other column name; fds: fd rows (status holds) with x = this column,
    same entity, with `y_name`."""
    n_i = int(row["n_instances"])
    parts = [f"{int(row['n_mentions'])} mentions in {int(row['n_dialogues'])} dialogues",
             f"{int(row['n_distinct'])} distinct values"]
    if n_i:
        multi = row["share_multi_value"]
        k = int(row["n_multi_value_instances"])
        if multi < 0.2:
            parts.append(f"usually one value per booking ({_frac(n_i - k, n_i)})")
        elif multi >= 0.5:
            parts.append(f"often several values per booking ({_frac(k, n_i)})")
        else:
            parts.append(f"sometimes several values per booking ({_frac(k, n_i)})")
        rep = row["share_repeated_values"]
        word = "rarely" if rep < 0.2 else ("often" if rep >= 0.5 else "sometimes")
        parts.append(f"values {word} repeat ({_frac(int(row['n_repeated_values']), int(row['n_distinct']))})")
        parts.append(f"mentioned first in {_frac(int(row['n_first']), n_i)} bookings")
    if partners is not None and len(partners):
        p = partners.iloc[0]
        parts.append(f"often with '{p['other']}' in the same booking (NPMI {p['npmi']:.2f}, {int(p['count'])} times)")
    if fds is not None and len(fds):
        f = fds.iloc[0]
        extra = f" (+{len(fds) - 1} more)" if len(fds) > 1 else ""
        parts.append(f"fixes '{f['y_name']}' in {int(f['n_agree'])}/{int(f['n'])} bookings{extra}")
    return "; ".join(parts) + "."


def build_cards(df, pairs, fd):
    names = dict(zip(df["column_id"], df["name"]))
    same = pairs[(pairs["scope"] == "same_entity") & (pairs["npmi"] >= 0.3) & (pairs["count"] >= 2)]
    both = pd.concat([same.rename(columns={"col_a": "me", "col_b": "o"}), same.rename(columns={"col_b": "me", "col_a": "o"})])
    both["other"] = both["o"].map(names)
    both = both.sort_values(["npmi", "count", "o"], ascending=[False, False, True])
    holds = fd[(fd["scope"] == "same_entity") & (fd["status"] == "holds")].copy()
    holds["y_name"] = holds["y"].map(names)
    holds = holds.sort_values(["n", "share", "y"], ascending=[False, False, True])
    cards = {}
    for _, r in df.iterrows():
        cards[r["column_id"]] = card_text(r, both[both["me"] == r["column_id"]], holds[holds["x"] == r["column_id"]])
    return cards


# ---------------------------------------------------------------- facade

def compute(columns, mentions):
    """columns: {entity: [{"id", "name", "mention_ids"}]}; mentions: DataFrame. Returns dict of DataFrames + cards."""
    cols, long = _prep(columns, mentions)
    df = _add_name_test(_column_rows(cols, long))
    pairs = _pairs(cols, long)
    fd = _fds(cols, long)
    df = _add_dependants(df, fd)
    return dict(columns=df, pairs=pairs, fd=fd, cards=build_cards(df, pairs, fd))


ROOT = Path(__file__).resolve().parents[1]
MENTION_COLS = ["mention_id", "dialogue_id", "instance_id", "norm_value", "turn", "char_start"]


def load_set(set_name, root=ROOT):
    """(columns dict from the handover files, mentions from results/graph_v22_<set>/spans/mentions.csv)."""
    root = Path(root)
    columns = {}
    for ent in ENTITIES:
        d = json.loads((root / "handover" / set_name / f"{ent}.json").read_text(encoding="utf-8"))
        columns[ent] = [{"id": c["id"], "name": c["name"], "mention_ids": c["mention_ids"]} for c in d["columns"]]
    m = pd.read_csv(root / "results" / f"graph_v22_{set_name}" / "spans" / "mentions.csv", usecols=MENTION_COLS,
                    dtype={"dialogue_id": str, "instance_id": str, "norm_value": str}, keep_default_na=False)
    return columns, m


@lru_cache(maxsize=4)
def _cards(set_name):
    return compute(*load_set(set_name))["cards"]


def signal_card(set_name, column_id):
    """Short plain-English signal text (<= 60 words) of one handover column, e.g. "train:4"."""
    return _cards(set_name)[column_id]


def summary_md(set_name, out):
    df, pairs, fd = out["columns"], out["pairs"], out["fd"]
    lines = [f"# Signals summary: {set_name}", "",
             "Entity | columns | instances | same-entity pairs (>=1) | cross pairs with it | FD holds | trivial | too few", "---|---|---|---|---|---|---|---"]
    for ent in ENTITIES:
        c = df[df["entity"] == ent]
        keys = set(c["column_id"])
        p = pairs[pairs["col_a"].isin(keys) | pairs["col_b"].isin(keys)]
        f = fd[(fd["scope"] == "same_entity") & fd["x"].isin(keys)]
        cross = int(((p["scope"] == "cross_entity")).sum())
        same = int(((p["scope"] == "same_entity")).sum())
        inst = int(c["n_entity_instances"].max()) if len(c) else 0
        lines.append(f"{ent} | {len(c)} | {inst} | {same} | {cross} | {int((f['status'] == 'holds').sum())} | "
                     f"{int((f['status'] == 'trivial').sum())} | {int((f['status'] == 'too_few').sum())}")
    cf = fd[fd["scope"] == "cross_entity"]
    lines += ["", f"Cross-entity FDs (columns of different entities, dialogues with one instance each side): "
              f"{int((cf['status'] == 'holds').sum())} hold, {int((cf['status'] == 'trivial').sum())} trivial, "
              f"{int((cf['status'] == 'too_few').sum())} too few, {int((cf['status'] == 'fails').sum())} fail.",
              "", "Name test: name_score = coverage x mean(distinct ratio capped at 1, 1 - repeated share, first share); "
              "rank 1 per entity:", ""]
    for ent in ENTITIES:
        c = df[(df["entity"] == ent) & (df["name_rank"] == 1)]
        for r in c.itertuples():
            lines.append(f"- {ent}: '{r.name}' ({r.name_score:.3f}, {r.n_instances} instances)")
    lines += ["", "FD: holds = n >= 3 and share >= 0.9; trivial = no X value occurs twice; too_few = n < 3.", ""]
    return "\n".join(lines)


def write_set(set_name, out_dir, root=ROOT):
    out = compute(*load_set(set_name, root))
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in ("columns", "pairs", "fd"):
        out[name].to_csv(out_dir / f"{name}.csv", index=False, encoding="utf-8", lineterminator="\n", float_format="%.4f")
    (out_dir / "cards.json").write_text(json.dumps(out["cards"], indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    (out_dir / "signals_summary.md").write_text(summary_md(set_name, out), encoding="utf-8", newline="\n")
    return out
