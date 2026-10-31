import importlib.util
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location("score_v34", ROOT / "scripts" / "score_v34.py")
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)


def row(setting, ent, variant, **kw):
    base = dict.fromkeys(S.COLS, "n/a")
    base.update(setting=setting, ent=ent, variant=variant, found_n=4, gold_n=7, noise_n=4, noise_marked_v=0.75,
                merge_n=3, merge_right=2, place_n=10, place_acc=0.9, name_right=5, name_base=8, unknown_n=2,
                merge_unjudged=1, wrong_entity_n=3, recall_after=0.5, noise_marked=0.5, merge_pure=0.5,
                place_right=0.5, real_acc=0.5)
    base.update(kw)
    return base


def test_sweep_md_counts_and_pooled():
    df = pd.DataFrame([row("default", "train", "A r1"), row("default", "hotel", "A r1", noise_n=6, noise_marked_v=0.5),
                       row("old", "train", "A r1")], columns=S.COLS)
    md = S.sweep_md(df)
    assert "| default | A r1 | 4/7 (0.571) | 3/4 (0.750) | 2/3 (0.667) | 9/10 (0.900) | 5/8 (0.625) | 2 | 1 | 3 |" in md
    assert "pooled noise marked 6/10 (0.600), target >= 0.70" in md
    # old setting: noise, place and names show the old decimals; found and merge keep their counts
    assert "| old | A r1 | 4/7 (0.571) | 0.500 | 2/3 (0.667) | 0.500 | 0.500 |" in md
