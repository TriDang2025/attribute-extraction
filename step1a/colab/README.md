# Loop-1 LLM run on Colab (Qwen2.5-32B-Instruct-AWQ + vLLM)
Spec: `../LOOP1_CONTRACT.md` ("LLM run"). Code: `../s1a/llm_cache.py`. Branch: `wf-v3` of `TriDang2025/attribute-extraction`.

Setup is the same as `chunking/colab/README.md`: Colab Secrets `HF_TOKEN` and `GH_TOKEN` (notebook access on). Never put a token in a notebook cell.

Before: prompts `step1a/results/loop1_check/pilot_train/prompts/{full,nocontext,nohints}.txt` must be committed on `wf-v3`.

1. **YOU:** open `step1a/colab/S1A_llm_colab.ipynb` from GitHub (branch wf-v3). Runtime = GPU with 24 GB or more (L4 or A100); the 32B AWQ model needs about 20 GB, a T4 only fits the 14B fallback (variable `MODEL` in cell 4).
2. **YOU:** set your git name and email in cell 1; run the cells in order. About 20-40 min (estimate, not measured).
3. The notebook stops if any prompt is over 30,000 tokens. T4 (no data) runs first, then full/r1, full/r2, nocontext/r1, nohints/r1. Reruns reuse the cache in the `.jsonl` files.
4. `colab/sync.sh push-results` pushes `contamination_raw.jsonl` and `pilot_train/responses_<variant>_<run_tag>.jsonl`. Then `git pull` locally.
