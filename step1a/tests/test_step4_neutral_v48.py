"""wf_v4.8 W3 variant B: neutral table ids in Step 4 pass 2 (s1a/step4_neutral_v48.py, chain key neutral_ids of s1a/step4_v44.py), fake model only."""
import json

from s1a import batch_v4 as B
from s1a import step4_fake_v44 as F
from s1a import step4_neutral_v48 as N
from s1a import step4_v44 as S
from s1a.log_v44 import RepairLog

from test_step4_p2batch_v46 import ALL_OFF, CFG, jobs_of, make_root, run


class ByEntityFake(F.FakeV44):
    """Pass 2: a column goes to the table at the position of its entity (boat -> 1st, shop -> 2nd, ...), all others as FakeV44."""
    def respond(self, job, prompt, schema):
        if job["format"] != "s43_p2":
            return super().respond(job, prompt, schema)
        enum = next(iter(schema["properties"].values()))["enum"][:-1]       # without "unused"
        order = ("boat", "shop", "port", "crew", "ticket", "route")
        return json.dumps({cid: enum[order.index(cid.split(":")[0]) % len(enum)] for cid in schema["properties"]})


def test_neutral_prompt_has_ids_and_hints():
    cols = [{"id": "a:1", "name": "x"}]
    text, schema, fmt = N.build_p2(lambda c, ids: (f"head\nTables: {', '.join(ids)}\n\nColumns", {"enum": ids}, "f"), cols, ["location", "hotel"])
    assert "Tables: table_1, table_2\nTable hints (" in text and "table_1 = location, table_2 = hotel" in text
    assert schema == {"enum": ["table_1", "table_2"]}


def test_name_tables_by_majority_entity_and_unique():
    cols = [{"id": f"{e}:{i}"} for i, e in enumerate(["hotel", "hotel", "train", "hotel", "train", "train"])]
    assign = {"hotel:0": "table_1", "hotel:1": "table_1", "train:2": "table_1", "hotel:3": "table_2", "train:4": "table_3", "train:5": None}
    got, names, ren = N.name_tables(assign, ["table_1", "table_2", "table_3"], cols, RepairLog())
    assert names == ["hotel", "hotel_2", "train"] and ren == {"table_1": "hotel", "table_2": "hotel_2", "table_3": "train"}
    assert got["train:2"] == "hotel" and got["train:5"] is None


def test_switch_off_is_unchanged_and_on_names_by_entity(tmp_path):
    root, _ = make_root(tmp_path, 45)
    assert "neutral_ids" not in S.with_switches(CFG) and S.with_switches(ALL_OFF, neutral_ids=True)["neutral_ids"] is True
    off, on = tmp_path / "off", tmp_path / "on"
    run(off, root, S.with_switches(ALL_OFF, p2_batch=20), backend=ByEntityFake())
    run(on, root, S.with_switches(ALL_OFF, p2_batch=20, neutral_ids=True), backend=ByEntityFake())
    t_off = (off / jobs_of(off, 2)[0]["prompt"]).read_text(encoding="utf-8")
    t_on = (on / jobs_of(on, 2)[0]["prompt"]).read_text(encoding="utf-8")
    assert "Table hints" not in t_off and "Tables: table_1" in t_on
    ch = B.read_json(on / "chains.json")[0]
    assert ch["neutral_ids"] is True
    st, err, _ = S.replay(on, ch, 4, root)
    assert err is None and all(n in ("boat", "shop", "port", "crew", "ticket", "route") or n.split("_")[0] in ("boat", "shop") for n in st["names"])
    assert all(st["assign"][c["id"]] is None or st["assign"][c["id"]].startswith(c["id"].split(":")[0]) for c in st["cols"])
