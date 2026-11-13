# wf_v4.3 U2: Step 3 v4.3 (names only, batches of 5) on Llama-3.1-8B

| set | row | found | columns | columns per found | dup columns | wrong columns | review edits | guard |
|---|---|---|---|---|---|---|---|---|
| dev50 | A s012 + split pass | 30/40 (8+11+11) | 75 | 2.033 | 31 | 8 | 39 | FAIL |
| dev50 | A s012 + reconcile (both orders) | 30/40 (8+11+11) | 60 | 1.8 | 24 | 7 | 31 | FAIL |
| dev50 | Final v3.9 | 30/40 (8+11+11) | 57 | 1.733 | 22 | 6 | 28 | FAIL |
| dev50b | A s012 + split pass | 27/41 (6+11+10) | 92 | 2.444 | 39 | 11 | 50 | FAIL |
| dev50b | A s012 + reconcile (both orders) | 27/41 (6+11+10) | 76 | 2.259 | 34 | 9 | 43 | FAIL |
| dev50b | Final v3.9 | 27/41 (6+11+10) | 71 | 2.222 | 33 | 9 | 42 | FAIL |

## Stage facts

- dev50 train: columns_split_pass 20, parts 13, reconcile_agree [9, 13], reconcile_joined_agreed 9, parts_moved_mentions 94, dup_joins_order0 [8, 8], dup_joins_order1 [6, 6], dup_same_groups_both 1, dup_on_agreed_columns 1, dup_role_pair_blocked 0, dup_joins_kept 1, columns_final 15, mentions_in_columns 288, dropped_clusters 12, dropped_mentions 62
- dev50 hotel: columns_split_pass 25, parts 17, reconcile_agree [13, 17], reconcile_joined_agreed 12, parts_moved_mentions 85, dup_joins_order0 [8, 8], dup_joins_order1 [5, 5], dup_same_groups_both 2, dup_on_agreed_columns 2, dup_role_pair_blocked 0, dup_joins_kept 2, columns_final 16, mentions_in_columns 170, dropped_clusters 11, dropped_mentions 30
- dev50 restaurant: columns_split_pass 30, parts 21, reconcile_agree [16, 21], reconcile_joined_agreed 15, parts_moved_mentions 108, dup_joins_order0 [1, 1], dup_joins_order1 [8, 8], dup_same_groups_both 0, dup_on_agreed_columns 0, dup_role_pair_blocked 0, dup_joins_kept 0, columns_final 25, mentions_in_columns 258, dropped_clusters 9, dropped_mentions 46
- dev50b train: columns_split_pass 24, parts 7, reconcile_agree [7, 7], reconcile_joined_agreed 7, parts_moved_mentions 100, dup_joins_order0 [5, 4], dup_joins_order1 [5, 4], dup_same_groups_both 3, dup_on_agreed_columns 3, dup_role_pair_blocked 0, dup_joins_kept 3, columns_final 16, mentions_in_columns 170, dropped_clusters 3, dropped_mentions 11
- dev50b hotel: columns_split_pass 41, parts 34, reconcile_agree [22, 34], reconcile_joined_agreed 21, parts_moved_mentions 96, dup_joins_order0 [22, 22], dup_joins_order1 [11, 11], dup_same_groups_both 0, dup_on_agreed_columns 0, dup_role_pair_blocked 0, dup_joins_kept 0, columns_final 33, mentions_in_columns 206, dropped_clusters 11, dropped_mentions 32
- dev50b restaurant: columns_split_pass 27, parts 17, reconcile_agree [14, 17], reconcile_joined_agreed 14, parts_moved_mentions 110, dup_joins_order0 [8, 8], dup_joins_order1 [11, 11], dup_same_groups_both 2, dup_on_agreed_columns 2, dup_role_pair_blocked 0, dup_joins_kept 2, columns_final 20, mentions_in_columns 209, dropped_clusters 13, dropped_mentions 26

## Calls

New calls 422, prompt tokens 755,941, output tokens 52,030, largest prompt 6,554; parse errors 42, cut off (finish length) 1. Reused A answers (not rerun): {'calls': 0, 'errors': 0, 'length': 0}.

- dupcheck_rc: calls 12, prompt_tokens 7931, output_tokens 4400, max_prompt_tokens 992, errors 0, length 0
- names: calls 138, prompt_tokens 530250, output_tokens 7717, max_prompt_tokens 6554, errors 1, length 1
- split: calls 54, prompt_tokens 100972, output_tokens 32536, max_prompt_tokens 2574, errors 41, length 0
- reconcile: calls 218, prompt_tokens 116788, output_tokens 7377, max_prompt_tokens 681, errors 0, length 0

## A answers (the vote's input)

18 answers; with parse errors 3; cut off 0; declared names no cluster uses 0; names used but never declared 0; `_end`-style names 0.

## Names stage

18 (set, entity, order) answers; batches 138, valid 135; names merged across batches 53; names no cluster uses 0; `_end`-style names 0; error lines 4.
