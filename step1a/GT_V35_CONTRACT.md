# wf_v3.5 contract: extended GT (MultiWOZ 2.2), rules v1, no-LLM checks (shared by workers W1–W5)

Source: `Attribute_Extraction (2).pdf`, section "31 Oct 2026" (tasks T1–T44; this version does T1–T13, T15, T16, T23, T26, T27, T35, T38). Plan: `C:\Users\nguye\.claude\plans\distributed-finding-nova.md`. Builds on `SCORER_V34_CONTRACT.md` (read it first: Rules, EntityData, stage-2 functions).

Hard limits:
- No LLM calls.
- Do not change Step 1a, `results/graph_v22_dev50`, `results/loop1_v31/v32/v34`, or the old scorer files (`s1a/pilot_score.py`, `pilot_verify.py`, `pilot_combine.py`, `recall.py`, `scripts/pilot_eval_v3*.py`).
- `score_v34.py --check-old` must still give 0 mismatches: every new switch has an `old` value that keeps the v3.4 behaviour.
- Toy tests only (no bge-m3, GLiNER, LLM or MultiWOZ files in tests). Venv `C:\Users\nguye\venvs\chunking`; run `python -m pytest -q tests` from `step1a/`.
- No commits.
- New outputs go to `results/loop1_v35/`.

Data:
- **MultiWOZ 2.2:** `C:\Users\nguye\data\MultiWOZ_2.2\` (train/dev/test `dialogues_*.json`, `dialog_acts.json`, `schema.json`). Pass it as `--mwoz`, never hard-coded in library code. 45 of the dev50 dialogues are in train, 1 in dev, 4 in test.
- **MultiWOZ 2.4 DBs:** inside `../chunking/data/MULTIWOZ2.4.zip` (`MULTIWOZ2.4/<domain>_db.json`).
- **dev50 mentions:** `results/graph_v22_dev50/spans/mentions.csv`. dialogue_id is the MultiWOZ id without `.json`. `turn` = 0-based turn index (0 = first user turn). char_start/char_end are relative to that turn's text.

## W1: span labels + matching + levels (T1–T6) — `scripts/multiwoz_span_labels.py`, `s1a/gt_ext.py`, `config/tear_to_mwoz.json`, `tests/test_gt_ext.py`

**T1 `scripts/multiwoz_span_labels.py --mwoz <dir> --ids <mentions.csv> --out data/mwoz22_spans.csv`** (only the dev50 ids; also accepts `--all`). One row per labelled span.
- Columns: `dialogue_id, turn, speaker (user|system), utterance, char_start, char_end, value, domain, slot, act, source`.
- `dialogues_*.json` frames → `slots` with `start`/`exclusive_end`: act = "inform", source = "slot". For the user, take the active-intent frame slots that have spans; for the system, take the frame slots.
- `dialog_acts.json` `span_info` entries `[act, slot, value, start, end]`: act = the act name, for example "Train-Inform" → domain train, act inform. source = "act_span".
- Request acts (`dialog_act` entries with act `*-Request`, value "?") have no span. One row each, with char_start/char_end empty, act = "request", source = "request".
- Duplicates (same turn, span, slot) are kept once; slot + act_span rows count as one.

**T2 `gt_ext.match(mentions, spans, utterances) -> DataFrame`**, one row per dev50 mention.
- Columns: `mention_id, dialogue_id, turn, mw_turn, text_match (exact|fuzzy|none), mw_domain, mw_slot, mw_act, match (span|value|none), request_slots` (`;`-joined slots requested in that turn).
- **Turn:** the same index if the normalised utterance (lowercase, whitespace collapsed) equals the dev50 turn text; else the turn in that dialogue with the highest `difflib` ratio ≥ 0.8 (fuzzy); else none.
- **Label:**
  - span overlap ≥ 50% of the mention's characters with a span of that turn (char offsets shifted when fuzzy: find the mention text in the MultiWOZ utterance near the same offset);
  - else equal normalised value within the same turn;
  - else none.
  - Several spans: take the largest overlap; ties prefer source slot > act_span.
- **T6 rule:** slot `choice` → `mw_slot = "choice"`, and it is treated as noise at every level (never a GT attribute).

**T4 `config/tear_to_mwoz.json`:** `{"Train destination": "train-destination", ...}` for every TEAR gold attr of the 3 entities (`MN.load_shared`'s gold_attrs). Also `"_notes"`: why one TEAR train attr has no user-goal slot (find which one; write the reason). Use the 2.2 slot names (`train-leaveat`, `hotel-bookpeople`, …).

**T3 levels `gt_ext.levels(mentions, matched, tear_map, db) -> DataFrame`**, one row per mention.
- Columns: `mention_id, gt_L1, gt_L2, gt_L3, ent_L1, ent_L2, ent_L3, is_request, is_choice`.
- **L1:** the current `gold_attr` / `entity_gold` (unchanged; empty = no label).
- **L2:** L1 if set; else the official schema slot from the match, when `schema.json` lists that slot. Its name is the TEAR attr when `tear_to_mwoz` maps to it, else `"<Domain> <slot without domain prefix>"` (for example "Train trainid", "Hotel phone"). ent = slot domain. `choice` is never a label; `is_choice` = True.
- **L3:** L2 if set; else the DB column. For an unlabelled mention, look for a DB row of the mention's cluster entity domain (train / hotel / restaurant) with a column whose normalised value equals the mention's norm_value. Name `"<Domain> <column>"` (for example "Restaurant signature"). Skip id-like columns (`id`, `location`) and columns where the value is in > 30% of rows (too common).
- `is_request` = the mention lies in a turn with a request act for a slot of the cluster's domain, and the mention text matches the request phrase pattern (a wh-word / "how many" within 3 tokens before, or the mention is the question word phrase itself). Output: the requested slot or "".

**Coverage tables `gt_ext.coverage(mentions, lv, old)`:**
- share of mentions labelled per level, by entity × speaker (counts "k/n (0.xxx)");
- how many of the 25 v3.4 "unknown" clusters (`results/loop1_v34/q2_table.csv` label under the default 0.6 = unknown; recompute if absent) and of the 178 "other" values (`results/loop1_v34/q1_table_values.csv`, kind = other) get an L2 or L3 label.

**CLI `scripts/gt_v35.py --run results/graph_v22_dev50 --mwoz <dir> --out results/loop1_v35`:** writes `mwoz_match.csv`, `gt_levels.csv`, `gt_coverage.csv`, `gt_coverage.md`, plus a list of match failures.

## W2: rules v1 (T8–T11) — `s1a/score_rules.py`, `s1a/rules_labels.py`, `s1a/rules_groups.py`, `s1a/rules_names.py` (+ tests)
New switches. Old value first, then the v1 default in **bold**:

| switch | values | meaning |
|---|---|---|
| `gt` | old (=L1) / L2 / L3 | GT level (W3 wires the data; W2 only adds the switch and passes it on) |
| `unknown` | old / **out** | out = clusters labelled unknown are left out of every base (noise base, merge judging); report `unknown_n` |
| `merge_gold` | old / **min2** | min2 = members with no gold top attr are left out; a merge is judged only when ≥ 2 members have gold; report `merge_unjudged` |
| `marked_found` | old / **skip** | skip = a group whose decision is in `PV.MARKED` (not_attribute etc.) cannot be the best group for found |
| `other_entity` | old / **wrong_entity** | wrong_entity = an `other_entity:<E>` mention gets class `wrong_entity`, which is neither real nor noise and counts against the top share; except "frequent" values: gold value in ≥ 2 entities, or in ≥ 20% of dev50 dialogues → stays as in old |

- Real values without gold stay `real_extra` (counted as real).
- "other" stays unlabeled.
- Placement stays reported but is not used in any verdict (document it in RULES_V1.md).
- `DEFAULT` gets the bold values, plus `gt=L1` (W3's runs set the level explicitly).

**New columns** (append to NEW_COLS): `unknown_n, merge_unjudged, wrong_entity_n`.

**T10 `fmt_count(k, n) -> str`:** gives "4/7 (0.571)" and "0/0 (n/a)". Used by every table writer in `scripts/score_v34.py` (sweep.md, report tables), replacing bare decimals for found, noise marked, merge precision, place, names and agreement (agreement counts = agreeing clusters / clusters).

**T11 pooled noise:** `pooled_noise(rows) -> dict(marked, n, share)` over the 3 entities per variant. sweep.md shows it in one extra row per variant: "pooled noise marked k/n (0.xx), target ≥ 0.70".

**T8 invalid runs:** `config/invalid_runs.json` `{"runs": [{"ent": "restaurant", "variant": "A r2", "reason": "6 parse errors"}]}`. `order_range` and `gain_verdict` drop invalid runs, and the range table marks them.

## W3: levels in the scorer + re-score (T3 wiring, T5, T12, T13) — after W1 and W2
- **`Rules.gt` wiring:** `v34_data.with_level(data, gt_levels_df, level) -> data copy` replaces each mention's `gold_attr` / `entity_gold` with `gt_L{level}` / `ent_L{level}`, and each ctx's gold attr list (`ctx.train` and its kin) with the level's attrs of that entity that occur in dev50. The rest of the scorer then works unchanged.
- **Names at L2/L3:** a group rated `valid_extra` whose majority gold attr at that level is a non-L1 attr counts as `right` for that attr. Document this approximation.
- **T5 `rules_labels.cue_scores(ed, label, gt_levels) -> dict(cue_n, cue_request, cue_share)`:** decisions with action `attribute_cue`, scored against `is_request`. `cue_request` = cue clusters whose mentions are ≥ 50% request mentions.
- **T12 `scripts/score_v35.py --setting v1 --levels 1,2,3`:**
  - variants = v3.2 A–D (as v3.4) + v3.3 C, E, E1, E2. Load them the way `../attribute-extraction-wf-v3.3/step1a/scripts/pilot_eval_v33.py` does, from that worktree's `results/loop1_v33` (pass `--dir33`);
  - writes `results/loop1_v35/all_variants.csv` (setting, level, ent, variant, columns) and `all_variants.md`: one table per level, variants × (found k/n, noise pooled, merge k/n + unjudged, names k/n, role k/n, cue k/n), all in counts.
- **T13 `step1a/RULES_V1.md`:** every rule in one line (switch = value), its reason, and the date 2026-10-31. Written by the lead after review.

## W4: roles + instability (T15, T16, T27) — `s1a/roles_v35.py`, `tests/test_roles_v35.py`
- **Gold role per mention** from the L2 slot: departure / destination / leaveat / arriveby (train, taxi). Hotel/restaurant name vs address etc. are separate attrs, not roles. Two-role cluster = ≥ 2 role slots of one pair, each ≥ 20% of the cluster's labelled mentions.
- **T15 `role_word_eval(mentions, gold_role) -> DataFrame`** per cluster: J = the role from `left_word` / the words before the value. Reuse the v3.3 role-word code (`grep -rn "role_word\|ROLE_WORDS\|left_word" s1a/` to find it). Columns: `cluster_id, n, n_gold_role, covered (J gives a role), correct, accuracy, coverage`.
- **T16 `context_split(mentions, vectors, thr=0.25) -> DataFrame`:** the context vector = bge-m3 of the turn with the value replaced by "[V]". Use the cached `results/graph_v22_dev50/spans/window_vectors.npz` if it holds per-mention windows (check its keys); else embed with `s1a`'s existing bge-m3 helper (CPU, about 850 short texts, < 5 min; the cache file is new and single-writer).
  - Split by KMeans k=2 when silhouette ≥ thr (fixed in advance); both parts are mapped to the majority gold role.
  - The same output columns as T15, plus `split (bool), silhouette`.
  - The function takes vectors as input, so tests use toy vectors.
- **T27 `train_instability(ed) -> DataFrame`:** C s0/s1/s2 clusters whose group (member set) changes, with a reason in {role_pair, noise_flip, mixed_cluster, name_wording, other}. Reuse `rules_names.order_diffs`.
- **CLI `scripts/roles_v35.py`:** writes `roles_j.csv`, `roles_context.csv`, `roles_summary.md`, `train_instability.csv`.

## W5: noise vote, value types, attribute checks, extras (T23, T26, T35, T38) — `s1a/checks_v35.py`, `tests/test_checks_v35.py`
- **T23 `noise_vote_2of3(seed_decs) -> Series`:** a cluster is marked noise when ≥ 2 of the 3 C orders mark it (`PV.MARKED`). Score it like `noise_marked_v`, plus the precision of the marked clusters against cluster labels at each level.
- **T26 value types:** find the step-1a value-type function (`grep -rn "value_type\|def vtype\|shape" s1a/`), and add a fixed copy `value_type_v35(text)` in checks_v35. Do not edit the frozen one.
  - Currency: number + GBP/gbp/GPB/pounds/£, with or without a space → "price".
  - Duration: number + minute(s)/min/mins/hour(s), with or without a hyphen → "duration".
  - Test pairs: "8.08GBP", "37.79 GPB" ~ "66 GBP"; "28-minute" ~ "105 minutes".
  - Report how many v2.2 cluster pairs change type agreement (a count only; Step 1a stays frozen).
- **T35 `attr_counts(ed, label) -> DataFrame`** per final attribute: `n_mentions, n_dialogues, n_distinct, variety (distinct/total), one_type (all value_type_v35 equal), types`.
- **T38 `extras_by_level(ed, label, gt_levels) -> DataFrame`** per final attribute (not group): `attr_id, name, majority_L1, majority_L2, majority_L3, kind`. kind ∈ {gt_found (L1 attr found by the Q5 rule), extra_L2, extra_L3, extra_none, wrong_extra (majority is noise/wrong_entity)}. Plus `extras_table(rows)`: counts per variant × kind, with distinct attributes counted once per entity.
- **CLI `scripts/checks_v35.py`:** writes `noise_vote.csv`, `value_types.csv`, `attr_counts.csv`, `extras_by_level.csv`, `extras_table.md`.
