# Scoring rules v1.3 (2026-11-05)

wf_v3.9: rules v1.2 (`RULES_V1_2.md`, unchanged and still reachable) plus the three changes below (diary 3 Nov, tasks 1–2). They were written before any rescoring. Old and new numbers are shown side by side for every v3.8 row. Everything else (GT levels, noise set, found / merge / names rules, recall guard, verdict rule v0, exit bar) is as in v1.2.

## 1. Role-pure columns (task 1)
- **Role-pair attributes:** the L2 slots that form a role pair, departure / destination and leave at / arrive by (`pilot_score.ROLE_SLOTS`, the pairs of `rules_groups._pairs`).
- **Role mention:** a mention whose L2 gold class is a role-pair attribute.
- **Role column:** a final column with at least one role mention. Every other column is left out.
- **Role-pure column:** at least 80% of its role mentions hold one role (the same slot).
- **Score:** role-pure columns / role columns, pooled over the entities of a set. Role-correct (one rightly named group per role attribute, v3.7) is still reported next to it.

Reason: role-correct saturates. It needs only one right group per attribute, so a second, mixed group is never penalised. Role-pure counts every column. Known limit: a column with one stray role mention counts as a role column, and it is pure trivially.

## 2a. Question clusters marked noise (task 2a)
- **Question cluster:** at least 60% of its counted mentions are request mentions (class `cue` or `request` of `rules_labels.mention_class`: a question phrase in a turn with a request act, as in the mwoz noise set of v3.6). The 60% is the Q2 cluster rule.
- **Rule:** when the variant's output has no `attribute_cue` label (A and A s012 have none), a question cluster marked noise counts as a right mark. A variant that has the `attribute_cue` label is scored as before: a question cluster is right only when it is marked `attribute_cue`.

Reason: A cannot say "question", so marking a question as noise is the best answer A can give. Before v1.3 it counted as a false noise mark.

## 2b. Another domain's values marked noise (task 2b)
- **Other-domain cluster:** at least 60% of its counted mentions are other-entity mentions (class `other_entity:<Entity>` or `wrong_entity`).
- **Rule:** when an other-domain cluster is marked noise, it is counted as **wrong entity, dropped**, in its own column. It is taken out of the noise marks (marks right / marks n). Noise caught (the denominator is the mwoz noise clusters) is unchanged.

**Amendment, 2026-11-05, made while implementing and before any result was read:** under `noise_kind=mwoz`, `mention_class` gives only the gold label, `noise` or `request`. The `cue`, `wrong_entity` and `other_entity:*` classes never occur, so two definitions change:
- A question mention is a `request` mention.
- An other-entity mention is a mention with an L2 label whose `entity_gold` is not the column's entity. Taxi counts as the entity's own for restaurant.
- Rule 2b is checked before 2a. At 60% the two cannot overlap.

Reason: dropping another domain's values is the right action for this entity's schema, but it is not noise. A separate count keeps both facts visible.
