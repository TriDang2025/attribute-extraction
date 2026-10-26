# Step 1a Residual Mining on Conversation
Tests Step 1a of the schema-expansion pipeline (OneDrive `TEAR/source_paper/pipeline.pdf`): cluster units of the Conversation dialogues and score them against TEAR's gold attributes. Reuses `../chunking/` (data, bge-m3 encoder, Chroma chunks from `chunking/results/S_n50`) and `../hdbscan/` (UMAP, HDBSCAN, metrics) by import; gold tables from `../tear/data/conversation/`.

## Setup and commands
venv `C:\Users\nguye\venvs\chunking`; `python -m pytest -q tests` (79 tests), then the scripts below. spaCy venv: `C:\Users\nguye\venvs\spacy`.
Timings on the laptop CPU for n50:
- `run.py`: about 7 min
- `rescore.py`: 2 min
- `step2.py`: 5 min
- `spans_compare.py`: 2 min
- `plug_in.py`: 5–8 min
- segmentation grid: 41 min

## Layout
- `s1a/units.py`: units: Chroma chunks, oracle segments (gold domain runs), gold values located in the text (3 variants: value, ±10-word window, whole turn).
- `s1a/cluster.py`: HDBSCAN / agglomerative / k-means grid on raw bge-m3 and UMAP-5D.
- `scripts/run.py --limit 50`: main grid.
- `scripts/relabel.py --limit 50`: scores value clusters vs attribute / entity / slot, plus the two-stage test.
- `s1a/segment.py`, `s1a/spans.py`, `scripts/entity_seg.py --limit 50`: entity segmentation (Chroma + bge-m3 at smaller sizes, merge if cosine >= tau and no new entity keyword) and GLiNER generic-label spans, in the two-stage test. GLiNER medium v2.1 in `CHK_MODELS/gliner_medium-v2.1` (its config points to the local `deberta-v3-base`).
  - Flags: `--sizes`, `--taus`, `--snap`, `--keywords`, `--out`, `--chunk-cache`.
  - With no flags it reproduces the original grid exactly.
- `s1a/split.py`: dev = ids[:300] (TEAR pool), test = ids[300:]; `--split dev|test` on the scripts. The n50 runs use dev 0–49.
- `s1a/gold.py`, `s1a/metrics.py`: v2 protocol.
  - Units: every verbatim mention; yes/no and unfound values are non-verbatim.
  - Classes: name and confirmed name merged (33 classes); lenient multi-label B-cubed.
  - `match_all`: a span takes every label at its position.
  - `span_recall`: mention, value and tight recall.
  - Report block: visible/hidden for TEAR levels 1–3, plus bootstrap CI.
  - `scripts/rescore.py`: old vs new protocol.
- `s1a/step2.py`, `scripts/step2.py`: Step 2 with gold entities (normalize, masked context with target mark, type partition, cannot-link constrained agglomerative, ceilings).
  - Adopted setting: `results/v2_n50/chosen_step2_joint.json` (α 0.5, average, t 0.45, type partition, cannot-link).
  - `merge_split_clusters` (C6) was rejected; it stays only as a reported ladder row.
- `scripts/plug_in.py`: Step 2 on predicted entities, original vs chosen stage 2. Defaults (v3): segments 5/25 snap + merge 0.40; spans from the per-turn GLiNER cache; `--step2` (spans) joint, `--step2-gold` window.
  - Best per input (v3): spans → original stage 2 (raw strings, t 0.4); gold mentions → window Step 2.
- `scripts/gliner_labels.py`: GLiNER once per turn without the speaker prefix (`spans.turn_windows`), label sets generic / hand / gold -> `results/v3_n50/gliner_labels/gliner_turn_<set>.jsonl` (threshold 0.3 stored).
- `scripts/step2_window.py`: window Step 2 grid on gold entities -> `results/v3_n50/chosen_step2_window.json`.
- `s1a/spacy_spans.py`, `scripts/spacy_extract.py`, `scripts/spans_compare.py`: GLiNER vs spaCy comparison. spaCy as main extractor was not adopted.
- `data/cache/` (not in git): bge-m3 cache, seeded from the chunking cache.
- Graph tasks 0–9 (pipeline v2 Step 1a without LLM; contract in `GRAPH_CONTRACT.md`):
  - `s1a/mentions.py` (T0 export)
  - `s1a/coverage.py` (T1)
  - `s1a/graph.py` (T2)
  - `s1a/signals.py`, `s1a/stability.py` (T3)
  - `s1a/labels.py` (T4)
  - `s1a/node_filter.py` (T5–T6)
  - `s1a/draft_schema.py`, `s1a/schema_eval.py` (T7–T8)
  - Run: `scripts/export_mentions.py --split dev|test --out results/graph_<split>50`, then `scripts/graph_run.py --run ... --stage coverage|graph|stability|signals|labels|select|schema` (`--chosen <dev chosen.json>` on test). `scripts/label_sheet.py --merge` folds filled label sheets in.
  - Spans use the original Step 2 (raw strings, t 0.4); gold values use the window Step 2.
- wf_v2.1 spans Step 3 variants:
  - `s1a/variants.py` (Variant = span filter + `cluster_fn`, hooked in through `mentions.Inputs.cluster_fn`)
  - `span_filter.py` (A), `shapes.py` (B), `cue.py` (C), `spans_step2.py` (D), `combos.py` (E)
  - Score: `scripts/v21_run.py --part A..E [--split test]` -> `results/v21_<part>[_test]/scores.{csv,md}`
  - Adopted: `E_AB_type` (stop list + code shapes + value-type split, t 0.4). Export with `export_mentions.py --variant E_AB_type --from-run results/graph_<split>50` -> `results/graph_v21_<split>50/`
- wf_v2.2 spans Step 3 variants (on top of wf_v2.1 via `combos.V21`, `V21_FILTER`, `V21_TEXT`):
  - `fold.py` (F), `staged.py` (G), `roleword.py` (H), `multiview.py` (I), `combos22.py` (J)
  - Score: `scripts/v21_run.py --part F..J [--split test]` -> `results/v22_<part>[_test]/`. Adds a one-to-one F1 (Hungarian matching of clusters to classes).
  - Adopted: `fold.CONFIGS["F_m2_t06_bk"]` (fold clusters < 2 members into the nearest kept centroid if cos ≥ 0.6, booking check).

## Data links
- `scripts/export_mentions.py` -> `results/graph_<split>50/{docs.jsonl, gold_values.csv, gold_attrs.txt, cache/}`, `<input>/{mentions,clusters,instances}.csv, vectors.npz` -> `scripts/graph_run.py` stages -> `<input>/{coverage.csv, graphs.pkl, stability.csv, nodes.csv, labels.csv, select/, schema/}`
- `../chunking/results/S_n50/chunks/chroma_bge-m3.jsonl` -> `s1a/paths.py` `CHROMA_CHUNKS` -> `scripts/run.py`, `scripts/plug_in.py` (size 50/400)
- `../tear/data/conversation/{pool,test}.jsonl`, `levels.json` -> `s1a/paths.py` `TEAR_DATA` -> `s1a/gold.py`, `s1a/units.py`, `scripts/run.py`
- `scripts/run.py` -> `results/n50/{metrics.csv, summary.md, examples.md, attribute_purity.csv}`
- `scripts/relabel.py` -> `results/n50/relabel.md` (embeddings from the cache)
- `scripts/entity_seg.py` -> `results/n50/{entity_seg.md, entity_seg.csv, entity_seg_examples.md, chosen_seg.json}` and caches `results/n50/entity_seg/{chunks_<a>_<b>.jsonl, gliner_<key>.jsonl}` -> `scripts/plug_in.py`, `scripts/rescore.py`, `scripts/spans_compare.py` (`chunks_25_100`, `gliner_25_100_m45`)
- `scripts/spans_compare.py --export-texts` -> `results/v2_n50/texts.jsonl` -> `scripts/spacy_extract.py` -> `results/v2_n50/spacy_spans.jsonl` -> `scripts/spans_compare.py` -> `results/v2_n50/spans_compare.{md,csv}`, `spans_compare_examples.md`
- `scripts/step2.py` -> `results/v2_n50/{chosen_step2.json, step2.csv, step2.md, step2_examples.md}`; the adopted `chosen_step2_joint.json` -> `scripts/plug_in.py` (`--step2`) -> `results/v2_n50/plug_in.md`
- `scripts/rescore.py` -> `results/v2_n50/{rescore.md, rescore.csv, rescore_examples.md}`; also checks against `results/n50/entity_seg.md`

## Status (2026-10-25)
- 2026-10-25, v3 ported from worktree `../attribute-extraction-v3` (n50 dev):
  - gold mentions on predicted entities 0.744 (K 36), window Step 2;
  - GLiNER spans F1 0.614, value recall 0.887, end to end 0.545 (original stage 2);
  - check run: `results/v3_n50/plug_in_main_check.md`. Not yet checked on test.
- 2026-10-22/23, v2: new protocol, snapped segments and joint Step 2 adopted; the code was built in worktree `../attribute-extraction-v2` and ported here.
  - Results:
    - GLiNER spans F1 0.583 → 0.630
    - end to end 0.344 → 0.456
    - gold mentions on predicted entities 0.549 → 0.672 (K 48)
  - Results in `results/v2_n50/`; reports in OneDrive `TEAR/report/step1a_v2/`.
  - Tuned on the scored 50 dialogues; not yet checked on test.

## History
- 2026-10-21, entity segmentation: 0.470 → 0.549 (Chroma 25/100 + merge 0.45). GLiNER spans find 59–64% of gold values; on matched spans F1 0.530 → 0.583. bge-m3 cosines of adjacent pieces are about 0.35–0.85, so merge cutoffs are 0.45–0.60. `entity_seg.py` takes 25 min on CPU (gliner 0.2.29 pins transformers 5.16.1 in the venv). Report: OneDrive `TEAR/report/step1a_entity_segmentation.md`.
- 2026-10-20, 5% sample: values alone cluster by slot, values with context by entity; two stages (entity, then value) reach B-cubed F1 0.66 with gold entities, 0.47 with Chroma-based entities. Report: OneDrive `TEAR/report/step1a_results.md`.
