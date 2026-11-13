# Retry rule check: "retry once unguided, keep the better answer"

Rule in code (the Llama / Nov 16 backend): a guided answer with parse errors is rerun once unguided, alone; the answer with fewer errors is
kept (the first one on a tie) and the row is marked `retried`, with both calls' tokens summed (`s1a/nov16_v41.py` lines 258-264, class
`VllmBackend.run`). Checked: the notebook helper each old Qwen-32B run used, and the cached rows (`responses/*.jsonl`, field `retried`; counts
by script over `results/<run>/**/responses`). Rows with parse errors that were guided = "should have been retried".

| run family | notebook that ran it | same rule? | evidence |
|---|---|---|---|
| Step 3 v3.9 `results/loop1_v39` | `colab/S1A_llm_v39_colab.ipynb` | yes | line 220 `if row["errors"] and guided:  # retry once unguided, alone; keep the better one, count both calls' tokens`, line 225 `retried=True`; 188 rows, 3 `retried`; 2 guided rows with errors, both retried |
| Step 3 v3.7 `results/loop1_v37` | `colab/S1A_llm_v37_colab.ipynb` | yes | lines 219 / 224, same code; 124 rows, 7 `retried`; 4 guided rows with errors, all 4 retried (the 3 other `retried` rows are retries whose unguided answer was the better one and was kept: `guided` False, no errors left) |
| Step 3 v3.6 `results/loop1_v36` | `colab/S1A_llm_v36_colab.ipynb` | yes | lines 221 / 226, same code; 46 rows, 7 `retried`; 4 guided rows with errors, all 4 retried; 3 more `retried` rows kept the unguided answer (`guided` False, no errors) |
| Step 3 v3.1 `results/loop1_v31` | `colab/S1A_llm_v31_colab.ipynb` | **no** | cell 6 only falls back to unguided when guided decoding itself raises (`generate`, docstring "If guided decoding raises for this schema, retry once without guidance", line 155 prints it); no error-triggered retry, no `retried` field, no token fields; 44 rows, 0 `retried`; 1 guided row with 6 parse errors (`restaurant_v2_r2`) was kept as is |
| Step 4 v0 `results/wf_v4` | `colab/S1A_llm_v4_colab.ipynb` | yes in code, never triggered | lines 212 / 217, same code; 106 rows, 0 `retried`, 0 rows with parse errors, so the rule had nothing to retry |
| Step 4 v4.1 `results/wf_v41` | Nov 16 notebook `colab/S1A_nov16_v41_colab.ipynb` (uses `nov16_v41.VllmBackend`, rule at `nov16_v41.py` 258-264) | yes in code; no Qwen call made by it yet | the 106 Qwen rows in `results/wf_v41` are the v0 base copy (`copy_v4_base`, identical to `wf_v4`), 0 errors, 0 `retried`; 43 rows are Gemini web-app answers by hand (no backend); the Nov 16 Qwen run is not in the repo |

Also (not asked): the v3.5 and v3.8 notebooks have the same rule (lines 214 and 219 of `S1A_llm_v35_colab.ipynb`; 219 and 224 of
`S1A_llm_v38_colab.ipynb`); `llm_cache.py` has no retry logic of its own (it only stores rows: `retried` is written by the notebook helper).

Answer: yes for Step 3 v3.9, v3.7, v3.6 and for Step 4 v0 / v4.1 (same rule, one unguided retry, better answer kept, both calls' tokens
counted); no for Step 3 v3.1 (only the guided-decoding-error fallback). In the Qwen Step 4 runs the rule never fired because no answer had
parse errors, so Qwen and Llama differ in how often it fired (Llama: 3 of 21 Step 3 calls and 5 of 50 Step 4 calls in option B), not in the rule.
