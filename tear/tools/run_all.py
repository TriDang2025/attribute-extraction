"""Run every remaining experiment in priority order, then write the report.

  python tools/run_all.py

Waits for the SFR embeddings and the trained surrogate, writes previews for the test
texts, then runs (each step resumes if interrupted):
  1. Table 2 RAG, seeds 0-2 (no previews needed, so it overlaps surrogate training)
  2. Table 2 TEAR, seed 0
  3. Level 2: TEAR extraction, discovery, coherence, integration, TEAR*
  4. Table 2 TEAR, seeds 1 and 2, then the report (CORE_DONE)
  5. With TEAR_ALL_LEVELS=1 set: levels 1 and 3, then the report again
Settings (environment variables; defaults reproduce the original laptop run):
  TEAR_N            number of Conversation test texts (default 20)
  TEAR_MODELS       folder holding surrogate_conversation_cont2 (default <project>/models)
  TEAR_LLAMA_SERVER llama.cpp llama-server binary (default tools/llama.cpp/bin/llama-server[.exe])
  TEAR_LLAMA_GGUF   Meta-Llama-3-8B-Instruct-Q4_K_M.gguf (default <TEAR_MODELS>/gguf/...)
  TEAR_LLAMA_ARGS   extra llama-server arguments, e.g. "-ngl 99" for a GPU (default "-t 10")
Progress goes to results/run_all.log; RUN_ALL_DONE or RUN_ALL_FAILED marks the end.
"""

import json
import os
import subprocess
import sys
import time
import traceback
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import eval.reproduce as R  # noqa: E402

LOG = ROOT / "results/run_all.log"
N = int(os.environ.get("TEAR_N", "20"))
MODELS = Path(os.environ.get("TEAR_MODELS", ROOT / "models"))
LLAMA_SERVER = Path(os.environ.get("TEAR_LLAMA_SERVER", ROOT / "tools/llama.cpp/bin" / (
    "llama-server.exe" if os.name == "nt" else "llama-server")))
LLAMA_GGUF = Path(os.environ.get("TEAR_LLAMA_GGUF", MODELS / "gguf/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf"))
LLAMA_ARGS = os.environ.get("TEAR_LLAMA_ARGS", "-t 10").split()
PY = sys.executable


def log(message: str) -> None:
    LOG.parent.mkdir(exist_ok=True)
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as out:
        out.write(line + "\n")


def wait_for(check, what: str, poll: int = 60) -> None:
    if not check():
        log(f"waiting for {what}")
    while not check():
        time.sleep(poll)


def embeddings_ready() -> bool:
    path = ROOT / "data/conversation/embeddings_sfr-embedding-mistral-q4_k_m.json"
    try:
        return len(json.loads(path.read_text(encoding="utf-8"))) >= 300 + N
    except (OSError, ValueError):
        return False


def surrogate_ready() -> bool:
    return (MODELS / "surrogate_conversation_cont2/model.safetensors").exists()


def _fresh(out: Path, source: Path) -> bool:
    """True if out exists and is newer than source (a larger TEAR_N adds proposals)."""
    return out.exists() and (not source.exists() or out.stat().st_mtime >= source.stat().st_mtime)


def previews() -> None:
    out = ROOT / "data/conversation/previews.jsonl"
    if out.exists() and len(out.read_text(encoding="utf-8").splitlines()) >= N:
        return
    subset = ROOT / f"results/conversation_input_first{N}.jsonl"
    lines = (ROOT / "data/conversation/input.jsonl").read_text(encoding="utf-8").splitlines()[:N]
    subset.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log("writing surrogate previews for the test texts")
    subprocess.run([PY, "-m", "surrogate.predict", "--model", str(MODELS / "surrogate_conversation_cont2"),
                    "--input", str(subset), "--out", str(out)], check=True)


def reproduce(*args: str) -> None:
    log("reproduce " + " ".join(args))
    R.main(list(args))


def coherence(level: str) -> None:
    out = ROOT / f"results/conversation/coh_L{level}_s0.json"
    if _fresh(out, ROOT / f"results/conversation/disc_L{level}_s0.jsonl"):
        return
    server = subprocess.Popen([str(LLAMA_SERVER), "-m", str(LLAMA_GGUF), "--port", "8081",
                               "-c", "8192", "-np", "4", "--poll", "0", "--no-webui", *LLAMA_ARGS],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(120):
            try:
                if b"ok" in urllib.request.urlopen("http://localhost:8081/health", timeout=5).read():
                    break
            except OSError:
                time.sleep(3)
        reproduce("coherence", "--dataset", "conversation", "--level", level, "--seed", "0")
    finally:
        server.terminate()
        server.wait(timeout=60)


def level_chain(level: str) -> None:
    common = ["--dataset", "conversation", "--level", level]
    reproduce("te", *common, "--methods", "tear", "--seeds", "0", "--n", str(N))
    reproduce("discover", *common, "--seed", "0", "--n", str(N))
    coherence(level)
    if not _fresh(ROOT / f"results/conversation/ar_L{level}_s0.json", ROOT / f"results/conversation/coh_L{level}_s0.json"):
        reproduce("integrate", *common, "--seed", "0")
    reproduce("tearstar", *common, "--seed", "0", "--n", str(N))


def main() -> None:
    log("run_all started")
    if not embeddings_ready():  # needs the SFR embedding server on port 8082
        reproduce("embed", "--dataset", "conversation", "--n", str(N))
    # RAG needs no previews, so all its seeds run while the surrogate is still training.
    reproduce("te", "--dataset", "conversation", "--methods", "rag", "--seeds", "0", "1", "2", "--n", str(N))
    wait_for(surrogate_ready, "the trained surrogate")
    previews()
    reproduce("te", "--dataset", "conversation", "--methods", "tear", "--seeds", "0", "--n", str(N))
    level_chain("2")
    reproduce("te", "--dataset", "conversation", "--methods", "tear", "--seeds", "1", "2", "--n", str(N))
    reproduce("report")
    log("CORE_DONE")
    if os.environ.get("TEAR_ALL_LEVELS"):
        level_chain("1")
        level_chain("3")
        reproduce("report")
    log("RUN_ALL_DONE")


if __name__ == "__main__":
    try:
        main()
    except BaseException:
        log("RUN_ALL_FAILED\n" + traceback.format_exc())
        raise
