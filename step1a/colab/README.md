# Loop-1 LLM run on Colab (Qwen2.5-32B-Instruct-AWQ + vLLM)
Spec: `../LOOP1_CONTRACT.md` ("LLM run"). Code: `../s1a/llm_cache.py`. Branch: `wf-v3` of `TriDang2025/attribute-extraction`.

Setup is the same as `chunking/colab/README.md`: Colab Secrets `HF_TOKEN` and `GH_TOKEN` (notebook access on). Never put a token in a notebook cell.

Before: prompts `step1a/results/loop1_check/pilot_train/prompts/{full,nocontext,nohints}.txt` must be committed on `wf-v3`.

1. **YOU:** open `step1a/colab/S1A_llm_colab.ipynb` from GitHub (branch wf-v3). Runtime = GPU with 24 GB or more (L4 or A100); the 32B AWQ model needs about 20 GB, a T4 only fits the 14B fallback (variable `MODEL` in cell 4).
2. **YOU:** set your git name and email in cell 1; run the cells in order. About 20-40 min (estimate, not measured).
3. The notebook stops if any prompt is over 30,000 tokens. T4 (no data) runs first, then full/r1, full/r2, nocontext/r1, nohints/r1. Reruns reuse the cache in the `.jsonl` files.
4. `colab/sync.sh push-results` pushes `contamination_raw.jsonl` and `pilot_train/responses_<variant>_<run_tag>.jsonl`. Then `git pull` locally.

## wf_v3.1 pilot (3 entities, prompt v2, split pass)
Notebook `S1A_llm_v31_colab.ipynb`, branch `wf-v3.1`, jobs from `results/loop1_v31/manifest.json` (contract `../PILOT_V31_CONTRACT.md`). Prompts and schemas must be committed on `wf-v3.1` first.
1. **YOU:** Runtime = **A100 (80 GB)**; the 32B AWQ model does not fit an L4 with a 21K-token prompt (cell 3 asserts >= 40 GB).
2. **YOU:** Colab Secrets `HF_TOKEN` and `GH_TOKEN` (notebook access on); set git name/email in cell 1.
3. Run cell 1, then cell 2 (`pip install vllm`; resolver warnings are harmless). Then **Runtime > Restart session**, rerun cell 1, skip cell 2.
4. Cells 3-7: GPU check, load model (cell 4 resolves the model revision sha and records it with the vLLM version), token counts (stop if any prompt > 30000), run entity jobs then split jobs with guided JSON per job schema (unguided retry marked `guided: false`). Responses go to `results/loop1_v31/responses/<job>.jsonl`; reruns reuse the cache.
5. Cell 8: `bash colab/sync.sh push-results` pushes `loop1_check` and `loop1_v31/responses`. Then `git pull` locally.

## wf_v3.3 pilot (carry-over rounds)
Notebook `S1A_llm_v33_colab.ipynb`, branch `wf-v3.3`, jobs from `results/loop1_v33/manifest.json` (contract `../PILOT_V33_CONTRACT.md`); same setup as v3.1; round 0 runs first, then rounds 1 and 2 after `pilot_combine.fill_carry`; push with `bash colab/sync.sh push-results "v3.3 pilot responses" loop1_v33`.
