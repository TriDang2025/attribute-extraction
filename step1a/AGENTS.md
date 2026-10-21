# Step 1a Residual Mining on Conversation (agent notes)

Tests Step 1a of the schema-expansion pipeline (OneDrive `TEAR/source_paper/pipeline.pdf`): cluster units of the Conversation dialogues and score them against TEAR's gold attributes. Reuses `../chunking/` (data, bge-m3 encoder, Chroma chunks from `chunking/results/S_n50`) and `../hdbscan/` (UMAP, HDBSCAN, metrics) by import; gold tables from `../tear/data/conversation/`.

## Files
- `s1a/units.py`: units: Chroma chunks, oracle segments (gold domain runs), gold values located in the text (3 variants: value, ±10-word window, whole turn).
- `s1a/cluster.py`: HDBSCAN / agglomerative / k-means grid on raw bge-m3 and UMAP-5D.
- `scripts/run.py --limit 50`: main grid -> `results/n50/{metrics.csv, summary.md, examples.md, attribute_purity.csv}`.
- `scripts/relabel.py --limit 50`: scores value clusters vs attribute / entity / slot, plus the two-stage test -> `results/n50/relabel.md`.
- `s1a/segment.py`, `s1a/spans.py`, `scripts/entity_seg.py --limit 50`: entity segmentation (Chroma + bge-m3 at smaller sizes, merge if cosine >= tau and no new entity keyword) and GLiNER generic-label spans, in the two-stage test -> `results/n50/entity_seg.{md,csv}`, `entity_seg_examples.md`, caches in `entity_seg/`. GLiNER medium v2.1 in `CHK_MODELS/gliner_medium-v2.1` (its config points to the local `deberta-v3-base`).
- `data/cache/` (not in git): bge-m3 cache, seeded from the chunking cache.

## Run
venv `C:\Users\nguye\venvs\chunking`; `python -m pytest -q tests`, then the scripts above (n50: about 7 min on the laptop CPU).

## Status (2026-10-21)
- 2026-10-20, 5% sample: values alone cluster by slot, values with context by entity; two stages (entity, then value) reach B-cubed F1 0.66 with gold entities, 0.47 with Chroma-based entities. Report: OneDrive `TEAR/report/step1a_results.md`.
- 2026-10-21, entity segmentation: 0.470 -> 0.549 (Chroma 25/100 + merge 0.45). GLiNER spans find 59–64% of gold values; on matched spans F1 0.530 -> 0.583. bge-m3 cosines of adjacent pieces are about 0.35–0.85, so merge cutoffs are 0.45–0.60. `entity_seg.py` takes 25 min on CPU (gliner 0.2.29 pins transformers 5.16.1 in the venv). Report: OneDrive `TEAR/report/step1a_entity_segmentation.md`.
