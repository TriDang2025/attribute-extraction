# wf_v4.3 U0: frozen Step 3 on Llama-3.1-8B option B A answers

| set | row | found | columns | columns per found | dup columns | wrong columns | review edits | guard |
|---|---|---|---|---|---|---|---|---|
| dev50 | A s012 + split pass | 29/40 (9+11+9) | 89 | 2.345 | 39 | 14 | 53 | FAIL |
| dev50 | A s012 + reconcile (both orders) | 29/40 (9+11+9) | 71 | 1.966 | 28 | 11 | 39 | FAIL |
| dev50 | Final v3.9 | 29/40 (9+11+9) | 70 | 1.931 | 27 | 11 | 38 | FAIL |
| dev50b | A s012 + split pass | 24/41 (5+9+10) | 87 | 2.5 | 36 | 9 | 45 | FAIL |
| dev50b | A s012 + reconcile (both orders) | 24/41 (5+9+10) | 73 | 2.125 | 27 | 6 | 33 | FAIL |
| dev50b | Final v3.9 | 24/41 (5+9+10) | 69 | 2.083 | 26 | 6 | 32 | FAIL |

## Stage facts

- dev50 train: columns_split_pass 30, parts 22, reconcile_agree [15, 22], reconcile_joined_agreed 15, parts_moved_mentions 149, dup_joins_order0 [6, 5], dup_joins_order1 [9, 9], dup_same_groups_both 1, dup_on_agreed_columns 1, dup_role_pair_blocked 0, dup_joins_kept 1, columns_final 23, mentions_in_columns 332, dropped_clusters 6, dropped_mentions 18
- dev50 hotel: columns_split_pass 28, parts 21, reconcile_agree [13, 21], reconcile_joined_agreed 12, parts_moved_mentions 64, dup_joins_order0 [5, 5], dup_joins_order1 [9, 9], dup_same_groups_both 0, dup_on_agreed_columns 0, dup_role_pair_blocked 0, dup_joins_kept 0, columns_final 21, mentions_in_columns 195, dropped_clusters 5, dropped_mentions 5
- dev50 restaurant: columns_split_pass 31, parts 26, reconcile_agree [17, 26], reconcile_joined_agreed 16, parts_moved_mentions 121, dup_joins_order0 [17, 17], dup_joins_order1 [8, 8], dup_same_groups_both 0, dup_on_agreed_columns 0, dup_role_pair_blocked 0, dup_joins_kept 0, columns_final 26, mentions_in_columns 302, dropped_clusters 2, dropped_mentions 2
- dev50b train: columns_split_pass 24, parts 7, reconcile_agree [7, 7], reconcile_joined_agreed 5, parts_moved_mentions 67, dup_joins_order0 [4, 3], dup_joins_order1 [4, 3], dup_same_groups_both 3, dup_on_agreed_columns 3, dup_role_pair_blocked 0, dup_joins_kept 3, columns_final 19, mentions_in_columns 180, dropped_clusters 1, dropped_mentions 1
- dev50b hotel: columns_split_pass 41, parts 36, reconcile_agree [21, 36], reconcile_joined_agreed 21, parts_moved_mentions 114, dup_joins_order0 [17, 17], dup_joins_order1 [12, 12], dup_same_groups_both 0, dup_on_agreed_columns 0, dup_role_pair_blocked 0, dup_joins_kept 0, columns_final 30, mentions_in_columns 236, dropped_clusters 1, dropped_mentions 2
- dev50b restaurant: columns_split_pass 22, parts 17, reconcile_agree [14, 17], reconcile_joined_agreed 14, parts_moved_mentions 110, dup_joins_order0 [5, 5], dup_joins_order1 [2, 2], dup_same_groups_both 1, dup_on_agreed_columns 1, dup_role_pair_blocked 0, dup_joins_kept 1, columns_final 17, mentions_in_columns 222, dropped_clusters 11, dropped_mentions 13

## Calls

New calls 324, prompt tokens 249,166, output tokens 44,534, largest prompt 2,574; parse errors 41, cut off (finish length) 0. Reused A answers (not rerun): {'calls': 18, 'errors': 3, 'length': 0}.

- dupcheck_rc: calls 12, prompt_tokens 8634, output_tokens 2393, max_prompt_tokens 1570, errors 0, length 0
- split: calls 54, prompt_tokens 100972, output_tokens 33431, max_prompt_tokens 2574, errors 41, length 0
- reconcile: calls 258, prompt_tokens 139560, output_tokens 8710, max_prompt_tokens 693, errors 0, length 0

## A answers (the vote's input)

18 answers; with parse errors 3; cut off 0; declared names no cluster uses 216; names used but never declared 7; `_end`-style names 43.
