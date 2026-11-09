# Compact A prompts (wf_v4.2, C1-C3 + C5), tokens of meta-llama/Meta-Llama-3-8B-Instruct

Budget 7500 tokens per call (prompt in the chat template + max answer). Answer estimate: 42.1 tokens per cluster (the largest compact rewrite of a saved answer) x 1.25 + 200.

| set | entity | clusters | full | C1 | C1+C2 | C1+C2+C3 | change | answer est. | calls (parts) | worst total |
|---|---|---|---|---|---|---|---|---|---|---|
| dev50 | train | 29 | 9,240 | 5,755 | 3,634 | 3,570 | -61% | 1,727 | 1 (29) | 5,297 |
| dev50 | hotel | 31 | 8,377 | 5,063 | 3,434 | 3,370 | -60% | 1,832 | 1 (31) | 5,202 |
| dev50 | restaurant | 57 | 13,433 | 8,154 | 6,012 | 5,948 | -56% | 3,200 | 2 (29 / 28) | 5,401 |
| dev50b | train | 20 | 7,171 | 4,581 | 2,933 | 2,869 | -60% | 1,253 | 1 (20) | 4,122 |
| dev50b | hotel | 31 | 9,575 | 5,633 | 3,779 | 3,715 | -61% | 1,832 | 1 (31) | 5,547 |
| dev50b | restaurant | 48 | 10,155 | 6,170 | 4,457 | 4,393 | -57% | 2,726 | 1 (48) | 7,119 |

21 compact A jobs (3 orders).

## Saved A answers rewritten in the compact format

| set | entity | file | clusters | full tokens | compact tokens | per cluster |
|---|---|---|---|---|---|---|
| dev50 | train | train_v2_r1.jsonl | 29 | 1,848 | 1,108 | 38.2 |
| dev50 | train | train_v2_r2.jsonl | 29 | 1,783 | 1,056 | 36.4 |
| dev50 | train | train_v2_s2.jsonl | 29 | 2,314 | 1,137 | 39.2 |
| dev50 | hotel | hotel_v2_r1.jsonl | 31 | 2,374 | 1,142 | 36.8 |
| dev50 | hotel | hotel_v2_r2.jsonl | 31 | 1,961 | 1,223 | 39.5 |
| dev50 | hotel | hotel_v2_s2.jsonl | 31 | 2,306 | 1,144 | 36.9 |
| dev50 | restaurant | restaurant_v2_r1.jsonl | 57 | 4,081 | 1,925 | 33.8 |
| dev50 | restaurant | restaurant_v2_r2.jsonl | 57 | 4,170 | 1,811 | 31.8 |
| dev50 | restaurant | restaurant_v2_s2.jsonl | 57 | 4,054 | 1,932 | 33.9 |
| dev50b | train | train_a_v22d50b_s0.jsonl | 21 | 1,726 | 811 | 38.6 |
| dev50b | train | train_a_v22d50b_s1.jsonl | 20 | 1,603 | 842 | 42.1 |
| dev50b | train | train_a_v22d50b_s2.jsonl | 20 | 1,577 | 840 | 42.0 |
| dev50b | hotel | hotel_a_v22d50b_s0.jsonl | 31 | 1,984 | 1,176 | 37.9 |
| dev50b | hotel | hotel_a_v22d50b_s1.jsonl | 31 | 2,018 | 1,211 | 39.1 |
| dev50b | hotel | hotel_a_v22d50b_s2.jsonl | 31 | 1,847 | 1,069 | 34.5 |
| dev50b | restaurant | restaurant_a_v22d50b_s0.jsonl | 48 | 3,419 | 1,646 | 34.3 |
| dev50b | restaurant | restaurant_a_v22d50b_s1.jsonl | 48 | 3,715 | 1,710 | 35.6 |
| dev50b | restaurant | restaurant_a_v22d50b_s2.jsonl | 48 | 2,833 | 1,715 | 35.7 |

Total: full 45,613 -> compact 23,498 tokens (-48%).
