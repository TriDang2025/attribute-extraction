# T6: can TEAR's attribute recommendation run with part of the schema?

Answer: **yes.** The task is defined that way, and the repo runs it today on a reduced schema.

## Paper (`tear_2026.pdf`; page numbers are PDF pages)
- p.4, Definition 3.6 (Attribute Recommendation): input = an *inadequate* schema S, labeled samples, unlabeled texts and a budget k; output = k new attributes S'. The metric is recall of S' against the hidden ground-truth attributes.
- p.6-7, Section 4.3 (Attribute Recommendation Workflow): the user gives "only a heuristic schema as an initial direction"; the system returns a ranked list of new attributes. Parts: 4.3.1 Discovery Mechanism, then the Hybrid Integration Strategy (duplicates), then the Schema Coherence Score (ranking by relevance to the given schema).
- p.8, Section 5.1: three exploratory levels hide 20%, 35% or 50% of the attributes (Conversation: 7 / 12 / 17 of 35 hidden). The hidden attributes are "completely hidden" and the system does not know the level. p.11, Section 6.3 gives the results (recall-AUC).

## Code (`tear/`)
- `eval/reproduce.py`: `_schema(key, level)` reads `levels.json["levels"][level]["schema"]`, so the schema is the full one minus the hidden attributes; `_pipeline` passes it to `TearPipeline`.
- `tear_reproduction/pipeline.py`: `TearPipeline.__init__` projects the labeled pool onto the given schema (hidden columns are gone from the demonstrations); `discover()` asks the LLM for new columns and drops names already in the schema or table (`known`).
- Chain per level: `te` (extract with the reduced schema) -> `discover` (`cmd_discover`) -> `coherence` (`CoherenceScorer`, needs the scoring server on port 8081) -> `integrate` (`HybridIntegrator`) -> `results/<dataset>/ar_L<level>_s<seed>.json` (`ranked` = the recommended attributes in order). `tearstar` then re-runs extraction with the accepted ones (not needed here). `tools/run_all.py` runs the chain for level 2 (`TEAR_ALL_LEVELS=1` adds 1 and 3).
- Limit: the levels are fixed. The hidden set comes from `data/conversation/levels.json` (keys 1, 2, 3; level 2 already hides 12 attributes, among them Train leave at, Train requested people, Train confirmed reference). `--level` takes any key, so a custom hidden set needs one extra entry in that file (data, not in git); no code change.
- Caveats: the surrogate that makes the previews was trained on the full-schema pool; its hidden columns are removed from the previews, but it saw the hidden attributes in training (tear/README.md, deviations). On `conversation_dev50` it also saw the 50 dev texts. `cmd_integrate` loads the whole `pool.jsonl` for the definitions of known attributes, which includes the 50 dev ids (only definitions, not demonstrations). Discovery costs about 300 s per text on the laptop model (tear/README.md), so run it on Colab, not here. I did not run TEAR.

## Command with some attributes hidden (dev50, three hidden)
Run from `tear/`. First the previews and the embedding cache of dev50 must exist (`TEAR_DEV50=1 bash colab/run.sh 50 0`, see `colab/DEV50_RUN.md`). Then add a custom level `h3` (hides Train leave at, Train requested people, Hotel stars):

```
python -I -c "import json,pathlib; p=pathlib.Path('data/conversation/levels.json'); d=json.loads(p.read_text(encoding='utf-8')); h=['Train leave at','Train requested people','Hotel stars']; d['levels']['h3']={'schema':[a for a in d['full_schema'] if a not in h],'hidden':h}; p.write_text(json.dumps(d,ensure_ascii=False,indent=1),encoding='utf-8',newline='\n')"
python -m eval.reproduce te        --dataset conversation_dev50 --methods tear --seeds 0 --level h3 --n 50
python -m eval.reproduce discover  --dataset conversation_dev50 --level h3 --seed 0 --n 50
python -m eval.reproduce coherence --dataset conversation_dev50 --level h3 --seed 0
python -m eval.reproduce integrate --dataset conversation_dev50 --level h3 --seed 0
```

Output: `results/conversation_dev50/ar_Lh3_s0.json` (`ranked`, `scores`, `cfr_ranked`). Compare `ranked` with the three hidden names. Other flags (`--base-url`, `--model`, `--embedding-url`) as in `tear/README.md`; the scoring server for `coherence` as in `tools/start_scoring_server.sh`. `cmd_report` skips dev50, so the recall is computed by hand from `ar_Lh3_s0.json`.
