# Scoring rules v1.1 (2026-11-02)

Setting `v1.1` in `s1a/score_rules.py` (`Rules.v1_1()`, `Rules.parse("v1.1")`), wf_v3.7: rules v1 (`RULES_V1.md`, setting `default`, unchanged and still reachable) with one change. Every v3.7 table uses `v1.1`. Switch values in brackets; `old` reproduces the v3.2 scorer (`score_v34.py --check-old`, 0 mismatches).

## Change from v1
- **Noise set:** `noise_kind=mwoz` replaces `noise_kind=pattern` as the only noise measure. A mention is noise iff it is a choice mention, or it has no label at the GT level and is not a request mention (a question phrase for a requested slot); a request mention with no label is neither noise nor an attribute. A cluster is noise when >= 60% of its counted mentions are noise (the Q2 rule). Reason: the noise set comes from MultiWOZ alone, not from a model or a word list; 13 clusters at L2. With this switch every mention is counted (the `unlabeled` rule does not apply: an unlabelled mention is noise or a request, never "unlabeled"; the v1 rules `unlabeled=exclude`, `other_entity=wrong_entity` and the noise patterns have no effect under mwoz; a values-of-another-entity mention with no L2 label is noise like any other).
- Everything else is as in v1 (below), including found / merge / names / placement / order rules.

The text below is `RULES_V1.md` with the noise line changed.

## Ground truth
- **Levels:** L1 = TEAR gold (user goal); L2 = L1 + MultiWOZ 2.2 schema slots (span match to the 2.2 span labels); L3 = L2 + MultiWOZ 2.4 DB columns (exact value match, same domain, column not id-like, value in ≤ 30% of rows). Every score is reported per level [`gt` = L1/L2/L3]. Reason: TEAR gold misses most system-offered values (L1 labels 491/963 mentions (0.51), L2 815/963 (0.85)).
- **Base:** the gold attribute set of an entity at a level = that level's attributes of the entity that occur in dev50 mentions.
- **choice** (number of results) is noise at every level, never an attribute. Reason: it is labelled in MultiWOZ but not in the official schema.
- **Request acts** (MultiWOZ `*-Request`) are the GT for `attribute_cue` decisions (cue request / cue clusters).
- **Booking acts** (`Booking-*`) belong to the dialogue's current entity.
- **Invalid runs** (`config/invalid_runs.json`) are left out of every table and of the order range: restaurant A r2 (6 parse errors).

## Mentions and cluster labels
- Unlabelled mentions are left out of purity; their count is reported [`unlabeled=exclude`].
- Noise kinds: MultiWOZ-only (see "Change from v1"): choice, or no L2 label and no request act → noise; a request mention with no label is not counted as noise [`noise_kind=mwoz`]. (v1: general patterns [`noise_kind=pattern`].)
- Real values without gold count as real (valid extra).
- Values of another entity get the class `wrong_entity`: not real, not noise, counted in n. Values frequent across entities (gold in ≥ 2 entities or in ≥ 20% of dev50 dialogues, e.g. "cambridge") keep their old class [`other_entity=wrong_entity`].
- Cluster label: real if top share ≥ 0.6, noise if noise share ≥ 0.6, else mixed [`cluster_label=0.6`]. A cluster with no counted mention is `unknown`. It stays out of every base, and its count is reported [`unknown=out`].
- Role pairs come from `config/role_pairs.json` [`role_pairs=config`].

## Groups
- Found: purity ≥ 0.6 and coverage ≥ 10%; a split part counts on its own [`found=cov10`]. A group marked not_attribute (any `PV.MARKED` status) never counts as found [`marked_found=skip`].
- Merge: right if all judged members have the same top attribute, the same role slot, and noise share < 20% [`merge=n20`]. Members with no gold top attribute are left out. A merge is judged only when ≥ 2 members have gold; the unjudged count is reported [`merge_gold=min2`].
- Placement: right = the entity of the majority of the cluster's mentions [`placement=majority`]. It is reported but not used in any verdict.

## Names and orders
- Names: 5 labels (right / too general / wrong role / valid extra / wrong), from 2 blind LLM raters; the lower label wins. Only right counts; the base is the gold attributes of the entity [`names=v34`]. At L2/L3 a valid-extra group whose level majority is a non-L1 attribute counts as right (approximation).
- Order agreement is reported separately for groups, noise and names [`agreement=split`].

## Reporting
- Every table shows counts: "k/n (share)".
- Noise marked is pooled over entities (13 noise clusters at L2), with target ≥ 0.70 pooled. It replaces the per-entity "70% noise marked" target, because each entity has only 3–5 noise clusters.
- Gain verdict (Q8): a gain counts if it is ≥ 2 attributes over all entities, no entity loses one, and it is larger than the order-only range (invalid runs excluded).

## Exit bar (T7, wf_v3.7)
Step 3 is frozen as v1 when all of these hold on dev50 (and are confirmed on dev50b, which is never tuned on):
- (a) it finds >= 90% of the attributes that Step 1a makes recoverable (ceiling: some single cluster passes the found rule, `s1a/ceiling_v37.py`);
- (b) found attributes change by <= 1 across orders (range of the totals over the 3 orders);
- (c) <= 1.2 columns per found attribute (`s1a/columns_v37.py`: distinct output attribute names per found attribute);
- (d) >= 9 of the 13 noise clusters caught, with >= 70% of the noise marks right;
- (e) it beats the LLM-only baseline.
Where A (3 orders) and A s012 stand: `results/loop1_v37/exit_bar.md` ((e) pending the baseline). The function takes the run and GT directories (`scripts/score_v37.py: exit_bar_from_dirs`), so it can be rerun on dev50b and with the baseline.
