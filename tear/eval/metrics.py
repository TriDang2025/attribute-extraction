"""
Evaluation metrics for the TEAR framework (Section 5.2 of the paper).

- header-F1: soft-set F1 between header sets (Equation 20)
- structured-F1: F1 over sets of records (Equation 21), with Dictionary F1 (Equation 22)
  aligning each header to its arg-max header and ignoring empty values (Example 5.2)
- recall-AUC: area under the recall curve of a ranked attribute list (Section 5.2.2)
- Similarities: Extract Match (EM), chrF_beta (chrf, beta = 2), rescaled BERTScore (BS)

Every similarity is called as f(prediction, reference); chrF is not symmetric.
"""

from collections import Counter
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional, Sequence


# ---------------------------------------------------------------------------
# String similarity functions
# ---------------------------------------------------------------------------

def _stringify(value: Any) -> str:
    """Convert values to strings without introducing object repr noise."""
    if value is None:
        return ""
    return str(value).strip()


def extract_match(s1: str, s2: str) -> float:
    """Exact match: 1.0 if strings are equal after trimming, else 0.0."""
    return 1.0 if _stringify(s1) == _stringify(s2) else 0.0


def chrf(hypothesis: str, reference: str, n: int = 6, beta: float = 2.0) -> float:
    """chrF_beta (Equation 9) as in sacreBLEU's chrF: character n-grams of order 1..n with
    whitespace removed, case-sensitive, F_beta per order averaged over the orders that
    both strings reach. beta = 2 is the metric's default (Popovic 2015)."""
    hyp = "".join(_stringify(hypothesis).split())
    ref = "".join(_stringify(reference).split())
    if not hyp and not ref:
        return 1.0
    if not hyp or not ref:
        return 0.0
    total, orders = 0.0, 0
    for order in range(1, n + 1):
        if len(hyp) < order or len(ref) < order:
            break
        h = Counter(hyp[i:i + order] for i in range(len(hyp) - order + 1))
        r = Counter(ref[i:i + order] for i in range(len(ref) - order + 1))
        matches = sum((h & r).values())
        precision = matches / sum(h.values())
        recall = matches / sum(r.values())
        orders += 1
        if precision + recall:
            total += (1 + beta ** 2) * precision * recall / (beta ** 2 * precision + recall)
    return total / orders if orders else 0.0


@lru_cache(maxsize=1)
def _bert_scorer():
    try:
        from bert_score import BERTScorer
    except ImportError as error:
        raise RuntimeError(
            "BERTScore requires the optional 'bert-score' package; install it to use BS metrics"
        ) from error
    return BERTScorer(lang="en", rescale_with_baseline=True)


@lru_cache(maxsize=200_000)
def _bertscore_cached(hypothesis: str, reference: str) -> float:
    _, _, scores = _bert_scorer().score([hypothesis], [reference])
    return float(scores[0])


def bertscore(hypothesis: str, reference: str) -> float:
    """Baseline-rescaled BERTScore F1; never substitute a different metric."""
    hyp, ref = _stringify(hypothesis), _stringify(reference)
    if not hyp and not ref:
        return 1.0
    if not hyp or not ref:
        return 0.0
    if hyp == ref:
        return 1.0
    return _bertscore_cached(hyp, ref)


VALUE_SIMILARITIES = {
    'EM': extract_match,
    'chrf': chrf,
    'BS': bertscore,
}


# ---------------------------------------------------------------------------
# Soft-set F1 (Equation 20) and header-F1
# ---------------------------------------------------------------------------

def soft_f1(
    predicted: Sequence[str],
    reference: Sequence[str],
    sim_fn: Callable[[str, str], float] = extract_match,
) -> float:
    """Equation 20: P = mean over predictions of the best reference match, R = mean over
    references of the best prediction match, F1 = 2 / (P^-1 + R^-1)."""
    xs = list(dict.fromkeys(_stringify(x) for x in predicted if _stringify(x)))
    ys = list(dict.fromkeys(_stringify(y) for y in reference if _stringify(y)))
    if not xs and not ys:
        return 1.0
    if not xs or not ys:
        return 0.0
    weights = [[sim_fn(x, y) for y in ys] for x in xs]
    precision = sum(max(row) for row in weights) / len(xs)
    recall = sum(max(col) for col in zip(*weights)) / len(ys)
    return 2 * precision * recall / (precision + recall) if precision and recall else 0.0


def header_f1(
    pred_headers: List[str],
    gold_headers: List[str],
    sim_fn: Callable[[str, str], float] = extract_match,
) -> float:
    """header-F1 = F1(H, H^; f) with Equation 20."""
    return soft_f1(pred_headers, gold_headers, sim_fn)


# ---------------------------------------------------------------------------
# Dictionary-F1 (Equation 22) and structured-F1 (Equation 21)
# ---------------------------------------------------------------------------

def _spans(value: Any) -> List[str]:
    if isinstance(value, list):
        return [_stringify(v) for v in value if _stringify(v)]
    text = _stringify(value)
    return [text] if text else []


def _value_similarity(v_pred: Any, v_gold: Any, sim_v: Callable[[str, str], float]) -> float:
    """Span-wise similarity aggregated via F1 (Section 5.2.1, multiple mentions)."""
    return soft_f1(_spans(v_pred), _spans(v_gold), sim_v)


def _non_empty(record: Dict[str, Any]) -> Dict[str, Any]:
    """Example 5.2: empty values are ignored, so they leave the record's domain."""
    return {h: v for h, v in record.items() if _stringify(h) and _spans(v)}


def dictionary_f1(
    pred: Dict[str, Any],
    gold: Dict[str, Any],
    sim_h: Callable[[str, str], float],
    sim_v: Callable[[str, str], float],
) -> float:
    """Equation 22. Each predicted header is aligned to its arg-max gold header (and each
    gold header to its arg-max predicted header), then the aligned values are compared:
      DP = 1/|R| sum_{h in H} f_v(R(h), R^(argmax_h^ f_k(h, h^)))
      DR = 1/|R^| sum_{h^ in H^} f_v(R(argmax_h f_k(h, h^)), R^(h^))
    Ties in the arg-max go to the first header in record order."""
    pred, gold = _non_empty(pred), _non_empty(gold)
    if not pred and not gold:
        return 1.0
    if not pred or not gold:
        return 0.0
    pred_headers, gold_headers = list(pred), list(gold)
    weights = [[sim_h(hp, hg) for hg in gold_headers] for hp in pred_headers]

    def argmax(values):
        return max(range(len(values)), key=lambda i: (values[i], -i))

    dp = sum(
        _value_similarity(pred[hp], gold[gold_headers[argmax(weights[i])]], sim_v)
        for i, hp in enumerate(pred_headers)
    ) / len(pred_headers)
    dr = sum(
        _value_similarity(pred[pred_headers[argmax([row[j] for row in weights])]], gold[hg], sim_v)
        for j, hg in enumerate(gold_headers)
    ) / len(gold_headers)
    return 2 * dp * dr / (dp + dr) if dp and dr else 0.0


def _table_to_records(table: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert {'headers', 'rows'} to records; entirely empty rows are not records."""
    headers = table.get('headers', [])
    rows = table.get('rows', [])
    if not isinstance(headers, list) or not isinstance(rows, list):
        raise ValueError("table headers and rows must be lists")
    records = []
    for index, row in enumerate(rows):
        if not isinstance(row, list) or len(row) != len(headers):
            raise ValueError(f"table row {index + 1} must contain exactly {len(headers)} cells")
        record = _non_empty(dict(zip(headers, row)))
        if record:
            records.append(record)
    return records


def structured_f1(
    pred_table: Dict[str, Any],
    gold_table: Dict[str, Any],
    sim_h: Callable[[str, str], float],
    sim_v: Callable[[str, str], float],
) -> float:
    """Equation 21: structured-F1 = F1(R, R^; DF1) with Equation 20 over record sets."""
    gold_records = _table_to_records(gold_table)
    pred_records = _table_to_records(pred_table)
    if not gold_records and not pred_records:
        return 1.0
    if not gold_records or not pred_records:
        return 0.0
    weights = [[dictionary_f1(p, g, sim_h, sim_v) for g in gold_records] for p in pred_records]
    precision = sum(max(row) for row in weights) / len(pred_records)
    recall = sum(max(col) for col in zip(*weights)) / len(gold_records)
    return 2 * precision * recall / (precision + recall) if precision and recall else 0.0


def table_headers(table: Dict[str, Any]) -> List[str]:
    """Header region H of a table, leaving out columns with no value in any record."""
    records = _table_to_records(table)
    return [h for h in table.get('headers', []) if any(h in r for r in records)]


# ---------------------------------------------------------------------------
# Attribute recommendation (Section 5.2.2)
# ---------------------------------------------------------------------------

def recall_curve(
    ranked: Sequence[str],
    hidden: Sequence[str],
    sim_fn: Callable[[str, str], float] = chrf,
) -> List[float]:
    """R(Z'[:k], S^', f) for k = 1..|Z'|: recall side of Equation 20, i.e. the mean over
    hidden attributes of the best similarity to any of the top-k candidates."""
    gold = list(dict.fromkeys(_stringify(a) for a in hidden if _stringify(a)))
    candidates = [_stringify(c) for c in ranked if _stringify(c)]
    if not gold:
        return []
    best = [0.0] * len(gold)
    curve = []
    for candidate in candidates:
        for i, attribute in enumerate(gold):
            best[i] = max(best[i], sim_fn(candidate, attribute))
        curve.append(sum(best) / len(gold))
    return curve


def recall_auc(
    ranked: Sequence[str],
    hidden: Sequence[str],
    sim_fn: Callable[[str, str], float] = chrf,
    pad_to: Optional[int] = None,
) -> float:
    """recall-AUC: normalized trapezoidal area under the recall curve over k. A shorter
    curve is padded with its final value up to `pad_to` so curves of different lengths
    are compared on the same k range."""
    curve = recall_curve(ranked, hidden, sim_fn)
    if not curve:
        return 0.0
    if pad_to and pad_to > len(curve):
        curve = curve + [curve[-1]] * (pad_to - len(curve))
    if len(curve) == 1:
        return curve[0]
    return sum((curve[i] + curve[i - 1]) / 2 for i in range(1, len(curve))) / (len(curve) - 1)
