# wf_v3.4 scorer contract: one switch per rule (Q1–Q10), A–D re-scored (shared by workers W1–W5)

Source: `Attribute_Extraction.pdf`, section "30 Oct 2026", tasks 1–25. Plan: `C:\Users\nguye\.claude\plans\distributed-finding-nova.md`.

Hard limits:
- No pipeline LLM run.
- Do not change Step 1a, `results/graph_v22_dev50`, `results/loop1_v31`, `results/loop1_v32`, or the old scorer files (`s1a/pilot_score.py`, `pilot_verify.py`, `pilot_combine.py`, `recall.py`, `scripts/pilot_eval_v3*.py`). Import from them.
- Toy tests only (no bge-m3, GLiNER or LLM in tests).
- Venv: `C:\Users\nguye\venvs\chunking`, run from `step1a/`: `python -m pytest -q tests`.
- No commits.

## Variants (keys used everywhere)
`VARIANTS = ["A r1", "A r2", "B s0", "C s0", "C s1", "C s2", "C s012", "D s012"]`

| key | source | how (copy what `scripts/pilot_eval_v32.py` does) |
|---|---|---|
| A r1 / A r2 | `results/loop1_v31` job variant `v2`, run_tag r1 / r2 | `pilot_eval_v31._decisions(job, path, cids, split31)` |
| B s0, C s0/s1/s2 | `results/loop1_v32` nbhd jobs, seed s | `PC.decisions_b(dir32, ent, s, split)` |
| C s012 | vote of the 3 seeds | `PC.vote([...])` → (dec, vote_stats) |
| D s012 | | `PC.decisions_d(dir32, ent)` |

Each variant is also scored after `PS.name_merge(dec, mentions, entity)`: label `"<letter>+namemerge <tag>"`, as in v3.2. Attributes come from `PV.final_attributes(dec, e.mentions, e.ids, e.x, ctx.examples, entity)` with **no** left_words (v3.2 had no cue spread). Examples: `loop1_v31/examples.csv` for A, `loop1_v32/examples.csv` for the others (`pilot_eval_v31._examples`).

## W1: data bundle `s1a/v34_data.py` + `scripts/evidence_v34.py`
```python
@dataclass
class VariantOut:            # one scored response
    dec: pd.DataFrame        # decision table (decisions.csv columns)
    attrs: pd.DataFrame      # PV.final_attributes attrs
    assign: dict             # {mention_id(int): attr_id}
    parts: dict              # split parts as returned by PV.final_attributes

@dataclass
class EntityData:
    ent: str                 # train / hotel / restaurant
    entity: str              # E1 / E0 / E2
    gold_ents: list          # pilot_eval_v31.GOLD_ENTS
    cids: list               # sorted cluster ids of the entity
    mentions: pd.DataFrame   # clustered mentions of the entity: mentions.csv columns + speaker, turn_text, prev_turn
    labels: pd.DataFrame     # labels.csv rows of these clusters (old noise labels)
    ctx_a: object            # PS.Ctx with loop1_v31 examples (for A)
    ctx_r: object            # PS.Ctx with loop1_v32 examples (B, C, D)
    variants: dict           # {label: VariantOut}; labels = VARIANTS + the "+namemerge" labels
    vote_stats: dict         # C vote stats (PC.vote)
    seed_decs: dict          # {"C s0": dec, "C s1": dec, "C s2": dec} (same objects as in variants)

@dataclass
class Shared:
    e: object; docs: object; gv: object; gold_attrs: object; labels_all: pd.DataFrame; clusters: pd.DataFrame

def load_all(run, dir32, dir31) -> tuple[Shared, dict[str, EntityData]]   # keys train, hotel, restaurant
def evidence_table(data: dict[str, EntityData]) -> pd.DataFrame
```
`speaker`, `turn_text` and `prev_turn` come from the docs (`MN.load_shared`; see how `PIN.cluster_example_lines` builds "[user] previous turn, system: ... | turn: ..."). `turn_text` is the full turn.

**evidence.csv** (`results/loop1_v34/evidence.csv`): one row per clustered mention of E0/E1/E2. Columns:
- base: `ent, entity, cluster_id, mention_id, value (text), norm_value, left_word, speaker, turn_text, prev_turn, gold_attr ("none" if empty), entity_gold, old_label`;
- then for each key in VARIANTS (spaces → `_`, e.g. `C_s012`): `<k>_name, <k>_action, <k>_group (attr_id or ""), <k>_place` (the placement of the cluster's decision row).

CLI: `python scripts/evidence_v34.py --run results/graph_v22_dev50 --dir32 results/loop1_v32 --dir31 results/loop1_v31 --out results/loop1_v34`. It writes evidence.csv and attrs.csv (`variant label, ent, attr_id, name, description, clusters, source, status`).

## W2: framework `s1a/score_rules.py` + `scripts/score_v34.py`
```python
@dataclass(frozen=True)
class Rules:
    unlabeled: str = "old"      # old | exclude | noise                         (Q3)
    noise_kind: str = "old"     # old | pattern | jury                          (Q1)
    cluster_label: str = "old"  # old | 0.5 | 0.6 | 0.7                         (Q2)
    role_pairs: str = "old"     # old | config                                  (Q10)
    names: str = "old"          # old | v34                                     (Q4)
    found: str = "old"          # old | cov0 | cov10 | cov25                    (Q5)
    merge: str = "old"          # old | n10 | n20 | n30                         (Q6)
    placement: str = "old"      # old | majority                                (Q9)
    agreement: str = "old"      # old | split                                   (Q7)
    @staticmethod
    def old() -> "Rules"
    @staticmethod
    def default() -> "Rules"    # exclude, pattern, 0.6, config, v34, cov10, n20, majority, split
    @staticmethod
    def parse(setting: str) -> "Rules"   # "old" | "default" | "default,found=cov25,merge=n10" | "old,unlabeled=exclude"
```
`score_entity(ed, shared, rules, extra) -> list[dict]`: one row per variant label. `extra` holds the files read once (role pairs config, jury.csv, rated names sheet).
- **Old columns:** always computed with `PS.score_file(dec, attrs, assign, parts, ctx, empty_verification, names)` exactly as `pilot_eval_v31.score_entries` does, with no GLiNER. They are `OLD_COLS` = merge_pure, merge_frag, split_done, split_side, noise_marked, noise_kept, place_right, recall_after, p1_after, plus real_acc / noise_rub / role_acc from `PS.rubric_accuracy(old name_rubric.csv of loop1_v32)`.
- **New columns:** computed by the stage-2 functions below. Each is looked up lazily by module and function name (`importlib`); a missing function gives "n/a", so W2 can finish before stage 2. The new columns are `NEW_COLS`:
  - `noise_n, noise_marked_v, cue_n` (labels);
  - `found_n, gold_n, recall_v` (Q5; `found_n/gold_n` printed as "4/7");
  - `merge_n, merge_right, merge_prec` (Q6);
  - `place_acc, place_n, place_base` (Q9);
  - `name_right, name_base, name_acc, valid_extra, role_right, role_base` (Q4 + Q10);
  - `agree_groups, agree_noise, agree_names` (Q7; C s012 only).
- **When a rule is `old`, the matching new column copies the old value:** noise_marked_v = noise_marked, recall_v = recall_after, merge_prec = merge_pure, place_acc = place_right, name_acc = real_acc, agree_* = PC.vote agree_mean.

`scripts/score_v34.py`:
- arguments: `--run results/graph_v22_dev50 --dir32 results/loop1_v32 --dir31 results/loop1_v31 --out results/loop1_v34 --setting <s> [--sweep]`;
- writes `scores_<slug>.csv` with columns setting, ent, variant, then OLD_COLS + NEW_COLS;
- `--sweep` runs `old`, `default`, and every single alternative from default (one field changed). It writes `sweep.csv` (all rows) and `sweep.md` (one table per entity: variant × setting, showing recall "n/m", noise_marked_v, merge_prec, place_acc, name_acc).
- **Regression test** (`tests/test_score_v34_old.py`): needs real data, so mark it `@pytest.mark.slow` and skip when `results/loop1_v32/summary.md` is missing. The `old` setting must reproduce the v3.2 summary.md values of OLD_COLS for every row (A r1, B s0, C s012, D s012 and their +namemerge), to 3 decimals. Also add a CLI flag `--check-old` that runs the same comparison and prints the mismatches.

## Stage 2 functions (exact names; each file has one writer)
All take `ed: EntityData` and `rules: Rules` unless stated otherwise. Labels: `real`, `mixed`, `noise`.

**W3 `s1a/rules_labels.py`** (Q3, Q1, Q2, Q10):
- `mention_class(ed, rules, extra) -> pd.Series`, indexed by mention_id, giving one of:
  - the gold attr string (multi-class kept as "A;B"),
  - `"unlabeled"`,
  - `"noise"`,
  - `"cue"`,
  - `"real_extra"` (a real value with no gold attr),
  - `"other_entity:<Entity>"`.

  Q3: `old` keeps `unlabeled`, `exclude` keeps `unlabeled` (and purity leaves it out), `noise` turns it into `noise`. Q1 `pattern` maps the kinds of `noise_kind_of` on unlabelled mentions: question → cue; result_count / general / broken → noise; odd_format → real_extra; other_entity → `other_entity:<E>`; other → unlabeled. Q1 `jury`: the unlabelled mentions of jury-noise clusters → noise, of jury-real clusters → real_extra (jury.csv = `results/loop1_v33/jury.csv`, copied to loop1_v34).
- `noise_kind_of(value, turn_text, gold_values_other) -> str`, using general patterns only, **no dataset word lists**:
  - **question:** starts with a wh-word or "how many/much" (a closed list of English question words is allowed);
  - **result_count:** a number followed by a plural noun, or "there are/is N";
  - **general:** determiner (+ adjective) + a lowercase noun, with no digit and no capital in the raw span;
  - **broken:** starts or ends with a function word (closed English list), or cuts a word in the turn;
  - **odd_format:** a time, price, number or code shape;
  - **other_entity:** the normalised value equals a gold value of another entity (from `shared.gv`);
  - **other:** anything else.
- `cluster_labels(ed, rules, extra) -> DataFrame` with columns `cluster_id, n, n_counted, top_attr, top_share, second_attr, second_share, noise_share, label`.
  - Shares are over the counted mentions: `exclude` drops unlabeled.
  - Threshold t = 0.5 / 0.6 / 0.7: real if top_share ≥ t; noise if noise_share ≥ t (noise includes cue); else mixed.
  - `old`: label from labels.csv (gold / valid_new → real, noise → noise, other → mixed).
- `q3_tables(data)`, `q1_table(data, shared)`, `q2_table(data, settings)`, `q10_tables(data)` → DataFrames for the report:
  - Q3: counts per entity × speaker; share per cluster; 30 random examples (seed 0; 10 per entity, 5 from system turns).
  - Q1: distinct non-gold values, with n, cluster, 2 example turns, kind, a `doubtful` flag, and counts per kind × entity.
  - Q2: per-cluster shares and labels under 0.5 / 0.6 / 0.7 and old, with a `differs_from_old` flag; plus a PNG plot (matplotlib) of top_share sorted.
  - Q10: gold attrs per entity; role counts per cluster (reuse `PS.role_table`); proposed pairs, i.e. gold attributes of one entity with value-set Jaccard ≥ 0.3 and the same value shape.
- `role_pairs(path="config/role_pairs.json") -> list[tuple[str, str]]`: slot-name pairs, e.g. ("departure", "destination"), ("leave at", "arrive by"), each listing the entities it applies to. W3 writes `config/role_pairs.json`.

**W4 `s1a/rules_groups.py`** (Q5, Q6, Q9):
- `found(ed, label, rules, extra) -> DataFrame`, one row per gold attr in `ctx.train`: `attr, found, best_group, purity, coverage, case`.
  - Groups = attrs of the variant; a split part counts on its own.
  - purity = attr mentions in the group / counted group mentions (Q3 decides "counted").
  - coverage = attr mentions in the group / all clustered mentions of the attr.
  - cov0 / cov10 / cov25 = found if purity ≥ 0.6 and coverage ≥ 0 / 0.10 / 0.25.
  - case ∈ {"", "mixed_only", "spread", "tiny_pure"}.
- `merges(ed, label, rules, extra) -> DataFrame`, one row per merged attribute (≥ 2 member clusters; for D also reconcile): `attr_id, name, members, member_attrs, member_roles, noise_share, right, reason`.
  - Right if all members have the same top attr and the same role slot (role pairs from Q10), and noise_share < 0.10 / 0.20 / 0.30.
  - reason ∈ {"", "wrong_attr", "wrong_role", "noise"}.
- `placement(ed, label, rules, extra) -> dict(place_acc, place_n, place_base)`.
  - Right = the decision's placement entity equals the entity of the majority of the cluster's mentions (gold attr's entity, `entity_gold`).
  - A booking reference counts as one attribute per entity.
  - Baseline: always the current entity.
- `q5_table(...)`, `q6_table(...)`, `q9_table(data)` → report tables. Q9: per cluster, mentions whose gold attr belongs to another entity.

**W5 `s1a/rules_names.py`** (Q4, Q7, Q8):
- `name_sheet(data, old_rubric) -> DataFrame`: one row per distinct (ent, variant label, attr_id, name), with `description, majority_gold_attr, role, cluster_label, top_values, old_final, freq, valid_extra_candidate`. A valid-extra candidate is a cluster whose values are real but have no TEAR gold, such as train id, price, duration or reference, detected by value shape.
- Writes `results/loop1_v34/name_rubric_prompt.md`: the 5 labels right / too_general / wrong_role / valid_extra / wrong, each defined with 2 examples. Includes the mixed rule (right only if it matches a part with ≥ 60% of the mentions) and the "lower label wins" tie rule.
- `name_scores(ed, label, rules, extra) -> dict(name_right, name_base, name_acc, valid_extra, role_right, role_base)`.
  - base = gold attrs in `ctx.train` (the same for every variant);
  - name_right = gold attrs that have at least one group named `right` (from the rated sheet `extra["names_rated"]`);
  - role_* = the same, restricted to attrs whose slot is in a role pair.
- `order_diffs(ed) -> DataFrame`: for C s0/s1/s2, every cluster whose decision differs, typed `wording` (same gold-meaning name, different string) / `meaning` / `membership` (different cluster set in its group) / `noise` (marked in some orders, not others).
- `agreement(ed, rules, extra) -> dict(agree_groups, agree_noise, agree_names)`: per-cluster agreement across the 3 orders, averaged.
- `order_range(rows) -> DataFrame`: found_n per entity for C s0/s1/s2 and A r1/r2 under the default rules, and the range.
- `gain_verdict(rows, base="A r1") -> DataFrame`: for B s0, C s012, D s012, a gain counts if it is ≥ 2 attributes over all entities, no entity loses one, and it is larger than the order-only range.

## Report data
`scripts/score_v34.py --report-tables` writes all `q*_table` outputs as CSV/PNG to `results/loop1_v34/`. The report itself is written by the lead.
