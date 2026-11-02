# wf_v3.7 Colab batch prompts (seed 0)

Tokens are estimated as chars / 3.5 (baseline: the est_prompt_tokens of W3's manifest rows). k drops 8 -> 6 -> 5 when a prompt reaches 28000. Output tokens: A = the v3.6 A answer of the same entity (`<ent>_v2_s2`, exact tokens of its response); split = mean of the v3.1 split answers (113; estimate: new clusters); baseline = 1,000 per call (W3's estimate). Runs: `v23d50` = `results/graph_v23_dev50`, `v22d50b` = `results/graph_v22_dev50b`, `v23d50b` = `results/graph_v23_dev50b`.

| job | run | entity | k | chars | est. prompt tokens | est. output tokens | status |
|---|---|---|---|---|---|---|---|
| train_a_v23d50_s0 | v23d50 | E1 | 8 | 36173 | 10335 | 2396 | ok |
| train_a_v23d50_s1 | v23d50 | E1 | 8 | 36173 | 10335 | 2396 | ok |
| train_a_v23d50_s2 | v23d50 | E1 | 8 | 36173 | 10335 | 2396 | ok |
| train_v23d50_split_E1-1_r1 | v23d50 | E1 | 16 | 4201 | 1200 | 113 | ok |
| train_v23d50_split_E1-2_r1 | v23d50 | E1 | 16 | 4101 | 1171 | 113 | ok |
| train_v23d50_split_E1-3_r1 | v23d50 | E1 | 16 | 3751 | 1071 | 113 | ok |
| train_v23d50_split_E1-4_r1 | v23d50 | E1 | 16 | 3735 | 1067 | 113 | ok |
| train_v23d50_split_E1-5_r1 | v23d50 | E1 | 16 | 2400 | 685 | 113 | ok |
| train_v23d50_split_E1-6_r1 | v23d50 | E1 | 16 | 3954 | 1129 | 113 | ok |
| train_v23d50_split_E1-8_r1 | v23d50 | E1 | 16 | 2345 | 670 | 113 | ok |
| train_v23d50_split_E1-9_r1 | v23d50 | E1 | 16 | 2328 | 665 | 113 | ok |
| train_v23d50_split_E1-10_r1 | v23d50 | E1 | 16 | 3614 | 1032 | 113 | ok |
| train_v23d50_split_E1-13_r1 | v23d50 | E1 | 16 | 4117 | 1176 | 113 | ok |
| train_v23d50_split_E1-14_r1 | v23d50 | E1 | 16 | 2423 | 692 | 113 | ok |
| train_v23d50_split_E1-17_r1 | v23d50 | E1 | 16 | 2963 | 846 | 113 | ok |
| train_v23d50_split_E1-18_r1 | v23d50 | E1 | 16 | 3998 | 1142 | 113 | ok |
| hotel_a_v23d50_s0 | v23d50 | E0 | 8 | 30828 | 8808 | 4665 | ok |
| hotel_a_v23d50_s1 | v23d50 | E0 | 8 | 30828 | 8808 | 4665 | ok |
| hotel_a_v23d50_s2 | v23d50 | E0 | 8 | 30828 | 8808 | 4665 | ok |
| hotel_v23d50_split_E0-0_r1 | v23d50 | E0 | 16 | 4100 | 1171 | 113 | ok |
| hotel_v23d50_split_E0-1_r1 | v23d50 | E0 | 16 | 4544 | 1298 | 113 | ok |
| hotel_v23d50_split_E0-4_r1 | v23d50 | E0 | 16 | 4279 | 1222 | 113 | ok |
| hotel_v23d50_split_E0-5_r1 | v23d50 | E0 | 16 | 4210 | 1202 | 113 | ok |
| hotel_v23d50_split_E0-6_r1 | v23d50 | E0 | 16 | 4205 | 1201 | 113 | ok |
| hotel_v23d50_split_E0-8_r1 | v23d50 | E0 | 16 | 4032 | 1152 | 113 | ok |
| hotel_v23d50_split_E0-11_r1 | v23d50 | E0 | 16 | 3218 | 919 | 113 | ok |
| hotel_v23d50_split_E0-12_r1 | v23d50 | E0 | 16 | 3259 | 931 | 113 | ok |
| hotel_v23d50_split_E0-14_r1 | v23d50 | E0 | 16 | 2663 | 760 | 113 | ok |
| restaurant_a_v23d50_s0 | v23d50 | E2 | 8 | 48795 | 13941 | 8271 | ok |
| restaurant_a_v23d50_s1 | v23d50 | E2 | 8 | 48795 | 13941 | 8271 | ok |
| restaurant_a_v23d50_s2 | v23d50 | E2 | 8 | 48795 | 13941 | 8271 | ok |
| restaurant_v23d50_split_E2-0_r1 | v23d50 | E2 | 16 | 3965 | 1132 | 113 | ok |
| restaurant_v23d50_split_E2-7_r1 | v23d50 | E2 | 16 | 4150 | 1185 | 113 | ok |
| restaurant_v23d50_split_E2-9_r1 | v23d50 | E2 | 16 | 3149 | 899 | 113 | ok |
| restaurant_v23d50_split_E2-10_r1 | v23d50 | E2 | 16 | 4335 | 1238 | 113 | ok |
| restaurant_v23d50_split_E2-11_r1 | v23d50 | E2 | 16 | 4443 | 1269 | 113 | ok |
| restaurant_v23d50_split_E2-12_r1 | v23d50 | E2 | 16 | 4257 | 1216 | 113 | ok |
| restaurant_v23d50_split_E2-14_r1 | v23d50 | E2 | 16 | 4095 | 1170 | 113 | ok |
| restaurant_v23d50_split_E2-15_r1 | v23d50 | E2 | 16 | 3703 | 1058 | 113 | ok |
| restaurant_v23d50_split_E2-17_r1 | v23d50 | E2 | 16 | 4415 | 1261 | 113 | ok |
| restaurant_v23d50_split_E2-19_r1 | v23d50 | E2 | 16 | 2685 | 767 | 113 | ok |
| train_a_v22d50b_s0 | v22d50b | E0 | 8 | 24340 | 6954 | 2396 | ok |
| train_a_v22d50b_s1 | v22d50b | E0 | 8 | 24340 | 6954 | 2396 | ok |
| train_a_v22d50b_s2 | v22d50b | E0 | 8 | 24340 | 6954 | 2396 | ok |
| train_v22d50b_split_E0-0_r1 | v22d50b | E0 | 16 | 4069 | 1162 | 113 | ok |
| train_v22d50b_split_E0-3_r1 | v22d50b | E0 | 16 | 3841 | 1097 | 113 | ok |
| train_v22d50b_split_E0-4_r1 | v22d50b | E0 | 16 | 3596 | 1027 | 113 | ok |
| train_v22d50b_split_E0-6_r1 | v22d50b | E0 | 16 | 2407 | 687 | 113 | ok |
| train_v22d50b_split_E0-7_r1 | v22d50b | E0 | 16 | 2717 | 776 | 113 | ok |
| train_v22d50b_split_E0-9_r1 | v22d50b | E0 | 16 | 3695 | 1055 | 113 | ok |
| hotel_a_v22d50b_s0 | v22d50b | E1 | 8 | 34948 | 9985 | 4665 | ok |
| hotel_a_v22d50b_s1 | v22d50b | E1 | 8 | 34948 | 9985 | 4665 | ok |
| hotel_a_v22d50b_s2 | v22d50b | E1 | 8 | 34948 | 9985 | 4665 | ok |
| hotel_v22d50b_split_E1-0_r1 | v22d50b | E1 | 16 | 4203 | 1200 | 113 | ok |
| hotel_v22d50b_split_E1-2_r1 | v22d50b | E1 | 16 | 4413 | 1260 | 113 | ok |
| hotel_v22d50b_split_E1-3_r1 | v22d50b | E1 | 16 | 4426 | 1264 | 113 | ok |
| hotel_v22d50b_split_E1-4_r1 | v22d50b | E1 | 16 | 4088 | 1168 | 113 | ok |
| hotel_v22d50b_split_E1-5_r1 | v22d50b | E1 | 16 | 4095 | 1170 | 113 | ok |
| hotel_v22d50b_split_E1-6_r1 | v22d50b | E1 | 16 | 2911 | 831 | 113 | ok |
| hotel_v22d50b_split_E1-7_r1 | v22d50b | E1 | 16 | 4207 | 1202 | 113 | ok |
| hotel_v22d50b_split_E1-9_r1 | v22d50b | E1 | 16 | 4327 | 1236 | 113 | ok |
| hotel_v22d50b_split_E1-12_r1 | v22d50b | E1 | 16 | 4066 | 1161 | 113 | ok |
| hotel_v22d50b_split_E1-13_r1 | v22d50b | E1 | 16 | 2388 | 682 | 113 | ok |
| restaurant_a_v22d50b_s0 | v22d50b | E3 | 8 | 36655 | 10472 | 8271 | ok |
| restaurant_a_v22d50b_s1 | v22d50b | E3 | 8 | 36655 | 10472 | 8271 | ok |
| restaurant_a_v22d50b_s2 | v22d50b | E3 | 8 | 36655 | 10472 | 8271 | ok |
| restaurant_v22d50b_split_E3-0_r1 | v22d50b | E3 | 16 | 4013 | 1146 | 113 | ok |
| restaurant_v22d50b_split_E3-1_r1 | v22d50b | E3 | 16 | 3652 | 1043 | 113 | ok |
| restaurant_v22d50b_split_E3-5_r1 | v22d50b | E3 | 16 | 4440 | 1268 | 113 | ok |
| restaurant_v22d50b_split_E3-11_r1 | v22d50b | E3 | 16 | 4454 | 1272 | 113 | ok |
| restaurant_v22d50b_split_E3-12_r1 | v22d50b | E3 | 16 | 4195 | 1198 | 113 | ok |
| restaurant_v22d50b_split_E3-13_r1 | v22d50b | E3 | 16 | 3782 | 1080 | 113 | ok |
| restaurant_v22d50b_split_E3-20_r1 | v22d50b | E3 | 16 | 3182 | 909 | 113 | ok |
| train_a_v23d50b_s0 | v23d50b | E0 | 8 | 27119 | 7748 | 2396 | ok |
| train_a_v23d50b_s1 | v23d50b | E0 | 8 | 27119 | 7748 | 2396 | ok |
| train_a_v23d50b_s2 | v23d50b | E0 | 8 | 27119 | 7748 | 2396 | ok |
| train_v23d50b_split_E0-0_r1 | v23d50b | E0 | 16 | 4069 | 1162 | 113 | ok |
| train_v23d50b_split_E0-3_r1 | v23d50b | E0 | 16 | 3841 | 1097 | 113 | ok |
| train_v23d50b_split_E0-4_r1 | v23d50b | E0 | 16 | 3596 | 1027 | 113 | ok |
| train_v23d50b_split_E0-6_r1 | v23d50b | E0 | 16 | 2407 | 687 | 113 | ok |
| train_v23d50b_split_E0-7_r1 | v23d50b | E0 | 16 | 2717 | 776 | 113 | ok |
| train_v23d50b_split_E0-9_r1 | v23d50b | E0 | 16 | 3018 | 862 | 113 | ok |
| hotel_a_v23d50b_s0 | v23d50b | E1 | 8 | 34934 | 9981 | 4665 | ok |
| hotel_a_v23d50b_s1 | v23d50b | E1 | 8 | 34934 | 9981 | 4665 | ok |
| hotel_a_v23d50b_s2 | v23d50b | E1 | 8 | 34934 | 9981 | 4665 | ok |
| hotel_v23d50b_split_E1-0_r1 | v23d50b | E1 | 16 | 4203 | 1200 | 113 | ok |
| hotel_v23d50b_split_E1-2_r1 | v23d50b | E1 | 16 | 4413 | 1260 | 113 | ok |
| hotel_v23d50b_split_E1-3_r1 | v23d50b | E1 | 16 | 4426 | 1264 | 113 | ok |
| hotel_v23d50b_split_E1-4_r1 | v23d50b | E1 | 16 | 4088 | 1168 | 113 | ok |
| hotel_v23d50b_split_E1-5_r1 | v23d50b | E1 | 16 | 4095 | 1170 | 113 | ok |
| hotel_v23d50b_split_E1-6_r1 | v23d50b | E1 | 16 | 2911 | 831 | 113 | ok |
| hotel_v23d50b_split_E1-7_r1 | v23d50b | E1 | 16 | 4207 | 1202 | 113 | ok |
| hotel_v23d50b_split_E1-9_r1 | v23d50b | E1 | 16 | 4327 | 1236 | 113 | ok |
| hotel_v23d50b_split_E1-12_r1 | v23d50b | E1 | 16 | 4066 | 1161 | 113 | ok |
| hotel_v23d50b_split_E1-13_r1 | v23d50b | E1 | 16 | 2388 | 682 | 113 | ok |
| restaurant_a_v23d50b_s0 | v23d50b | E3 | 8 | 36571 | 10448 | 8271 | ok |
| restaurant_a_v23d50b_s1 | v23d50b | E3 | 8 | 36571 | 10448 | 8271 | ok |
| restaurant_a_v23d50b_s2 | v23d50b | E3 | 8 | 36571 | 10448 | 8271 | ok |
| restaurant_v23d50b_split_E3-0_r1 | v23d50b | E3 | 16 | 4013 | 1146 | 113 | ok |
| restaurant_v23d50b_split_E3-1_r1 | v23d50b | E3 | 16 | 3652 | 1043 | 113 | ok |
| restaurant_v23d50b_split_E3-5_r1 | v23d50b | E3 | 16 | 4440 | 1268 | 113 | ok |
| restaurant_v23d50b_split_E3-11_r1 | v23d50b | E3 | 16 | 4454 | 1272 | 113 | ok |
| restaurant_v23d50b_split_E3-12_r1 | v23d50b | E3 | 16 | 4195 | 1198 | 113 | ok |
| restaurant_v23d50b_split_E3-13_r1 | v23d50b | E3 | 16 | 3782 | 1080 | 113 | ok |
| restaurant_v23d50b_split_E3-15_r1 | v23d50b | E3 | 16 | 2323 | 663 | 113 | ok |
| restaurant_v23d50b_split_E3-20_r1 | v23d50b | E3 | 16 | 3182 | 909 | 113 | ok |

## Estimated calls and tokens per family

| family | calls | est. prompt tokens | est. output tokens |
|---|---|---|---|
| a | 27 | 266016 | 137988 |
| split | 79 | 83855 | 8927 |
| baseline | 18 | 148299 | 18000 |
| total | 124 | 498170 | 164915 |

v3.6 batch: 46 calls, 385,398 prompt, 101,931 output tokens. Change: +78 calls, +112,772 prompt, +62,984 output tokens.

## Byte check: this builder on `results/graph_v22_dev50` against the old files (LF text)

| entity | check | result |
|---|---|---|
| train | order 0 vs loop1_v31/prompts/train_v2.txt | identical |
| train | order 1 vs loop1_v31/prompts/train_v2_r2.txt | identical |
| train | order 2 vs loop1_v36/colab/prompts/train_v2_s2.txt | identical |
| hotel | order 0 vs loop1_v31/prompts/hotel_v2.txt | identical |
| hotel | order 1 vs loop1_v31/prompts/hotel_v2_r2.txt | identical |
| hotel | order 2 vs loop1_v36/colab/prompts/hotel_v2_s2.txt | identical |
| restaurant | order 0 vs loop1_v31/prompts/restaurant_v2.txt | identical |
| restaurant | order 1 vs loop1_v31/prompts/restaurant_v2_r2.txt | identical |
| restaurant | order 2 vs loop1_v36/colab/prompts/restaurant_v2_s2.txt | identical |
