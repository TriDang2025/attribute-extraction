"""wf_v3.6 task 4 (GT_V36_CONTRACT.md, W1): role-word J with all cue words vs only the general ones.

python scripts/roles_v36.py [--run results/graph_v22_dev50 --dir32 results/loop1_v32 --dir31 results/loop1_v31]
                            [--levels results/loop1_v35/gt_levels.csv --out results/loop1_v36]
General words: from, after (start); to, into, by, before (end). Domain words: the rest of pilot_input.CUE_ROLES (leave,
leaving, depart, departing, departs; arrive, arriving, arrives). Same groups and gold roles as scripts/roles_v35.py
(L2 role slots of train / taxi). No encoder, no LLM. Writes <out>/roles_summary.md.
"""

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from s1a import paths  # noqa: E402
from s1a import pilot_input as PIN  # noqa: E402
from s1a import roles_v35 as R  # noqa: E402
from s1a import rules_labels as RL  # noqa: E402
from s1a import v34_data as D  # noqa: E402
from roles_v35 import clustered_mentions, count  # noqa: E402


def group_rows(m, role, two, ent_of, pairs):
    """[(group title, ids or None, {words name: pooled dict})] for the 3 groups of v3.5 (two-role all, two-role train,
    all clusters with a gold role) and the word sets full / general."""
    sets = {"full": None, "general": R.CUE_GENERAL}
    evals = {name: R.role_word_eval(m, role, pairs, words) for name, words in sets.items()}
    groups = (("Two-role clusters, all entities", set(two)),
              ("Two-role clusters, train", {c for c in two if ent_of[c] == "train"}),
              ("All clusters with a gold role", None))
    return [(t, ids, {n: R.pooled(df, ids) for n, df in evals.items()}) for t, ids in groups]


def word_table(m, role, pairs):
    """DataFrame (word, kind, side, mentions, correct, accuracy): per cue word, the gold-role mentions whose nearest cue
    word (all words) is it, and how many of those it labels with the right side."""
    kind = {w: "general" for ws in R.CUE_GENERAL.values() for w in ws} | {w: "domain" for ws in R.CUE_DOMAIN.values() for w in ws}
    hit = defaultdict(lambda: [0, 0])
    for i, r in m[role != ""].iterrows():
        side, word = R.j_word(r)
        if word is not None:
            hit[word][0] += 1
            hit[word][1] += side == R._side(role.loc[i], pairs)
    rows = [{"word": w, "kind": kind[w], "side": "start" if side == 0 else "end",
             "mentions": hit[w][0], "correct": hit[w][1],
             "accuracy": hit[w][1] / hit[w][0] if hit[w][0] else float("nan")}
            for side, name in enumerate(("start", "end")) for w in sorted(PIN.CUE_ROLES[name])]
    return pd.DataFrame(rows).sort_values(["kind", "side", "word"], ascending=[True, False, True])


def summary_md(groups, words):
    parts = ["# Role words: all cue words vs general words only (wf_v3.6, task 4)", "",
             "Same data as `results/loop1_v35/roles_summary.md`: gold role = L2 slot of a role pair (train / taxi); two-role "
             "cluster = both slots of one pair, each >= 20% of the cluster's labelled mentions. J = nearest cue word among "
             "the 3 words before the value. **full** = all of `pilot_input.CUE_ROLES`; **general** = from, after (start) and "
             "to, into, by, before (end), no domain word. accuracy = correct / covered, coverage = covered / gold-role "
             "mentions; counts are k/n (share).", ""]
    for title, _, pooled in groups:
        n = pooled["full"]["n_gold_role"]
        parts += [f"## {title} ({pooled['full']['clusters']} clusters, {n} gold-role mentions)", "",
                  "| cue words | accuracy | coverage |", "|---|---|---|"]
        parts += [f"| {name} | {count(p['correct'], p['covered'])} | {count(p['covered'], p['n_gold_role'])} |"
                  for name, p in pooled.items()]
        parts.append("")
    parts += ["## Each cue word (all clusters with a gold role; the word is the nearest cue word before the value)", "",
              "| word | kind | side | mentions covered | accuracy |", "|---|---|---|---|---|"]
    parts += [f"| {r.word} | {r.kind} | {r.side} | {r.mentions} | {count(r.correct, r.mentions)} |"
              for r in words.itertuples()]
    return "\n".join(parts) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", default="results/graph_v22_dev50")
    ap.add_argument("--dir32", default="results/loop1_v32")
    ap.add_argument("--dir31", default="results/loop1_v31")
    ap.add_argument("--levels", default="results/loop1_v35/gt_levels.csv")
    ap.add_argument("--out", default="results/loop1_v36")
    a = ap.parse_args()
    out = paths.ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    shared, data = D.load_all(a.run, a.dir32, a.dir31)
    m = clustered_mentions(shared, data)
    gt = pd.read_csv(paths.ROOT / a.levels).drop_duplicates("mention_id").set_index("mention_id")["gt_L2"]
    l2 = m["mention_id"].astype(int).map(gt).fillna("").astype(str)
    pairs = RL.role_pairs()
    role = R.gold_role(l2, pairs)
    two = R.two_role_clusters(m, role, l2 != "", pairs)
    ent_of = dict(zip(m["cluster_id"], m["ent"]))
    groups = group_rows(m, role, two, ent_of, pairs)
    md = summary_md(groups, word_table(m, role, pairs))
    (out / "roles_summary.md").write_text(md, encoding="utf-8", newline="\n")
    print(md)


if __name__ == "__main__":
    main()
