# wf_v3.8 duplicate columns of A s012, with and without the split pass (L2, rules v1.1)

A pair = two columns (distinct normalised output names) whose groups have the same found attribute as majority L2 label (a found attribute with k columns gives k(k-1)/2 pairs). Causes, in this order: **split_pass** = a column comes from a split part (group id `cluster/k`); **neighbourhood** = columns from different neighbourhood groups: always 0 for A, which reads one entity prompt and has no neighbourhoods; **wording** = unsplit columns whose names share a content word (entity word dropped, plural s removed), the same thing worded twice; **other** = unsplit columns whose names share no word. Same role = both columns have <= 20% of their L2-labelled mentions in the role-pair partner slot of the attribute (config/role_pairs.json).

## dev50

| row | split_pass | neighbourhood | wording | other | pairs | same role |
|---|---|---|---|---|---|---|
| A s012 | 29 | 0 | 1 | 1 | 31 | 24/31 |
| A s012 nosplit | 0 | 0 | 1 | 1 | 2 | 2/2 |

## dev50b

| row | split_pass | neighbourhood | wording | other | pairs | same role |
|---|---|---|---|---|---|---|
| A s012 | 23 | 0 | 0 | 2 | 25 | 22/25 |
| A s012 nosplit | 0 | 0 | 0 | 2 | 2 | 1/2 |

Full lists: dups_dev50.csv, dups_dev50b.csv (columns set, row, ent, attr, col_a, col_b, cause, same_role, partner shares, top values, groups).
