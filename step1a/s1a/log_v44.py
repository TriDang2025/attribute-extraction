"""wf_v4.4 shared logging (diary Nov 14, rules "save the raw text of every guided answer, also when it fails" and "log for every call").
Shared by Step 3 v4.4, Step 4 v4.4 and the T3/T8/T9 checks; the agents import it and do not edit it.

- RepairLog: re-exported from log_v43 (repairs per run, saved as repairs.json).
- VllmBackend44: VllmBackend (nov16_v41.py) that also keeps the guided answer when the unguided retry wins
  (fields guided_raw, guided_errors, guided_finish_reason) and the per-job time job_seconds = batch_seconds / batch_size.
- save_load_time / load_time: the model loading time, logged once per Colab session in <results>/model_load.json.
- call_rows(out): log_v43.call_rows plus the new fields.
"""
import hashlib
import json
import time
from pathlib import Path

from s1a import llm_cache as LC
from s1a import log_v43 as L43
from s1a import nov16_v41 as NV

RepairLog = L43.RepairLog
call_totals = L43.call_totals
CALL_FIELDS = L43.CALL_FIELDS + ("batch_size", "job_seconds", "guided_finish_reason")


def job_seconds(row):
    """Model seconds of one job: its batch's seconds split evenly over the batch (None if not logged)."""
    s, n = row.get("batch_seconds"), row.get("batch_size")
    return round(s / n, 3) if s is not None and n else s


def call_rows(out):
    """One dict per cached answer under out/**/responses, with CALL_FIELDS (missing fields -> None)."""
    rows = []
    for p in sorted(Path(out).glob("**/responses/*.jsonl")):
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                r.setdefault("job_seconds", job_seconds(r))
                rows.append({k: r.get(k) for k in CALL_FIELDS} | {"file": p.relative_to(out).as_posix()})
    return rows


def save_load_time(path, seconds, model="", revision=""):
    """Write the model loading time once (an existing file is kept, so a rerun after a crash does not overwrite it)."""
    path = Path(path)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    d = {"model": model, "revision": revision, "load_seconds": round(float(seconds), 1),
         "logged_at": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(d, indent=1) + "\n", encoding="utf-8", newline="\n")
    return d


def load_time(path):
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


class VllmBackend44(NV.VllmBackend):
    """VllmBackend with the v4.4 logging; same cache keys and retry rule as VllmBackend."""

    def run(self, out, jobs):
        out, todo = Path(out), []
        for j in jobs:
            prompt = (out / j["prompt"]).read_text(encoding="utf-8")
            schema = json.loads((out / j["schema"]).read_text(encoding="utf-8"))
            n = NV.prompt_tokens(self.tok, j["job"], prompt, self.limit)
            max_tokens = min(j["max_tokens"], self.max_len - n - 64)
            schema_sha = hashlib.sha256(json.dumps(schema, sort_keys=True).encode("utf-8")).hexdigest()[:16]
            params = {"temperature": 0, "max_tokens": max_tokens, "guided_json": j["schema"], "schema_sha": schema_sha}
            k, path = LC.key(self.model_id, params, prompt, j["run_tag"]), out / "responses" / f"{j['job']}.jsonl"
            if LC.get(path, k) is None:
                todo.append({"job": j, "prompt": prompt, "schema": schema, "max_tokens": max_tokens, "params": params, "key": k, "path": path})
        self.log(f"{len(jobs) - len(todo)} cached, {len(todo)} to run in batches of {self.batch}")
        bad = 0
        for b0 in range(0, len(todo), self.batch):
            items = todo[b0:b0 + self.batch]
            t0 = time.time()
            outs, flags = self._generate([self.chat(it["prompt"]) for it in items], items)
            secs = time.time() - t0
            for it, o, guided in zip(items, outs, flags):
                row = self._row(it, o, guided, LC.token_fields(o, secs, len(items)))
                row["job_seconds"] = job_seconds(row)
                if row["errors"] and guided:
                    t1 = time.time()
                    o2 = self.engine.generate([self.chat(it["prompt"])], self.sampling(it["max_tokens"], None))[0]
                    row2 = self._row(it, o2, False, LC.token_fields(o2, time.time() - t1, 1))
                    best = dict(row2 if len(row2["errors"]) < len(row["errors"]) else row)
                    best.update(retried=True, prompt_tokens=row["prompt_tokens"] + row2["prompt_tokens"],
                                output_tokens=row["output_tokens"] + row2["output_tokens"],
                                job_seconds=round((row["job_seconds"] or 0) + (row2["batch_seconds"] or 0), 3),
                                guided_raw=row["raw"], guided_errors=row["errors"], guided_finish_reason=row["finish_reason"])
                    row = best
                bad += bool(row["errors"])
                LC.put(it["path"], it["key"], row)
                self.log(f"{it['job']['job']}: tokens in {row['prompt_tokens']} out {row['output_tokens']}, errors {len(row['errors'])}, "
                         f"guided {row['guided']}, finish {row['finish_reason']}")
            self.log(f"batch of {len(items)} took {secs:.0f} s ({b0 + len(items)}/{len(todo)} done)")
        return {"jobs": len(jobs), "run": len(todo), "parse_errors": bad}
