# Size-constrained semantic chunking on Conversation
Reproduces three chunkers and compares them on the 1,000 Conversation (MultiWOZ 2.4) dialogues. Separate from `../tear/` and `../hdbscan/`. Checklist and background: OneDrive `TEAR/report/chunking_repro_checklist.md`, `texttiling_semantic_chunking_papers.md`.

## Critical rules
- Don't change published settings or metric code without asking.
- Data and models never go in git.

## Setup and commands
- venv: `C:\Users\nguye\venvs\chunking` (`--system-site-packages`, reuses the global torch). Models are in `CHK_MODELS` (default `~/models`: `bge-m3`, `potion-base-32M`).
- `python -m pytest -q tests`, then `python scripts/run.py --setting S|T [--seed 42] [--limit 50]`. Output goes to `results/<run>/`.
- `scripts/make_viewer.py <run>` -> `results/<run>/viewer.html` (per-run browser view).
- `scripts/make_showcase.py --out X.html`: 4 real examples side by side, the score tables, and the differences from each source. A copy is `results/examples_5pct.html`.
- Full run is on Colab (ready, not used): `colab/README.md`, notebook `colab/CHK_colab.ipynb`, agent steps `colab/COLAB_AGENT.md`. Data is on the HF dataset `database-lab/attribute-extraction-data`, folder `chunking/`.

## Layout
- `chk/methods.py`: the chunkers; settings in `chk/config.py`.
  - `rsc`: Recursive Semantic Chunking (Latif et al., ICNLSP 2025). No public code, so it is rebuilt from Algorithm 1 on LangChain `SemanticChunker`.
  - `chroma`: ClusterSemanticChunker, official `chunking_evaluation` @ e708410. Uses bge-m3, not the OpenAI default.
  - `chonkie`: `chonkie.SemanticChunker` 1.7.0 with defaults, run once with potion-base-32M (the default) and once with bge-m3.
  - Baselines: `fixed` (400 cl100k tokens) and `texttiling` (NLTK).
- `chk/data.py`: data and gold.
  - `data/` is not in git: `MULTIWOZ2.4.zip`, `conversation_ids.txt` (the 1,000 ids), `cache/` (embedding cache).
  - Each turn's gold domain comes from the system dialogue acts (`dialogue_acts.json` key k = log turn 2k-1), with the belief-state change as fallback. Hand-checked on 20 dialogues.
  - Setting S = one dialogue per document. Setting T = 20 shuffled dialogues per document; gold boundaries there also include dialogue boundaries.
  - Retrieval queries are the goal messages per domain.
- `scripts/`, `tests/`, `colab/`, `results/`.

## Data links
- `scripts/run.py` -> `results/<run>/chunks/<method>.jsonl` (resumable) and `results/<run>/metrics.csv` -> `scripts/make_viewer.py`, `scripts/make_showcase.py` (reads `S_n50`, `T_seed{42,0,1}_n50`), and `../step1a/` (reads `results/S_n50/chunks/chroma_bge-m3.jsonl`)
- `data/MULTIWOZ2.4.zip` + `data/conversation_ids.txt` -> `chk/data.py` `load_dialogues` -> `scripts/run.py`, and `../step1a/` (imports it)
- `chk/embed.py` -> pickle embedding cache (`data/cache/`) -> same module

## Status (2026-10-20)
- The scope is a 5% sample (the first 50 dialogues), run on the laptop: `results/S_n50` and `results/T_seed{42,0,1}_n50` (3 stitched documents per seed). The Colab full run is ready but not used.
- Main patterns, from this sample only:
  - Chonkie (both models) over-cuts: about 8 chunks per dialogue, and half its cuts fall inside turns.
  - RSC cuts rarely, and about half its cuts also fall inside turns (LangChain's sentence regex).
  - Chroma almost never cuts inside a turn, and it has the best coherence gap and boundary F1 on the stitched documents.

## History
- 2026-10-19: smoke runs on the laptop: `results/S_n50`, `results/T_seed42_n40`.
