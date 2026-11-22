"""wf_v5.0 G3 (S6): "no joins" post-step on the final Step 3 columns. A group that joins several Step 1a clusters (equal names, merge
yes/no, 3-order vote, reconcile, duplicate check) is split back into one column per cluster. Split parts of one cluster stay together.
No signal and no threshold, so nothing is tuned on a dev set. Switch: `unjoin` (off = the columns unchanged). CPU only, no LLM.

The column keeps its name for its biggest cluster; every other cluster becomes a new column named by the cluster's own pre-merge name
(majority over the 3 orders of the names / rescue answers), else "<column name> <cluster id>". Same-name columns stay separate (the
duplicate check that would join them is exactly what is undone here).
"""

import glob
import json
import re
from collections import Counter


def premerge_names(step3_dir, run):
    """{cluster id: majority pre-merge name over the orders} from responses/*_{names,rescuen}_<run>_s<n>_*.jsonl (a names answer wins over
    a rescue answer of the same order; not_attribute is ignored)."""
    per = {}
    for fam in ("rescuen", "names"):       # names last: it overwrites a rescue name of the same order
        for f in sorted(glob.glob(f"{step3_dir}/responses/*_{fam}_{run}_s*_*.jsonl")):
            order = re.search(r"_s(\d)_", f).group(1)
            for line in open(f, encoding="utf-8"):
                parsed = json.loads(line).get("parsed") or {}
                if isinstance(parsed, dict):
                    per.update({(c, order): n for c, n in parsed.items() if "#" in c and isinstance(n, str)})
    votes = {}
    for (c, _o), n in per.items():
        if n and n != "not_attribute":
            votes.setdefault(c, Counter())[n.replace("_", " ")] += 1
    return {c: sorted(v.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] for c, v in votes.items()}


def unjoin(columns, cluster_of, names):
    """New column list of one entity. columns = final_columns.json entries (cid, name, members "cluster@group", mention_ids, ...);
    cluster_of = {mention_id: cluster id}; names = premerge_names. New columns get cid = max cid + k and `unjoined_from` = the old cid."""
    out, next_cid = [], max((c["cid"] for c in columns), default=0) + 1
    for col in columns:
        ids = [int(i) for i in col["mention_ids"]]
        clusters = list(dict.fromkeys(m.split("@")[0] for m in col["members"]))
        if len(clusters) < 2:
            out.append(col)
            continue
        size = Counter(cluster_of.get(i) for i in ids)
        clusters.sort(key=lambda c: (-size[c], c))
        for k, cl in enumerate(clusters):
            mine = [i for i in ids if cluster_of.get(i) == cl]
            if not mine:
                continue
            new = {**col, "members": [m for m in col["members"] if m.split("@")[0] == cl], "mention_ids": mine, "n_mentions": len(mine)}
            if k == 0:
                new["groups"] = [m.split("@")[1] for m in new["members"]]
            else:
                new.update(cid=next_cid, name=names.get(cl) or f"{col['name']} {cl}", unjoined_from=col["cid"],
                           groups=[m.split("@")[1] for m in new["members"]])
                next_cid += 1
            out.append(new)
    return out
