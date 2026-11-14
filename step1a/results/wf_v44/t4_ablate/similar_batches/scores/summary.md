# wf_v4.4 Step 3 (Llama-3.1-8B): names variant + boosters

| set | row | found | columns | columns per found | dup columns | wrong columns | review edits | guard |
|---|---|---|---|---|---|---|---|---|
| dev50 | A s012 + split pass | 32/40 (8+11+13) | 76 | 2.281 | 41 | 6 | 47 | FAIL |
| dev50 | A s012 + reconcile (both orders) | 32/40 (8+11+13) | 66 | 2.094 | 35 | 5 | 40 | FAIL |
| dev50 | Final v3.9 | 32/40 (8+11+13) | 62 | 2.062 | 34 | 5 | 39 | FAIL |
| dev50b | A s012 + split pass | 26/41 (7+9+10) | 82 | 2.615 | 42 | 8 | 50 | FAIL |
| dev50b | A s012 + reconcile (both orders) | 26/41 (7+9+10) | 64 | 2.115 | 29 | 8 | 37 | FAIL |
| dev50b | Final v3.9 | 26/41 (7+9+10) | 62 | 2.077 | 28 | 7 | 35 | FAIL |

## Stage facts

- dev50 train: columns_split_pass 22, parts 23, reconcile_agree [15, 23], reconcile_joined_agreed 15, parts_moved_mentions 259, dup_joins_order0 [13, 13], dup_joins_order1 [7, 7], dup_same_groups_both 0, dup_on_agreed_columns 0, dup_role_pair_blocked 0, dup_joins_kept 0, columns_final 20, mentions_in_columns 316, dropped_clusters 7, dropped_mentions 34
- dev50 hotel: columns_split_pass 25, parts 23, reconcile_agree [18, 23], reconcile_joined_agreed 17, parts_moved_mentions 98, dup_joins_order0 [7, 7], dup_joins_order1 [7, 7], dup_same_groups_both 1, dup_on_agreed_columns 1, dup_role_pair_blocked 0, dup_joins_kept 1, columns_final 19, mentions_in_columns 185, dropped_clusters 5, dropped_mentions 15
- dev50 restaurant: columns_split_pass 29, parts 24, reconcile_agree [17, 24], reconcile_joined_agreed 16, parts_moved_mentions 116, dup_joins_order0 [9, 9], dup_joins_order1 [6, 6], dup_same_groups_both 3, dup_on_agreed_columns 3, dup_role_pair_blocked 0, dup_joins_kept 3, columns_final 23, mentions_in_columns 273, dropped_clusters 5, dropped_mentions 31
- dev50b train: columns_split_pass 22, parts 11, reconcile_agree [9, 11], reconcile_joined_agreed 9, parts_moved_mentions 104, dup_joins_order0 [8, 8], dup_joins_order1 [7, 7], dup_same_groups_both 2, dup_on_agreed_columns 2, dup_role_pair_blocked 0, dup_joins_kept 2, columns_final 17, mentions_in_columns 175, dropped_clusters 2, dropped_mentions 6
- dev50b hotel: columns_split_pass 33, parts 34, reconcile_agree [26, 34], reconcile_joined_agreed 26, parts_moved_mentions 159, dup_joins_order0 [1, 1], dup_joins_order1 [9, 9], dup_same_groups_both 0, dup_on_agreed_columns 0, dup_role_pair_blocked 0, dup_joins_kept 0, columns_final 23, mentions_in_columns 229, dropped_clusters 3, dropped_mentions 9
- dev50b restaurant: columns_split_pass 27, parts 25, reconcile_agree [17, 25], reconcile_joined_agreed 16, parts_moved_mentions 66, dup_joins_order0 [1, 1], dup_joins_order1 [4, 4], dup_same_groups_both 0, dup_on_agreed_columns 0, dup_role_pair_blocked 0, dup_joins_kept 0, columns_final 22, mentions_in_columns 218, dropped_clusters 7, dropped_mentions 17

## Calls

New calls 338, prompt tokens 244,210, output tokens 13,186, largest prompt 3,277; parse errors 0, cut off (finish length) 0. Reused A answers (not rerun): {'calls': 0, 'errors': 0, 'length': 0}.

- dupcheck_rc: calls 12, prompt_tokens 6949, output_tokens 1636, max_prompt_tokens 654, errors 0, length 0
- names: calls 46, prompt_tokens 88375, output_tokens 2294, max_prompt_tokens 3277, errors 0, length 0
- reconcile: calls 280, prompt_tokens 148886, output_tokens 9256, max_prompt_tokens 666, errors 0, length 0

## A answers (the vote's input)

18 answers; with parse errors 0; cut off 0; declared names no cluster uses 0; names used but never declared 0; `_end`-style names 0.

## Calls per stage (v4.4)

- dupcheck: calls 12, prompt_tokens 6949, output_tokens 1636, retried 0, job_seconds 3.72, guided_parse_rate 1.0
- merge_q: calls 28, prompt_tokens 9023, output_tokens 196, retried 0, job_seconds 0.56, guided_parse_rate 1.0
- names: calls 46, prompt_tokens 88375, output_tokens 2294, retried 0, job_seconds 7.36, guided_parse_rate 1.0
- rescue_n: calls 33, prompt_tokens 32058, output_tokens 364, retried 0, job_seconds 0.99, guided_parse_rate 1.0
- rescue_q: calls 58, prompt_tokens 16013, output_tokens 406, retried 0, job_seconds 0.58, guided_parse_rate 1.0
- split: calls 54, prompt_tokens 58760, output_tokens 13663, retried 0, job_seconds 10.08, guided_parse_rate 1.0
- reconcile: calls 280, prompt_tokens 148886, output_tokens 9256, retried 0, job_seconds 8.88, guided_parse_rate 1.0
- total: calls 511, prompt_tokens 360064, output_tokens 27815, retried 0, job_seconds 32.17, guided_parse_rate 1.0

## Boosters

```json
{
 "rescue": {
  "not_attribute_cluster_orders": 58,
  "asked": 58,
  "yes": 33,
  "no": 25,
  "unparsed": 0,
  "names_asked": 33,
  "named": 29
 },
 "merge": {
  "pairs_asked": 28,
  "yes": 8,
  "no": 20,
  "unparsed": 0,
  "merged": 8
 },
 "by_set": {
  "dev50": {
   "rescue_asked": 33,
   "rescue_yes": 19,
   "rescue_named": 16,
   "merge_pairs_asked": 21,
   "merge_yes": 7,
   "merged": 7
  },
  "dev50b": {
   "rescue_asked": 25,
   "rescue_yes": 14,
   "rescue_named": 13,
   "merge_pairs_asked": 7,
   "merge_yes": 1,
   "merged": 1
  }
 }
}
```
