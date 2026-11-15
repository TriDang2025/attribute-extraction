# FROZEN v4.5 (draft, Nov 15 2026)

All later work (loop 2, TEAR comparison, second dataset) uses exactly this. **Status: draft.** Step 4 waits for W1; the commit hash is filled in at the freeze commit.

- **Commit:** _pending_ (branch `wf-v4.5`, from `wf-v4.4` 5b59491)
- **Model:** `meta-llama/Llama-3.1-8B-Instruct`, revision `0e9e39f249a16976918f6564b8830bc894c89659`, bf16 (no quantization), vLLM 0.33.0, max_model_len 32768, gpu_memory_utilization 0.80, batch 64 (`config/wf_v41_models.json` setting `llama8b`).
- **Decoding:** temperature 0; guided JSON from each job's schema; if the guided answer does not parse, one unguided retry (`s1a/nov16_v41.VllmBackend`, logged by `s1a/log_v44.VllmBackend44`: guided raw text, finish reason, per-job seconds).

## Steps 1a-2 (cheap models, no LLM)
- Segmentation: Chroma chunks 5/25 + snap, merge cosine 0.40 (bge-m3) (`s1a/segment.py`, `scripts/plug_in.py` defaults).
- Spans: GLiNER medium v2.1, generic labels, once per turn, threshold 0.3 (`scripts/gliner_labels.py`).
- Clustering: wf_v2.2 variant `F_m2_t06_bk` = wf_v2.1 `E_AB_type` (stop list, code shapes, value-type split, t 0.4) + fold (clusters < 2 members into the nearest centroid if cos >= 0.6, booking check) (`s1a/fold.py`, `s1a/combos.py`).
- Export: `scripts/export_mentions.py --variant F_m2_t06_bk`, then `scripts/graph_run.py` stages.

## Step 3 (frozen as run in wf_v4.4 T4)
- Code `s1a/step3_v44.py` (on `step3_v43.py`, `split_v44.py`, `step3_post_v43.py`); config `config/wf_v44_step3.json`:

| setting | value |
|---|---|
| names schema | v1 (no regex `pattern`; `results/wf_v44/t1/choice.json`) |
| batch / orders | 5 clusters / 0, 1, 2 (vote) |
| similar_batches | on |
| rescue | on |
| merge | on, name cosine >= 0.75, max 20 pairs per entity and order |
| split pass | keyed (`split_v44`) |
| after A | reconcile, then v3.8 duplicate check |

## Step 4 (decided by W1)
- Code `s1a/step4_v44.py` (on `step4_v43.py`); config `config/wf_v44_step4.json`.
- If W1 passes: switches entity_hint on, **other_choice off**, key_candidates on, code_links on, vote on (3 seeds + vote).
- If W1 fails: v4.3 Step 4 (`s1a/step4_v43.py`, all v4.4 switches off).

| threshold | value |
|---|---|
| key_min_mentions | 5 |
| key_distinct_share | 0.9 |
| link_min_shared_values | 2 |
| link_overlap_share | 0.2 |
| vote_table_jaccard | 0.5 |

## Prompts and schemas (by file)
- Step 3: `s1a/step3_v43.py` (names prompt, car-rental examples `s1a/examples_v43.py`), `s1a/step3_v44.py` (`names_schema_v44` v1, rescue and merge yes/no), `s1a/split_v44.py` (keyed split), `s1a/step3_post_v43.py` (reconcile, duplicate check).
- Step 4: `s1a/step4_v43.py` (`INSTRUCTION_P2`, pass 1, pairs, keys), `s1a/step4_v44.py` (hint-mode pass 2, key choice, link pair schemas), `s1a/step4_sql.py` (SQL).
- Scorer: `s1a/step4_score.py` + `step4_v44.score_map_dir` (corrected mapping), GT `gt/schema_gt_v1.yaml`.
