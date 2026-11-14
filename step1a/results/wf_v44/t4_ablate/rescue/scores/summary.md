# wf_v4.4 Step 3 (Llama-3.1-8B): names variant + boosters

| set | row | found | columns | columns per found | dup columns | wrong columns | review edits | guard |
|---|---|---|---|---|---|---|---|---|
| dev50 | A s012 + split pass | 30/40 (8+10+12) | 74 | 2.367 | 41 | 8 | 49 | FAIL |
| dev50 | A s012 + reconcile (both orders) | 30/40 (8+10+12) | 59 | 2.1 | 33 | 4 | 37 | FAIL |
| dev50 | Final v3.9 | 30/40 (8+10+12) | 55 | 1.967 | 29 | 4 | 33 | FAIL |
| dev50b | A s012 + split pass | 29/41 (8+11+10) | 77 | 2.448 | 42 | 7 | 49 | FAIL |
| dev50b | A s012 + reconcile (both orders) | 29/41 (8+11+10) | 65 | 2.207 | 35 | 6 | 41 | FAIL |
| dev50b | Final v3.9 | 29/41 (8+11+10) | 63 | 2.207 | 35 | 6 | 41 | FAIL |

## Stage facts

- dev50 train: columns_split_pass 22, parts 21, reconcile_agree [15, 21], reconcile_joined_agreed 15, parts_moved_mentions 249, dup_joins_order0 [6, 6], dup_joins_order1 [7, 7], dup_same_groups_both 0, dup_on_agreed_columns 0, dup_role_pair_blocked 0, dup_joins_kept 0, columns_final 18, mentions_in_columns 306, dropped_clusters 6, dropped_mentions 44
- dev50 hotel: columns_split_pass 26, parts 25, reconcile_agree [20, 25], reconcile_joined_agreed 19, parts_moved_mentions 98, dup_joins_order0 [8, 8], dup_joins_order1 [6, 6], dup_same_groups_both 1, dup_on_agreed_columns 1, dup_role_pair_blocked 0, dup_joins_kept 1, columns_final 20, mentions_in_columns 163, dropped_clusters 7, dropped_mentions 37
- dev50 restaurant: columns_split_pass 26, parts 27, reconcile_agree [23, 27], reconcile_joined_agreed 22, parts_moved_mentions 159, dup_joins_order0 [7, 7], dup_joins_order1 [5, 5], dup_same_groups_both 3, dup_on_agreed_columns 3, dup_role_pair_blocked 0, dup_joins_kept 3, columns_final 17, mentions_in_columns 292, dropped_clusters 7, dropped_mentions 12
- dev50b train: columns_split_pass 20, parts 9, reconcile_agree [7, 9], reconcile_joined_agreed 7, parts_moved_mentions 96, dup_joins_order0 [6, 4], dup_joins_order1 [5, 4], dup_same_groups_both 1, dup_on_agreed_columns 1, dup_role_pair_blocked 0, dup_joins_kept 1, columns_final 17, mentions_in_columns 158, dropped_clusters 5, dropped_mentions 23
- dev50b hotel: columns_split_pass 30, parts 31, reconcile_agree [22, 31], reconcile_joined_agreed 22, parts_moved_mentions 128, dup_joins_order0 [6, 6], dup_joins_order1 [6, 6], dup_same_groups_both 1, dup_on_agreed_columns 1, dup_role_pair_blocked 0, dup_joins_kept 1, columns_final 23, mentions_in_columns 224, dropped_clusters 3, dropped_mentions 14
- dev50b restaurant: columns_split_pass 27, parts 25, reconcile_agree [18, 25], reconcile_joined_agreed 17, parts_moved_mentions 83, dup_joins_order0 [11, 11], dup_joins_order1 [8, 8], dup_same_groups_both 0, dup_on_agreed_columns 0, dup_role_pair_blocked 0, dup_joins_kept 0, columns_final 23, mentions_in_columns 221, dropped_clusters 8, dropped_mentions 14

## Calls

New calls 334, prompt tokens 242,532, output tokens 14,281, largest prompt 3,026; parse errors 0, cut off (finish length) 0. Reused A answers (not rerun): {'calls': 0, 'errors': 0, 'length': 0}.

- dupcheck_rc: calls 12, prompt_tokens 7245, output_tokens 2849, max_prompt_tokens 1076, errors 0, length 0
- names: calls 46, prompt_tokens 88375, output_tokens 2258, max_prompt_tokens 3026, errors 0, length 0
- reconcile: calls 276, prompt_tokens 146912, output_tokens 9174, max_prompt_tokens 676, errors 0, length 0

## A answers (the vote's input)

18 answers; with parse errors 0; cut off 0; declared names no cluster uses 0; names used but never declared 0; `_end`-style names 0.

## Calls per stage (v4.4)

- dupcheck: calls 12, prompt_tokens 7245, output_tokens 2849, retried 1, job_seconds 17.36, guided_parse_rate 0.917
- merge_q: calls 30, prompt_tokens 9820, output_tokens 210, retried 0, job_seconds 0.6, guided_parse_rate 1.0
- names: calls 46, prompt_tokens 88375, output_tokens 2258, retried 0, job_seconds 7.36, guided_parse_rate 1.0
- split: calls 54, prompt_tokens 58760, output_tokens 13663, retried 0, job_seconds 10.31, guided_parse_rate 1.0
- reconcile: calls 276, prompt_tokens 146912, output_tokens 9174, retried 0, job_seconds 8.68, guided_parse_rate 1.0
- total: calls 418, prompt_tokens 311112, output_tokens 28154, retried 1, job_seconds 44.31, guided_parse_rate 0.998

## Boosters

```json
{
 "rescue": {
  "not_attribute_cluster_orders": 36,
  "asked": 0,
  "yes": 0,
  "no": 0,
  "unparsed": 0,
  "names_asked": 0,
  "named": 0
 },
 "merge": {
  "pairs_asked": 30,
  "yes": 5,
  "no": 25,
  "unparsed": 0,
  "merged": 5
 },
 "by_set": {
  "dev50": {
   "rescue_asked": 0,
   "rescue_yes": 0,
   "rescue_named": 0,
   "merge_pairs_asked": 18,
   "merge_yes": 5,
   "merged": 5
  },
  "dev50b": {
   "rescue_asked": 0,
   "rescue_yes": 0,
   "rescue_named": 0,
   "merge_pairs_asked": 12,
   "merge_yes": 0,
   "merged": 0
  }
 }
}
```
