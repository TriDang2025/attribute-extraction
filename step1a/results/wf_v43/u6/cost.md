# U6: cost, option B (wf_v4.2) vs v4.3, dev50 and dev50b

Option B Step 3 = `results/wf_v42/t1b_step3_keyed` (A calls only, 18 jobs); Step 4 = `results/wf_v42/t2c_step4_keyed_ext` (12 chains: input c1 and input a, 4 calls each where they got that far). v4.3 reads `results/wf_v43/u2` (Step 3), `u4` (Step 4) and `u0` (post-step calls, own row); "not run" = no response rows there yet. Calls = jobs + unguided retries (a retried row holds both calls' tokens).

| row | option B dev50 | option B dev50b | option B both | v4.3 dev50 | v4.3 dev50b | v4.3 both | note |
|---|---|---|---|---|---|---|---|
| Step 3 calls | 10 | 11 | 21 | not run | not run | not run | jobs + unguided retries |
| Step 3 of which unguided retries | 1 | 2 | 3 | not run | not run | not run |  |
| Step 3 tokens in | 101,787 | 101,299 | 203,086 | not run | not run | not run |  |
| Step 3 tokens out | 35,815 | 47,097 | 82,912 | not run | not run | not run |  |
| Step 3 GPU minutes | n/a (batches shared) | n/a (batches shared) | 2.5 | not run | not run | not run | both sets together |
| Step 4 calls | 26 | 24 | 50 | not run | not run | not run | jobs + unguided retries |
| Step 4 of which unguided retries | 2 | 3 | 5 | not run | not run | not run |  |
| Step 4 tokens in | 183,577 | 154,311 | 337,888 | not run | not run | not run |  |
| Step 4 tokens out | 42,609 | 35,839 | 78,448 | not run | not run | not run |  |
| Step 4 GPU minutes | n/a (batches shared) | n/a (batches shared) | 4.6 | not run | not run | not run | both sets together |
| Post-step (U0) calls | not run | not run | not run | 10 | 11 | 21 | jobs + unguided retries |
| Post-step (U0) of which unguided retries | not run | not run | not run | 1 | 2 | 3 |  |
| Post-step (U0) tokens in | not run | not run | not run | 101,787 | 101,299 | 203,086 |  |
| Post-step (U0) tokens out | not run | not run | not run | 35,815 | 47,097 | 82,912 |  |
| Post-step (U0) GPU minutes | not run | not run | not run | n/a (batches shared) | n/a (batches shared) | 2.5 | both sets together |
| GPU minutes total (model time, batches counted once) | n/a (batches shared) | n/a (batches shared) | 7.1 | n/a (batches shared) | n/a (batches shared) | 2.5 | both sets together; from batch_seconds |
| Model loading time | n/a | n/a | not logged | n/a | n/a | not logged | minutes, from run_info.json |
| LLM tokens (in + out) | 363,788 | 338,546 | 702,334 | 137,602 | 148,396 | 285,998 | Steps 3 + 4 (+ post-step) |
| Corpus tokens | 14,915 | 13,140 | 28,055 | 14,915 | 13,140 | 28,055 | dialogue turns, Llama-3.1 tokenizer where marked tok, else est. (4 chars/token): dev50 tok, dev50b tok |
| LLM tokens / corpus tokens (in + out) | 24.4 | 25.8 | 25.0 | 9.2 | 11.3 | 10.2 |  |
| Output tokens / corpus tokens | 5.3 | 6.3 | 5.8 | 2.4 | 3.6 | 3.0 |  |


First option B Step 4 run (`t2b_step4_keyed`, 4.3 not capped): 43 calls, 275,243 tokens in, 70,967 out, 3.9 GPU minutes.


Caveats: GPU time of a batch is shared by both sets, so it is given for both sets together; the seconds of an unguided retry are lost when the first (guided) row is kept, so GPU minutes can be slightly low. Model loading time is not logged in any committed run file (run_info.json holds job counts only; the notebooks print no timing).
