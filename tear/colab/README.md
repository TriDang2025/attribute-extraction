# Running TEAR on Google Colab (GitHub + Hugging Face)

- **Code:** this repo, folder `tear/`.
- **Data and surrogate:** Hugging Face.
- **Results:** committed back to this repo under `tear/results/`.

Steps marked **YOU** need a person.

## Where things live
| What | Where |
|---|---|
| Code, Colab scripts, results | GitHub `TriDang2025/attribute-extraction`, `tear/` |
| `tear/data/`: Conversation, small sets, embedding caches | HF dataset `database-lab/attribute-extraction-data`, folder `tear/` |
| BART surrogate `surrogate_conversation_cont2` | HF model `database-lab/tear-surrogate` |
| `llama-server` built for each GPU type | HF dataset, folder `cache/` |
| Llama-3-8B and SFR GGUFs | their public HF repos, downloaded each session |

The repo ids are set in `colab/env.sh`.

## One-time setup
1. **YOU: create a Hugging Face write token** at hf.co/settings/tokens. Never paste a token into a notebook cell or a file in this repo, because the repo is public.
2. **YOU: create a GitHub classic token** at github.com/settings/tokens with the `public_repo` scope. Fine-grained tokens can't push to a repo you only collaborate on.
3. **YOU: add both tokens to Colab Secrets.** Click the key icon on the left of any notebook, add `HF_TOKEN` and `GH_TOKEN`, and turn on notebook access. Secrets belong to your Google account, so this is done once.
4. **Collaborators:** the HF repos are private, so each person needs read access, and write access to upload. They are in the HF organization `database-lab`, so every collaborator must be a member with write access (huggingface.co/database-lab > Settings > Members). Each person uses their own tokens; a fine-grained token needs write permission for `database-lab`.
5. **Data upload:** done once from a PC that has the data, with `python tools/upload_to_hf.py --data-repo database-lab/attribute-extraction-data --model-repo database-lab/tear-surrogate`.

## Each session
1. **YOU: open the notebook.** In Colab, File > Open notebook > GitHub, search `TriDang2025/attribute-extraction`, and pick `tear/colab/TEAR_colab.ipynb`.
2. **YOU: pick the GPU.** Runtime > Change runtime type > **L4** (or A100).
3. **YOU: fill in your git name and email** in cell 1, then run cells 1–3:
   - cell 1: logins, then clone or pull
   - cell 2: setup. The first time on a GPU type it takes about 20–30 min while it builds `llama-server` and caches it on HF; later it takes about 5 min.
   - cell 3: starts the model servers
4. **Run cell 4.** Start with N = 25 as a benchmark (5 new texts).
   - Results are committed to GitHub every 30 min and when the run ends.
   - The growing embedding cache and previews go to HF.
   - `results/RUN_OWNER` records who is running. Only one TEAR run at a time across everyone, because all runs write the same result files.
5. **Cell 5 shows progress.** Or let Claude Code drive it: run the last two cells, then in Terminal tell it `Read colab/COLAB_AGENT.md and follow it.`
6. **YOU: keep the tab open.** After a disconnect, run cells 1–3 and the same cell 4 line again; the run resumes from the committed results.
7. **Results:** `git pull` on any machine.

## Scripts
- `setup.sh`, `start_servers.sh`, `run.sh N [ALL_LEVELS]`, `status.sh`
- `sync.sh pull-data | push-data | push-results MSG`
- `env.sh`: shared settings
