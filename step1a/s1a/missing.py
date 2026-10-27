"""T3: why is a gold attribute not strictly recovered? One row per attribute with strict == False (LOOP1_CONTRACT.md)."""
import pandas as pd

from .coverage import _kept, value_coverage
from .labels import _classes

FIX = {
    "implicit": "extractive limit or Loop-2 yes/no probe",
    "missed": "Loop-2 probe with the LLM-suggested name",
    "wrong_entity": "entity fix (over-cluster then merge; shared-value signal)",
    "mixed": "LLM split in Step 3",
    "diluted": "selective role split in Step 1a or Loop-2 probe",
}
COLUMNS = ["gold_attr", "gold_entity", "n_verbatim", "n_nonverbatim", "gliner_cov", "cluster_cov", "best_cluster",
           "best_size", "best_purity", "best_pred_entity", "best_entity_majority_gold", "cause", "planned_fix"]


def _cov(g: pd.DataFrame, mentions: pd.DataFrame) -> float:
    """Share of the verbatim gold rows `g` overlapped by any row of `mentions` (nan if g is empty)."""
    return value_coverage(mentions.assign(cluster_id="all"), g)


def _mode(s: pd.Series) -> str:
    s = s.dropna().astype(str)
    s = s[s != ""]
    return s.value_counts().sort_index().idxmax() if len(s) else ""  # ties: alphabetical


def cause_of(n_verb, n_non, gliner_cov, best_cluster, best_purity, best_ent_major, gold_entity) -> str:
    """First matching rule: implicit, missed, wrong_entity, mixed, diluted."""
    if n_verb + n_non and n_non / (n_verb + n_non) > 0.5:
        return "implicit"
    if gliner_cov < 0.5:
        return "missed"
    if best_cluster != "" and best_ent_major != gold_entity:
        return "wrong_entity"
    if best_cluster != "" and 0.25 <= best_purity < 0.6:
        return "mixed"
    return "diluted"


def missing_table(mentions: pd.DataFrame, gold_values: pd.DataFrame, recall_tab: pd.DataFrame,
                  raw_spans: pd.DataFrame | None = None) -> pd.DataFrame:
    """One row per attribute of `recall_tab` with strict == False (recall_tab: recall.recall_table output).
    gliner_cov is measured on `raw_spans` (dialogue_id, char_start, char_end: GLiNER output before the span
    filter) when given, else on every row of `mentions`.

    No best cluster (best_cluster empty / nan): wrong_entity and mixed cannot fire, so it ends as implicit, missed or diluted.
    best_size = mentions in best_cluster; best_entity_majority_gold ignores unmatched spans (entity_gold == "")."""
    clustered = _kept(mentions)
    size = clustered["cluster_id"].value_counts()
    cl_entity = clustered.groupby("cluster_id")["entity"].agg(_mode)
    ent_major = clustered.groupby("entity")["entity_gold"].agg(_mode)
    rows = []
    for r in recall_tab[~recall_tab["strict"].astype(bool)].itertuples():
        g = gold_values[gold_values["gold_attr"].map(lambda v: r.gold_attr in _classes(v))]
        verb = g[g["verbatim"].astype(bool)]
        bc = "" if pd.isna(r.best_cluster) else str(r.best_cluster)
        bp = float(r.best_purity) if not pd.isna(r.best_purity) else 0.0
        pent = cl_entity.get(bc, "") if bc else ""
        major = ent_major.get(pent, "") if pent else ""
        gcov, ccov = _cov(verb, mentions if raw_spans is None else raw_spans), _cov(verb, clustered)
        ge = _mode(g["entity_gold"])
        cause = cause_of(len(verb), len(g) - len(verb), gcov, bc, bp, major, ge)
        rows.append(dict(gold_attr=r.gold_attr, gold_entity=ge, n_verbatim=len(verb), n_nonverbatim=len(g) - len(verb),
                         gliner_cov=gcov, cluster_cov=ccov, best_cluster=bc, best_size=int(size.get(bc, 0)),
                         best_purity=bp, best_pred_entity=pent, best_entity_majority_gold=major,
                         cause=cause, planned_fix=FIX[cause]))
    return pd.DataFrame(rows, columns=COLUMNS)
