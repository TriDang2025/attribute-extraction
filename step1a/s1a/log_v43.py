"""wf_v4.3 shared logging (diary Nov 13, rule "log for every call"). Shared by Step 3 v4.3, Step 4 v4.3 and the U5/U6 checks; the
agents import it and do not edit it.

- RepairLog: every repair code makes to a model answer (type, count, up to 3 examples per type), saved as repairs.json per run.
- call_rows(out): per-call rows from the cached VllmBackend / FakeLLM answers (responses/*.jsonl): job, prompt and output tokens,
  seconds, finish reason, guided, retried. VllmBackend (nov16_v41.py) already writes these fields; this reader only collects them.
"""
import json
from collections import Counter
from pathlib import Path

CALL_FIELDS = ("job", "format", "prompt_tokens", "output_tokens", "batch_seconds", "finish_reason", "guided", "retried")


class RepairLog:
    """Counts code repairs by type; keeps the first `keep` examples of each type."""

    def __init__(self, keep=3):
        self.keep = keep
        self.counts = Counter()
        self.examples = {}

    def add(self, kind, where="", detail=""):
        self.counts[kind] += 1
        ex = self.examples.setdefault(kind, [])
        if len(ex) < self.keep:
            ex.append({"where": where, "detail": detail})

    def merge(self, other):
        for kind, n in other.counts.items():
            self.counts[kind] += n
            ex = self.examples.setdefault(kind, [])
            ex.extend(other.examples.get(kind, [])[: max(0, self.keep - len(ex))])
        return self

    def total(self):
        return sum(self.counts.values())

    def to_dict(self):
        return {"total": self.total(), "counts": dict(sorted(self.counts.items())), "examples": self.examples}

    def save(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(self.to_dict(), indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    @classmethod
    def load(cls, path):
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        log = cls()
        log.counts.update(d.get("counts", {}))
        log.examples = d.get("examples", {})
        return log


def call_rows(out):
    """One dict per cached answer under out/responses (recursive), with CALL_FIELDS (missing fields -> None)."""
    rows = []
    for p in sorted(Path(out).glob("**/responses/*.jsonl")):
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                rows.append({k: r.get(k) for k in CALL_FIELDS} | {"file": p.relative_to(out).as_posix()})
    return rows


def call_totals(rows):
    """Calls, prompt / output tokens, finish reasons and retries over call rows."""
    return {"calls": len(rows),
            "prompt_tokens": sum(r["prompt_tokens"] or 0 for r in rows),
            "output_tokens": sum(r["output_tokens"] or 0 for r in rows),
            "finish": dict(Counter(str(r["finish_reason"]) for r in rows)),
            "retried": sum(bool(r["retried"]) for r in rows)}
