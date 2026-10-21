"""Paths, and sys.path entries so the sibling folders' packages (chk, hbe) import.

The folders themselves go on sys.path, not the repo root: the repo's `hdbscan/` folder would
otherwise shadow the hdbscan library.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
for sub in ("chunking", "hdbscan"):
    p = str(REPO / sub)
    if p not in sys.path:
        sys.path.insert(0, p)

TEAR_DATA = REPO / "tear" / "data" / "conversation"
CHROMA_CHUNKS = REPO / "chunking" / "results" / "S_n50" / "chunks" / "chroma_bge-m3.jsonl"
CACHE = ROOT / "data" / "cache"
RESULTS = ROOT / "results"
