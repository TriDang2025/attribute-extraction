"""wf_v3.3 variant F: de-lexicalise a prompt (contract: PILOT_V33_CONTRACT.md, "F de-lexicalisation").

Name-like values (stations, hotel / restaurant / attraction names, train ids) are replaced by fake strings,
so the model cannot name a cluster from a value it knows. `build_map` makes {lowercased real string: fake};
`apply` rewrites a text with it. Fakes are deterministic (crc32 seed), unique, pronounceable, and keep the
length and shape of the real string; train ids TR1234 become TX1234-like ids.
"""

import json
import random
import re
import zipfile
import zlib

import pandas as pd

NAME_ATTRS = ("train departure", "train destination", "hotel name", "restaurant name", "attraction name",
              "taxi departure", "taxi destination", "train id")
TR_ID = re.compile(r"\bTR\d{4}\b", re.IGNORECASE)
MIN_LEN = 3
# wf_v3.6 F2: generic words that must never be mapped, even when a database name or a station equals one of them
STOP = frozenset({
    "hotel", "hotels", "restaurant", "restaurants", "guesthouse", "guest house", "guesthouses", "guest houses",
    "bed and breakfast", "b and b", "lodge", "train", "trains", "taxi", "taxis", "cab", "bus", "station",
    "attraction", "attractions", "museum", "college", "park", "church", "theatre", "cinema", "gallery", "pool",
    "swimming pool", "bar", "pub", "cafe", "travel time", "time", "centre", "center", "city centre", "city center",
    "town centre", "town center", "north", "south", "east", "west", "cambridge", "the", "and", "road", "street",
    "place", "house", "room", "area", "name", "address", "phone", "postcode", "food", "price"})
NAME_DBS = ("hotel", "restaurant", "attraction")
_VOWELS, _CONSONANTS = "aeiou", "bcdfghjklmnprstvw"


def _fake(key, salt):
    rng = random.Random(zlib.crc32(f"{key}|{salt}".encode()))
    if re.fullmatch(r"tr\d{4}", key):
        return "tx" + "".join(rng.choice("0123456789") for _ in range(4))
    out = []
    for ch in key:
        if ch.isalpha():
            out.append(rng.choice(_VOWELS if ch in _VOWELS else _CONSONANTS))
        elif ch.isdigit():
            out.append(rng.choice("0123456789"))
        else:
            out.append(ch)
    return "".join(out)


def _norm(s):
    return " ".join(str(s).lower().split())


def add_tr_ids(mp, text):
    """`mp` plus a fake for every TR\\d{4} string in `text` (existing entries are kept)."""
    return extend(mp, [m.group(0) for m in TR_ID.finditer(text)])


def extend(mp, keys):
    """`mp` plus a fake for each new key (lowercased, whitespace-normalised); keys in sorted order, so the
    result does not depend on the order of `keys`. Fakes differ from every key and from each other."""
    mp = dict(mp)
    new = sorted({_norm(k) for k in keys} - set(mp))
    taken = set(mp) | set(mp.values()) | set(new)
    for key in new:
        salt = 0
        fake = _fake(key, salt)
        while fake in taken or fake == key:
            salt += 1
            fake = _fake(key, salt)
        taken.add(fake)
        mp[key] = fake
    return mp


def build_map(mentions, gold_attrs=NAME_ATTRS, texts=()):
    """{real lowercased string: fake} for the norm values and raw span texts (`norm_value`, optional `text`) of the
    mentions whose gold attribute is one of `gold_attrs` (case-insensitive; "A;B" counts if A or B is). With a
    `cluster_id` column, an unlabelled span also counts when more than half of its cluster's labelled spans are
    names. Plus every TR + 4-digit train id in `texts`. Values shorter than 3 characters are skipped."""
    want = {a.lower() for a in gold_attrs}
    named = [isinstance(a, str) and bool(want & {p.strip().lower() for p in a.split(";")}) for a in mentions["gold_attr"]]
    if "cluster_id" in mentions:  # unlabelled spans of a cluster whose labelled spans are mostly names count too
        labelled = mentions["gold_attr"].map(lambda a: isinstance(a, str) and a != "")
        share = pd.Series(named, index=mentions.index)[labelled].groupby(mentions["cluster_id"][labelled]).mean()
        name_cl = set(share[share > 0.5].index) - {""}
        named = [ok or (not lab and c in name_cl) for ok, lab, c in zip(named, labelled, mentions["cluster_id"])]
    cols = [c for c in ("norm_value", "text") if c in mentions]  # norm_value is stemmed; text is the span as written
    keys = [v.strip().lower() for c in cols for v, ok in zip(mentions[c], named)
            if ok and isinstance(v, str) and len(v.strip()) >= MIN_LEN]
    mp = extend({}, keys)
    for t in texts:
        mp = add_tr_ids(mp, t)
    return mp


def db_names(zip_path):
    """Real entity names of the MultiWOZ 2.4 databases (MULTIWOZ2.4.zip): the `name` of every hotel, restaurant and
    attraction, and every train departure / destination station. Sorted list of distinct lowercased strings."""
    z = zipfile.ZipFile(zip_path)
    out = set()
    for d in NAME_DBS:
        out |= {r["name"] for r in json.loads(z.read(f"MULTIWOZ2.4/{d}_db.json")) if r.get("name")}
    for r in json.loads(z.read("MULTIWOZ2.4/train_db.json")):
        out |= {r["departure"], r["destination"]}
    return sorted({_norm(n) for n in out})


def build_map_v2(names, texts=()):
    """wf_v3.6 F2 map {real lowercased string: fake}: only real entity names. `names` = db_names(...) (strings;
    lowercased and whitespace-normalised here; a name with a leading "the" is mapped with and without it), plus every TR + 4-digit train id in `texts`. Strings in STOP and
    strings shorter than 3 characters are never mapped. The span labels of a run play no part (v3.3 F, build_map,
    mapped generic words that the spans of name clusters held)."""
    keys = []
    for n in (_norm(x) for x in names):
        keys += [k for k in (n, n[4:] if n.startswith("the ") else n) if len(k) >= MIN_LEN and k not in STOP]
    mp = extend({}, keys)
    for t in texts:
        mp = add_tr_ids(mp, t)
    return mp


def _case(fake, real):
    """`fake` in the case pattern of `real`: all caps, else the first letter of each word as in `real`."""
    if len(real) > 1 and real.isupper():
        return fake.upper()
    rw, fw = real.split(), fake.split()
    if len(rw) == len(fw):
        return " ".join(f[:1].upper() + f[1:] if r[:1].isupper() else f for f, r in zip(fw, rw))
    return fake[:1].upper() + fake[1:] if real[:1].isupper() else fake


def apply(text, mp):
    """`text` with every key of `mp` replaced by its fake: case-insensitive, whole words only, longest key
    first, keeping the case pattern of the original."""
    if not mp:
        return text
    keys = sorted(mp, key=lambda k: (-len(k), k))
    alt = "|".join(re.escape(k).replace(r"\ ", r"\s+") for k in keys)
    pat = re.compile(rf"(?<![A-Za-z0-9_])(?:{alt})(?![A-Za-z0-9_])", re.IGNORECASE)
    return pat.sub(lambda m: _case(mp[_norm(m.group(0))], m.group(0)), text)
