# wf_v3.2 pilot prompts, stage 1 (run `results/graph_v22_dev50`, seed 0)

Tokens are estimated as chars / 3.5; k drops 8 -> 6 -> 5 when a nbhd prompt reaches 28000.

| prompt | entity | k | chars | est. tokens | status |
|---|---|---|---|---|---|
| train_nbhd0_s0 | E1 | 8 | 9543 | 2726 | ok |
| train_nbhd0_s1 | E1 | 8 | 9543 | 2726 | ok |
| train_nbhd0_s2 | E1 | 8 | 9543 | 2726 | ok |
| train_nbhd1_s0 | E1 | 8 | 26446 | 7556 | ok |
| train_nbhd1_s1 | E1 | 8 | 26446 | 7556 | ok |
| train_nbhd1_s2 | E1 | 8 | 26446 | 7556 | ok |
| train_noise_E1-0 | E1 | 6 | 2041 | 583 | ok |
| train_noise_E1-6 | E1 | 6 | 1253 | 358 | ok |
| train_noise_E1-19 | E1 | 6 | 1365 | 390 | ok |
| train_noise_E1-21 | E1 | 6 | 1398 | 399 | ok |
| train_noise_E1-23 | E1 | 6 | 1188 | 339 | ok |
| train_noise_E1-24 | E1 | 6 | 1231 | 351 | ok |
| train_noise_E1-25 | E1 | 6 | 1187 | 339 | ok |
| train_noise_E1-27 | E1 | 6 | 1448 | 413 | ok |
| train_noise_E1-28 | E1 | 6 | 1262 | 360 | ok |
| train_noise_E1-1 | E1 | 6 | 2066 | 590 | ok |
| train_noise_E1-2 | E1 | 6 | 1912 | 546 | ok |
| train_noise_E1-3 | E1 | 6 | 1735 | 495 | ok |
| train_noise_E1-4 | E1 | 6 | 1970 | 562 | ok |
| train_noise_E1-5 | E1 | 6 | 2136 | 610 | ok |
| train_noise_E1-7 | E1 | 6 | 1909 | 545 | ok |
| train_noise_E1-8 | E1 | 6 | 2093 | 598 | ok |
| train_noise_E1-9 | E1 | 6 | 1009 | 288 | ok |
| train_noise_E1-10 | E1 | 6 | 2124 | 606 | ok |
| train_noise_E1-11 | E1 | 6 | 2169 | 619 | ok |
| train_noise_E1-12 | E1 | 6 | 1781 | 508 | ok |
| train_noise_E1-13 | E1 | 6 | 1780 | 508 | ok |
| train_noise_E1-14 | E1 | 6 | 1916 | 547 | ok |
| train_noise_E1-15 | E1 | 6 | 1696 | 484 | ok |
| train_noise_E1-16 | E1 | 6 | 1435 | 410 | ok |
| train_noise_E1-17 | E1 | 6 | 1016 | 290 | ok |
| train_noise_E1-18 | E1 | 6 | 1394 | 398 | ok |
| train_noise_E1-20 | E1 | 6 | 1276 | 364 | ok |
| train_noise_E1-22 | E1 | 6 | 1031 | 294 | ok |
| train_noise_E1-26 | E1 | 6 | 1175 | 335 | ok |
| train_gate_E1-0 | E1 | 16 | 2896 | 827 | ok |
| train_split_E1-0 | E1 | 16 | 2950 | 842 | ok |
| train_gate_E1-1 | E1 | 16 | 4147 | 1184 | ok |
| train_split_E1-1 | E1 | 16 | 4201 | 1200 | ok |
| train_gate_E1-2 | E1 | 16 | 4047 | 1156 | ok |
| train_split_E1-2 | E1 | 16 | 4101 | 1171 | ok |
| train_gate_E1-3 | E1 | 16 | 3545 | 1012 | ok |
| train_split_E1-3 | E1 | 16 | 3599 | 1028 | ok |
| train_gate_E1-4 | E1 | 16 | 3681 | 1051 | ok |
| train_split_E1-4 | E1 | 16 | 3735 | 1067 | ok |
| train_gate_E1-5 | E1 | 16 | 3475 | 992 | ok |
| train_split_E1-5 | E1 | 16 | 3529 | 1008 | ok |
| train_gate_E1-7 | E1 | 16 | 2291 | 654 | ok |
| train_split_E1-7 | E1 | 16 | 2345 | 670 | ok |
| train_gate_E1-8 | E1 | 16 | 2367 | 676 | ok |
| train_split_E1-8 | E1 | 16 | 2421 | 691 | ok |
| train_gate_E1-10 | E1 | 16 | 4063 | 1160 | ok |
| train_split_E1-10 | E1 | 16 | 4117 | 1176 | ok |
| train_gate_E1-11 | E1 | 16 | 2369 | 676 | ok |
| train_split_E1-11 | E1 | 16 | 2423 | 692 | ok |
| train_gate_E1-14 | E1 | 16 | 2909 | 831 | ok |
| train_split_E1-14 | E1 | 16 | 2963 | 846 | ok |
| train_gate_E1-15 | E1 | 16 | 3868 | 1105 | ok |
| train_split_E1-15 | E1 | 16 | 3922 | 1120 | ok |
| hotel_nbhd0_s0 | E0 | 8 | 24311 | 6946 | ok |
| hotel_nbhd0_s1 | E0 | 8 | 24311 | 6946 | ok |
| hotel_nbhd0_s2 | E0 | 8 | 24311 | 6946 | ok |
| hotel_nbhd1_s0 | E0 | 8 | 10304 | 2944 | ok |
| hotel_nbhd1_s1 | E0 | 8 | 10304 | 2944 | ok |
| hotel_nbhd1_s2 | E0 | 8 | 10304 | 2944 | ok |
| hotel_noise_E0-0 | E0 | 6 | 1917 | 547 | ok |
| hotel_noise_E0-1 | E0 | 6 | 2330 | 665 | ok |
| hotel_noise_E0-2 | E0 | 6 | 1940 | 554 | ok |
| hotel_noise_E0-3 | E0 | 6 | 1250 | 357 | ok |
| hotel_noise_E0-4 | E0 | 6 | 2208 | 630 | ok |
| hotel_noise_E0-5 | E0 | 6 | 1978 | 565 | ok |
| hotel_noise_E0-7 | E0 | 6 | 1267 | 362 | ok |
| hotel_noise_E0-8 | E0 | 6 | 1980 | 565 | ok |
| hotel_noise_E0-10 | E0 | 6 | 2032 | 580 | ok |
| hotel_noise_E0-11 | E0 | 6 | 2049 | 585 | ok |
| hotel_noise_E0-12 | E0 | 6 | 2134 | 609 | ok |
| hotel_noise_E0-13 | E0 | 6 | 1633 | 466 | ok |
| hotel_noise_E0-15 | E0 | 6 | 1717 | 490 | ok |
| hotel_noise_E0-17 | E0 | 6 | 981 | 280 | ok |
| hotel_noise_E0-21 | E0 | 6 | 1102 | 314 | ok |
| hotel_noise_E0-23 | E0 | 6 | 1077 | 307 | ok |
| hotel_noise_E0-25 | E0 | 6 | 1434 | 409 | ok |
| hotel_noise_E0-27 | E0 | 6 | 929 | 265 | ok |
| hotel_noise_E0-28 | E0 | 6 | 1546 | 441 | ok |
| hotel_noise_E0-29 | E0 | 6 | 1033 | 295 | ok |
| hotel_noise_E0-6 | E0 | 6 | 2186 | 624 | ok |
| hotel_noise_E0-9 | E0 | 6 | 1286 | 367 | ok |
| hotel_noise_E0-14 | E0 | 6 | 2029 | 579 | ok |
| hotel_noise_E0-16 | E0 | 6 | 960 | 274 | ok |
| hotel_noise_E0-18 | E0 | 6 | 1282 | 366 | ok |
| hotel_noise_E0-19 | E0 | 6 | 1014 | 289 | ok |
| hotel_noise_E0-20 | E0 | 6 | 1054 | 301 | ok |
| hotel_noise_E0-22 | E0 | 6 | 1195 | 341 | ok |
| hotel_noise_E0-24 | E0 | 6 | 965 | 275 | ok |
| hotel_noise_E0-26 | E0 | 6 | 1036 | 296 | ok |
| hotel_noise_E0-30 | E0 | 6 | 983 | 280 | ok |
| hotel_gate_E0-0 | E0 | 16 | 4046 | 1156 | ok |
| hotel_split_E0-0 | E0 | 16 | 4100 | 1171 | ok |
| hotel_gate_E0-1 | E0 | 16 | 4490 | 1282 | ok |
| hotel_split_E0-1 | E0 | 16 | 4544 | 1298 | ok |
| hotel_gate_E0-4 | E0 | 16 | 4225 | 1207 | ok |
| hotel_split_E0-4 | E0 | 16 | 4279 | 1222 | ok |
| hotel_gate_E0-5 | E0 | 16 | 4156 | 1187 | ok |
| hotel_split_E0-5 | E0 | 16 | 4210 | 1202 | ok |
| hotel_gate_E0-6 | E0 | 16 | 4151 | 1186 | ok |
| hotel_split_E0-6 | E0 | 16 | 4205 | 1201 | ok |
| hotel_gate_E0-8 | E0 | 16 | 3978 | 1136 | ok |
| hotel_split_E0-8 | E0 | 16 | 4032 | 1152 | ok |
| hotel_gate_E0-11 | E0 | 16 | 3164 | 904 | ok |
| hotel_split_E0-11 | E0 | 16 | 3218 | 919 | ok |
| hotel_gate_E0-12 | E0 | 16 | 3205 | 915 | ok |
| hotel_split_E0-12 | E0 | 16 | 3259 | 931 | ok |
| hotel_gate_E0-14 | E0 | 16 | 2609 | 745 | ok |
| hotel_split_E0-14 | E0 | 16 | 2663 | 760 | ok |
| restaurant_nbhd0_s0 | E2 | 8 | 28135 | 8038 | ok |
| restaurant_nbhd0_s1 | E2 | 8 | 28135 | 8038 | ok |
| restaurant_nbhd0_s2 | E2 | 8 | 28135 | 8038 | ok |
| restaurant_nbhd1_s0 | E2 | 8 | 14782 | 4223 | ok |
| restaurant_nbhd1_s1 | E2 | 8 | 14782 | 4223 | ok |
| restaurant_nbhd1_s2 | E2 | 8 | 14782 | 4223 | ok |
| restaurant_nbhd2_s0 | E2 | 8 | 12922 | 3692 | ok |
| restaurant_nbhd2_s1 | E2 | 8 | 12922 | 3692 | ok |
| restaurant_nbhd2_s2 | E2 | 8 | 12922 | 3692 | ok |
| restaurant_noise_E2-0 | E2 | 6 | 2119 | 605 | ok |
| restaurant_noise_E2-1 | E2 | 6 | 1779 | 508 | ok |
| restaurant_noise_E2-2 | E2 | 6 | 1669 | 476 | ok |
| restaurant_noise_E2-6 | E2 | 6 | 1817 | 519 | ok |
| restaurant_noise_E2-7 | E2 | 6 | 2076 | 593 | ok |
| restaurant_noise_E2-9 | E2 | 6 | 2147 | 613 | ok |
| restaurant_noise_E2-10 | E2 | 6 | 2174 | 621 | ok |
| restaurant_noise_E2-11 | E2 | 6 | 2231 | 637 | ok |
| restaurant_noise_E2-15 | E2 | 6 | 2012 | 574 | ok |
| restaurant_noise_E2-17 | E2 | 6 | 2039 | 582 | ok |
| restaurant_noise_E2-18 | E2 | 6 | 1486 | 424 | ok |
| restaurant_noise_E2-19 | E2 | 6 | 2114 | 604 | ok |
| restaurant_noise_E2-20 | E2 | 6 | 1506 | 430 | ok |
| restaurant_noise_E2-26 | E2 | 6 | 1594 | 455 | ok |
| restaurant_noise_E2-29 | E2 | 6 | 1669 | 476 | ok |
| restaurant_noise_E2-40 | E2 | 6 | 1476 | 421 | ok |
| restaurant_noise_E2-42 | E2 | 6 | 1645 | 470 | ok |
| restaurant_noise_E2-46 | E2 | 6 | 1534 | 438 | ok |
| restaurant_noise_E2-48 | E2 | 6 | 1621 | 463 | ok |
| restaurant_noise_E2-51 | E2 | 6 | 1192 | 340 | ok |
| restaurant_noise_E2-3 | E2 | 6 | 1895 | 541 | ok |
| restaurant_noise_E2-4 | E2 | 6 | 1092 | 312 | ok |
| restaurant_noise_E2-8 | E2 | 6 | 1320 | 377 | ok |
| restaurant_noise_E2-14 | E2 | 6 | 2178 | 622 | ok |
| restaurant_noise_E2-16 | E2 | 6 | 1222 | 349 | ok |
| restaurant_noise_E2-23 | E2 | 6 | 1086 | 310 | ok |
| restaurant_noise_E2-25 | E2 | 6 | 917 | 262 | ok |
| restaurant_noise_E2-27 | E2 | 6 | 992 | 283 | ok |
| restaurant_noise_E2-28 | E2 | 6 | 1167 | 333 | ok |
| restaurant_noise_E2-30 | E2 | 6 | 1427 | 407 | ok |
| restaurant_noise_E2-32 | E2 | 6 | 1466 | 418 | ok |
| restaurant_noise_E2-36 | E2 | 6 | 1042 | 297 | ok |
| restaurant_noise_E2-37 | E2 | 6 | 1219 | 348 | ok |
| restaurant_noise_E2-41 | E2 | 6 | 983 | 280 | ok |
| restaurant_noise_E2-49 | E2 | 6 | 1246 | 356 | ok |
| restaurant_noise_E2-50 | E2 | 6 | 1608 | 459 | ok |
| restaurant_noise_E2-52 | E2 | 6 | 1025 | 292 | ok |
| restaurant_noise_E2-53 | E2 | 6 | 1515 | 432 | ok |
| restaurant_noise_E2-54 | E2 | 6 | 1150 | 328 | ok |
| restaurant_noise_E2-56 | E2 | 6 | 1167 | 333 | ok |
| restaurant_noise_E2-5 | E2 | 6 | 1092 | 312 | ok |
| restaurant_noise_E2-12 | E2 | 6 | 2255 | 644 | ok |
| restaurant_noise_E2-13 | E2 | 6 | 908 | 259 | ok |
| restaurant_noise_E2-21 | E2 | 6 | 1954 | 558 | ok |
| restaurant_noise_E2-22 | E2 | 6 | 1086 | 310 | ok |
| restaurant_noise_E2-24 | E2 | 6 | 1071 | 306 | ok |
| restaurant_noise_E2-31 | E2 | 6 | 1263 | 360 | ok |
| restaurant_noise_E2-33 | E2 | 6 | 1001 | 286 | ok |
| restaurant_noise_E2-34 | E2 | 6 | 1014 | 289 | ok |
| restaurant_noise_E2-35 | E2 | 6 | 1016 | 290 | ok |
| restaurant_noise_E2-38 | E2 | 6 | 1290 | 368 | ok |
| restaurant_noise_E2-39 | E2 | 6 | 1211 | 346 | ok |
| restaurant_noise_E2-43 | E2 | 6 | 1208 | 345 | ok |
| restaurant_noise_E2-44 | E2 | 6 | 1332 | 380 | ok |
| restaurant_noise_E2-45 | E2 | 6 | 1420 | 405 | ok |
| restaurant_noise_E2-47 | E2 | 6 | 1402 | 400 | ok |
| restaurant_noise_E2-55 | E2 | 6 | 1022 | 292 | ok |
| restaurant_gate_E2-0 | E2 | 16 | 3911 | 1117 | ok |
| restaurant_split_E2-0 | E2 | 16 | 3965 | 1132 | ok |
| restaurant_gate_E2-7 | E2 | 16 | 4096 | 1170 | ok |
| restaurant_split_E2-7 | E2 | 16 | 4150 | 1185 | ok |
| restaurant_gate_E2-9 | E2 | 16 | 3095 | 884 | ok |
| restaurant_split_E2-9 | E2 | 16 | 3149 | 899 | ok |
| restaurant_gate_E2-10 | E2 | 16 | 4281 | 1223 | ok |
| restaurant_split_E2-10 | E2 | 16 | 4335 | 1238 | ok |
| restaurant_gate_E2-11 | E2 | 16 | 4389 | 1254 | ok |
| restaurant_split_E2-11 | E2 | 16 | 4443 | 1269 | ok |
| restaurant_gate_E2-12 | E2 | 16 | 4203 | 1200 | ok |
| restaurant_split_E2-12 | E2 | 16 | 4257 | 1216 | ok |
| restaurant_gate_E2-14 | E2 | 16 | 4041 | 1154 | ok |
| restaurant_split_E2-14 | E2 | 16 | 4095 | 1170 | ok |
| restaurant_gate_E2-15 | E2 | 16 | 3649 | 1042 | ok |
| restaurant_split_E2-15 | E2 | 16 | 3703 | 1058 | ok |
| restaurant_gate_E2-17 | E2 | 16 | 4361 | 1246 | ok |
| restaurant_split_E2-17 | E2 | 16 | 4415 | 1261 | ok |
| restaurant_gate_E2-19 | E2 | 16 | 2631 | 751 | ok |
| restaurant_split_E2-19 | E2 | 16 | 2685 | 767 | ok |

## Estimated prompt tokens per variant (stage 1)

B = seed-0 entity jobs + all split jobs; C = 3 orders + all split jobs; D = C + noise + gate jobs (upper bound: all split jobs are counted although only gate-failed clusters run; reconcile jobs are stage 2 and not counted).

| entity | variant | calls | est. prompt tokens |
|---|---|---|---|
| train | B | 14 | 21793 |
| train | C | 18 | 42357 |
| train | D | 59 | 66810 |
| hotel | B | 11 | 19746 |
| hotel | C | 15 | 39526 |
| hotel | D | 55 | 62522 |
| restaurant | B | 13 | 27148 |
| restaurant | C | 19 | 59054 |
| restaurant | D | 86 | 93833 |
