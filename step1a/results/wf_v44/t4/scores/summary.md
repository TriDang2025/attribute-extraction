# wf_v4.4 Step 3 (Llama-3.1-8B): names variant + boosters

| set | row | found | columns | columns per found | dup columns | wrong columns | review edits | guard |
|---|---|---|---|---|---|---|---|---|
| dev50 | A s012 + split pass | 31/40 (8+11+12) | 76 | 2.355 | 42 | 6 | 48 | FAIL |
| dev50 | A s012 + reconcile (both orders) | 31/40 (8+11+12) | 61 | 2.097 | 34 | 3 | 37 | FAIL |
| dev50 | Final v3.9 | 31/40 (8+11+12) | 58 | 2.032 | 32 | 3 | 35 | FAIL |
| dev50b | A s012 + split pass | 27/41 (6+11+10) | 77 | 2.407 | 38 | 7 | 45 | FAIL |
| dev50b | A s012 + reconcile (both orders) | 27/41 (6+11+10) | 62 | 2.0 | 27 | 6 | 33 | FAIL |
| dev50b | Final v3.9 | 27/41 (6+11+10) | 59 | 1.963 | 26 | 6 | 32 | FAIL |

## Stage facts

- dev50 train: columns_split_pass 22, parts 25, reconcile_agree [17, 25], reconcile_joined_agreed 17, parts_moved_mentions 237, dup_joins_order0 [6, 6], dup_joins_order1 [4, 4], dup_same_groups_both 2, dup_on_agreed_columns 2, dup_role_pair_blocked 0, dup_joins_kept 2, columns_final 14, mentions_in_columns 331, dropped_clusters 3, dropped_mentions 19
- dev50 hotel: columns_split_pass 28, parts 27, reconcile_agree [18, 27], reconcile_joined_agreed 18, parts_moved_mentions 103, dup_joins_order0 [6, 6], dup_joins_order1 [5, 5], dup_same_groups_both 0, dup_on_agreed_columns 0, dup_role_pair_blocked 0, dup_joins_kept 0, columns_final 23, mentions_in_columns 196, dropped_clusters 4, dropped_mentions 4
- dev50 restaurant: columns_split_pass 26, parts 26, reconcile_agree [18, 26], reconcile_joined_agreed 17, parts_moved_mentions 131, dup_joins_order0 [7, 7], dup_joins_order1 [6, 6], dup_same_groups_both 0, dup_on_agreed_columns 0, dup_role_pair_blocked 0, dup_joins_kept 0, columns_final 21, mentions_in_columns 294, dropped_clusters 6, dropped_mentions 10
- dev50b train: columns_split_pass 20, parts 11, reconcile_agree [9, 11], reconcile_joined_agreed 9, parts_moved_mentions 104, dup_joins_order0 [6, 6], dup_joins_order1 [11, 11], dup_same_groups_both 3, dup_on_agreed_columns 3, dup_role_pair_blocked 0, dup_joins_kept 3, columns_final 15, mentions_in_columns 175, dropped_clusters 2, dropped_mentions 6
- dev50b hotel: columns_split_pass 31, parts 34, reconcile_agree [24, 34], reconcile_joined_agreed 24, parts_moved_mentions 152, dup_joins_order0 [8, 8], dup_joins_order1 [6, 6], dup_same_groups_both 0, dup_on_agreed_columns 0, dup_role_pair_blocked 0, dup_joins_kept 0, columns_final 23, mentions_in_columns 232, dropped_clusters 2, dropped_mentions 6
- dev50b restaurant: columns_split_pass 26, parts 25, reconcile_agree [14, 25], reconcile_joined_agreed 14, parts_moved_mentions 81, dup_joins_order0 [2, 2], dup_joins_order1 [9, 9], dup_same_groups_both 0, dup_on_agreed_columns 0, dup_role_pair_blocked 0, dup_joins_kept 0, columns_final 21, mentions_in_columns 233, dropped_clusters 2, dropped_mentions 2

## Calls

New calls 446, prompt tokens 428,695, output tokens 18,253, largest prompt 3,077; parse errors 0, cut off (finish length) 0. Reused A answers (not rerun): {'calls': 0, 'errors': 0, 'length': 0}.

- dupcheck_rc: calls 12, prompt_tokens 6772, output_tokens 1578, max_prompt_tokens 671, errors 0, length 0
- names: calls 138, prompt_tokens 265125, output_tokens 6843, max_prompt_tokens 3077, errors 0, length 0
- reconcile: calls 296, prompt_tokens 156798, output_tokens 9832, max_prompt_tokens 667, errors 0, length 0

## A answers (the vote's input)

18 answers; with parse errors 0; cut off 0; declared names no cluster uses 0; names used but never declared 0; `_end`-style names 0.

## Calls per stage (v4.4)

- dupcheck: calls 12, prompt_tokens 6772, output_tokens 1578, retried 0, job_seconds 3.41, guided_parse_rate 1.0
- merge_q: calls 73, prompt_tokens 23668, output_tokens 514, retried 0, job_seconds 1.26, guided_parse_rate 1.0
- names: calls 138, prompt_tokens 265125, output_tokens 6843, retried 0, job_seconds 14.4, guided_parse_rate 1.0
- rescue_n: calls 61, prompt_tokens 61157, output_tokens 675, retried 0, job_seconds 1.22, guided_parse_rate 1.0
- rescue_q: calls 63, prompt_tokens 17508, output_tokens 441, retried 0, job_seconds 0.63, guided_parse_rate 1.0
- split: calls 54, prompt_tokens 58760, output_tokens 13663, retried 0, job_seconds 8.64, guided_parse_rate 1.0
- reconcile: calls 296, prompt_tokens 156798, output_tokens 9832, retried 0, job_seconds 9.28, guided_parse_rate 1.0
- total: calls 697, prompt_tokens 589788, output_tokens 33546, retried 0, job_seconds 38.84, guided_parse_rate 1.0

## Boosters

```json
{
 "rescue": {
  "not_attribute_cluster_orders": 114,
  "asked": 63,
  "yes": 38,
  "no": 25,
  "unparsed": 0,
  "names_asked": 61,
  "named": 46
 },
 "merge": {
  "pairs_asked": 73,
  "yes": 18,
  "no": 55,
  "unparsed": 0,
  "merged": 18
 },
 "by_set": {
  "dev50": {
   "rescue_asked": 32,
   "rescue_yes": 19,
   "rescue_named": 21,
   "merge_pairs_asked": 43,
   "merge_yes": 8,
   "merged": 8
  },
  "dev50b": {
   "rescue_asked": 31,
   "rescue_yes": 19,
   "rescue_named": 25,
   "merge_pairs_asked": 30,
   "merge_yes": 10,
   "merged": 10
  }
 }
}
```
