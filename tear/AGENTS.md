# TEAR reproduction (agent notes)

Reproduces TEAR (table extraction TEW + attribute recommendation ARW) from the source paper. Full guide: `README.md`. Colab: `colab/README.md`; agent steps on Colab: `colab/COLAB_AGENT.md`.

## Where things are
- Code: `tear_reproduction/` (method), `surrogate/` (BART-Large preview model), `eval/` (metrics, experiment steps), `tools/run_all.py` (all steps, resumable), `data_build/` (dataset builders).
- Data: `data/` is not in git; it comes from the HF dataset (`colab/sync.sh pull-data`, folder `tear/`). The surrogate is an HF model repo. Repo ids: `colab/env.sh`.
- Results: `results/`, committed to git (from Colab by `colab/sync.sh push-results`). `results/RUN_OWNER` says who is running; one TEAR run at a time.

## Status (2026-10-17)
- All paper components implemented; 49 unit tests pass.
- First 20 Conversation test texts run on a CPU laptop (Llama-3-8B Q4): Table 2 structured-F1 EM RAG 68.2 (paper 76.9), TEAR 71.5 (paper 82.4). Details: `results/report.md`.
- Next: larger runs on Colab GPU (N=100, then 700).

## Rules
- Don't change method code or prompts without asking. Never force-push or rewrite `results/`.
- Data and models never go in git; tokens never go in files or notebooks (Colab Secrets only).
