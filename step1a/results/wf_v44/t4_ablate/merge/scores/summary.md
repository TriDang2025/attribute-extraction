# wf_v4.4 Step 3 (Llama-3.1-8B): names variant + boosters

| set | row | found | columns | columns per found | dup columns | wrong columns | review edits | guard |
|---|---|---|---|---|---|---|---|---|
| dev50 | A s012 + split pass | 31/40 (8+11+12) | 77 | 2.323 | 41 | 7 | 48 | FAIL |
| dev50 | A s012 + reconcile (both orders) | 31/40 (8+11+12) | 63 | 2.065 | 33 | 4 | 37 | FAIL |
| dev50 | Final v3.9 | 31/40 (8+11+12) | 60 | 2.0 | 31 | 3 | 34 | FAIL |
| dev50b | A s012 + split pass | 29/41 (8+11+10) | 82 | 2.586 | 46 | 6 | 52 | FAIL |
| dev50b | A s012 + reconcile (both orders) | 29/41 (8+11+10) | 67 | 2.276 | 37 | 5 | 42 | FAIL |
| dev50b | Final v3.9 | 29/41 (8+11+10) | 65 | 2.241 | 36 | 5 | 41 | FAIL |

## Stage facts

- dev50 train: columns_split_pass 23, parts 25, reconcile_agree [16, 25], reconcile_joined_agreed 14, parts_moved_mentions 187, dup_joins_order0 [6, 6], dup_joins_order1 [6, 5], dup_same_groups_both 0, dup_on_agreed_columns 0, dup_role_pair_blocked 0, dup_joins_kept 0, columns_final 18, mentions_in_columns 331, dropped_clusters 3, dropped_mentions 19
- dev50 hotel: columns_split_pass 28, parts 27, reconcile_agree [21, 27], reconcile_joined_agreed 20, parts_moved_mentions 110, dup_joins_order0 [7, 7], dup_joins_order1 [4, 4], dup_same_groups_both 1, dup_on_agreed_columns 1, dup_role_pair_blocked 0, dup_joins_kept 1, columns_final 22, mentions_in_columns 196, dropped_clusters 4, dropped_mentions 4
- dev50 restaurant: columns_split_pass 26, parts 25, reconcile_agree [21, 25], reconcile_joined_agreed 20, parts_moved_mentions 148, dup_joins_order0 [6, 6], dup_joins_order1 [6, 6], dup_same_groups_both 2, dup_on_agreed_columns 2, dup_role_pair_blocked 0, dup_joins_kept 2, columns_final 20, mentions_in_columns 296, dropped_clusters 5, dropped_mentions 8
- dev50b train: columns_split_pass 22, parts 11, reconcile_agree [8, 11], reconcile_joined_agreed 8, parts_moved_mentions 103, dup_joins_order0 [5, 4], dup_joins_order1 [6, 6], dup_same_groups_both 2, dup_on_agreed_columns 2, dup_role_pair_blocked 0, dup_joins_kept 2, columns_final 18, mentions_in_columns 175, dropped_clusters 2, dropped_mentions 6
- dev50b hotel: columns_split_pass 33, parts 34, reconcile_agree [25, 34], reconcile_joined_agreed 24, parts_moved_mentions 115, dup_joins_order0 [10, 10], dup_joins_order1 [10, 10], dup_same_groups_both 0, dup_on_agreed_columns 0, dup_role_pair_blocked 0, dup_joins_kept 0, columns_final 23, mentions_in_columns 235, dropped_clusters 1, dropped_mentions 3
- dev50b restaurant: columns_split_pass 27, parts 25, reconcile_agree [19, 25], reconcile_joined_agreed 18, parts_moved_mentions 109, dup_joins_order0 [6, 6], dup_joins_order1 [10, 10], dup_same_groups_both 0, dup_on_agreed_columns 0, dup_role_pair_blocked 0, dup_joins_kept 0, columns_final 24, mentions_in_columns 224, dropped_clusters 5, dropped_mentions 11

## Calls

New calls 352, prompt tokens 251,303, output tokens 13,698, largest prompt 3,026; parse errors 0, cut off (finish length) 0. Reused A answers (not rerun): {'calls': 0, 'errors': 0, 'length': 0}.

- dupcheck_rc: calls 12, prompt_tokens 6984, output_tokens 1656, max_prompt_tokens 652, errors 0, length 0
- names: calls 46, prompt_tokens 88375, output_tokens 2258, max_prompt_tokens 3026, errors 0, length 0
- reconcile: calls 294, prompt_tokens 155944, output_tokens 9784, max_prompt_tokens 669, errors 0, length 0

## A answers (the vote's input)

18 answers; with parse errors 0; cut off 0; declared names no cluster uses 0; names used but never declared 0; `_end`-style names 0.

## Calls per stage (v4.4)

- dupcheck: calls 12, prompt_tokens 6984, output_tokens 1656, retried 0, job_seconds 3.24, guided_parse_rate 1.0
- names: calls 46, prompt_tokens 88375, output_tokens 2258, retried 0, job_seconds 7.36, guided_parse_rate 1.0
- rescue_n: calls 21, prompt_tokens 21830, output_tokens 230, retried 0, job_seconds 0.63, guided_parse_rate 1.0
- rescue_q: calls 36, prompt_tokens 10119, output_tokens 252, retried 0, job_seconds 0.36, guided_parse_rate 1.0
- split: calls 54, prompt_tokens 58760, output_tokens 13663, retried 0, job_seconds 10.44, guided_parse_rate 1.0
- reconcile: calls 294, prompt_tokens 155944, output_tokens 9784, retried 0, job_seconds 9.2, guided_parse_rate 1.0
- total: calls 463, prompt_tokens 342012, output_tokens 27843, retried 0, job_seconds 31.23, guided_parse_rate 1.0

## Boosters

```json
{
 "rescue": {
  "not_attribute_cluster_orders": 36,
  "asked": 36,
  "yes": 21,
  "no": 15,
  "unparsed": 0,
  "names_asked": 21,
  "named": 16
 },
 "merge": {
  "pairs_asked": 0,
  "yes": 0,
  "no": 0,
  "unparsed": 0,
  "merged": 0
 },
 "by_set": {
  "dev50": {
   "rescue_asked": 20,
   "rescue_yes": 11,
   "rescue_named": 8,
   "merge_pairs_asked": 0,
   "merge_yes": 0,
   "merged": 0
  },
  "dev50b": {
   "rescue_asked": 16,
   "rescue_yes": 10,
   "rescue_named": 8,
   "merge_pairs_asked": 0,
   "merge_yes": 0,
   "merged": 0
  }
 }
}
```
