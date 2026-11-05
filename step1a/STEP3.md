# Step 3, frozen (wf_v3.9, 2026-11-05)

Frozen on diary 3 Nov, task 10, whatever the task 9 result. Any later change needs a new version and a written reason.

- Code: branch `wf-v3.9`, commit `9168d0f`.
- Rules: scoring rules v1.3 (`RULES_V1_3.md`, on top of v1.2 and v1.1).
- Input: Step 1a v2.2 clusters (`results/graph_v22_<set>/spans`).
- Output: `handover/` (format in `handover/HANDOVER_FORMAT.md`).

## Steps, in order
1. **A prompt.** One call per entity: `pilot_input.INSTRUCTION_V2` with `render_v2` and `schema_v2`. It names the attributes and assigns the clusters; there is no `attribute_cue` label.
2. **3-order vote.** A runs in cluster orders s0, s1 and s2, and `pilot_combine.vote` combines them into "A s012".
3. **Split pass.** For clusters A marks as holding two roles: `pilot_input.INSTRUCTION_SPLIT` / `schema_split`, then `pilot_verify.split_parts`.
4. **Reconcile** (v3.9 task 4).
   - One call per split part, with the part and its 5 nearest other columns of the same entity (bge-m3 centroid), in 2 shuffled orders (seeds 0 and 1).
   - A part joins a column only when both orders pick the same column. `batch_v38.check_joins` blocks role-pair joins.
   - Code: `s1a/batch_v39.py` (`apply_reconcile`, `assemble_columns`).
5. **Duplicate check** (v3.9 task 5).
   - The v3.8 duplicate check runs on the columns of each reconcile order.
   - A join is kept only when both orders unite exactly the same A s012 groups. The role-pair block applies.
6. **Checker, as a flag only.** Each column gets the v3.8 evidence card (example check and neighbour check) and a verdict (rule v0). No column is removed by a verdict.

**Not in Step 3:**
- Split back (task 7): fails the decision line on one set in each version.
- A-cue (task 8): dev50 marks right stay at 10 while marks rise from 12 to 15.
- J (Step 1a v2.3) stays a Step 1a option only (task 3).

## Settings
- **Model:** Qwen2.5-32B-Instruct-AWQ (vLLM), temperature 0, guided JSON.
- **max_tokens:**
  - A: 12,000
  - split pass: 3,000
  - reconcile: 256
  - duplicate check: 1,024
  - evidence: 512
- **Embeddings:** bge-m3 vectors (`spans/vectors.npz`, gitignored).
- **Thresholds:**
  - Recall guard per entity: dev50 8/12/11, dev50b 8/10/11.
  - Verdict v0: noise if support < 0.4; too general if neighbour fit > 0.5; real if support ≥ 0.7 and neighbour fit ≤ 0.3.
- **Notebooks and contracts:** `colab/S1A_llm_v38_colab.ipynb` (evidence) and `colab/S1A_llm_v39_colab.ipynb` (reconcile, duplicate check); `WF_V38_BATCH.md`, `WF_V39_BATCH.md`.
- **Scoring:** `scripts/final_v39.py` writes `results/loop1_v39/final/` and `handover/`.

## Result (L2, rules v1.3)

| set | found | columns (per found) | review edits | recall guard | role-pure | noise marks right |
|---|---|---|---|---|---|---|
| dev50 | 31/40 | 55 (1.516) | 24 (A s012: 34) | pass | 2/10 | 10/12 |
| dev50b | 29/41 | 47 (1.345) | 16 (A s012: 23) | pass | 3/7 | 8/11 |

## Known limits (exit-bar points that fail, and other weak spots)
- **(c) columns per found ≤ 1.2:** fails on both sets (dev50 1.516, dev50b 1.345).
- **(d) noise:** fails on dev50b. 5/9 noise caught (bar 9/13) and marks right 0.333 (bar 0.70), under the v1.1/v1.2 marks used by every exit bar. Under v1.3 the marks are 8/11.
- **(b) order range:** n/a for the vote. Across the raw orders the range is 1 on dev50 (pass) and 5 on dev50b (fail).
- **(e) right names:** passes, but as a lower bound only (dev50 27 vs 26, dev50b 31 vs 27). Renamed columns have no rating.
- **(a) found:** passes (dev50 27/29, dev50b 27/30). The ceiling is still Step 1a: 29/40 and 30/41 are recoverable.
- **Wrong reconcile joins:** about a third of the joins both orders agree on are wrong (dev50 4/16, dev50b 2/7). Review edits do not count them.
- **Wrong merges inside A's answer** are not fixed (8 on dev50, 6 on dev50b before reconcile).
- **Role-pure is low:** big train columns mix leave at / arrive by and departure / destination.
- **Verdict v0 is unreliable:** for example, the real train "arrival location" column gets noise (support 1/10). This is why the checker is a flag only.
