"""Label-free candidate spans with spaCy (run in the spaCy venv; standalone).

python scripts/spacy_extract.py --texts results/v2_n50/texts.jsonl --out results/v2_n50/spacy_spans.jsonl
Per turn (text after the speaker prefix): entities (source "ner"), noun chunks without leading
determiners and pronoun-only chunks ("np"), numbers and times not inside an entity ("num").
Output jsonl {doc_id, spans: [[start, end, source, label], ...]} in dialogue offsets; resumable.
"""

import argparse
import importlib.util
import json
import re
import time
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "spacy_spans", Path(__file__).resolve().parents[1] / "s1a" / "spacy_spans.py")
SS = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(SS)

TIME_RE = re.compile(r"\b\d{1,2}[:.]\d{2}\s*(?:[ap]\.?m\.?)?(?!\w)|\b\d{1,2}\s*[ap]\.?m\.?(?!\w)", re.I)


def overlaps(s, e, spans):
    return any(s < b and e > a for a, b in spans)


def candidates(doc):
    """[(start, end, source, label)] local to one turn body."""
    ents = [(x.start_char, x.end_char) for x in doc.ents]
    out = [(x.start_char, x.end_char, "ner", x.label_) for x in doc.ents]
    for nc in doc.noun_chunks:
        r = SS.strip_determiner(doc.text, nc.start_char, nc.end_char)
        if r:
            out.append((r[0], r[1], "np", "NP"))
    times = [(m.start(), m.end()) for m in TIME_RE.finditer(doc.text)]
    for s, e in times:
        if not overlaps(s, e, ents):
            out.append((s, e, "num", "TIME"))
    for t in doc:
        if (t.like_num or t.pos_ == "NUM") and not overlaps(t.idx, t.idx + len(t), ents + times):
            out.append((t.idx, t.idx + len(t), "num", "NUM"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--texts", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="en_core_web_trf")
    args = ap.parse_args()
    import spacy
    nlp = spacy.load(args.model)
    out = Path(args.out)
    done = set()
    if out.exists():
        done = {json.loads(l)["doc_id"] for l in open(out, encoding="utf-8")}
    t0 = time.time()
    with open(out, "a", encoding="utf-8", newline="\n") as f:
        for line in open(args.texts, encoding="utf-8"):
            r = json.loads(line)
            if r["doc_id"] in done:
                continue
            bodies = SS.turn_bodies(r["text"], r["turns"])
            spans = []
            for (off, _), doc in zip(bodies, nlp.pipe([b for _, b in bodies], batch_size=16)):
                for s, e, src, label in candidates(doc):
                    spans.append([*SS.to_dialogue(off, s, e), src, label])
            spans.sort(key=lambda x: (x[0], x[1], x[2]))
            f.write(json.dumps({"doc_id": r["doc_id"], "spans": spans}) + "\n")
            f.flush()
            print(f"{r['doc_id']}: {len(spans)} spans, {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
