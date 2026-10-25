# TEAR reproduction
Reproduces TEAR (table extraction TEW + attribute recommendation ARW) from the source paper. Full guide: `README.md`. Colab: `colab/README.md`; agent steps on Colab: `colab/COLAB_AGENT.md`.

## Critical rules
- Don't change method code or prompts without asking. Never force-push or rewrite `results/`.
- Data and models never go in git; tokens never go in files or notebooks (Colab Secrets only).
- One TEAR run at a time (`results/RUN_OWNER` says who is running).

## Setup and commands
Long runs (workflow):
1. Test locally first (unit tests, `bash -n colab/*.sh`), then push the code to GitHub. Data, models and tokens never go in git.
2. Data and models live on Hugging Face (`database-lab`, private): dataset `attribute-extraction-data` (folder `tear/`) and model `tear-surrogate`; one TEAR run at a time (`results/RUN_OWNER`).
3. Run on Colab with `colab/TEAR_colab.ipynb` (see `colab/README.md`); start with a small benchmark and give a time estimate before the full run.
4. Results are committed back to `tear/results/` by `colab/sync.sh` (every 30 min and at the end); `git pull` to get them.
5. Tokens only in Colab Secrets (`HF_TOKEN`, `GH_TOKEN` = classic token with `public_repo`).

## Layout
- `tear_reproduction/` (method), `surrogate/` (BART-Large preview model), `eval/` (metrics, experiment steps), `tools/run_all.py` (all steps, resumable; progress in `results/run_all.log`, ends with `RUN_ALL_DONE` or `RUN_ALL_FAILED`), `data_build/` (dataset builders).
- `data/`: not in git; from the HF dataset (`colab/sync.sh pull-data`, folder `tear/`). The surrogate is an HF model repo. Repo ids: `colab/env.sh`.
- `results/`: committed to git (from Colab by `colab/sync.sh push-results`).

## Data links
- `data_build/multiwoz.py` -> `data/conversation/{pool,test,input}.jsonl`, `levels.json`, `README.md` -> `eval/reproduce.py`, `tools/run_all.py`, `surrogate/train.py` (`--pool`), and `../step1a/` (`pool`, `test`, `levels.json`)
- `tools/run_all.py` (previews step) -> `data/conversation/previews.jsonl` -> `eval/reproduce.py`
- `eval/reproduce.py` -> `results/<dataset>/te_<method>_L<level>_s<seed>.jsonl` -> `disc_L<l>_s<s>.jsonl` -> `coh_L<l>_s<s>.json` -> `ar_L<l>_s<s>.json` -> `te_tearstar_L<l>_s<s>.jsonl` (+ meta json) -> `results/report.{md,json}`
- `eval/reproduce.py` -> `data/conversation/embeddings_<name>.json` (embedding cache)
- `tools/run_all.py` -> `results/conversation_input_first<N>.jsonl`, `results/run_all.log`

## Status (2026-10-19)
- All paper components implemented; 49 unit tests pass.
- 200 Conversation test texts run on a Colab L4 (2026-10-19, commit e4d0304):
  - Table 2 structured-F1 EM: RAG 65.9 (paper 76.9), TEAR 67.1 (paper 82.4)
  - recall-AUC 64-75 chrF
  - TEAR* +9.0 at level 3

  Details: `results/report.md`.
- Next: the remaining 500 texts (about 14 h on an L4).
