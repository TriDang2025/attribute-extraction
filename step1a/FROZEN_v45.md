# FROZEN v4.5 (Nov 15-16 2026)

All later work (loop 2, TEAR comparison, second dataset) uses exactly this. One command runs it on any corpus:
`s1a/pipeline_v45.run_pipeline(corpus.jsonl, out, set_name, backend, bge_m3 encoder, encoder(), step4_config("v43"))` (`scripts/run_pipeline.py`).

- **Code commit:** `858f0e77` (branch `wf-v4.5`, from `wf-v4.4` 5b59491). Later commits on the branch add results and report scripts only.
- **Model:** `meta-llama/Llama-3.1-8B-Instruct`, revision `0e9e39f249a16976918f6564b8830bc894c89659`, bf16 (no quantization), vLLM 0.33.0, max_model_len 32768, gpu_memory_utilization 0.80, batch 64 (`config/wf_v41_models.json` setting `llama8b`). Prompts over 30,000 tokens are refused by the backend.
- **Decoding:** temperature 0; guided JSON from each job's schema; if the guided answer does not parse, one unguided retry (`s1a/nov16_v41.VllmBackend`, logged by `s1a/log_v44.VllmBackend44`).

## Steps 1a-2 (cheap models, no LLM; `s1a/corpus_v45.py`)
- Input: JSONL `{"id", "text"}`, text = `User:` / `System:` lines. No gold of any kind.
- Segments: Chroma chunks 5/25 (bge-m3), snapped to turns, adjacent pieces merged at cosine >= 0.40 with the entity-keyword check (`plug_in.DEFAULT_SEG = "5/25,0.40,on,on"`).
- Spans: GLiNER medium v2.1, generic labels, once per turn, spans kept at score >= 0.5 (`export_mentions.span_inputs`).
- Entities: k-means on segment vectors, k = 5, seed 42 (`mentions._spans`); **all 5 go to Step 3**, each named by the most frequent `segment.ENTITY_WORDS` keyword in its segments (`corpus_v45.entity_names`), a repeated name gets `_2`.
- Clusters: variant `F_m2_t06_bk` (wf_v2.1 `E_AB_type`: stop list, code shapes, value-type split, t 0.4; plus fold of clusters < 2 members into the nearest centroid at cos >= 0.6, booking check).

## Step 3 (frozen as run in wf_v4.4 T4)
- Code `s1a/step3_v44.py` (on `step3_v43.py`, `split_v44.py`, `step3_post_v43.py`); config `config/wf_v44_step3.json`; A and split prompts built per corpus with the frozen builders (`pilot_build_v37.a_prompts`, `pilot_input.render_split`, k 16, min_share 0).

| setting | value |
|---|---|
| names schema | v1 (no regex `pattern`; `results/wf_v44/t1/choice.json`) |
| batch / orders | 5 clusters / 0, 1, 2 (vote) |
| similar_batches | on |
| rescue | on |
| merge | on, name cosine >= 0.75, max 20 pairs per entity and order |
| split pass | keyed (`split_v44`) |
| after A | reconcile (2 orders), then v3.8 duplicate check |

## Step 4: v4.3 (W1, Nov 15)
- W1 (`results/wf_v45/w1/freeze.md`): v4.4 with "other" off passed 1 of 3 checks (GT placed a_llama44 0.573 >= 0.536; table F1 c1 0.652 < 0.753; table F1 a_llama44 0.658 < 0.672), so **v4.3 Step 4 is frozen**.
- Run as `s1a/step4_v44.py` with **all five switches off** (`pipeline_v45.STEP4["v43"]`) = the v4.3 jobs, prompts and answer formats (`s1a/step4_v43.py`): 2-pass grouping, yes/no pair links, keys per table; 3 seeds, no vote; the command's schema is the first finished seed.
- Output limits (`step4_v43.MAX_TOKENS`): p1 300, p2 1500, pair 100, key 400. **Known limit (W4):** pass 2 lists every column, so it fails from about 300 dialogues (n300 2/3 chains, n500 0/3, n1000 prompt over 30K).

## Prompts and schemas (by file)
- Step 3: `s1a/step3_v43.py` (names prompt, car-rental examples `s1a/examples_v43.py`), `s1a/step3_v44.py` (`names_schema_v44` v1, rescue and merge yes/no), `s1a/split_v44.py` (keyed split), `s1a/step3_post_v43.py` (reconcile, duplicate check).
- Step 4: `s1a/step4_v43.py` (`INSTRUCTION_P2`, pass 1, pairs, keys), `s1a/step4_sql.py` (SQL).
- Scorer: `s1a/step4_score.py` + `step4_v44.score_map_dir` (corrected mapping), GT `gt/schema_gt_v1.yaml`.
