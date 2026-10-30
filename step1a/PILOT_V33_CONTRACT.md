# wf_v3.3 Step-3 pilot contract (shared by workers W1–W4)

Goal: wf_v3.2 variant C (neighbourhood prompts + 3-order vote) plus the following, as ablations:
- measuring fixes;
- an `attribute_cue` action and a noise rule;
- role-aware examples;
- a cue-word split spread;
- carry-over of names across groups;
- a gate-only split (no noise probe, no reconcile).

Run setup:
- Step 1a is frozen: run `results/graph_v22_dev50` (spans).
- Same 3 entities, gold names, scorer metrics and placement options as v3.1/v3.2.
- `loop1_v31` and `loop1_v32` scores must not change, except the new columns (baseline, role, human noise).
- Plan: `C:\Users\nguye\.claude\plans\distributed-finding-nova.md`.

## Variants
| variant | what | new LLM jobs |
|---|---|---|
| C | v3.2 C, scored from `results/loop1_v32` (no rerun) | – |
| E | C prompts + P1 cue + P2 noise rule + P3 role-aware examples + P5 carry-over; then vote → gate → gated split (P6) with the P4 spread | 7 groups × 3 seeds = 21 |
| E1 | E without carry-over: group 0 jobs are shared with E (identical prompt); groups ≥ 1 rendered with no carry block | 4 groups × 3 = 12 |
| E2 | E without P1 and P2 (v3 instruction as in v3.2), with P3 and P5 | 21 |
| F | E on de-lexicalised prompt text, seed 0 only, with carry-over; no gate/split (names test only) | 7 |

Gate and split are reused, not rerun: E, E1 and E2 use the v3.2 gate and split responses from `results/loop1_v32/responses/` (same prompts). A cluster is split only if its gate says `coherent: false` and its split result `is_mixed` (as v3.2 `apply_gate`).

The token cost of each variant is its own entity jobs plus, for E, E1 and E2, the 31 gate jobs and the split jobs of the failed gates, as measured in v3.2.

## Folder `results/loop1_v33/`
```
prompts/<ent>_<var>_nbhd<g>_s<seed>.txt / .schema.json   entity jobs; var in e, e1, e2, f
prompts/<ent>_<var>_nbhd<g>_s<seed>.tmpl.txt             only for jobs with carry_from: text with the line
                                                          {{CARRY_OVER}} where the carry block goes
neighbourhoods.csv, examples.csv     as v3.2 (examples.csv ex ids unique per job: <cid>:<var>s<seed>e<j>)
delex_map.json                       F only: {real lowercased string: fake string}
manifest.json                        jobs (below)
prompt_stats.md                      chars, est. tokens (template + 300 tokens for carry jobs)
responses/<job>.jsonl                one llm_cache row per job (token fields as v3.2)
role_mix.csv, noise_sheet.csv        W1 outputs (Part 0)
```

Manifest job fields (the v3.2 fields, plus 2 new ones):
- v3.2 fields: `job, entity, ent, variant (e|e1|e2|f), run_tag ("s<seed>"), kind ("entity"), stage (1), nbhd, cluster_id "", prompt, schema, max_tokens, format ("v3")`;
- **`round`**: int, the group index when the job has carry-over, else 0;
- **`carry_from`**: a list of job names, the same variant and seed, groups 0..round−1; `[]` when there is no carry.

A job with `carry_from` has a `.tmpl.txt`. Its `.txt` is written on Colab by `PC.fill_carry` just before its round runs.

## P1 attribute_cue (W2 text, W3 decisions/scoring)
Added to the instruction as one paragraph after the not_attribute sentence:

`Use "attribute_cue" for clusters whose examples are questions or requests about an attribute rather than its values (what day, how many tickets, which area); it means an attribute exists but this cluster is not a column.`

Its schema stays a free string. It is a reserved name like `not_attribute`, and the example in the instruction shows one cluster with it.

How the decisions handle it:
- `pilot_verify.decisions_from_v2` maps norm_name `attribute cue` to action `attribute_cue`.
- `PV.ACTIONS` gains `attribute_cue` and `PV.MARKED` = `("not_attribute", "unsure", "attribute_cue")`. So it scores as "not a column" and counts as noise marked.
- The vote treats `attribute_cue` as its own key.
- The reports count cue clusters separately.

## P2 noise rule (W2)
Added to the instruction after the noise sentence:

`If fewer than half of a cluster's examples are real values that a database would store, choose "not_attribute" (or "attribute_cue" for questions).`

E2 has neither the P1 nor the P2 text.

## P3 role-aware examples (W2, `select_examples(..., roles=None)`)
- `roles`: a {mention_id: cue word} map from `mentions.left_word`.
- Cue sets (fixed, in `pilot_input.CUE_ROLES`):
  - start = {from, leaving, leave, depart, departing, departs, after};
  - end = {to, arrive, arriving, arrives, into, by, before}.
- If the cluster has mentions of both start and end, the first 2 picks are one start and one end mention (the most frequent value of each). The rest is the usual round-robin. k stays the same.
- It uses the word before the span only, never gold. It applies to the E/E1/E2/F entity prompts. Gate and split are unchanged (reused).

## P4 cue-word split spread (W3, `pilot_verify.final_attributes`)
For a split cluster:
- Each part's cue set = the left words of its example mentions.
- A remaining mention whose left word is in exactly one part's cue set goes to that part.
- Otherwise it goes to the nearest part centroid, as now.

The left words come from a new `mentions` column computed with `MN.left_word`, or are passed in. W3 decides; nothing is written to mentions.csv. For scoring, P4 applies to every variant, including the re-scored C, and the report states this. C's old numbers stay available with `--no-cue-spread`.

## P5 carry-over (W2 render, W3 fill)
- `PIN.render_v3(..., carry=None, cue_rule=True)`.
  - `carry` = None means no block.
  - The string `"{{CARRY_OVER}}"` writes that placeholder line.
  - `cue_rule` False gives the v3.2 instruction (E2).
- The carry block (rendered by `PC.render_carry(attrs)`, plain Python, used on Colab) reads:
```
Attributes already found in other parts of this entity (reuse the exact name and list it again in your
attributes if a cluster is the same attribute; otherwise make a new one):
- departure_station: the station the train leaves from
```
  `attrs` = [(name, description)] from the parsed responses of `carry_from`: unique by norm_name, first seen wins, `not_attribute`/`attribute_cue` excluded.
- `PC.fill_carry(out_dir, round) -> list[job]` writes `.txt` from `.tmpl.txt` for every job of that round whose parents all have parsed responses. It raises if a parent is missing. It is deterministic.
- Name merge across groups (`PS.name_merge`, as v3.2) joins the reused names.

## F de-lexicalisation (W2, `s1a/delex.py`)
- `build_map(mentions, gold_attrs)` collects the norm values of mentions whose gold attr is a name-like slot: train departure/destination, hotel/restaurant/attraction name, taxi departure/destination, train ID.
  - It also adds every `TR\d{4}` string found in the prompt texts.
  - Each value maps to a fake string: deterministic (crc32 seed), pronounceable, unique, the same length class; train IDs become `TX\d{4}`.
- `apply(text, mp)` does a case-insensitive whole-word replacement, longest key first, keeping the case pattern of the first letter.
- It is applied to the whole rendered prompt text of F, including the carry block on Colab: `fill_carry` applies the map when the job's variant is `f`.
- Scoring is by cluster id, so it needs no back-mapping. GLiNER is skipped for F.

## Part 0 measuring (W1, `s1a/pilot_score.py`)
- `placement_baseline(dec, ctx) -> (ratio, n)`: `_placement_checks` with every placement replaced by `current entity <ctx.entity>`.
  - summary.md gets `place_base` next to `place_right`.
  - The report also needs the share of rows whose placement is the current entity: `place_current`.
- `role_table(mentions, entity) -> DataFrame` with columns `entity, cluster_id, n, departure, destination, leave_at, arrive_by, role_kind (place|time|""), major_role, major_share`, counted from `gold_attr` with `SPLIT_KINDS`. It is written to `role_mix.csv`. `rubric_accuracy` role_acc keeps its definition; the report shows the table.
- `noise_sheet(mentions, labels, decisions_list, docs) -> DataFrame` with one row per cluster that is gold noise (labels.csv) **or** marked not_attribute/unsure in any of the given decision tables. Columns: `ent, entity, cluster_id, n, top_values, examples (6 lines, " || " joined), gold_label, model_marked_by, human`, where `human` is left empty.
  - Built by `scripts/noise_sheet.py` from v3.1 v2 r1, v3.2 A–D and, later, v3.3 decisions.
- `apply_human_labels(labels, sheet) -> labels` changes the label of each filled row:
  - noise → `noise`;
  - real → `valid_new` if it was noise, else unchanged;
  - mixed → `mixed`.

  A `mixed` row is excluded from the noise denominator and counted in the report. The eval uses it when `--human-noise <sheet>` is given and the sheet has filled rows.

## Combine + eval (W3)
- `PC.decisions_e(out_dir, ent, var, gate_dir) -> (DataFrame, stats)`: vote over the seeds of `var` (seeds 0..2, or seed 0 only for f), then `apply_gate` with the gate and split results from `gate_dir` (v3.2), except for F.
  - E1 jobs: group 0 comes from variant `e`, groups ≥ 1 from `e1`.
  - stats: vote agreement, ties, cue count, gate-failed, split applied.
- `scripts/pilot_eval_v33.py --run ... --dir results/loop1_v33 --dir32 results/loop1_v32 [--no-gliner] [--human-noise ...] [--no-cue-spread]` scores C (from dir32), E, E1, E2 and F, each as is and `+namemerge`. It writes the v3.2 outputs plus `place_base`, `place_current` and the cue count.
- Token table: as v3.2 `PS.token_table`, with variant costs as above (E1 = shared group-0 jobs of `e` + its own jobs).
- **W1** extends `PS.variant_jobs(jobs, variant, gate_failed)` for the variant letters `E`, `E1`, `E2` and `F`. `jobs` is the v3.3 manifest jobs plus the v3.2 gate and split jobs, which W3's eval appends before calling it.
  - E = entity jobs of variant `e` + all gate jobs + the split jobs of gate-failed clusters.
  - E1 = `e` jobs with nbhd 0 + `e1` jobs + gate + failed splits.
  - E2 = `e2` jobs + gate + failed splits.
  - F = `f` jobs only.
  - The v3.2 letters keep working.

## Colab (W4, `colab/S1A_llm_v33_colab.ipynb`)
- Copy of the v3.2 notebook (same cells 1–6, the token fields, the revision pin, the guided fallback), pointed at `loop1_v33` and branch `wf-v3.3`.
- Stage = rounds: run all round-0 jobs; then for r = 1, 2: `PC.fill_carry(O, r)`, prep, run. Then the summary cell and the push cell (`sync.sh push-results ... loop1_v33`).
- The prompt-length check (> 30000 stops) runs on each round's filled prompts.

## Ownership (one writer per file)
| Worker | Files |
|---|---|
| W1 | `s1a/pilot_score.py`, `scripts/noise_sheet.py`, `tests/test_pilot_score_v33.py` |
| W2 | `s1a/pilot_input.py`, `s1a/delex.py`, `scripts/pilot_build_v33.py`, `tests/test_pilot_input_v33.py`, `tests/test_delex.py` |
| W3 | `s1a/pilot_verify.py`, `s1a/pilot_combine.py`, `scripts/pilot_eval_v33.py`, `tests/test_pilot_combine_v33.py` (+ edits to `tests/test_pilot_verify.py`) |
| W4 | `colab/S1A_llm_v33_colab.ipynb`, `colab/README.md` (one line) |

## Tests
Toy tables only. No bge-m3, GLiNER or LLM on real data in tests. Workers do not run real data and do not commit. All existing tests must still pass: `python -m pytest -q tests` from `step1a/`, with venv `C:\Users\nguye\venvs\chunking`.
