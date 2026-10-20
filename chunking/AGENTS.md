# Size-constrained semantic chunking on Conversation (agent notes)

Reproduces three chunkers and compares them on the 1,000 Conversation (MultiWOZ 2.4) dialogues. Separate from `../tear/` and `../hdbscan/`. Checklist and background: OneDrive `TEAR/report/chunking_repro_checklist.md`, `texttiling_semantic_chunking_papers.md`.

## Methods (`chk/methods.py`, settings in `chk/config.py`)
1. `rsc`: Recursive Semantic Chunking (Latif et al., ICNLSP 2025). No public code, so it is rebuilt from Algorithm 1 on LangChain `SemanticChunker`.
2. `chroma`: ClusterSemanticChunker, official `chunking_evaluation` @ e708410. Uses bge-m3, not the OpenAI default.
3. `chonkie`: `chonkie.SemanticChunker` 1.7.0 with defaults, run once with potion-base-32M (the default) and once with bge-m3.
Baselines: `fixed` (400 cl100k tokens) and `texttiling` (NLTK).

## Data and gold (`chk/data.py`)
- `data/` is not in git: `MULTIWOZ2.4.zip`, `conversation_ids.txt` (the 1,000 ids), `cache/` (embedding cache).
- Each turn's gold domain comes from the system dialogue acts (`dialogue_acts.json` key k = log turn 2k-1), with the belief-state change as fallback. Hand-checked on 20 dialogues.
- Setting S = one dialogue per document. Setting T = 20 shuffled dialogues per document; gold boundaries there also include dialogue boundaries.
- Retrieval queries are the goal messages per domain.

## Run
- venv: `C:\Users\nguye\venvs\chunking` (`--system-site-packages`, reuses the global torch). Models are in `CHK_MODELS` (default `~/models`: `bge-m3`, `potion-base-32M`).
- `python -m pytest -q tests`, then `python scripts/run.py --setting S|T [--seed 42] [--limit 50]`. Output goes to `results/<run>/`.
- The full run is on Colab: `colab/README.md`, notebook `colab/CHK_colab.ipynb`, agent steps in `colab/COLAB_AGENT.md`. The data is on the HF dataset `database-lab/attribute-extraction-data`, folder `chunking/`.
- Smoke runs on the laptop (2026-10-19): `results/S_n50`, `results/T_seed42_n40`.

## Status (2026-10-20)
- The scope is a 5% sample (the first 50 dialogues), run on the laptop: `results/S_n50` and `results/T_seed{42,0,1}_n50` (3 stitched documents per seed). The Colab full run is ready but not used.
- `scripts/make_viewer.py <run>` gives a per-run browser view (`results/<run>/viewer.html`). `scripts/make_showcase.py --out X.html` builds 4 real examples side by side, the score tables, and the differences from each source. A copy of that page is `results/examples_5pct.html`.
- Main patterns, from this sample only:
  - Chonkie (both models) over-cuts: about 8 chunks per dialogue, and half its cuts fall inside turns.
  - RSC cuts rarely, and about half its cuts also fall inside turns (LangChain's sentence regex).
  - Chroma almost never cuts inside a turn, and it has the best coherence gap and boundary F1 on the stitched documents.

## Rules
- Don't change published settings or metric code without asking. Data and models never go in git.
