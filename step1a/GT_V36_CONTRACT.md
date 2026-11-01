# wf_v3.6 contract: Colab batch prep, TEAR on dev50, noise with the L2 GT (shared by workers W1–W3)

Source: Overleaf diary `Diary.tex`, second "31 Oct 2026" section (16 tasks, 4 parts). Plan: `C:\Users\nguye\.claude\plans\distributed-finding-nova.md`. Builds on `GT_V35_CONTRACT.md`, `RULES_V1.md`, `PILOT_V35_BATCH.md` (read them first).

Hard limits:
- Step 1a and rules v1 are frozen. Do not change Step 1a, `results/graph_v22_dev50`, or `results/loop1_v31/v32/v33/v34/v35`.
- Old behaviour stays reachable. Every change to shared code is a flag or switch whose default keeps the v3.5 output:
  - `score_v34.py --check-old` gives 0 mismatches;
  - `score_v35.py` output is unchanged unless the new flag is passed.
- No LLM calls (Haiku rating sheets are prepared; I run the raters).
- Toy tests only, with no bge-m3, GLiNER, LLM or MultiWOZ files in tests. Venv `C:\Users\nguye\venvs\chunking`; run `python -m pytest -q tests` from `step1a/`. 471 tests pass now.
- No commits. New outputs go to `results/loop1_v36/`.
- Follow `C:\Users\nguye\.claude\coding-rules.md` and `step1a/AGENTS.md`.

Data: as in the v3.5 contract.
- MultiWOZ 2.2 is at `C:\Users\nguye\data\MultiWOZ_2.2\`, and the 2.4 DBs are in `../chunking/data/MULTIWOZ2.4.zip`.
- The L1/L2/L3 labels are in `results/loop1_v35/gt_levels.csv` and `mwoz_match.csv`; the readers are `v34_data.read_gt_levels` / `with_level`.

## W1: Part 1, batch preparation

**1. Parse repair (T8).** The restaurant A r2 (`results/loop1_v31/responses/restaurant_v2_r2.jsonl`) has finish_reason "stop" and 6 errors "clusters[i] attribute X not in the attribute list" (`s1a/llm_cache.py` ~l.165): the model used names in `clusters` it never declared.
- Add `llm_cache.repair_undeclared(obj) -> (obj, repaired_names)`: every non-`not_attribute`/`attribute_cue` cluster attribute missing from `attributes` is appended as `{"name": X, "description": "", "role": "", "repaired": true}` (keys as the format needs), first-seen order.
- Wire it in as an opt-in flag on the response loaders used by scoring (trace the v34/v35 data path: `v34_data`, `v35_data`, the decision builders). Default off.
- `score_v35.py --repair` turns it on and writes `results/loop1_v36/repairs.csv` with columns `variant, ent, job, repaired_names, n_repaired`. Remove "A r2" from `config/invalid_runs.json` only in a new `config/invalid_runs_v36.json` (empty runs list), chosen by `--invalid config/invalid_runs_v36.json`.
- Test: the A r2 shape (8 declared names, 4 undeclared used) gives 0 errors after the repair and 4 repaired names.

**2. Builder `scripts/pilot_build_v36.py`** → `results/loop1_v36/colab/{prompts/, manifest.json, prompt_stats.md}`. Same manifest format as v3.5.
- **A s2:** `PIN.render_v2(inp, export, docs, "v2", order_seed=2)`, schema `schema_v2`, format v2, `max_tokens` as v3.1 (12000), job `{ent}_v2_s2`, run_tag `s2`. Build `inp` exactly as `pilot_build_v31.py` does for v2 (same k from `fit`), so that order_seed None reproduces `results/loop1_v31/prompts/{ent}_v2.txt` byte for byte and SHUFFLE_SEED 1 reproduces `{ent}_v2_r2.txt`. Test or check this once on the real data and report it.
- **AE (A + E's noise instruction):** a new instruction `INSTRUCTION_V2_AE` = `INSTRUCTION_V2` with E's noise rule (`pilot_input.NOISE_RULE`) added right after the v2 noise sentence, nothing else changed. Look at how `INSTRUCTION_V3` → E inserts it (~l.599–608). Do not add the attribute_cue line, which is not part of the noise instruction.
  - Flag `render_v2(..., noise_rule=False)`; the default is byte-identical.
  - Jobs `{ent}_ae_s{0,1,2}` with order_seed None / 1 / 2.
  - Test: the AE text minus the A text = exactly the inserted noise rule.
- **F2 (fixed delex):** v3.3 F (`../attribute-extraction-wf-v3.3/step1a`, `PILOT_V33*.md` "F de-lexicalisation", `scripts/pilot_build_v33.py`, `s1a/delex.py`) = E seed 0 on de-lexicalised prompts with carry-over, 7 jobs. It was invalid because the map pulled generic words ("hotel", "restaurant", "travel time") from unlabelled spans of name clusters.
  - New `delex.build_map_v2(names, texts)`: only real entity names are mapped:
    - the `name` fields of the 2.4 `*_db.json` (hotel, restaurant, attraction);
    - train stations (`departure`/`destination` of `train_db.json`);
    - `TR\d{4}` ids.
  - Minus a stop list `delex.STOP` (generic words: hotel, restaurant, guesthouse, guest house, train, taxi, travel time, centre, center, north, south, east, west, cambridge, the, ...; keep it in code, listed in the contract answer).
  - Same fake-string function. Jobs `f2_*` mirror the v3.3 F job set (rounds and carry; `fill_carry` applies the map for variant `f2`).
  - Test: "hotel", "restaurant" and "travel time" are never keys; a DB name and a TR id are.
- **Reused v3.5 jobs:** the oracle (6) and g (21) jobs are copied as is (prompt + schema files, manifest rows) from `results/loop1_v35/colab/`. The T8 `restaurant_v2_r2_rerun` job is dropped.
- **prompt_stats.md:** calls and estimated prompt/output tokens per family (chars / 3.5; output = the v3.1 A per-call output for A/AE, the v3.3 F per-call output for F2), with a total and the change vs the v3.5 batch (28 calls, 158,886 / 45,943).
- **Notebook** `colab/S1A_llm_v36_colab.ipynb`: copy of `S1A_llm_v35_colab.ipynb`, pointed at `loop1_v36/colab` and branch `wf-v3.6`. It must support the carry rounds that F2 needs (copy that logic from the v3.3 notebook). Results go via `bash colab/sync.sh push-results "v3.6 batch responses" loop1_v36/colab`.

**3. J general cue words (task 4).** In `s1a/roles_v35.py` (or a v36 module importing it):
- `CUE_GENERAL = {"start": {"from", "after"}, "end": {"to", "into", "by", "before"}}`;
- domain words = the rest of `pilot_input.CUE_ROLES` (leave/leaving, depart/departing/departs, arrive/arriving/arrives).
- `j_side(row, k, words=...)` takes an optional word set.
- `scripts/roles_v36.py` writes `results/loop1_v36/roles_summary.md`: J accuracy and coverage with full vs general words, for the same 3 groups as v3.5 (two-role all, train, all gold-role clusters), as k/n (share). Also a table of each cue word: general/domain, mentions covered, accuracy.

## W2: Part 3, the main claim

**1. TEAR on dev50 (T40).** Read `tear/AGENTS.md`, `tear/README.md`, `tear/data_build/multiwoz.py`, `tear/eval/reproduce.py`, `tear/colab/*`.
- Find how TEAR picks demonstrations and from which pool. Report whether any dev50 id can enter it.
- Write `tear/data_build/dev50.py` → `tear/data/conversation_dev50.jsonl` (the same row format as `tear/results/conversation_input_first200.jsonl`: `id`, `text`, ...) for the 50 dev50 ids, with text from MultiWOZ in TEAR's own format (same builder as `multiwoz.py`). The demonstration pool must exclude the 50 ids, via a flag or config, not by editing shared defaults.
- Add the Colab run config: env vars or arguments for `tear/colab/run.sh`, seed 0, the TEAR method only (the `te_tear_Lfull` setting), output `tear/results/conversation_dev50/`. Write the exact command in `tear/colab/DEV50_RUN.md`, with a time estimate from the 10-18 benchmark (~100 s/text on an L4).
- Do not run TEAR.

**2. TEAR scorer `step1a/scripts/score_tear_v36.py`** (+ `s1a/tear_cols.py`). Input: TEAR output rows (`id`, `table`, `schema`, as in `te_tear_Lfull_s0.jsonl`; read the real file to get the shape).
- Each TEAR column is mapped to an entity and a GT attribute:
  - **by value:** cell values normalised (as `gt_ext`) and matched to the MultiWOZ 2.2 span values of the same dialogue (`data/mwoz22_spans.csv`). The majority (domain, slot) over the matched cells gives the slot; ties and < 2 matched cells give "unmatched".
  - **by name:** a sheet `results/loop1_v36/tear_names_to_rate.csv` (column name, sample values, candidate GT attrs) for 2 blind Haiku raters; read back later as `tear_names_rater{1,2}.csv`, lower label wins.
- Final label = the value label, or the name label when the value label is unmatched. Disagreements go to `tear_label_disagree.csv`.
- Output: `results/loop1_v36/tear_extras.md/.csv` in the format of `results/loop1_v35/extras_table.md` (gt_found, extra_L2, extra_L3, extra_none, wrong) at each level.
- Toy test with a 2-dialogue fake TEAR output.

**3. Task 11: F delex.** Re-score v3.3 F (`../attribute-extraction-wf-v3.3/step1a/results/loop1_v33/decisions.csv`, variant F) at L2 with rules v1. Show its extras by level next to E s0 (the same prompt without delex).
- Mark F invalid (broken map) in the table.
- Leave an F2 hook: the same code runs on `loop1_v36/colab` F2 decisions once they exist.

**4. T41: column precision.** For every variant in `score_v35.SHOWN` (+ F) and for TEAR, each output column (distinct attribute name of the variant, not group) gets exactly one bucket, at L1 and L2: `gt` (majority attr is a GT attr of that level), `extra_confirmed` (non-L1 attr confirmed at L2/L3), `extra_none` (no level), `wrong` (wrong_entity or majority noise). Reuse the T38 extras code in `s1a/checks_v35.py`.
- Output: `results/loop1_v36/column_precision.md/.csv`, k/n with `fmt_count`.

## W3: Part 4, noise with the new GT

**1. Task 13: unmatched mentions.** The 165 mentions with `match == none` in `mwoz_match.csv`, grouped by kind with rules first:
- value shape: time, number, price, ref code, phone, postcode, day;
- word lists: yes/no/ok/thanks, booking words, choice words, request words, pronoun/generic noun;
- `other` for the rest.
- Output: `results/loop1_v36/unmatched_kinds.md/.csv` with the count and share per kind and 2 examples each (turn text with the value in [[ ]]).
- Also write `unmatched_other_to_rate.csv`, so a Haiku pass can split `other`.

**2. Task 14: model-free noise.** A mention is noise iff (no L2 span label and no request act in its turn for that value) or it is choice. Use `gt_levels.csv` / `mwoz_match.csv`; choice is `is_choice` as in v3.5.
- A cluster is noise when ≥ 60% of its mentions are noise (the Q2 rule, `cluster_label` "0.6" in `s1a/score_rules.py`).
- Add this as a new noise_kind switch value `mwoz` in `Rules`; the default is unchanged.
- Output: `results/loop1_v36/noise_mwoz.md/.csv`: noise clusters at L2 vs the L1 noise set (current rules v1 default), with counts and the list of clusters that changed, plus why.

**3. Task 15: noise at L2 for all variants.** Using the `mwoz` noise set: for each variant (`score_v35.SHOWN`, and new rows later via the same function), pooled over entities, report:
- noise marked (k/n of noise clusters marked not_attribute);
- precision of noise marks (k/n of marked clusters that are noise);
- real clusters marked noise (count).
- Output: `results/loop1_v36/noise_l2.md/.csv`. It must accept the v3.6 batch decisions later via the same loader.

**4. Task 16: names against L2 slot names.** A sheet `results/loop1_v36/names_to_rate_l2.csv`: every (variant, ent, group name, majority L2 slot name + description from `schema.json`) that the names rule scores at L2. Blind: no variant column in the rater copy, rows shuffled with a fixed seed, plus a key file. Rubric in `names_l2_rubric.md` (right / partly / wrong).
- Add a names switch value `l2rated` in `s1a/rules_names.py` that reads `names_l2_rater{1,2}.csv` (lower label wins) and replaces the valid_extra approximation at L2/L3; the default is unchanged.
- Test with a toy rated file.

## What each worker returns
- Files changed and created.
- Test count.
- Anything in the contract that did not fit the code.
- For W1: the byte-identity check result.
- For W2: how TEAR picks demonstrations.
