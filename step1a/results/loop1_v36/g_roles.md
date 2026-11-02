# wf_v3.6 variant g: role examples vs gold L2 roles

g = the v3.2 C prompt with the role-aware example picker, the mixed instruction asking for `role_examples` (an attribute and its example ids per role) and an optional `role_examples` field. Two-role clusters (gold L2 roles of both slots of a pair, each >= 20%): 9, all in train (E1#0, E1#1, E1#11, E1#13, E1#21, E1#24, E1#25, E1#27, E1#3). Accuracy: each role_examples group takes the majority gold role of its examples (a tie takes none); the largest group claims a role first and a later group with a role already claimed gets none; k = examples whose gold role is their group's role, n = examples with a gold role of the pair.

| order | two-role clusters flagged mixed | with role_examples | roles told apart | role accuracy k/n | mixed flags elsewhere |
|---|---|---|---|---|---|
| g s0 | 0/9 | 0/9 | 0/0 | 0/0 (n/a) | 1/108 |
| g s1 | 1/9 | 1/9 | 0/1 | 1/3 (0.333) | 3/108 |
| g s2 | 4/9 | 4/9 | 4/4 | 15/16 (0.938) | 1/108 |
| all 3 orders | 5/27 | 5/27 | 4/5 | 16/19 (0.842) | |

## Two-role clusters (per order: mixed / role_examples groups / k/n)

| cluster | roles | s0 | s1 | s2 |
|---|---|---|---|---|
| E1#0 | departure vs destination | not mixed / 0 groups / 0/0 | not mixed / 0 groups / 0/0 | mixed / 2 groups / 6/7 |
| E1#1 | leave at vs arrive by | not mixed / 0 groups / 0/0 | mixed / 2 groups / 1/3 | not mixed / 0 groups / 0/0 |
| E1#3 | departure vs destination | not mixed / 0 groups / 0/0 | not mixed / 0 groups / 0/0 | not mixed / 0 groups / 0/0 |
| E1#11 | departure vs destination | not mixed / 0 groups / 0/0 | not mixed / 0 groups / 0/0 | not mixed / 0 groups / 0/0 |
| E1#13 | leave at vs arrive by | not mixed / 0 groups / 0/0 | not mixed / 0 groups / 0/0 | not mixed / 0 groups / 0/0 |
| E1#21 | departure vs destination | not mixed / 0 groups / 0/0 | not mixed / 0 groups / 0/0 | mixed / 2 groups / 4/4 |
| E1#24 | departure vs destination | not mixed / 0 groups / 0/0 | not mixed / 0 groups / 0/0 | not mixed / 0 groups / 0/0 |
| E1#25 | departure vs destination | not mixed / 0 groups / 0/0 | not mixed / 0 groups / 0/0 | mixed / 2 groups / 2/2 |
| E1#27 | departure vs destination | not mixed / 0 groups / 0/0 | not mixed / 0 groups / 0/0 | mixed / 2 groups / 3/3 |

## Role guard on g's cross-group name merge

`role_guard.forbidden_merge` on the cluster pairs that `PS.name_merge` (same normalized name and placement, as in v3.2 C+namemerge) newly joins across the responses; text = attribute name + role. A merge across a role pair (departure / destination, leave at / arrive by, location / address) would be blocked. There is no reconcile job in this batch, so only the name merge is checked; `own` = the same check on the merges inside each response.

| order | name-merge pairs examined | blocked | own merges blocked |
|---|---|---|---|
| g s0 | 32 | 0 | 0 |
| g s1 | 12 | 0 | 0 |
| g s2 | 10 | 0 | 0 |
