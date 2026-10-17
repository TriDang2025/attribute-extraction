"""Proactive Demonstration Module retrieval (TEAR Section 4.2.2-4.2.3 and 4.3.1).

Equations implemented:
- Eq. 7  header utility   sc_h(H_p, D_l) = |H_p & H_l| + |H_l - H_p| / (|S| + 1)
- Eq. 8  value utility    sc_v(V_p, D_l) = F1(V_p, V_l; chrF_beta), V_p falls back to [W_u]
- Eq. 9  chrF_beta with the default beta = 2
- Eq. 10 semantic utility sc_s(W_u, W_l) = Emb(W_u)^T Emb(W_l) on normalized vectors
- Eq. 11 X_te = union of the top-k_te indices under each utility
- Eq. 13 X_ar = same retrieval with previews taken from D_u, each table split into D_l-/D_l+
- Eq. 20 soft-set F1 with P = mean_x max_y f(x, y) and R = mean_y max_x f(x, y)
"""

import math
from typing import Any, Callable, Dict, List, Optional, Sequence

from eval.metrics import chrf


def _span_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(span).strip() for span in value if str(span).strip()]
    normalized = str(value).strip()
    return [normalized] if normalized else []


def _norm(header: str) -> str:
    return " ".join(str(header).split()).lower()


def table_values(table: Dict[str, Any]) -> List[str]:
    """V_l: the union of all spans in the table's non-header region."""
    return list(dict.fromkeys(
        span
        for row in table["rows"]
        for cell in row
        for span in _span_list(cell)
    ))


def soft_f1(
    predicted: Sequence[str],
    reference: Sequence[str],
    similarity: Callable[[str, str], float] = chrf,
) -> float:
    """Eq. 20: F1(X, Y; f) = 2 / (P^-1 + R^-1) with max-similarity precision and recall."""
    xs = [value.strip() for value in predicted if value and value.strip()]
    ys = [value.strip() for value in reference if value and value.strip()]
    if not xs and not ys:
        return 1.0
    if not xs or not ys:
        return 0.0
    weights = [[similarity(x, y) for y in ys] for x in xs]
    precision = sum(max(row) for row in weights) / len(xs)
    recall = sum(max(weights[i][j] for i in range(len(xs))) for j in range(len(ys))) / len(ys)
    return 2 * precision * recall / (precision + recall) if precision and recall else 0.0


def header_utility(header_preview: Sequence[str], headers: Sequence[str], schema_size: int) -> float:
    """Eq. 7. Headers are compared after case and whitespace normalization."""
    preview = {_norm(h) for h in header_preview if str(h).strip()}
    labeled = {_norm(h) for h in headers if str(h).strip()}
    return len(preview & labeled) + len(labeled - preview) / (schema_size + 1)


def value_utility(value_preview: Sequence[str], text: str, table: Dict[str, Any]) -> float:
    """Eq. 8, with the input text as a single span when no value is previewed."""
    spans = [v for v in value_preview if v and v.strip()] or [text]
    return soft_f1(spans, table_values(table), chrf)


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    """Eq. 10: dot product of L2-normalized embeddings."""
    if len(left) != len(right) or not left:
        raise ValueError("Embedding vectors must have the same non-zero dimension")
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)


def semantic_utilities(text: str, pool: Sequence[Dict[str, Any]], embedder: Optional[Any]):
    if embedder is not None:
        vectors = embedder.embed([text] + [item["text"] for item in pool])
        return [cosine_similarity(vectors[0], vector) for vector in vectors[1:]], "embedding_cosine"
    return [chrf(text, item["text"]) for item in pool], "chrF proxy (embedding model not configured)"


def _top_k(scores: Sequence[float], k: int) -> List[int]:
    # Ties go to the earlier pool index; the paper does not specify tie-breaking.
    return sorted(range(len(scores)), key=lambda index: (-scores[index], index))[:k]


def rank_examples(
    text: str,
    header_preview: Sequence[str],
    value_preview: Sequence[str],
    pool: Sequence[Dict[str, Any]],
    shots_per_utility: int,
    embedder: Optional[Any] = None,
    schema: Optional[Sequence[str]] = None,
    semantic: Optional[tuple] = None,
) -> List[Dict[str, Any]]:
    """Eq. 11: return the union of the top-k examples under sc_h, sc_v and sc_s, in pool order."""
    if shots_per_utility < 0:
        raise ValueError("shots_per_utility must be non-negative")
    if not pool or shots_per_utility == 0:
        return []
    schema_size = len(schema) if schema is not None else len(header_preview)
    semantic_scores, semantic_method = semantic or semantic_utilities(text, pool, embedder)
    utilities: Dict[str, List[float]] = {
        "header": [header_utility(header_preview, item["table"]["headers"], schema_size) for item in pool],
        "value": [value_utility(value_preview, text, item["table"]) for item in pool],
        "semantic": list(semantic_scores),
    }
    selected: Dict[int, Dict[str, Any]] = {}
    for utility, scores in utilities.items():
        for index in _top_k(scores, shots_per_utility):
            entry = selected.setdefault(
                index,
                {"index": index, "example": pool[index], "utilities": {}, "semantic_method": semantic_method},
            )
            entry["utilities"][utility] = scores[index]
    return [selected[index] for index in sorted(selected)]


def split_table(table: Dict[str, Any], known_headers: Sequence[str]) -> Dict[str, Dict[str, Any]]:
    """Example 4.1: split D_l into D_l- (columns already in D_u) and D_l+ (the rest)."""
    known = {_norm(h) for h in known_headers}
    keep = [i for i, h in enumerate(table["headers"]) if _norm(h) in known]
    new = [i for i, h in enumerate(table["headers"]) if _norm(h) not in known]

    def project(indices):
        return {
            "headers": [table["headers"][i] for i in indices],
            "rows": [[row[i] for i in indices] for row in table["rows"]],
        }

    return {"known_table": project(keep), "new_table": project(new)}


def discovery_examples(
    text: str,
    schema: Sequence[str],
    extracted_table: Dict[str, Any],
    pool: Sequence[Dict[str, Any]],
    shots_per_utility: int,
    embedder: Optional[Any] = None,
    semantic: Optional[tuple] = None,
) -> List[Dict[str, Any]]:
    """Eq. 13: retrieve with previews updated from D_u, then split each table by D_u's headers.
    Every retrieved example is kept, including those whose D_l+ is empty."""
    header_view = list(extracted_table["headers"])
    value_view = table_values(extracted_table)
    retrieved = rank_examples(
        text, header_view, value_view, pool, shots_per_utility, embedder, schema, semantic
    )
    demonstrations = []
    for entry in retrieved:
        parts = split_table(entry["example"]["table"], header_view)
        demonstrations.append({"text": entry["example"]["text"], **parts})
    return demonstrations
