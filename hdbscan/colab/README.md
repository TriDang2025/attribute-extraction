# Running BGE-M3 -> UMAP -> HDBSCAN on Google Colab (GitHub + Hugging Face)

- **Code:** this repo, folder `hdbscan/`. It is separate from `tear/`.
- **Data:** Hugging Face, plus the paper's public sources.
- **Results:** committed back to this repo under `hdbscan/results/`.

Steps marked **YOU** need a person.

## Where things live
| What | Where |
|---|---|
| Code, Colab scripts, result tables and labels | GitHub `TriDang2025/attribute-extraction`, `hdbscan/` |
| The 1,000 Conversation dialogues; bge-m3 embeddings (added by the first Colab run) | HF dataset `database-lab/attribute-extraction-data`, folder `hdbscan/` |
| Hansard speeches, gold labels, the repo's UMAP and labels | public sources, downloaded by `scripts/fetch_data.py` |
| bge-m3 model | public HF repo, pinned revision |

The repo id is set in `colab/sync.sh`.

## One-time setup
Tokens and Colab Secrets work the same way as for TEAR (`tear/colab/README.md`):
- `HF_TOKEN`: a write token
- `GH_TOKEN`: a classic token with the `public_repo` scope

**Never put a token in a notebook cell or a file.** The data upload is done once from a PC: `python -I scripts/upload_to_hf.py --data-repo database-lab/attribute-extraction-data`.

## Each session
1. **YOU: open the notebook.** In Colab, File > Open notebook > GitHub, pick `hdbscan/colab/HBE_colab.ipynb`, and choose any GPU (T4 is enough).
2. **YOU: fill in your git name and email** in cell 1, then run cells 1 and 2.
3. **Run cell 2.** It works in the background and takes about 1–2 h, mostly for embedding.
   - Embeddings are saved to HF every 30 min, so a new VM resumes them.
   - The result tables are committed to GitHub at the end.
4. **Cell 3 shows progress.** The log ends with `HBE_DONE`. Or let Claude Code drive it: run the last two cells, then in Terminal tell it `Read colab/COLAB_AGENT.md and follow it.`
5. **YOU: keep the tab open.** After a disconnect, run cells 1 and 2 again.
6. **Results:** `git pull` on any machine.
