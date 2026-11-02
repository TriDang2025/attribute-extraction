# wf_v3.7 contract: checks on cached data, dev50b, Step 1a v2.3, LLM-only baseline (workers W1–W3)

Source: Overleaf diary `Diary.tex`, section "1 Nov 2026" (14 tasks, 4 parts). Builds on `GT_V35_CONTRACT.md`, `GT_V36_CONTRACT.md`, `RULES_V1.md`, `SPLITS.md` (read them first) and on `scripts/score_v36.py`, the v3.6 scorer.

Hard limits:
- Step 1a v2.2 and rules v1 stay reachable unchanged. Do not change `results/graph_v22_dev50` or `results/loop1_v31` … `loop1_v36`. Every change to shared code is a flag, switch or new name whose default keeps the old output. `score_v36.py` output must stay byte-identical (check it once at the end: run it to a temp `--out` and diff against `results/loop1_v36`).
- No LLM calls. Haiku rating sheets are prepared only; I run the raters.
- Toy tests only (no bge-m3, GLiNER, LLM or MultiWOZ files in tests). Venv `C:\Users\nguye\venvs\chunking`; run `python -m pytest -q tests` from `step1a/`. 531 pass now.
- No commits. New outputs go to `results/loop1_v37/` (or the folders named below).
- Only W2 may run bge-m3 or GLiNER: the bge-m3 cache (`data/cache/bge-m3.pkl`) has a single writer.
- Follow `C:\Users\nguye\.claude\coding-rules.md` and `step1a/AGENTS.md`. Reuse the v3.4–v3.6 code (score_levels, rules switches, PC.vote, noise_v36, range_v36, names_l2); do not copy it.

Data:
- MultiWOZ 2.2: `C:\Users\nguye\data\MultiWOZ_2.2`. v3.3 run: `../../attribute-extraction-wf-v3.3/step1a/results/loop1_v33` (pass as `--dir33`).
- GT levels for dev50: `results/loop1_v35/gt_levels.csv`, `mwoz_match.csv`. L2 base: train 10, hotel 14, restaurant 16 = 40.
- A orders: A r1 / A r2 / A s2 = orders 0 / 1 / 2 (score_v36 reads them with the parse repair on).
- Model-free noise ("mwoz" noise kind, v3.6 task 14): 13 noise clusters at L2.

## W1: Part 1, checks on cached dev50 data (T1–T5, T7) — `scripts/score_v37.py`, `s1a/*_v37.py`

**T1 ceiling and loss table.** New `s1a/ceiling_v37.py`, written so that W2 can call it on dev50b:
- `ceiling_table(entity_data, gt_level) -> DataFrame`: one row per L2 base attribute of the entity. Columns: `ent, attr, present` (some mention with that L2 label is in a Step-1a cluster of the entity), `recoverable` (some single cluster passes the found rule: purity ≥ 0.6 and coverage ≥ 10%), `best_cluster, best_purity, best_coverage`, and `step1a_reason` for non-recoverable ones:
  - `never_found`: no mention carries the attribute (GLiNER missed every value);
  - `mixed_roles`: the best cluster's top other attribute is the role partner (`config/role_pairs.json`);
  - `diluted`: otherwise.
- Reuse the found rule, do not re-implement it: score "identity decisions" (every cluster its own attribute, nothing marked) through the existing scorer. Say how you did it.
- `loss_table`: for every attribute that A does not find, per A order (0/1/2), the stage: Step 1a (not recoverable, with the reason above) or Step 3 (recoverable, but A dropped it: marked not_attribute; merged wrongly: its best group fails purity because of a merge; mixed roles: merged with the role partner). One row per (attr, order). Add a column `missed_orders` (k/3).
- Output: `results/loop1_v37/ceiling_dev50.md/.csv` (per entity: present k/n, recoverable k/n; out of 40 in total) and `loss_dev50.md/.csv`.

**T2 A s012.** `PC.vote` over the 3 A orders, read the same way as AE s012 in `v36_data`. Score at L2 with rules v1.1 (T5): found, noise caught k/13, precision of noise marks, real clusters marked noise, names right, columns. One table with A s012 next to AE s012 and the 3 A orders (as a range).
- Names: A s012's names that are not in `names_l2_rater{1,2}.csv` / `names_l2_new_*` go into a blind sheet `results/loop1_v37/names_to_rate_l2_v37.csv` + key, in the v3.6 format. Rated files: `names_l2_v37_rater{1,2}.csv`. Until they exist, show the count of unrated names.
- Decision line, printed in the md: keep AE only if AE s012 catches more of the 13 than A s012 and finds no fewer attributes at L2; else drop AE.
- Output: `results/loop1_v37/a_s012.md/.csv`.

**T3 duplicate columns.** For A ×3 orders, A s012, AE s012, Oracle s012 and E1 s012, at L2: columns per found attribute = the number of distinct output attribute names (groups) whose majority L2 attribute is that found attribute. Report the mean, the max, and a list of attributes with ≥ 2 columns with their column names. Output: `results/loop1_v37/dup_columns.md/.csv`.

**T4 train stability.** For Oracle and C (3 orders each, train only): group agreement across the orders (the existing `agreement=split` code), and role-pair flips. A flip = a two-role cluster pair (departure/destination, leaveat/arriveby from `config/role_pairs.json`) whose role-side assignment differs between two orders. Define it exactly in the md. Output: `results/loop1_v37/train_stability.md`.

**T5 rules v1.1.** A new setting `v1.1` in `s1a/score_rules.py` = `default` with `noise_kind=mwoz` (the 13-cluster set) as the only noise measure. `default` stays v1. Write `RULES_V1_1.md`: a copy of `RULES_V1.md` with the change and its reason line ("the noise set comes from MultiWOZ alone, not from a model or a word list; 13 clusters at L2"). Every v3.7 table uses `v1.1`. Add a re-score of the main v3.6 table (`all_variants`) with v1.1 at L2 → `results/loop1_v37/all_variants_v11.md/.csv`.

**T7 exit bar.** Add to `RULES_V1_1.md`: Step 3 is frozen as v1 when (a) it finds ≥ 90% of the attributes that Step 1a makes recoverable (T1); (b) found attributes change by ≤ 1 across orders; (c) ≤ 1.2 columns per found attribute; (d) ≥ 9 of the 13 noise clusters caught, with ≥ 70% of noise marks right; (e) it beats the LLM-only baseline. Report where A (3 orders) and A s012 stand on (a)–(d) in `results/loop1_v37/exit_bar.md`, with (e) "pending the baseline". Make the function take the run and GT dirs, so that it can be rerun on dev50b and with the baseline later.

`scripts/score_v37.py` takes the same arguments as score_v36 plus `--out results/loop1_v37`, and writes all of the above.

## W2: Part 2 + 4, dev50b and Step 1a v2.3 (T8, T9, T12, T13) — the only worker that runs models

**T8 dev50b.** dev50b = TEAR pool[50:100] (`chunking/data/conversation_ids.txt`). It does not overlap dev50 (pool[0:50]) or fresh (test[350:450]); check both and print the result.
- Add the split to `s1a/split.py` as a name (`dev50b`) or an `--offset` on the scripts, with the default unchanged. Add it to `SPLITS.md` ("dev50b: confirm decisions only, never tune").
- Labels: run the v3.5 GT pipeline (`scripts/multiwoz_span_labels.py`, `scripts/gt_v35.py`) on the dev50b run → `results/loop1_v37/dev50b/gt/{mwoz_match.csv, gt_levels.csv, gt_coverage.md}`. Report the labelled share by entity × speaker at L1 and L2, as in v3.5.

**T9 Step 1a v2.2 on dev50b.** The frozen v2.2 recipe, as in AGENTS.md "wf_v3 Loop-1 readiness check" T1: `export_mentions.py --variant F_m2_t06_bk` (with the dev50b split) → `results/graph_v22_dev50b`, then `graph_run.py` stages. The labels stage writes a label sheet for non-gold clusters; leave it unfilled and say what downstream code needs it (rules v1.1 noise does not).
- Run it detached with a log (`results/graph_v22_dev50b/export.log`); time it and report the time.
- Report recall@K at L1 and L2 (K, strict, recoverable, present: `scripts/loop1_recall.py` / `s1a/recall.py` with L2 labels) and the L2 ceiling (`s1a/ceiling_v37.ceiling_table`, from W1; if it does not exist yet when you get there, finish the rest and say so) next to dev50 → `results/loop1_v37/step1a_v22_v23.md`.

**T12 cue words.** On the 9 two-role train clusters of dev50 (as in `roles_v35` / v3.6 task 4):
- (a) J with the general words only (`CUE_GENERAL`; v3.6: 89/97 = 0.918 accuracy, 97/162 = 0.599 coverage);
- (b) learned cue words: for each cluster, the word just before each mention; keep a word when splitting the cluster by it gives two parts that are each ≥ 20% of the mentions. Say exactly how a learned word is mapped to a role side (no gold roles may be used to learn it; gold roles are used only to score).
- Accuracy and coverage of both, k/n. Choose (b) if its accuracy ≥ (a)'s, else (a). Output: `results/loop1_v37/cue_words.md`.

**T13 Step 1a v2.3 = J + the value-type fix (T26).** A new export variant (for example `V23` in `s1a/combos*.py` on top of `F_m2_t06_bk`), so v2.2 stays reachable:
- the T26 value-type fix from v3.5 (`value_type_v35`: "8.08GBP", "37.79 GPB", "66 GBP" are price; "28-minute", "105 minutes" are duration) applied in Step 1a;
- J with the T12 cue words: a cluster is split when J puts ≥ 20% of its mentions on each side. Mentions with no cue word go into an "unknown role" part (its own cluster), never a guessed side. No gold labels.
- Run on dev50 → `results/graph_v23_dev50` and dev50b → `results/graph_v23_dev50b`. Report recall@K at L1 and L2 (K, strict, recoverable, present) and the L2 ceiling next to v2.2 for both sets, in `results/loop1_v37/step1a_v22_v23.md`, plus how many clusters J split and the unknown-part sizes.

## W3: Part 3, LLM-only baseline, and T6 (no models)

**T10 baseline prompts.** `scripts/baseline_build_v37.py` → `results/loop1_v37/colab/baseline/{prompts/*.txt, *.schema.json}` and rows in `results/loop1_v37/colab/manifest.json` (the v3.6 manifest format, family `baseline`).
- For each entity (train, hotel, restaurant), set (dev50, dev50b) and version (v0, v1, v2) = 18 prompts. The dialogues of an entity = the set's dialogues whose MultiWOZ 2.2 `services` include that domain. Full dialogue text in the format the pipeline shows (speaker-tagged turns).
- Fill each prompt with as many whole dialogues as fit in a budget: MAX_LEN 32768 − output max_tokens (4096) − instruction tokens, using the repo's token estimate (`pilot_input.est_tokens`). v0 = the set order; v1, v2 = shuffled with seeds 1, 2 (a different sample when not all fit). Record the number of dialogues used per prompt.
- Instruction (no clusters, hints or dataset name): "List the attributes (columns) that a database table for this entity should store, each with a one-sentence description." The entity is named by its common word ("train journey", "hotel", "restaurant"). Guided JSON: `{"attributes": [{"name": str, "description": str}]}`.
- `results/loop1_v37/colab/baseline/prompt_stats.md`: prompts, dialogues used, estimated prompt tokens, output estimate 1,000 per call (mark it as an estimate), totals.

**T11 prep (code only, runs after the batch).** `s1a/baseline_v37.py` + `scripts/score_baseline_v37.py`:
- read the baseline responses (`results/loop1_v37/colab/responses/baseline_*.jsonl`, the v3.6 response format);
- write a blind rating sheet against the L2 slot names (same rubric file and format as `results/loop1_v36/names_to_rate_l2*.csv`), one row per (set, ent, version, name);
- support check: for each listed attribute, is there a value in the set's dialogues? (an L2 span of the matching slot, using the rated slot; for an attribute with no L2 slot, a search of the dialogue text for the attribute's words and any typed values: say what you search for);
- the table: baseline (each version and their union) next to A at L2: right names, extras with no GT, wrong attributes, attributes with no support, number of columns. Test with toy responses.

**T6 TEAR attribute recommendation.** Read `C:\Users\nguye\OneDrive\Desktop\Work\TEAR\papers\tear_2026.pdf` (recommendation part) and `tear/` code (`tear/AGENTS.md`, `tear/README.md`, the recommendation code). Answer: can the recommendation run with only part of the schema given and suggest the missing attributes? Yes or no, with the page/section and the code path. If yes, write the exact command with some attributes hidden. Do not run TEAR. Output: `results/loop1_v37/tear_recommend.md`.

## What each worker returns
- Files changed and created, test count, and anything in this contract that did not fit the code.
- W1: how the found rule is reused for the ceiling; the byte-identity check of score_v36.
- W2: run times, the overlap check, and how learned cue words map to sides.
- W3: the dialogues used per prompt and the token totals.
