"""Data helpers for the surrogate (no torch import, so tests stay fast)."""

import json
import re

from surrogate.serialize import SPECIAL_TOKENS, _norm

_AROUND_TOKEN_RE = re.compile(r'\s*(' + '|'.join(re.escape(t) for t in SPECIAL_TOKENS) + r')\s*')


def load_jsonl(path):
    with open(path, encoding='utf8') as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path, rows):
    with open(path, 'w', encoding='utf8') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')


def load_hidden(levels_file, level):
    """Hidden attributes for one exploratory level.

    Accepted layouts: {"1": [...], "2": [...]}, {"1": {"hidden": [...]}},
    either one wrapped as {"levels": ...}, or [{"level": 1, "hidden": [...]}, ...].
    """
    with open(levels_file, encoding='utf8') as f:
        data = json.load(f)
    if isinstance(data, dict) and 'levels' in data:
        data = data['levels']
    if isinstance(data, list):
        data = {str(d.get('level')): d for d in data}
    entry = data.get(str(level))
    if entry is None:
        raise KeyError(f"level {level} not in {levels_file} (have {sorted(data)})")
    if isinstance(entry, dict):
        entry = entry.get('hidden', [])
    return {_norm(h) for h in entry}


def _empty(cell):
    if cell is None:
        return True
    if isinstance(cell, list):
        return not any(str(v).strip() for v in cell)
    return not str(cell).strip()


def drop_hidden(table, hidden):
    """Remove hidden columns (and rows left with no values) from a table."""
    if not hidden:
        return table
    headers = table.get('headers', [])
    keep = [i for i, h in enumerate(headers) if _norm(h) not in hidden]
    rows = []
    for row in table.get('rows', []):
        new = [row[i] if i < len(row) else [] for i in keep]
        if not all(_empty(c) for c in new):
            rows.append(new)
    return {'headers': [headers[i] for i in keep], 'rows': rows}


def from_model_text(text):
    """Canonical Seq(D): no whitespace around separators."""
    return _AROUND_TOKEN_RE.sub(r'\1', text).strip()


def to_model_text(seq):
    """Seq(D) with a space after each separator, so words tokenize as they do
    mid-sentence in the source ("ĠSmith", not "Smith"). from_model_text undoes it."""
    return _AROUND_TOKEN_RE.sub(r'\1 ', seq).strip()


def length_batches(lengths, batch_size, rng=None, pool_factor=50):
    """Length-bucketed batches: shuffle, sort within pools of batch_size*pool_factor,
    cut into batches, shuffle batch order. rng=None keeps a deterministic sorted order."""
    idx = list(range(len(lengths)))
    if rng is None:
        idx.sort(key=lambda i: lengths[i])
        return [idx[i:i + batch_size] for i in range(0, len(idx), batch_size)]
    rng.shuffle(idx)
    pool = batch_size * pool_factor
    batches = []
    for start in range(0, len(idx), pool):
        chunk = sorted(idx[start:start + pool], key=lambda i: lengths[i])
        batches.extend(chunk[i:i + batch_size] for i in range(0, len(chunk), batch_size))
    rng.shuffle(batches)
    return batches

