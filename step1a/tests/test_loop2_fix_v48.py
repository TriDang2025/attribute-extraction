import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import loop2_fix_v48 as F  # noqa: E402

CFG = {"drop_name_values": {"on": True}, "loop1_embed": {"on": True, "tau": 0.8, "share": 0.5, "l1_share": 0.25},
       "mix": {"on": True, "share": 0.8, "distinct_jaccard": 0.5}, "join_new": {"on": True, "jaccard": 0.5}}


def cluster(cid, label, vals):
    return {"id": cid, "label": label, "mentions": [{"mention_id": f"{cid}:{i}", "norm_value": v} for i, v in enumerate(vals)]}


def row(name, cid):
    return {"name": name, "description": "", "clusters": [cid], "status": "new", "duplicate_of": [], "joined": []}


def exact(a, b):
    return 1.0 if a == b else 0.0


def test_is_name_value():
    assert F.is_name_value("price range", ["price_range".replace("_", " ")])
    assert F.is_name_value("your price range", ["price range"])
    assert F.is_name_value("how many seat", ["seating capacity"])          # seat ~ seating, how / many are stop words
    assert not F.is_name_value("moderate price range", ["price range"])
    assert not F.is_name_value("4 star rating", ["rating"])                 # a digit: a real value
    assert not F.is_name_value("free wifi", ["internet"])


def test_loop1_embed_needs_both_shares():
    cl = {"a": cluster("a", "menu", ["indian", "indian", "thai"])}
    loop1 = {"cuisine": Counter({"indian": 3, "thai": 1}), "catch_all": Counter({"indian": 1, "north": 30})}
    cols, ch = F.loop1_embed(F.columns_of([row("menu", "a")], cl), loop1, exact, 0.8, 0.5, 0.25)
    assert ch == ["menu -> cuisine"] and cols[0]["status"] == "duplicate"
    cols, ch = F.loop1_embed(F.columns_of([row("menu", "a")], cl), {"catch_all": loop1["catch_all"]}, exact, 0.8, 0.5, 0.25)
    assert ch == [] and cols[0]["status"] == "new"                       # one stray value in a big loop-1 column: no join


def test_mix_and_join():
    cl = {"w": cluster("w", "internet", ["free wifi"] * 4 + ["wifi"]), "w2": cluster("w2", "internet options", ["free wifi", "wifi"]),
          "p": cluster("p", "parking", ["free parking"] * 4), "m": cluster("m", "amenities", ["free wifi", "free parking", "free parking"]),
          "s": cluster("s", "services", ["free wifi", "free parking", "wifi"])}
    rows = [row("internet", "w"), row("internet_options", "w2"), row("parking", "p"), row("amenities", "m"), row("services", "s")]
    cols, log = F.apply(rows, cl, {}, exact, CFG)
    assert sorted(log["mix"]) == ["amenities", "services"]                 # both mixes, though each holds the other alone
    assert log["join_new"] == ["internet_options -> internet"]             # mixes are never joined
    by = {c["name"]: c for c in cols}
    assert by["internet"]["joined"] == ["internet_options"] and len(by["internet"]["mentions"]) == 7
    assert by["amenities"]["mix"] and by["amenities"]["status"] == "new"   # flagged, kept


def test_drop_then_row():
    cl = {"p": cluster("p", "parking", ["free parking", "parking", "parking"])}
    cols, log = F.apply([row("parking", "p")], cl, {}, exact, CFG)
    r = F.to_row(cols[0])
    assert log["drop_name_values"] == ["parking"] and r["n_mentions"] == 1 and r["dropped_values"] == {"parking": 2}
    assert F.all_values(cols[0]) == Counter({"parking": 2, "free parking": 1})   # mix / join still see the dropped values
