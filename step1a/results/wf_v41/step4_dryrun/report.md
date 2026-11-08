# wf_v4.1 task 4: v4.1 Step-4 prompts, dry run on c1 / dev50 / seed 0

**DRY RUN, not a result.** v4.1 answers come from Gemini; the v0 column is the real Qwen2.5-32B run of the same chain (different models, so the comparison only shows whether the prompt changes work as intended).

- chain c1_dev50_s0: ok, repairs 0

| | v0 (Qwen) | v4.1 (Gemini dry run) |
|---|---|---|
| tables | 3 | 6 |
| links | 0 | 6 |
| unused | 6 | 2 |
| table_names | train_information, hotel_information, restaurant_information | train, train_booking, hotel, hotel_booking, restaurant, restaurant_booking |
| table_f1 (full GT) | 0.750 | 0.769 |
| grouping_f1 (full GT) | 1.000 | 0.887 |
| gt_columns_placed (full GT) | 31/50 | 35/54 |
| placement (full GT) | 31/31 | 30/35 |
| pk_right (full GT) | 0/3 | 3/5 |
| pk_right_b (full GT) | 3/3 | 3/5 |
| rel_recall (full GT) | 0/0 | 2/2 |
| rel_precision (full GT) | 0/0 | 2/3 |
| types_right (full GT) | 31/31 | 31/33 |
| unused_real (full GT) | 4/6 | 2/2 |
| duplicates (full GT) | 0/0 | 0/0 |
