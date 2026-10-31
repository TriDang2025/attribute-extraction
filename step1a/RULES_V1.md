# Scoring rules v1 (frozen 2026-10-31)

Setting `default` in `s1a/score_rules.py` (`Rules.default()`), wf_v3.5. Later changes get a new version (v2, …) with a reason line. Switch values in brackets; `old` reproduces the v3.2 scorer (`score_v34.py --check-old`, 0 mismatches).

## Ground truth
- **Levels:** L1 = TEAR gold (user goal); L2 = L1 + MultiWOZ 2.2 schema slots (span match to the 2.2 span labels); L3 = L2 + MultiWOZ 2.4 DB columns (exact value match, same domain, column not id-like, value in ≤ 30% of rows). Every score is reported per level [`gt` = L1/L2/L3]. Reason: TEAR gold misses most system-offered values (L1 labels 491/963 mentions (0.51), L2 815/963 (0.85)).
- **Base:** the gold attribute set of an entity at a level = that level's attributes of the entity that occur in dev50 mentions.
- **choice** (number of results) is noise at every level, never an attribute. Reason: it is labelled in MultiWOZ but not in the official schema.
- **Request acts** (MultiWOZ `*-Request`) are the GT for `attribute_cue` decisions (cue request / cue clusters).
- **Booking acts** (`Booking-*`) belong to the dialogue's current entity.
- **Invalid runs** (`config/invalid_runs.json`) are left out of every table and of the order range: restaurant A r2 (6 parse errors).

## Mentions and cluster labels
- Unlabelled mentions are left out of purity; their count is reported [`unlabeled=exclude`].
- Noise kinds by general patterns: question → cue; result count, general word, broken span → noise; odd format → real extra; "other" stays unknown, no word list [`noise_kind=pattern`].
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
- Noise marked is pooled over entities, with target ≥ 0.70 pooled. It replaces the per-entity "70% noise marked" target, because each entity has only 3–5 noise clusters.
- Gain verdict (Q8): a gain counts if it is ≥ 2 attributes over all entities, no entity loses one, and it is larger than the order-only range (invalid runs excluded).
