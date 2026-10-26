import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import spans_step2 as SP  # noqa: E402
from s1a import step2 as S  # noqa: E402
from test_step2 import _Enc, _doc, _mentions  # noqa: E402


def _setup():
    doc = _doc()
    ms = _mentions(doc)
    ms.append(type(ms[0])("D1", "17:30", ms[5].start, ms[5].end, labels=ms[5].labels))  # same string twice
    return {"D1": doc}, ms, ["Train"] * len(ms)


def test_grid_size_and_flags():
    assert len(SP.CONFIGS) <= 24
    assert all(v.cluster_fn and '"normalize": true' in v.note and '"linkage": "average"' in v.note
               for v in SP.CONFIGS.values())


def test_cluster_fn_matches_step2_and_one_label_per_span():
    docs, ms, groups = _setup()
    books = [("D1", "Train")] * len(ms)
    cfg = {"normalize": True, "by_type": True, "linkage": "average", "alpha": 0.2, "t": 0.45, "cannot_link": True}
    x, lab = SP.make_cluster_fn(cfg)(ms, docs, _Enc(), groups, books)
    assert len(lab) == len(ms) and len(x) == len(ms)
    assert lab == S.run_best(ms, docs, groups, books, _Enc(), cfg)


def test_every_config_runs_and_cannot_link_respected():
    docs, ms, groups = _setup()
    books = [("D1", "Train")] * len(ms)
    pairs = S.cannot_links(ms, books)
    for name, v in SP.CONFIGS.items():
        x, lab = v.cluster_fn(ms, docs, _Enc(), groups, books)
        assert len(lab) == len(ms), name
        if '"cannot_link": true' in v.note:
            assert all(lab[a] != lab[b] for a, b in pairs), name
