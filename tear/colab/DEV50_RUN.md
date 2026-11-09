# TEAR on dev50 and dev50b (wf_v3.6 T40; dev50b added in wf_v4.1)

Goal: TEAR (`te_tear_Lfull`, seed 0, full 35-attribute schema) on the Step-1a dev dialogues, so its columns can be scored against the same GT as the Step-1a variants (`step1a/scripts/score_tear_v36.py`, and the main claim `step1a/scripts/mainclaim_v41.py --tear`). Do not run RAG or the other levels.
- dev50 = ids 0-49 of TEAR's pool; dev50b = ids 50-99 (`step1a/s1a/split.py` DEV50B). Same pool, same model, same settings.

## Demonstrations and leakage
- TEAR picks `shots` (8 for Conversation) demonstrations per text from the labeled pool `data/conversation/pool.jsonl` (300 texts, train + val), ranked by header preview, value preview and SFR embedding cosine (`tear_reproduction/retrieval.py`, `pipeline.extract`).
- Both sets are pool texts, so in the normal run a text would retrieve itself (cosine 1.0) with its gold table. Datasets `conversation_dev50` and `conversation_dev50b` (`eval/reproduce.py`, `HELD_OUT`) remove their 50 ids from the pool (250 left) and read their texts from `data/conversation_dev50.jsonl` / `data/conversation_dev50b.jsonl`. Nothing else changes (`conversation` is untouched).
- Not removed: the BART surrogate (`surrogate_conversation_cont2`) was trained on the pool, so its previews saw these dialogues in training and are better than on unseen texts. Retraining without the ids is not done here. Report TEAR on dev50 and dev50b with this caveat.

## Steps
1. Laptop, once (needs `hf auth login`; check with `hf auth whoami`): upload the inputs. dev50 is already on the HF dataset; dev50b is not yet.
   `hf upload database-lab/attribute-extraction-data tear/data/conversation_dev50b.jsonl tear/conversation_dev50b.jsonl --repo-type dataset`
   (build from `tear/` with `python -I data_build/dev50.py --start 50`; dev50 with no `--start`. 50 rows each, checked against `pool.jsonl`.)
2. Colab, L4: notebook `colab/TEAR_colab.ipynb`, cells 1-3 (logins, setup, servers; `pull-data` fetches the new file).
3. In cell 4, replace the run command with:
   `TEAR_DEV50=both bash colab/run.sh 50 0`
   (`TEAR_DEV50=dev50` or `dev50b` runs one set; `1` = dev50, as before.) `run.sh` claims `results/RUN_OWNER`, starts `tools/run_all.py`, and pushes results every 30 min. With `TEAR_DEV50` set, run_all does only, per set: embedding cache check, previews for the 50 texts (`data/conversation/previews_<set>.jsonl`), then `te --dataset conversation_<set> --methods tear --seeds 0 --level full --n 50`.
4. Output: `tear/results/conversation_dev50/te_tear_Lfull_s0.jsonl` and `tear/results/conversation_dev50b/te_tear_Lfull_s0.jsonl` (50 rows each: id, table, preview, demonstration_indices, schema, seconds, calls). Progress: `bash colab/status.sh`; end marker `RUN_ALL_DONE` in `results/run_all.log`. Rerun the same command after a disconnect: done texts are skipped.
5. Laptop: `git pull`, then from `step1a/`:
   - `python scripts/score_tear_v36.py --set dev50 --tear ../tear/results/conversation_dev50/te_tear_Lfull_s0.jsonl`
   - `python scripts/score_tear_v36.py --set dev50b --tear ../tear/results/conversation_dev50b/te_tear_Lfull_s0.jsonl --out results/wf_v41/tear_dev50b`
   - main claim: `python scripts/mainclaim_v41.py --set <set> --loop2 <loop-2 clusters.json> --tear <the TEAR file of the set>`

## Scorer dry run (wf_v4.1, 2026-11-09)
Both scorers were run on a fake TEAR output: the gold table of each text in TEAR's output format. 35 columns per set, 0 unmatched. Main claim: TEAR found (span) 28/40 on dev50 and 28/41 on dev50b. This is TEAR's ceiling under this scorer, because Hotel internet and parking (yes/no values) and the gold attributes outside TEAR's 35-attribute schema cannot be found by span. Internet and parking go to the blind check sheet with a name match, as in loop 2.

## Time estimate
- TEAR extraction on the L4 took a median 8 s per text in the 200-text run (te_tear_Lfull_s0: mean 8.0 s per text after the first 20 laptop texts). 50 texts: about 7 min per set, about 14 min for both. The 10-18 benchmark of about 100 s per text covers all steps (discovery, coherence, integration, TEAR*), which are not run here.
- Previews (surrogate on 50 texts, GPU): 1-2 min per set. Embedding check: cached (both sets are pool texts), under 1 min.
- Colab setup before this: about 5 min (20-30 min the first time on a new GPU type).
- Total about 20-25 min for both sets on a warm L4 session.
