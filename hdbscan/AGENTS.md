# BGE-M3 -> UMAP -> HDBSCAN reproduction (agent notes)

Reproduces the clustering of *Trilingual Topic Modeling of Sri Lankan Parliamentary Debates* (arXiv 2608.20365; code HimathX/lk-hansard-topic-modeling), then runs the same pipeline on the 1,000 Conversation (MultiWOZ) dialogues. Separate from `../tear/`. Colab: `colab/README.md`; agent steps: `colab/COLAB_AGENT.md`.

## Where things are
- `hbe/`: config (paper settings, targets), data loaders, embedding, clustering, metrics. `scripts/`: `fetch_data.py` (public paper data), `embed_all.py`, `reproduce_hansard.py` (Stage A: repo UMAP; Stage B: our embeddings), `run_conversation.py`, `upload_to_hf.py`.
- `data/` is not in git: Hansard data from public sources; Conversation dialogues and bge-m3 embeddings from the HF dataset (folder `hdbscan/`, repo id in `colab/sync.sh`).
- `results/`: committed to git.

## Status (2026-10-17)
- Stage A matches the repo artifacts exactly (K 336, noise 35.4%, silhouette 0.574, ARI/NMI vs repo 1.0). The paper's Table III (288 gold, 11 topics) differs from the repo's own artifacts (269, 92).
- Stage B and Conversation need the GPU embeddings (Colab).

## Long runs (workflow)
1. Test locally first (unit tests, `bash -n colab/*.sh`), then push the code to GitHub. Data, models and tokens never go in git.
2. Data and models live on Hugging Face (`database-lab`, private): dataset `attribute-extraction-data` (folder `hdbscan/`); Hansard data comes from the paper's public sources.
3. Run on Colab with `colab/HBE_colab.ipynb` (see `colab/README.md`); start with a small benchmark and give a time estimate before the full run.
4. Results are committed back to `hdbscan/results/` by `colab/sync.sh` (every 30 min and at the end); `git pull` to get them.
5. Tokens only in Colab Secrets (`HF_TOKEN`, `GH_TOKEN` = classic token with `public_repo`).

## Rules
- Don't change paper settings or metric code without asking. Never force-push.
- Data never goes in git; tokens never go in files or notebooks.
