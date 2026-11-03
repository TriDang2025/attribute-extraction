# Scoring rules v1.2 (2026-11-03)

wf_v3.8: rules v1.1 (`RULES_V1_1.md`, unchanged and still reachable) plus the recall guard and verdict rule v0 below. Both were written before any v3.8 result existed. Everything else (GT levels, noise set, found / merge / names rules, exit bar) is as in v1.1.

## Recall guard (diary 2 Nov, task 2)
A precision change is kept only if, on **both** sets, its vote finds no fewer L2 attributes than A s012 on Step 1a v2.2 in **any** entity:

| set | train | hotel | restaurant | total |
|---|---|---|---|---|
| dev50 | 8 | 12 | 11 | 31/40 |
| dev50b | 8 | 10 | 11 | 29/41 |

Reason: v3.8 works on precision (duplicate and wrong columns); a change that buys precision by losing attributes is not wanted. Per entity, not only the total, so a gain in one entity cannot hide a loss in another. The precision dashboard marks every row pass / fail.

## Verdict rule v0 (diary 2 Nov, task 10)
Each final column gets an evidence card: support (share of its own examples that fit, T32), neighbour fit (share of its 2 nearest columns' examples that fit, T33), and the counting checks (T35: mentions, dialogues, distinct values, one value type). The verdict, checked in this order:
1. **noise** if support < 0.4;
2. **too general or mixed roles** if neighbour fit > 0.5;
3. **real** if support >= 0.7 and neighbour fit <= 0.3;
4. **unsure** otherwise.

A column whose neighbour that fits is its role partner (from the method's own names and role fields) is flagged **mixed roles**, not too general. Nothing is deleted: rejected columns stay in the table. The checker becomes a filter only if it rejects at least half of the wrong columns and the recall guard passes; otherwise it is a flag for the final review (task 11).
