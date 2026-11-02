# wf_v3.7 LLM-only baseline prompts

Tokens are estimated as chars / 3.5. Budget per prompt: 32768 - 4096 = 28672 estimated tokens (instruction included). Output tokens are an ESTIMATE of 1000 per call, not measured. v0 = set order, v1 / v2 = shuffled with seed 1 / 2; a dialogue that does not fit is skipped.

| prompt | set | entity | dialogues used / available | est. prompt tokens | est. output tokens |
|---|---|---|---|---|---|
| baseline_train_dev50_v0 | dev50 | train | 28/28 | 10436 | 1000 |
| baseline_train_dev50_v1 | dev50 | train | 28/28 | 10436 | 1000 |
| baseline_train_dev50_v2 | dev50 | train | 28/28 | 10436 | 1000 |
| baseline_hotel_dev50_v0 | dev50 | hotel | 18/18 | 7410 | 1000 |
| baseline_hotel_dev50_v1 | dev50 | hotel | 18/18 | 7410 | 1000 |
| baseline_hotel_dev50_v2 | dev50 | hotel | 18/18 | 7410 | 1000 |
| baseline_restaurant_dev50_v0 | dev50 | restaurant | 27/27 | 9572 | 1000 |
| baseline_restaurant_dev50_v1 | dev50 | restaurant | 27/27 | 9572 | 1000 |
| baseline_restaurant_dev50_v2 | dev50 | restaurant | 27/27 | 9572 | 1000 |
| baseline_train_dev50b_v0 | dev50b | train | 17/17 | 5649 | 1000 |
| baseline_train_dev50b_v1 | dev50b | train | 17/17 | 5649 | 1000 |
| baseline_train_dev50b_v2 | dev50b | train | 17/17 | 5649 | 1000 |
| baseline_hotel_dev50b_v0 | dev50b | hotel | 23/23 | 8558 | 1000 |
| baseline_hotel_dev50b_v1 | dev50b | hotel | 23/23 | 8558 | 1000 |
| baseline_hotel_dev50b_v2 | dev50b | hotel | 23/23 | 8558 | 1000 |
| baseline_restaurant_dev50b_v0 | dev50b | restaurant | 25/25 | 7808 | 1000 |
| baseline_restaurant_dev50b_v1 | dev50b | restaurant | 25/25 | 7808 | 1000 |
| baseline_restaurant_dev50b_v2 | dev50b | restaurant | 25/25 | 7808 | 1000 |

## Totals

| set | prompts | dialogues used | est. prompt tokens | est. output tokens |
|---|---|---|---|---|
| dev50 | 9 | 219 | 82254 | 9000 |
| dev50b | 9 | 195 | 66045 | 9000 |
| all | 18 | 414 | 148299 | 18000 |

## By entity, set and version (dialogues used)

| entity | set | available | v0 | v1 | v2 |
|---|---|---|---|---|---|
| train | dev50 | 28 | 28 | 28 | 28 |
| train | dev50b | 17 | 17 | 17 | 17 |
| hotel | dev50 | 18 | 18 | 18 | 18 |
| hotel | dev50b | 23 | 23 | 23 | 23 |
| restaurant | dev50 | 27 | 27 | 27 | 27 |
| restaurant | dev50b | 25 | 25 | 25 | 25 |
