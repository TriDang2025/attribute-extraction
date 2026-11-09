"""Build the dev50 / dev50b TEAR inputs: the Step 1a development dialogues (ids 0-49 / 50-99 of TEAR's pool).

Usage (from tear/; standard library only):
    python -I data_build/dev50.py [--zip PATH] [--ids PATH] [--pool PATH] [--out PATH] [--n 50] [--start 0]
    python -I data_build/dev50.py --start 50          -> data/conversation_dev50b.jsonl (wf_v4.1: pool[50:100], step1a split.DEV50B)

Text and gold table come from the same builder as data_build/multiwoz.py (dialogue_text, build_table) on
MULTIWOZ2.4/data.json. Rows: {id, text, schema, table}; the first three are the format of
results/conversation_input_first200.jsonl, table is the gold (for scoring only). Each text is checked against
the pool.jsonl row of the same id when --pool exists.

These ids are in TEAR's demonstration pool (data/conversation/pool.jsonl). eval/reproduce.py datasets
`conversation_dev50` / `conversation_dev50b` drop them from the pool (`pool_without`), so a text never retrieves itself.
"""

import argparse
import collections
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data_build import multiwoz as MW  # noqa: E402

DEFAULT_IDS = ROOT.parent / "chunking" / "data" / "conversation_ids.txt"
DEFAULT_ZIP = ROOT.parent / "chunking" / "data" / "MULTIWOZ2.4.zip"
DEFAULT_POOL = ROOT / "data" / "conversation" / "pool.jsonl"
OUT = {0: ROOT / "data" / "conversation_dev50.jsonl", 50: ROOT / "data" / "conversation_dev50b.jsonl"}
N_DEV = 50


def read_ids(path, n=N_DEV, start=0):
    """Ids start .. start+n-1 of a conversation_ids.txt (TEAR pool first, then test)."""
    ids = [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(ids) < start + n or len(set(ids)) != len(ids):
        raise ValueError(f"{path}: need {start + n} unique ids, got {len(ids)} ({len(set(ids))} unique)")
    return ids[start:start + n]


def build_rows(data, ids):
    """Rows {id, text, schema, table} for `ids` from MultiWOZ 2.4 data (dict "<id>.json" -> dialogue), in the
    order of `ids`. Same text and table builder as multiwoz.py; a dialogue with an empty table is an error."""
    rows = []
    for did in ids:
        log = data[f"{did}.json"]["log"]
        text = MW.dialogue_text(log)
        table = MW.build_table(log[-1].get("metadata") or {}, text, collections.Counter())
        if table is None:
            raise ValueError(f"{did}: empty table")
        rows.append({"id": did, "text": text, "schema": MW.SCHEMA, "table": table})
    return rows


def check_against_pool(rows, pool):
    """Ids of `rows` whose text or table differs from the pool row of the same id (missing id counts)."""
    by_id = {r["id"]: r for r in pool}
    return [r["id"] for r in rows
            if r["id"] not in by_id or by_id[r["id"]]["text"] != r["text"] or by_id[r["id"]]["table"] != r["table"]]


def pool_without(pool, ids):
    """Demonstration pool minus the rows whose id is in `ids` (the pool is never edited)."""
    drop = set(ids)
    return [r for r in pool if r["id"] not in drop]


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--zip", type=Path, default=DEFAULT_ZIP)
    ap.add_argument("--ids", type=Path, default=DEFAULT_IDS)
    ap.add_argument("--pool", type=Path, default=DEFAULT_POOL)
    ap.add_argument("--out", type=Path, help="default data/conversation_dev50.jsonl (start 0) or _dev50b.jsonl (start 50)")
    ap.add_argument("--n", type=int, default=N_DEV)
    ap.add_argument("--start", type=int, default=0)
    a = ap.parse_args(argv)
    if a.out is None:
        if a.start not in OUT:
            ap.error("give --out for a start other than 0 or 50")
        a.out = OUT[a.start]

    ids = read_ids(a.ids, a.n, a.start)
    with zipfile.ZipFile(a.zip) as z:
        data = json.loads(z.read(MW.DATA_MEMBER).decode("utf-8"))
    rows = build_rows(data, ids)
    if a.pool.exists():
        pool = read_jsonl(a.pool)
        bad = check_against_pool(rows, pool)
        if bad:
            raise SystemExit(f"{len(bad)} rows differ from {a.pool.name}: {bad[:5]}")
        print(f"{len(rows)} rows match {a.pool.name} ({len(pool_without(pool, ids))} pool rows remain without them)")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    MW.write_jsonl(a.out, rows)
    print(f"wrote {len(rows)} rows to {a.out}")


if __name__ == "__main__":
    main()
