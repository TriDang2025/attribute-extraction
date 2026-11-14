# T9 prep: quick cost check (not run)

**Status: not done.** Step 1a + 2 can run on a sample now; Step 3 and Step 4 cannot (see Missing). Sizes 50, 300 (ratio 6x), seed 0, source `tear/data/conversation/pool.jsonl` (300 training dialogues; 500 does not exist there, test.jsonl is not used). Samples: `sample_<n>.json` (the 50 are the first 50 of the 300).

## Corpus and TEAR (estimated, TEAR is not run)

| dialogues | corpus tokens | TEAR calls | TEAR tokens in | TEAR tokens out | extraction / discovery tokens in | definitions + judgements calls |
|---|---|---|---|---|---|---|
| 50 | 12,579 (tok) | 109 | 385,726 | 9,417 | 187,344 / 193,768 | 6 |
| 300 | 82,164 (tok) | 654 | 2,345,826 | 56,500 | 1,138,591 / 1,179,549 | 34 |
| ratio 300/50 | 6.53 | 5.99 | 6.08 | 6.00 | | |

How TEAR is estimated: per text, 1 extraction call + 1 discovery call (1.01 / 1.05 attempts per call, measured on 200 texts), each prompt built with TEAR's own builders (`tear_reproduction.prompts`) with 8 stand-in demonstrations (random pool dialogues instead of the retrieved ones) and the gold table as the hints / known table; output tokens = the measured mean (98 extraction, 82 discovery). Corpus-level calls: 0.075 definition + 0.040 judge calls per text (measured L1 run), scaled linearly (upper bound; 40 / 2 output tokens assumed). So TEAR is linear in the dialogues by construction (ratio = size ratio).

## Our pipeline: what runs now and what is missing

- **Runs now (current code, no GPU needed):** Step 1a + Step 2 = `scripts/export_mentions.py --variant F_m2_t06_bk` (GLiNER generic spans, 5/25 snapped segments, v2.2 clustering) through `python scripts/t9_cost_v44.py step1a`, which swaps `split.dialogues` for the seeded sample. Gives mentions, clusters, vectors (`<out>/spans/`).
- **Missing for the LLM part (not written, would be new code, not a small change):**
  1. Entities: `run_data_v37.entity_ids` finds exactly three entities (train / hotel / restaurant) through the gold `entity_gold` labels; 300 dialogues also hold attraction, taxi, hospital, police. Step 3 would need to iterate over all Step 1a entities without GT.
  2. Step 3 prompts: `step3_v43.build` cuts the frozen A prompts of `results/wf_v42/t1b_step3_keyed` (made by `pilot_build_v37.py` for the two dev sets); a new run needs that builder (render_v2) on the new `spans/` folder.
  3. Scoring-side inputs the builders read: `spans/labels.csv` (graph_run label stage) and `docs.jsonl`; the Step 4 inputs (`step4_inputs`, `inputs_v4.py`) read `results/wf_v4/inputs/<set>` of dev50 / dev50b only.
  4. Counting: `count` reads `log_v44.call_rows` of the Step 3 / Step 4 run folders, `spans/clusters.csv` and the final columns file; ready.
- Data: `get_conversation_data.py` must have been run (`chunking/data/conversation_ids.txt`, `MULTIWOZ2.4.zip`; gitignored, absent in a fresh worktree).

## Commands (Step 1a + 2 only)

```
python scripts/get_conversation_data.py            # once: gitignored data (conversation_ids.txt, MULTIWOZ2.4.zip)
python scripts/t9_cost_v44.py step1a --n 50 --seed 0 --out results/wf_v44/t9/graph_n50
python scripts/t9_cost_v44.py step1a --n 300 --seed 0 --out results/wf_v44/t9/graph_n300
```

Then, once Steps 3 / 4 are wired: `python scripts/t9_cost_v44.py count --n <n> --run results/wf_v44/t9/graph_n<n> --llm-dirs <step3 folder> <step4 folder> --columns <final columns json>` for each size, and compare the two with the `growth` ratios.

## Time estimate (minutes, assumptions)

| part | 50 dialogues | 300 dialogues |
|---|---|---|
| Step 1a + 2 (CPU, Colab) | 2.0-25.0 | 12.0-150.0 |
| Step 3 + 4 calls (GPU) | 1.5-2.5 | 9.0-15.0 |
| model loading (GPU, once) | 2-5 | 2-5 |
| **total** | **6-32** | **23-170** |

Assumptions: Step 1a + 2 2-25 min per 50 dialogues (low = the 117 s `export_mentions` run on dev50 with the GLiNER cache seeded; high = the 25 min of `entity_seg.py` on a laptop CPU, AGENTS.md); GPU calls 1.5-2.5 min per 50 (v4.3: 3.2 + 1.2 = 4.4 min job seconds for 100 dialogues, a lower bound for the names stage, one order instead of three; scaled linearly, so an upper bound when clusters saturate); model loading 2-5 min is a guess (not logged in v4.3; v4.4 writes `results/wf_v44/model_load.json`). Not including the missing wiring. Measure the 50 first and multiply by 6.
