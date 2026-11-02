"""wf_v3.7 T12: J with the general cue words only (a) vs general + cue words learned per cluster (b), on dev50.

python scripts/cue_words_v37.py [--run results/graph_v22_dev50 --dir32 results/loop1_v32 --dir31 results/loop1_v31
                                 --levels results/loop1_v35/gt_levels.csv --out results/loop1_v37]
Same clusters, gold roles and scoring as scripts/roles_v36.py (two-role clusters of train, L2 role slots). The gold roles
only choose the clusters and score the side; learning uses the mentions' left words and the general cue words only
(s1a/roles_v37.py). No encoder, no LLM. Writes <out>/cue_words.md and <out>/cue_words_learned.csv.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from s1a import paths  # noqa: E402
from s1a import roles_v35 as R  # noqa: E402
from s1a import roles_v37 as R37  # noqa: E402
from s1a import rules_labels as RL  # noqa: E402
from s1a import v34_data as D  # noqa: E402
from roles_v35 import clustered_mentions, count  # noqa: E402


def evaluate(m, role, pairs):
    """(table of (a), table of (b), table of (b0), learned-word table of (b))."""
    ev_a, _ = R37.learned_eval(m, role, pairs, learn=False)
    ev_b, words = R37.learned_eval(m, role, pairs, learn=True)
    ev_0, _ = R37.learned_eval(m, role, pairs, learn=True, ev_share=0.0)
    return ev_a, ev_b, ev_0, words


def choice(a, b):
    """(b) when its accuracy is >= (a)'s, else (a) (the T12 rule)."""
    return "b" if b["accuracy"] >= a["accuracy"] else "a"


def summary_md(groups, learned, chosen):
    parts = ["# Cue words: general only (a) vs general + learned per cluster (b) (wf_v3.7, T12)", "",
             "Data and scoring as `results/loop1_v36/roles_summary.md`: gold role = L2 slot of a role pair (train / taxi); "
             "two-role cluster = both slots of one pair, each >= 20% of the cluster's labelled mentions (the 9 train "
             "clusters of dev50). J = nearest cue word among the 3 words before the value. accuracy = correct / covered, "
             "coverage = covered / gold-role mentions.", "",
             "**(a)** general words only: from, after (start); to, into, by, before (end).", "",
             "**(b)** (a) plus words learned per cluster, no gold role used:",
             "1. candidate = the word just before a mention; kept for a cluster when splitting the cluster by it leaves "
             f"two parts that are each >= {R37.MIN_SHARE:.0%} of the cluster's mentions;",
             "2. its side comes from the general cue words: among the mentions it precedes, take the side given by the "
             "nearest general cue word in the 3 words before the value (e.g. \"from the\" -> the word \"the\" gets "
             f"evidence for the start side); the word takes the majority side when >= {R37.MIN_EVIDENCE} mentions give "
             f"evidence, they are >= {R37.EV_SHARE:.0%} of the mentions the word precedes, and the majority is >= "
             f"{R37.AGREE:.0%} of them; otherwise it is not used;",
             "3. J side of a mention = nearest word of the 3 before the value in (a) plus the cluster's learned words of "
             "that side.", "",
             "**(b0)** the first version of the mapping rule, without the 20% evidence share (a word needed only 2 mentions "
             "with side evidence): shown for comparison, it was replaced by (b) before the choice.", "",
             "The gold roles are used only to pick the two-role clusters and to score; the learning never sees them.", ""]
    for title, a, b, b0 in groups:
        parts += [f"## {title}", "", "| cue words | accuracy | coverage |", "|---|---|---|",
                  f"| (a) general | {count(a['correct'], a['covered'])} | {count(a['covered'], a['n_gold_role'])} |",
                  f"| (b) general + learned | {count(b['correct'], b['covered'])} | {count(b['covered'], b['n_gold_role'])} |",
                  f"| (b0) first mapping rule | {count(b0['correct'], b0['covered'])} | {count(b0['covered'], b0['n_gold_role'])} |", ""]
    parts += [f"**Choice: ({chosen})** ((b) when its accuracy >= (a)'s, on the two-role train clusters).", "",
              "## Learned words per cluster (candidates that pass the share rule)", "",
              "| cluster | word | mentions with the word | cluster size | evidence start | evidence end | side |",
              "|---|---|---|---|---|---|---|"]
    side = {0: "start", 1: "end"}
    parts += [f"| {r.cluster_id} | {r.word} | {r.n_word} | {r.n_cluster} | {r.ev_start} | {r.ev_end} | "
              f"{side.get(r.side, 'not used') if pd.notna(r.side) else 'not used'} |" for r in learned.itertuples()]
    return "\n".join(parts) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", default="results/graph_v22_dev50")
    ap.add_argument("--dir32", default="results/loop1_v32")
    ap.add_argument("--dir31", default="results/loop1_v31")
    ap.add_argument("--levels", default="results/loop1_v35/gt_levels.csv")
    ap.add_argument("--out", default="results/loop1_v37")
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
    ev_a, ev_b, ev_0, words = evaluate(m, role, pairs)
    train = {c for c in two if ent_of[c] == "train"}
    groups = [("Two-role clusters, train (%d clusters)" % len(train), R.pooled(ev_a, train), R.pooled(ev_b, train), R.pooled(ev_0, train)),
              ("All clusters with a gold role (%d clusters)" % ev_a["cluster_id"].nunique(), R.pooled(ev_a), R.pooled(ev_b), R.pooled(ev_0))]
    chosen = choice(groups[0][1], groups[0][2])
    words.to_csv(out / "cue_words_learned.csv", index=False, encoding="utf-8", lineterminator="\n")
    shown = words[words["cluster_id"].isin(train)]
    md = summary_md(groups, shown, chosen)
    (out / "cue_words.md").write_text(md, encoding="utf-8", newline="\n")
    print(md)


if __name__ == "__main__":
    main()
