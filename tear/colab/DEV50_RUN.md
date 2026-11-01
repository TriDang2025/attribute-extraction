# TEAR on dev50 (wf_v3.6, T40)

Goal: TEAR (`te_tear_Lfull`, seed 0, full 35-attribute schema) on the 50 Step-1a dev dialogues (first 50 ids of TEAR's pool), so its columns can be scored against the same GT as the Step-1a variants (`step1a/scripts/score_tear_v36.py`). Do not run RAG or the other levels.

## Demonstrations and leakage
- TEAR picks `shots` (8 for Conversation) demonstrations per text from the labeled pool `data/conversation/pool.jsonl` (300 texts, train + val), ranked by header preview, value preview and SFR embedding cosine (`tear_reproduction/retrieval.py`, `pipeline.extract`).
- The dev50 ids are the first 50 pool ids, so in the normal run a dev50 text would retrieve itself (cosine 1.0) with its gold table. Dataset `conversation_dev50` (`eval/reproduce.py`, `HELD_OUT`) removes the 50 ids from the pool (250 left) and reads its texts from `data/conversation_dev50.jsonl`. Nothing else changes (`conversation` is untouched).
- Not removed: the BART surrogate (`surrogate_conversation_cont2`) was trained on the pool, so on dev50 its previews saw these dialogues in training and are better than on unseen texts. Retraining without the 50 ids is not done here. Report TEAR on dev50 with this caveat.

## Steps
1. Laptop, once (needs `hf auth login`; check with `hf auth whoami`): upload the input.
   `hf upload database-lab/attribute-extraction-data tear/data/conversation_dev50.jsonl tear/conversation_dev50.jsonl --repo-type dataset`
   (rebuild with `python -I data_build/dev50.py` from `tear/`; 50 rows, checked against `pool.jsonl`.)
2. Colab, L4: notebook `colab/TEAR_colab.ipynb`, cells 1-3 (logins, setup, servers; `pull-data` fetches the new file).
3. In cell 4, replace the run command with:
   `TEAR_DEV50=1 bash colab/run.sh 50 0`
   `run.sh` claims `results/RUN_OWNER`, starts `tools/run_all.py`, and pushes results every 30 min. With `TEAR_DEV50=1` run_all does only: embedding cache check, previews for the 50 texts (`data/conversation/previews_dev50.jsonl`), then `te --dataset conversation_dev50 --methods tear --seeds 0 --level full --n 50`.
4. Output: `tear/results/conversation_dev50/te_tear_Lfull_s0.jsonl` (50 rows: id, table, preview, demonstration_indices, schema, seconds, calls). Progress: `bash colab/status.sh`; end marker `RUN_ALL_DONE` in `results/run_all.log`. Rerun the same command after a disconnect: done texts are skipped.
5. Laptop: `git pull`, then `python scripts/score_tear_v36.py --tear ../tear/results/conversation_dev50/te_tear_Lfull_s0.jsonl` from `step1a/`.

## Time estimate
- TEAR extraction on the L4 took a median 8 s per text in the 200-text run (te_tear_Lfull_s0: mean 8.0 s per text after the first 20 laptop texts). 50 texts: about 7 min. The 10-18 benchmark of about 100 s per text covers all steps (discovery, coherence, integration, TEAR*), which are not run here.
- Previews (surrogate on 50 texts, GPU): 1-2 min. Embedding check: cached, under 1 min.
- Colab setup before this: about 5 min (20-30 min the first time on a new GPU type).
- Total about 15 min on a warm L4 session.
