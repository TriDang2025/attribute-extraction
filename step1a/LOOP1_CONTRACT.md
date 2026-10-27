# wf_v3 Loop-1 check: shared data contract (T2–T5)

Source: 26 Oct plan in `Attribute_Extraction.pdf` (§2.6–2.11). Builds on `GRAPH_CONTRACT.md`. Rules: no LLM in T2/T3, nothing tuned on test, never delete a node (mark it), toy-table tests only.

## Inputs
- Run dir `R = results/graph_v22_dev50/` (v2.2 = `fold.CONFIGS["F_m2_t06_bk"]`), same layout as GRAPH_CONTRACT: `R/{docs.jsonl, gold_values.csv, gold_attrs.txt}`, `R/spans/{mentions,clusters,instances}.csv, vectors.npz, nodes.csv, labels.csv`.
- Load with `s1a.mentions.load(R/"spans")` and `s1a.mentions.load_shared(R)`.
- "Verbatim gold mention" = `gold_values.csv` row with `verbatim == True`.
- Pilot entity: the predicted entity whose clustered mentions have majority `entity_gold == "train"` (E1 in v2.1); find it by that rule, never hard-code.
- Output root `O = results/loop1_check/`.

## T2: `s1a/recall.py` (W1)
- `purity_table(mentions) -> DataFrame[cluster_id, entity, gold_attr, n_class, size, purity]`: one row per (cluster, gold class that appears in it). `size` = all members of the cluster (labelled or not); a member with several classes (`;`) counts for each. Same rule as `labels.gold_labels`.
- `inside_counts(mentions, gold_values) -> Series[gold_attr -> n]`: number of verbatim gold mentions of the class overlapped by a clustered span (reuse `coverage._value_hits`).
- `recall_table(mentions, gold_values, attrs, strict=0.6, recov=0.25, min_inside=2) -> DataFrame[gold_attr, strict, recoverable, present, n_inside, best_cluster, best_purity]`
  - strict: some cluster has purity ≥ 0.6
  - recoverable: strict, or (n_inside ≥ 2 and some purity ≥ 0.25)
  - present: n_inside ≥ 1
- `summary(mentions, table) -> dict(K, strict, recoverable, present)`, with K = number of clusters.
- `bootstrap(mentions, gold_values, attrs, n=1000, seed=0) -> dict[measure -> (lo, hi)]`: resample dialogues, 95% range.
- `scripts/loop1_recall.py`: sweep for v2.2 (Step-2 threshold t × fold tau/min_size, 5–6 points spread over K), plus J and G as single points. Seed 42; encodes with bge-m3, so it runs alone. Outputs:
  - `O/recall.csv`: setting, params, K, strict, recoverable, present, with bootstrap lo/hi for the v2.2 point
  - `O/recall_by_attr.csv`: v2.2 point, one row per gold attribute
  - `O/fig/loop1_recall_at_k.png`: line chart, K on x, recall on y; strict and recoverable as two lines per setting; value labels on the points

## T3: `s1a/missing.py` (W2)
`missing_table(mentions, gold_values, recall_tab) -> DataFrame`: one row per attribute with `strict == False`. Columns:
- gold_attr, gold_entity (mode of `entity_gold` in gold_values)
- n_verbatim, n_nonverbatim
- gliner_cov: share of verbatim mentions overlapped by any span row in mentions.csv, clustered or not
- cluster_cov: share overlapped by a clustered span
- best_cluster, best_size, best_purity
- best_pred_entity, best_entity_majority_gold: the majority `entity_gold` over all clustered mentions of that predicted entity
- cause, planned_fix

Cause is the first rule that matches:
1. `implicit` if n_nonverbatim / (n_verbatim + n_nonverbatim) > 0.5
2. `missed` if gliner_cov < 0.5
3. `wrong_entity` if best_entity_majority_gold ≠ gold_entity
4. `mixed` if 0.25 ≤ best_purity < 0.6
5. `diluted` otherwise (best purity < 0.25)

Fix map: mixed → LLM split in Step 3; wrong_entity → entity fix (over-cluster then merge; shared-value signal); diluted → selective role split in Step 1a or Loop-2 probe; missed → Loop-2 probe with the LLM-suggested name; implicit → extractive limit or Loop-2 yes/no probe.

`scripts/loop1_missing.py` → `O/missing_attributes.csv` (reads `O/recall_by_attr.csv` or recomputes with `recall.recall_table`).

## T5 input: `s1a/pilot_input.py`, `scripts/pilot_build.py` (W3)
- Per cluster of the pilot entity:
  - id, n_mentions, n_values
  - 8 examples spread over different values and dialogues (never 8 copies of one value)
  - low_conf flag: the cluster's mean `gliner_score` is in the bottom third of the entity's clusters
  - no raw signal scores
- Each example:
  - `ex_id` (`"<cluster>:<j>"`)
  - speaker (user/system)
  - the turn with the mention marked `[[...]]`, plus the previous turn
- Withheld: identifier, column/table hint, spans sub-entities (from Task 7).
- Merge hints (no decision): the 3 nearest other clusters of the entity by centroid cosine, each with:
  - cosine percentile among all cluster pairs of the entity
  - `exclusive`: never in the same instance_id
  - shared top left/right context words
  - value-type agreement (`step2.value_type` majority)
- Placement hints (no decision), ranked:
  - options: current entity, each other predicted entity (id + top values of its 3 biggest clusters), sub-entity of current, relationship(current, X), separate table
  - the 5 signals, shown where they apply:
    1. entity share: share of the cluster's mentions in, or one turn next to, an instance of that entity (instances.csv turns)
    2. co-occurrence: mean positive NPMI over dialogues with the option's clusters
    3. similarity: max centroid-cosine percentile to the option's clusters
    4. cardinality: mean distinct values per instance; > 1.2 favors a separate table
    5. shared values: share of the cluster's values also found in another entity in the same dialogue; favors a relationship
  - rank by the mean of the signals scaled to [0, 1]; the rank is only a hint
- Writes to `O/pilot_train/`:
  - `prompts/full.txt`, `prompts/nocontext.txt` (values only, no context windows), `prompts/nohints.txt`
  - `examples.csv`: ex_id, cluster_id, mention_id
  - `prompt_stats.md`: estimated tokens, chars/3.5; must be < 30K or the script warns
- The prompt asks for one JSON array, one object per cluster (schema below), with nothing else around it.

## LLM output (one object per cluster; §2.9.4)
```json
{"cluster_id": "E1#3", "name": "str", "description": "str",
 "value_type": "time|day|number|name|code|other",
 "action": "keep|merge|split|not_attribute|unsure",
 "merge_with": ["E1#5"], "split": [{"name": "str", "examples": ["E1#3:0"]}],
 "placement": "<option text exactly as listed>", "evidence": "<one quoted example>"}
```

## LLM run: `s1a/llm_cache.py`, `colab/S1A_llm_colab.ipynb` (W4)
- Model: `Qwen/Qwen2.5-32B-Instruct-AWQ` with vLLM; fallback `Qwen/Qwen2.5-14B-Instruct-AWQ`. Temperature 0, max_model_len 32768, JSON-guided output.
- Cache key: sha256 of (model, params, prompt, run_tag). `run_tag` makes run 2 a real second call.
- Output `O/pilot_train/responses_<variant>_<run_tag>.jsonl`: one row with prompt_sha, model, params, raw, parsed.
- Runs: full/r1, full/r2, nocontext/r1, nohints/r1.
- T4: `O/t4_questions.txt` (the 2 questions, verbatim from §2.8) → `O/contamination_raw.jsonl`; `O/contamination.md` is written locally.
- Results go back to git as in `chunking/colab/sync.sh`. Tokens only from Colab Secrets.

## T5 eval: `s1a/pilot_verify.py`, `s1a/pilot_score.py`, `scripts/pilot_eval.py` (W5)
- `O/pilot_train/decisions.csv`: one row per cluster per response file (variant, run_tag, plus the JSON fields).
  - Final attributes: keep = itself; merge groups = union (transitive); split parts = each mention goes to the part whose example-vector centroid is nearest; not_attribute/unsure = marked, not deleted.
- Verification: GLiNER (`spans.load`, per-turn windows `spans.turn_windows`) over the pilot entity's instance turns, with the generated name as the only label → set A of normalized values (`step2.normalize`); B = normalized values of the attribute's mentions.
  - J = |A∩B| / |A∪B|; below 0.2 → `unverified` (kept)
  - GLiNER output cached per name
  - → `O/pilot_train/verification.csv`
- Gold: Task-4 `labels.csv` (gold / valid_new / noise, with gold_attr) and mentions' gold_attr. `O/pilot_train/scores.md` has one block per check in §2.10, each against its initial target:
  - Merges: share of LLM merge groups whose gold-labelled clusters share one gold_attr (≥0.8); share of same-class fragment pairs merged (≥0.6)
  - Splits: the mixed clusters whose top two classes are {departure, destination} or {leave at, arrive by} are split (both); share of example mentions on the right side (≥0.7)
  - Noise: share of `noise` clusters marked not_attribute/unsure (≥0.7); noise clusters given keep + a name (≤2)
  - Placement: share placed in the right entity (≥0.8); "right" = chosen option's entity majority gold == the cluster's majority entity_gold; sub-entity of current counts as current
  - Train attributes: strict recall over the train gold classes before vs after (no loss); one-to-one precision after (≥0.6; reuse `scripts/v21_run.one_to_one`)
  - Suggestions: share of followed merge hints that were right (report only)
  - Verification: mean J for right vs wrong names; "right" from `O/pilot_train/name_check.csv`, pre-filled by token overlap with the gold_attr name and corrected by hand
  - Context: every measure for full vs nocontext (clearly lower without context)
  - Stability: share of clusters whose action, merge_with or name differ between full r1 and r2 (report only)
