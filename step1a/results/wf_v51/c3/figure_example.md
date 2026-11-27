# wf_v5.1 C3 figure: one train time cluster, v5.0 vs v5.1 (real Step 3 + context split, no rename)

Set dev50, entity train_info. Roles from the gold, used only to describe. Snippets: the value is in [ ].

## v5.0 Step 3 (before the context split): column "time str" (#18, 61 mentions): 37 Train leave at + 18 Train arrive by (two roles mixed)

- as Train leave at: `... is the one that leaves at [7:16] and it costs ...`
- as Train arrive by: `... leaves at 21:16 and arrives by [22:35] . ...`

## v5.1 (Step 3 + context split): the columns of this entity that hold these roles

- column "time" (#17, 54 mentions): 52 Train leave at, 0 Train arrive by
  - `... and would like to leave after [12:15] , please.`
  - `... depart from birmingham new street after [14:45] .`
- column "time str" (#18, 100 mentions): 4 Train leave at, 31 Train arrive by
  - `[TR4202] is the one ...`
  - `... by 16:55 and TR6838 arrives by [17:55] . ...`

(v5.1 names are the Step 3 names of the parts: no rename ran. The separation comes from the context split, as in v5.0.)

Columns of this entity that hold the two roles, by variant:

- v5.0: time str #18 (58: 52 Train leave at / 0 Train arrive by); time #16 (38: 4 Train leave at / 31 Train arrive by)
- v5.1 Step 3 (no split): time #17 (57: 37 Train leave at / 18 Train arrive by); time str #18 (97: 19 Train leave at / 13 Train arrive by)
- v5.1 Step 3 + split: time #17 (54: 52 Train leave at / 0 Train arrive by); time str #18 (100: 4 Train leave at / 31 Train arrive by)
