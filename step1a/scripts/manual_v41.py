"""wf_v4.1 dry runs by hand in the Gemini web app (no API key; user choice 2026-11-07). DRY RUN, not a result.

python scripts/manual_v41.py --export   writes every prompt that has no answer yet to <pack>/todo/<job>.txt and <pack>/CHECKLIST.md
python scripts/manual_v41.py --import   reads <pack>/answers/<job>.txt (the chat answer, pasted as is), writes the response rows the other
                                        scripts read (<job dir>/responses/<job>.jsonl), moves the answered prompt to <pack>/done/, builds the
                                        next Step-4 stage when a stage is complete, then exports again
After --import: python scripts/step1b_v41.py --check ; python scripts/judge_v41.py --collect ; python scripts/step4_v41.py --report
<pack> = OneDrive report/3_main/wf_v4.1/gemini_chats (--pack to change). <pack>/MODEL.txt (optional) holds the model name the app shows.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from s1a import batch_v4 as B  # noqa: E402
from s1a import batch_v4_fake as F  # noqa: E402

RES = ROOT / "results" / "wf_v41"
PACK = Path(r"C:\Users\nguye\OneDrive\Desktop\Work\TEAR\report\3_main\wf_v4.1\gemini_chats")
STEP4 = RES / "step4_dryrun"
# (group, job dir, manifests); Step 4 has one manifest per stage, built one after the other
GROUPS = [("step1b", RES / "step1b", ["manifest.json"]),
          ("step4", STEP4, ["manifest.json"] + [f"manifest_stage{k}.json" for k in (2, 3, 4)]),
          ("judge", RES / "judge", ["manifest.json"]),
          ("step3", RES / "step3_loop2" / "dev50", ["manifest.json"]),
          ("step3", RES / "step3_loop2" / "dev50b", ["manifest.json"])]
HINT = {"step1b": "Step 1b review and suggestions", "step4": "Step 4 v4.1 chain (one step; the next step appears after --import)",
        "judge": "judge packet (a repeat `_r2` is a new chat too)", "step3": "Step 3 naming of the loop-2 clusters (orders s0-s2: 3 chats)"}


def pending():
    """[(group, dir, job)] of the jobs whose manifest exists and that have no response row yet, in GROUPS order."""
    out = []
    for g, d, mans in GROUPS:
        for m in mans:
            if (d / m).exists():
                out += [(g, d, j) for j in B.read_json(d / m)["jobs"] if B.last_row(d / "responses" / f"{j['job']}.jsonl") is None]
    return out


def export(pack):
    todo = pending()
    (pack / "todo").mkdir(parents=True, exist_ok=True)
    (pack / "answers").mkdir(exist_ok=True)
    lines = ["# Gemini web-app dry runs: checklist", "", "**DRY RUN, not a result.** For each file below:",
             "1. Open a **new chat** at gemini.google.com (Gemini Apps Activity off, so no memory).",
             "2. Open the file in `todo/`, copy all of it, paste it as the only message, send.",
             "3. Copy the whole answer (the copy button under it) into a new text file `answers/<same file name>` (the same name as in todo/, .txt).",
             "4. When a batch is done, tell Claude \"answers saved\" (it runs `--import`; new Step-4 steps appear in todo/ after that).",
             "Write the model name the app shows (for example \"2.5 Pro\") once into `MODEL.txt`.", "",
             "| # | done | file | what |", "|---|---|---|---|"]
    for i, (g, d, j) in enumerate(todo, 1):
        shutil.copyfile(d / j["prompt"], pack / "todo" / f"{j['job']}.txt")
        lines.append(f"| {i} | [ ] | todo/{j['job']}.txt | {HINT[g]} |")
    if not todo:
        lines.append("| - | - | nothing left | |")
    B.write(pack / "CHECKLIST.md", "\n".join(lines) + "\n")
    print(f"{len(todo)} prompts in {pack / 'todo'}")


def import_answers(pack):
    model_file = pack / "MODEL.txt"
    model = model_file.read_text(encoding="utf-8").strip() if model_file.exists() else "gemini web app (model not noted)"
    n, bad = 0, []
    for g, d, j in pending():
        f = pack / "answers" / f"{j['job']}.txt"
        if not f.exists():
            continue
        raw = f.read_text(encoding="utf-8-sig")

        def respond(job, prompt, schema, raw=raw):
            return raw
        respond.last = {"guided": False, "model": f"{model} (Gemini web app, by hand)", "finish_reason": "manual"}
        from dryrun_v41 import parsers
        ps = parsers()
        from s1a import llm_cache as LC

        def parse(raw, job, schema):
            if job["format"] in ps:
                return ps[job["format"]](raw, job, schema)
            return LC.parse_job(raw, job["format"], schema)[:2]
        if F.run_jobs(d, [j], model=respond, parse=parse):
            bad.append(j["job"])
        n += 1
        (pack / "done").mkdir(exist_ok=True)
        src = pack / "todo" / f"{j['job']}.txt"
        if src.exists():
            shutil.move(str(src), str(pack / "done" / src.name))
    print(f"{n} answers imported" + (f"; parse errors in {bad}" if bad else ""))
    next_step4()
    export(pack)


def next_step4():
    """Build the next Step-4 stage when every job of the last built stage has a response (stage 1 is built if missing)."""
    import step4_v41 as S4
    if not (STEP4 / "manifest.json").exists():
        S4.build(STEP4, 1)
        return
    for k in (2, 3, 4):
        prev = STEP4 / ("manifest.json" if k == 2 else f"manifest_stage{k - 1}.json")
        cur = STEP4 / f"manifest_stage{k}.json"
        if cur.exists():
            continue
        jobs = B.read_json(prev)["jobs"]
        if jobs and all(B.last_row(STEP4 / "responses" / f"{j['job']}.jsonl") for j in jobs):
            built = S4.build(STEP4, k)
            print(f"Step 4 stage {k}: {len(built)} new prompt(s)")
        return


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--export", action="store_true")
    ap.add_argument("--import", dest="imp", action="store_true")
    ap.add_argument("--pack", type=Path, default=PACK)
    a = ap.parse_args()
    if a.export:
        next_step4()
        export(a.pack)
    if a.imp:
        import_answers(a.pack)


if __name__ == "__main__":
    main()
