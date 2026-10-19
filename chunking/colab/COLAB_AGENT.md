# Instructions for an agent: chunking comparison on Colab

Project: `/content/attribute-extraction/chunking`, a clone of the shared GitHub repo `TriDang2025/attribute-extraction`. Work from there.
- It compares three size-constrained semantic chunkers (RSC, Chroma ClusterSemanticChunker, Chonkie SemanticChunker) and two baselines on the 1,000 Conversation (MultiWOZ 2.4) dialogues.
- Background: `AGENTS.md`, plus `chk/config.py` for the published settings.
- Notebook cell 1 set up the HF and GitHub logins. If `hf auth whoami` or `git push` fails, ask the user to run it again.
- GitHub pushes use the `GH_TOKEN` environment variable that cell 1 sets. Jobs started from notebook cells inherit it; the Colab Terminal does not. Start runs from the notebook cells.

## Rules
- Do not change the settings in `chk/config.py` or the metric code without asking the user.
- Never delete files in `data/` or `results/`, or on HF; the run resumes from them. Never force-push.
- Result commits made by `colab/sync.sh` are allowed. **Ask before committing or pushing code changes.**
- Give the user a time estimate before anything over 5 minutes, and wait for a go-ahead.
- Never print, echo or write tokens.

## Steps
1. `bash colab/run_colab.sh` runs in the background. Check it with `bash colab/run_colab.sh status` until it shows `CHK_DONE` or `CHK_FAILED`.
   - Order: setting S, then T with seeds 42, 0 and 1. Each run prints `chunked <method> in Ns`, then one metrics line per method.
   - Laptop CPU took about 6 s per dialogue for RSC and Chonkie-bge-m3; a GPU should be 20–40 times faster.
2. After a disconnect, on a new VM: once cell 1 has run, run the same command. Finished documents are skipped.
3. Errors are in `results/colab_logs/chk.log`. If it says `PUSH_FAILED`, run `git status` and `git log origin/main..`, and ask the user.

## Check the results
- `results/S/metrics.csv` and `results/T_seed{42,0,1}/metrics.csv`, with one row per method.
- Sanity checks: `align_failed` is 0, and `pct_outside_limit` is 0 for every method.
- Write a short summary for the user covering Pk, F1_tol1, coherence_gap, purity, recall@5 and chunks_per_doc for each method.
