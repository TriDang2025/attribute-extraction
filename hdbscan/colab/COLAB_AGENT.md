# Instructions for an agent: BGE-M3 -> UMAP -> HDBSCAN on Colab

Project: `/content/attribute-extraction/hdbscan`, a clone of the shared GitHub repo `TriDang2025/attribute-extraction`. Work from there.
- It reproduces the clustering of *Trilingual Topic Modeling of Sri Lankan Parliamentary Debates* (arXiv 2608.20365, code HimathX/lk-hansard-topic-modeling).
- It then applies the same pipeline to the 1,000 Conversation dialogues in `data/conversation`, downloaded from Hugging Face.
- Background: `AGENTS.md`, and `hbe/config.py` for the paper settings and targets.
- Notebook cell 1 set up the HF and GitHub logins. If `hf auth whoami` or `git push` fails, ask the user to run it again.

- GitHub pushes use the `GH_TOKEN` environment variable that notebook cell 1 sets. Jobs started from notebook cells inherit it; the Colab Terminal does not. So start runs from the notebook cells (`run.sh` / `run_colab.sh`), and if a push from the Terminal fails with `could not read Username`, ask the user to run the push from a notebook cell instead.

## Rules
- Do not change the paper settings in `hbe/config.py` or the metric code without asking the user.
- Never delete files in `data/` or `results/`, or on HF; the run resumes from them. Never force-push.
- Result commits made by `colab/sync.sh` are allowed. **Ask before committing or pushing code changes.**
- Give the user a time estimate before anything over 5 minutes, and wait for a go-ahead.
- Never print, echo or write tokens.

## Steps
1. `bash colab/run_colab.sh` runs in the background. Check it with `bash colab/run_colab.sh status` every few minutes until it shows `HBE_DONE` or `HBE_FAILED`.
   - Embedding 19,553 speeches at up to 8,192 tokens is the slow part: about 1–2 h on a T4, less on an L4 or A100. The log shows `N/19553 encoded`.
   - Embeddings go to HF every 30 min, and the result tables are committed to GitHub at the end.
2. After a disconnect, on a new VM: once cell 1 has run, run the same command. The embeddings resume from HF.
3. Errors are in `results/colab_logs/hbe.log`. If it says `PUSH_FAILED`, run `git status` and `git log origin/main..`, and ask the user.

## Check the results
- Hansard (`results/hansard/results_all.md`): compare each run with the two target rows.
  - Stage A (repo's UMAP, our HDBSCAN) already matched the repo exactly on the laptop: K 336, noise 35.4%, silhouette 0.574, ARI/NMI vs repo 1.0. It should again.
  - Stage B (our embeddings and UMAP) will differ by UMAP randomness; report K, noise %, internal metrics, gold B-cubed/ARI/NMI, ARI vs repo and kNN overlap, and the spread over seeds 42/0/1.
  - The paper's Table III (288 gold speeches, 11 predicted topics) does not match the repo's own artifacts (269, 92); say which one each run is closer to.
- Conversation (`results/conversation/sweep_mean.csv`, `clusters_paper_config.csv`): K and noise % at the paper setting (min_cluster_size 10), how well clusters match the domain sets / main domains (purity, B-cubed, ARI, NMI), and how the sweep (5/10/20/40) changes this.
- Write a short summary for the user with both tables and what matches or differs from the paper.
