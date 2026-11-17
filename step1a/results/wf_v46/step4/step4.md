# Step 4 (v4.3, seed 0) on the v4.6 runs

| set | run | GT view | tables | table_f1 | grouping_f1 | gt_columns_placed | pk_right | pk_right_b | calls | prompt / output tokens | largest prompt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| dev50 | v4.5 keyword names | full | 5 | 0.800 | 1.000 | 31/50 (0.620) | 0/4 (0.000) | 4/4 (1.000) | 17 | 51,732 / 828 | 9,969 |
| dev50 | v4.5 keyword names | Y1 rule | 5 | 0.800 | 1.000 | 31/46 (0.674) | 0/4 (0.000) | 4/4 (1.000) | 17 | 51,732 / 828 | 9,969 |
| dev50 | v4.6 LLM names | full | 1 | 0.333 | 0.379 | 32/50 (0.640) | 0/1 (0.000) | 1/1 (1.000) | 3 | 25,761 / 779 | 9,861 |
| dev50 | v4.6 LLM names | Y1 rule | 1 | 0.333 | 0.379 | 32/46 (0.696) | 0/1 (0.000) | 1/1 (1.000) | 3 | 25,761 / 779 | 9,861 |
| dev50 | v4.6 LLM names, p2 batches of 20 | full | 4 | 0.889 | 0.815 | 32/50 (0.640) | 0/4 (0.000) | 4/4 (1.000) | 15 | 47,059 / 975 | 9,861 |
| dev50 | v4.6 LLM names, p2 batches of 20 | Y1 rule | 4 | 0.889 | 0.815 | 32/46 (0.696) | 0/4 (0.000) | 4/4 (1.000) | 15 | 47,059 / 975 | 9,861 |
| dev50b | v4.6 LLM names | full | 3 | 0.750 | 0.281 | 39/50 (0.780) | 1/3 (0.333) | 2/3 (0.667) | 8 | 37,076 / 883 | 9,589 |
| dev50b | v4.6 LLM names | Y1 rule | 3 | 0.750 | 0.281 | 39/47 (0.830) | 1/3 (0.333) | 2/3 (0.667) | 8 | 37,076 / 883 | 9,589 |
| dev50b | v4.6 LLM names, p2 batches of 20 | full | 5 | 0.800 | 0.677 | 29/50 (0.580) | 1/4 (0.250) | 4/4 (1.000) | 20 | 41,695 / 991 | 9,589 |
| dev50b | v4.6 LLM names, p2 batches of 20 | Y1 rule | 5 | 0.800 | 0.677 | 29/47 (0.617) | 1/4 (0.250) | 4/4 (1.000) | 20 | 41,695 / 991 | 9,589 |

Tables per chain:

- dev50 v4.5 keyword names: hotel train restaurant attraction attraction_2
- dev50 v4.6 LLM names: location
- dev50 v4.6 LLM names, p2 batches of 20: train_info food_establishment address location
- dev50b v4.6 LLM names: location establishment phone_number
- dev50b v4.6 LLM names, p2 batches of 20: train_schedule accommodation_option location establishment phone_number
