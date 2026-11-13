# U6: cost, option B (wf_v4.2) vs v4.3, dev50 and dev50b

Option B Step 3 = `results/wf_v42/t1b_step3_keyed` (A calls only, 18 jobs); Step 4 = `results/wf_v42/t2c_step4_keyed_ext` (12 chains: input c1 and input a, 4 calls each where they got that far). v4.3 reads `results/wf_v43/u2` (Step 3), `u4` (Step 4) and `u0` (post-step calls, own row); "not run" = no response rows there yet. Calls = jobs + unguided retries (a retried row holds both calls' tokens).

| row | option B dev50 | option B dev50b | option B both | v4.3 dev50 | v4.3 dev50b | v4.3 both | note |
|---|---|---|---|---|---|---|---|
| Step 3 calls | 10 | 11 | 21 | 321 | 301 | 622 | jobs + unguided retries |
| Step 3 of which unguided retries | 1 | 2 | 3 | 98 | 84 | 182 |  |
| Step 3 tokens in | 101,787 | 101,299 | 203,086 | 400,592 | 355,349 | 755,941 |  |
| Step 3 tokens out | 35,815 | 47,097 | 82,912 | 23,972 | 28,058 | 52,030 |  |
| Step 3 GPU minutes | n/a (batches shared) | n/a (batches shared) | 2.5 | n/a (batches shared) | n/a (batches shared) | 1.7 | both sets together |
| Step 4 calls | 26 | 24 | 50 | 185 | 77 | 262 | jobs + unguided retries |
| Step 4 of which unguided retries | 2 | 3 | 5 | 0 | 0 | 0 |  |
| Step 4 tokens in | 183,577 | 154,311 | 337,888 | 346,559 | 270,270 | 616,829 |  |
| Step 4 tokens out | 42,609 | 35,839 | 78,448 | 6,237 | 5,009 | 11,246 |  |
| Step 4 GPU minutes | n/a (batches shared) | n/a (batches shared) | 4.6 | n/a (batches shared) | n/a (batches shared) | 1.2 | both sets together |
| Post-step (U0) calls | not run | not run | not run | 208 | 180 | 388 | jobs + unguided retries |
| Post-step (U0) of which unguided retries | not run | not run | not run | 24 | 22 | 46 |  |
| Post-step (U0) tokens in | not run | not run | not run | 236,882 | 215,370 | 452,252 |  |
| Post-step (U0) tokens out | not run | not run | not run | 57,661 | 69,785 | 127,446 |  |
| Post-step (U0) GPU minutes | not run | not run | not run | n/a (batches shared) | n/a (batches shared) | 4.2 | both sets together |
| GPU minutes total (model time, batches counted once) | n/a (batches shared) | n/a (batches shared) | 7.1 | n/a (batches shared) | n/a (batches shared) | 7.2 | both sets together; from batch_seconds |
| Model loading time | n/a | n/a | not logged | n/a | n/a | not logged | minutes, from run_info.json |
| LLM tokens (in + out) | 363,788 | 338,546 | 702,334 | 1,071,903 | 943,841 | 2,015,744 | Steps 3 + 4 (+ post-step) |
| Corpus tokens | 14,915 | 13,140 | 28,055 | 14,915 | 13,140 | 28,055 | dialogue turns, Llama-3.1 tokenizer where marked tok, else est. (4 chars/token): dev50 tok, dev50b tok |
| LLM tokens / corpus tokens (in + out) | 24.4 | 25.8 | 25.0 | 71.9 | 71.8 | 71.8 |  |
| Output tokens / corpus tokens | 5.3 | 6.3 | 5.8 | 5.9 | 7.8 | 6.8 |  |


First option B Step 4 run (`t2b_step4_keyed`, 4.3 not capped): 43 calls, 275,243 tokens in, 70,967 out, 3.9 GPU minutes.


Caveats: GPU time of a batch is shared by both sets, so it is given for both sets together; the seconds of an unguided retry are lost when the first (guided) row is kept, so GPU minutes can be slightly low. Model loading time is not logged in any committed run file (run_info.json holds job counts only; the notebooks print no timing).
