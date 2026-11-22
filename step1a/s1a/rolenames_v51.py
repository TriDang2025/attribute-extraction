"""wf_v5.1 R3 + R4 (diary Nov 24): role names. New code only; the frozen Step 3 v4.4 code has two small hooks, both guarded by a switch
(default off = the v5.0 prompts and jobs byte for byte; switches live in cfg["switches"], a missing key means off).

R4 `naming_context`: every cluster block of a names prompt gets 3 short context snippets after its example lines, e.g.
    Short contexts (the value is in [ ]):
    - "... leave after [09:15] ..."
  The snippets come from the mention table (results/graph_v22_<set>/spans/mentions.csv) and the turn text (docs.jsonl), no word lists:
  at most `max_words` words (default 15: value up to 6, left up to 6, right up to 3), cut at the sentence ends, the value in [ ].
  Choice of mentions: round robin over the dialogues of the cluster (dialogue order and the mention order inside a dialogue shuffled by
  a seed derived from the cluster id), so the 3 snippets come from 3 different dialogues when the cluster has them; identical texts skipped.
  Hook: step3_v44.names_jobs_for_v44(..., snippets={cluster id: [lines]}) and step3_v44.build(..., snips=...).

R3 `name_clash`: after names, rescue and merge (the point where v5.0 joins equal names: step3_v44.assemble_a_v44 makes equal names one
  attribute), the clusters of one entity and order with the same name are checked. Per name the clusters with >= `min_mentions` mentions
  are taken, the biggest `max_per_name` of them; the biggest is the anchor and each other cluster is asked against it, once per
  (name, pair) over the 3 orders: "Are A and B the same information, or two different roles? If different, give each a name." Keyed guided
  schema {"answer": same|different, "<id A>": name, "<id B>": name} (no regex pattern: v4.4 found it breaks guided decoding).
  same / unusable answer -> the names stay as they are (the join as before); different -> both clusters get the two new names (the anchor
  only when it was not renamed by an earlier answer of its name group). An unusable answer (malformed JSON, missing key, equal names, no
  response) is a safe fallback (join as before) and is counted in <out>/clash_log.json. A row whose finish_reason is "error" raises
  (v5.0 session 1 lost guided decoding silently).
  Blocker: `blocked(pair)` (optional, R2's future function; pair = (cluster id a, cluster id b), sorted) is evaluated at build time and
  stored in the job row; a pair it blocks is still asked (the names are needed) but a "same" answer is overridden: the pair stays apart
  as <name> / <name>_2 and the override is logged. No import of R2.
  Hook: step3_v44.run(..., blocked=None) calls run_clash between merge and assemble_a_v44.
"""
import copy
import json
import random
import re
import zlib
from pathlib import Path

from . import batch_v4 as B
from . import llm_cache as LC
from . import log_v43 as L43
from . import mentions as MN
from . import step3_v43 as S3_43
from . import step3_v44 as S3

ROOT = S3.ROOT
CONFIG = ROOT / "config" / "wf_v51_roles.json"
CONTEXT_HEAD = "Short contexts (the value is in [ ]):"
CLASH_MAX_TOKENS = 120
ANSWERS = ("same", "different")
_END = re.compile(r"[.!?]$")
_SPACE = re.compile(r"\s+")


def load_config(path=CONFIG):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def clash_params(cfg):
    """The name_clash settings of `cfg` (the frozen Step 3 config has none: then config/wf_v51_roles.json)."""
    return cfg.get("name_clash") or load_config()["name_clash"]


def switch_on(cfg, name):
    """True when cfg["switches"][name] is set; a missing key (the frozen v4.4 config) means off."""
    return bool(cfg["switches"].get(name, False))


# ---------------------------------------------------------------- R4: snippets
def snippet_from_turn(text, start, end, left=6, right=3, value_words=6):
    """One snippet line: up to `left` words before and `right` words after the value text[start:end], the value in [ ] (cut to
    `value_words` words), left and right cut at sentence ends; "..." where text was left out. Pure: text is the turn text."""
    lw = text[:start].split()
    for i in range(len(lw) - 1, -1, -1):             # keep only the words after the last sentence end
        if _END.search(lw[i]):
            lw = lw[i + 1:]
            break
    cut_left = len(text[:start].split()) > len(lw[-left:])
    lw = lw[-left:] if left else []
    rw = []
    for w in text[end:].split():
        rw.append(w)
        if _END.search(w):
            break
    cut_right = len(text[end:].split()) > len(rw[:right])
    rw = rw[:right]
    vw = _SPACE.sub(" ", text[start:end]).strip().split()
    value = " ".join(vw[:value_words]) + (" ..." if len(vw) > value_words else "")
    parts = (["..."] if cut_left else []) + lw + [f"[{value}]"] + rw + (["..."] if cut_right else [])
    return " ".join(parts)


def n_words(line):
    """Words of a snippet line without the "..." marks and with the value brackets removed (the cap of the test)."""
    return len([w for w in line.replace("[", " ").replace("]", " ").split() if w != "..."])


def pick_mentions(rows, cid, seed=0, k=3):
    """Up to `k` rows of one cluster, round robin over its dialogues (dialogues and mentions shuffled by a seed from the cluster id).
    rows: list of dicts with mention_id and dialogue_id. Deterministic."""
    rng = random.Random(zlib.crc32(f"{seed}|{cid}".encode("utf-8")))
    by = {}
    for r in sorted(rows, key=lambda r: int(r["mention_id"])):
        by.setdefault(r["dialogue_id"], []).append(r)
    order = sorted(by)
    rng.shuffle(order)
    for d in order:
        rng.shuffle(by[d])
    res, depth = [], 0
    while len(res) < k * 4 and any(len(by[d]) > depth for d in order):    # a few spare rows: identical texts are skipped later
        res += [by[d][depth] for d in order if len(by[d]) > depth]
        depth += 1
    return res


def cluster_snippets(rows, texts, cid, k=3, seed=0, left=6, right=3, value_words=6):
    """The snippet lines (at most `k`, distinct) of one cluster. `texts(row) -> (turn text, start, end)` cuts the text out of the corpus."""
    out = []
    for r in pick_mentions(rows, cid, seed, k):
        line = snippet_from_turn(*texts(r), left=left, right=right, value_words=value_words)
        if line not in out:
            out.append(line)
        if len(out) == k:
            break
    return out


def text_source(set_name, root=ROOT):
    """(mention table of results/graph_v22_<set>, texts) with texts(row) -> (turn text, start, end) for cluster_snippets (read only)."""
    run = Path(root) / "results" / f"graph_v22_{set_name}"
    docs, _, _ = MN.load_shared(run)

    def texts(r):
        lo, _ = MN.turn_bounds(docs[r["dialogue_id"]], int(r["turn"]))
        t_lo, t_hi = lo, docs[r["dialogue_id"]].spans[int(r["turn"])][1]
        return docs[r["dialogue_id"]].text[t_lo:t_hi], int(r["char_start"]) - t_lo, int(r["char_end"]) - t_lo

    return MN.load(run / "spans").mentions, texts


def _rows(g):
    return g[["mention_id", "dialogue_id", "turn", "char_start", "char_end"]].to_dict("records")


def set_snippets(set_name, cfg=None, root=ROOT):
    """{cluster id: [snippet lines]} of every cluster of a set, from results/graph_v22_<set> (mentions.csv, docs.jsonl; read only)."""
    cfg = (cfg or load_config())["naming_context"]
    m, texts = text_source(set_name, root)
    return {str(cid): cluster_snippets(_rows(g), texts, str(cid), cfg["snippets"], cfg["seed"], cfg["left"], cfg["right"], cfg["value_words"])
            for cid, g in m.groupby("cluster_id")}


def column_snippets(set_name, columns, cfg=None, root=ROOT, source=None):
    """{key: [snippet lines]} for `columns` = {key: mention ids} (the clusters of set_snippets, here the mentions of a final column).
    source = text_source(set_name, root) when the caller keeps it (it loads the vectors of the set)."""
    cfg = (cfg or load_config())["naming_context"]
    m, texts = source or text_source(set_name, root)
    m = m.copy()
    m["mention_id"] = m["mention_id"].astype(int)
    return {key: cluster_snippets(_rows(m[m["mention_id"].isin({int(i) for i in ids})]), texts, key, cfg["snippets"], cfg["seed"], cfg["left"],
                                  cfg["right"], cfg["value_words"]) for key, ids in columns.items()}


def add_context(block, lines):
    """The cluster block with the short context lines after its example lines (block unchanged when there are none)."""
    if not lines:
        return block
    return block.rstrip("\n") + "\n" + CONTEXT_HEAD + "\n" + "\n".join(f'- "{x}"' for x in lines)


def with_context(blocks, snippets):
    """[(cluster id, block text)] with the context lines of `snippets` ({cluster id: [lines]}) added."""
    return [(c, add_context(t, snippets.get(c, []))) for c, t in blocks]


# ---------------------------------------------------------------- R3: clash questions
class ClashError(RuntimeError):
    """A clash answer row ended with finish_reason "error" (guided decoding lost)."""


def pair_key(a, b):
    return tuple(sorted((a, b)))


def clash_pairs(st, blocks, min_mentions, max_per_name):
    """[(name, anchor, other)] of one (set, entity, order) state: per name the clusters with >= min_mentions mentions, the biggest
    `max_per_name` (ties: frozen order); the first is the anchor, each other cluster one pair. Names with < 2 such clusters give none."""
    res, pos = [], {c: i for i, c in enumerate(st["frozen_ids"])}
    for name, cids in S3.name_clusters(st).items():
        big = [c for c in cids if S3.block_mentions(blocks[c]) >= min_mentions]
        big = sorted(big, key=lambda c: (-S3.block_mentions(blocks[c]), pos[c]))[:max_per_name]
        res += [(name, big[0], c) for c in big[1:]]
    return res


def clash_schema(a, b, variant):
    """Keyed guided schema: answer (same | different) and one name per cluster id (written as the model sees it)."""
    base = S3.names_schema_v44([a, b], variant)
    props = {"answer": {"type": "string", "enum": list(ANSWERS)}, **base["properties"]}
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


def _side(label, cid, block, lines, variant):
    vals = ", ".join(f"[[{v}]]" for v in S3.block_values(block, 6))
    ctx = "".join(f'\n  - "{x}"' for x in lines)
    return f"Cluster {label} ({S3.wire_id(cid, variant)}, {S3.block_mentions(block)} mentions): {vals}\n  Short contexts (the value is in [ ]):{ctx}"


def render_clash_q(entity, name, a, b, blocks, snips, variant="v0"):
    """The closed question for the clusters a and b of one entity that were both named `name`."""
    wa, wb = S3.wire_id(a, variant), S3.wire_id(b, variant)
    return (f"Below are two clusters of values taken from the dialogue turns of entity {entity} (a candidate table). Both were named "
            f'"{name}".\n\n{_side("A", a, blocks[a], snips.get(a, []), variant)}\n\n{_side("B", b, blocks[b], snips.get(b, []), variant)}'
            f"\n\nAre A and B the same information, or two different roles? If different, give each a name.\n"
            f"Same information means the same kind of value with the same role. Values that play different roles (where something starts "
            f"and where it ends, the earliest and the latest time allowed) are different information. Use short snake_case names that "
            f'tell the role. If they are the same, answer "same" and repeat "{name}" for both.\n'
            f'Return ONLY one JSON object, nothing before or after it: "answer" is "same" or "different", and the keys {wa} and {wb} '
            f'hold the name of each cluster, like {{"answer": "different", "{wa}": "<name>", "{wb}": "<name>"}}.\n')


def build_clash_q(out, cfg, state, variant, snips, blocked=None):
    """One job per distinct (set, entity, name, cluster pair) over the orders of `state`. snips = {set: {cluster id: [lines]}}.
    Writes prompts, schemas and manifest_clash.json (stage 5); returns the rows (each with "blocked", "orders")."""
    out, doc, c = Path(out), S3.blocks_doc(out), clash_params(cfg)
    asked = {}
    for key, st in sorted(state.items()):
        s, ent, o = key
        for name, a, b in clash_pairs(st, doc[f"{s}/{ent}"]["blocks"], c["min_mentions"], c["max_per_name"]):
            asked.setdefault((s, ent, name, pair_key(a, b)), []).append(o)
    rows, per_ent = [], {}
    for (s, ent, name, pair), orders in sorted(asked.items()):
        d = doc[f"{s}/{ent}"]
        k = per_ent[(s, ent)] = per_ent.get((s, ent), -1) + 1
        job = f"{ent}_clashq_{S3.PP.RUN_KEY[s]}_p{k}"
        B.write(out / "prompts" / f"{job}.txt", render_clash_q(d["entity"], name, *pair, d["blocks"], snips.get(s, {}), variant))
        B.write_json(out / "prompts" / f"{job}.schema.json", clash_schema(*pair, variant))
        rows.append({"job": job, "entity": d["entity"], "ent": ent, "set": s, "run": S3.PP.RUN_KEY[s], "family": "clash_q", "format": "judge",
                     "format51": "clash", "names_variant": variant, "run_tag": "c", "name": name, "cluster_ids": list(pair),
                     "orders": sorted(orders), "blocked": bool(blocked(pair)) if blocked else False, "prompt": f"prompts/{job}.txt",
                     "schema": f"prompts/{job}.schema.json", "max_tokens": CLASH_MAX_TOKENS})
    B.write_json(out / "manifest_clash.json", {"stage": 5, "jobs": rows})
    return rows


def parse_clash(raw, ids, variant="v0"):
    """({"answer", "names": {cluster id: name}}, "") of a clash answer; (None, reason) when it is not usable: not a JSON object, answer not
    same / different, a name key missing, a name empty / too long / not_attribute, or (different) the two names equal."""
    try:
        obj = LC._extract_json(raw, "{", dict)
    except (ValueError, TypeError):
        return None, "not valid JSON"
    ans = str(obj.get("answer", "")).strip().lower()
    if ans not in ANSWERS:
        return None, f"answer {obj.get('answer')!r} is not same / different"
    names = {}
    for c in ids:
        v = obj.get(S3.wire_id(c, variant))
        n = S3_43.norm_name(v) if isinstance(v, str) else ""
        if ans == "different" and (not n or len(n) > S3_43.NAME_MAX or n == S3_43.NOT_ATTRIBUTE):
            return None, f"bad name for {c}: {v!r}"
        names[c] = n
    if ans == "different" and len(set(names.values())) < 2:
        return None, "the two names are equal"
    return {"answer": ans, "names": names}, ""


def read_answers(out, jobs, log):
    """{job name: parsed answer or None}. Raises ClashError when a row ended with finish_reason "error" (also guided_finish_reason of a
    retried row). Other problems are the safe fallback None and one entry in `log` (RepairLog): clash_no_response, clash_malformed,
    clash_unguided."""
    res = {}
    for j in jobs:
        row = B.last_row(Path(out) / "responses" / f"{j['job']}.jsonl")
        if row is None:
            log.add("clash_no_response", j["job"])
            res[j["job"]] = None
            continue
        if "error" in (row.get("finish_reason"), row.get("guided_finish_reason")):
            raise ClashError(f"{j['job']}: finish_reason error (guided decoding lost); stop and fix before running anything")
        if row.get("guided") is False:
            log.add("clash_unguided", j["job"])
        parsed, why = parse_clash(row.get("raw") or "", j["cluster_ids"], j["names_variant"])
        if parsed is None:
            log.add("clash_malformed", j["job"], why)
        res[j["job"]] = parsed
    return res


def apply_clash(state, blocks_of, jobs, answers, cfg, log):
    """Copy of `state` with the answers applied (see the module doc); returns (state, {(set, ent, order): {cluster id: new name}}).
    blocks_of(set, ent) -> {cluster id: block text}. Joins are the equal names that remain."""
    c = clash_params(cfg)
    by_pair = {(j["set"], j["ent"], j["name"], pair_key(*j["cluster_ids"])): j for j in jobs}
    state, changed = copy.deepcopy(state), {}
    for key, st in sorted(state.items()):
        s, ent, o = key
        renamed = {}
        for name, a, b in clash_pairs(st, blocks_of(s, ent), c["min_mentions"], c["max_per_name"]):
            j = by_pair.get((s, ent, name, pair_key(a, b)))
            ans = answers.get(j["job"]) if j else None
            if ans is not None and ans["answer"] == "same" and j["blocked"]:
                log.add("clash_blocked_same", j["job"], f"{a} {b}")
                ans = {"answer": "different", "names": {a: name, b: f"{name}_2"}}
            if ans is None or ans["answer"] == "same":
                if a in renamed and b not in renamed:           # join as before: b follows the (renamed) anchor
                    st["names"][b] = st["names"][a]
                continue
            new_a, new_b = ans["names"][a], ans["names"][b]
            if a in renamed:
                new_a = st["names"][a]
            if new_a == new_b:                                  # the anchor was renamed earlier to the name b would get: keep the join
                log.add("clash_name_taken", j["job"], f"{a} {b}")
                continue
            st["names"][a], st["names"][b] = new_a, new_b
            renamed[a] = renamed[b] = True
            changed.setdefault(key, {}).update({a: new_a, b: new_b})
    return state, changed


def run_clash(out, backend, cfg, state, variant, blocked=None, snips=None):
    """Build the questions of `state`, run them on `backend`, apply the answers. snips = {set: {cluster id: lines}} (default: set_snippets of
    each set). Writes <out>/clash_log.json (+ counts same / different). Returns (backend info, new state)."""
    out = Path(out)
    sets = sorted({k[0] for k in state})
    snips = snips if snips is not None else {s: set_snippets(s) for s in sets}
    jobs = build_clash_q(out, cfg, state, variant, snips, blocked)
    info = backend.run(out, jobs) if jobs else {"jobs": 0, "run": 0, "parse_errors": 0}
    log = L43.RepairLog()
    answers = read_answers(out, jobs, log)
    doc = S3.blocks_doc(out)
    new, changed = apply_clash(state, lambda s, e: doc[f"{s}/{e}"]["blocks"], jobs, answers, cfg, log)
    for a in answers.values():
        if a is not None:
            log.add(f"clash_{a['answer']}")
    log.save(out / "clash_log.json")
    return {**info, "pairs": len(jobs), "renamed_clusters": sum(len(v) for v in changed.values())}, new


# ---------------------------------------------------------------- laptop fake
class FakeStep51(S3.FakeStep44):
    """FakeStep44 that also answers the clash questions: "different" with two names for the odd job numbers, else "same"."""

    def respond(self, job, prompt, schema):
        if job["family"] != "clash_q":
            return super().respond(job, prompt, schema)
        self.n_made += 1
        a, b = [k for k in schema["properties"] if k != "answer"]
        if zlib.crc32(job["job"].encode()) % 2:
            return json.dumps({"answer": "different", a: "fake_role_a", b: "fake_role_b"})
        return json.dumps({"answer": "same", a: job["name"], b: job["name"]})
