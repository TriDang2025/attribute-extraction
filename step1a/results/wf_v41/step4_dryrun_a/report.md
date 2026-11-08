# wf_v4.1: v4.1 Step-4 prompts, dry run on a_dev50_s0, a_dev50b_s0

**DRY RUN, not a result.** v4.1 answers come from Gemini; the v0 column is the real Qwen2.5-32B run of the same chain (different models, so the comparison only shows whether the prompt changes work as intended).

- chain a_dev50_s0: ok, repairs 6
- chain a_dev50b_s0: ok, repairs 0

| | v0 (Qwen) | v4.1 (Gemini dry run) |
|---|---|---|
| tables | 3 | 6 |
| links | 0 | 6 |
| unused | 31 | 12 |
| table_names | train_journey, hotel_booking, restaurant_reservation | train, train_booking, hotel, hotel_booking, restaurant, restaurant_booking |
| table_f1 (full GT) | 0.750 | 0.857 |
| grouping_f1 (full GT) | 1.000 | 0.951 |
| gt_columns_placed (full GT) | 22/50 | 32/56 |
| placement (full GT) | 22/22 | 31/32 |
| pk_right (full GT) | 0/3 | 3/6 |
| pk_right_b (full GT) | 3/3 | 3/6 |
| rel_recall (full GT) | 0/0 | 3/3 |
| rel_precision (full GT) | 0/0 | 3/3 |
| types_right (full GT) | 23/23 | 38/40 |
| unused_real (full GT) | 21/31 | 4/12 |
| duplicates (full GT) | 0/1 | 5/9 |

| | v0 (Qwen) | v4.1 (Gemini dry run) |
|---|---|---|
| tables | 9 | 6 |
| links | 10 | 6 |
| unused | 12 | 5 |
| table_names | train_journey, train_timing, train_booking, hotel_details, hotel_booking, restaurant_location, restaurant_reservation, restaurant_booking, restaurant_cuisine | train_journey, train_booking, hotel, hotel_reservation, restaurant, restaurant_reservation |
| table_f1 (full GT) | 0.706 | 0.857 |
| grouping_f1 (full GT) | 0.591 | 0.909 |
| gt_columns_placed (full GT) | 33/56 | 35/56 |
| placement (full GT) | 23/33 | 33/35 |
| pk_right (full GT) | 4/6 | 3/6 |
| pk_right_b (full GT) | 6/6 | 3/6 |
| rel_recall (full GT) | 2/3 | 3/3 |
| rel_precision (full GT) | 2/6 | 3/3 |
| types_right (full GT) | 34/34 | 39/39 |
| unused_real (full GT) | 7/12 | 2/5 |
| duplicates (full GT) | 0/2 | 5/6 |
