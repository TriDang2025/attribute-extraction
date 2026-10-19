# TEAR reproduction (agent notes)

Reproduces TEAR (table extraction TEW + attribute recommendation ARW) from the source paper. Full guide: `README.md`. Colab: `colab/README.md`; agent steps on Colab: `colab/COLAB_AGENT.md`.

## Where things are
- Code: `tear_reproduction/` (method), `surrogate/` (BART-Large preview model), `eval/` (metrics, experiment steps), `tools/run_all.py` (all steps, resumable), `data_build/` (dataset builders).
- Data: `data/` is not in git; it comes from the HF dataset (`colab/sync.sh pull-data`, folder `tear/`). The surrogate is an HF model repo. Repo ids: `colab/env.sh`.
- Results: `results/`, committed to git (from Colab by `colab/sync.sh push-results`). `results/RUN_OWNER` says who is running; one TEAR run at a time.

## Status (2026-10-19)
- All paper components implemented; 49 unit tests pass.
- 200 Conversation test texts run on a Colab L4 (2026-10-19, commit e4d0304):
  - Table 2 structured-F1 EM: RAG 65.9 (paper 76.9), TEAR 67.1 (paper 82.4)
  - recall-AUC 64-75 chrF
  - TEAR* +9.0 at level 3

  Details: `results/report.md`.
- Next: the remaining 500 texts (about 14 h on an L4).

## Long runs (workflow)
1. Test locally first (unit tests, `bash -n colab/*.sh`), then push the code to GitHub. Data, models and tokens never go in git.
2. Data and models live on Hugging Face (`database-lab`, private): dataset `attribute-extraction-data` (folder `tear/`) and model `tear-surrogate`; one TEAR run at a time (`results/RUN_OWNER`).
3. Run on Colab with `colab/TEAR_colab.ipynb` (see `colab/README.md`); start with a small benchmark and give a time estimate before the full run.
4. Results are committed back to `tear/results/` by `colab/sync.sh` (every 30 min and at the end); `git pull` to get them.
5. Tokens only in Colab Secrets (`HF_TOKEN`, `GH_TOKEN` = classic token with `public_repo`).

## Rules
- Don't change method code or prompts without asking. Never force-push or rewrite `results/`.
- Data and models never go in git; tokens never go in files or notebooks (Colab Secrets only).
