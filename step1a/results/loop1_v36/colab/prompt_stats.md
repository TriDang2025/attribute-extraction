# wf_v3.6 Colab batch prompts (run `results/graph_v22_dev50`, seed 0)

Tokens are estimated as chars / 3.5, plus 300 for the carry block of F2 carry jobs (their `.txt` is written on Colab). k drops 8 -> 6 -> 5 when a prompt reaches 28000. Output tokens: A and AE = the v3.1 A answer of the entity (`<ent>_v2_r1`); F2 = the v3.3 F answer of the same job; oracle and g = the v3.5 estimates (copied).

| prompt | entity | k | chars | est. prompt tokens | est. output tokens | status |
|---|---|---|---|---|---|---|
| train_v2_s2 | E1 | 8 | 32252 | 9214 | 1886 | ok |
| train_ae_s0 | E1 | 8 | 32364 | 9246 | 1886 | ok |
| train_ae_s1 | E1 | 8 | 32364 | 9246 | 1886 | ok |
| train_ae_s2 | E1 | 8 | 32364 | 9246 | 1886 | ok |
| train_f2_nbhd0_s0 | E1 | 8 | 10088 | 2882 | 864 | ok |
| train_f2_nbhd1_s0 | E1 | 8 | 26987 | 8010 | 3607 | ok |
| hotel_v2_s2 | E0 | 8 | 30852 | 8814 | 2502 | ok |
| hotel_ae_s0 | E0 | 8 | 30964 | 8846 | 2502 | ok |
| hotel_ae_s1 | E0 | 8 | 30964 | 8846 | 2502 | ok |
| hotel_ae_s2 | E0 | 8 | 30964 | 8846 | 2502 | ok |
| hotel_f2_nbhd0_s0 | E0 | 8 | 24726 | 7064 | 3001 | ok |
| hotel_f2_nbhd1_s0 | E0 | 8 | 10865 | 3404 | 837 | ok |
| restaurant_v2_s2 | E2 | 8 | 48711 | 13917 | 4365 | ok |
| restaurant_ae_s0 | E2 | 8 | 48823 | 13949 | 4365 | ok |
| restaurant_ae_s1 | E2 | 8 | 48823 | 13949 | 4365 | ok |
| restaurant_ae_s2 | E2 | 8 | 48823 | 13949 | 4365 | ok |
| restaurant_f2_nbhd0_s0 | E2 | 8 | 28680 | 8194 | 1903 | ok |
| restaurant_f2_nbhd1_s0 | E2 | 8 | 15343 | 4683 | 1502 | ok |
| restaurant_f2_nbhd2_s0 | E2 | 8 | 13483 | 4152 | 1314 | ok |
| train_oracle_nbhd0_s0 | E1 | reused | - | 4124 | 1556 | ok |
| train_oracle_nbhd0_s1 | E1 | reused | - | 4124 | 1556 | ok |
| train_oracle_nbhd0_s2 | E1 | reused | - | 4124 | 1556 | ok |
| train_oracle_nbhd1_s0 | E1 | reused | - | 7464 | 1729 | ok |
| train_oracle_nbhd1_s1 | E1 | reused | - | 7464 | 1729 | ok |
| train_oracle_nbhd1_s2 | E1 | reused | - | 7464 | 1729 | ok |
| train_g_nbhd0_s0 | E1 | reused | - | 2820 | 978 | ok |
| train_g_nbhd0_s1 | E1 | reused | - | 2820 | 978 | ok |
| train_g_nbhd0_s2 | E1 | reused | - | 2820 | 978 | ok |
| train_g_nbhd1_s0 | E1 | reused | - | 7643 | 1889 | ok |
| train_g_nbhd1_s1 | E1 | reused | - | 7643 | 1889 | ok |
| train_g_nbhd1_s2 | E1 | reused | - | 7643 | 1889 | ok |
| hotel_g_nbhd0_s0 | E0 | reused | - | 7002 | 1824 | ok |
| hotel_g_nbhd0_s1 | E0 | reused | - | 7002 | 1824 | ok |
| hotel_g_nbhd0_s2 | E0 | reused | - | 7002 | 1824 | ok |
| hotel_g_nbhd1_s0 | E0 | reused | - | 3037 | 1003 | ok |
| hotel_g_nbhd1_s1 | E0 | reused | - | 3037 | 1003 | ok |
| hotel_g_nbhd1_s2 | E0 | reused | - | 3037 | 1003 | ok |
| restaurant_g_nbhd0_s0 | E2 | reused | - | 8132 | 1700 | ok |
| restaurant_g_nbhd0_s1 | E2 | reused | - | 8132 | 1700 | ok |
| restaurant_g_nbhd0_s2 | E2 | reused | - | 8132 | 1700 | ok |
| restaurant_g_nbhd1_s0 | E2 | reused | - | 4316 | 1700 | ok |
| restaurant_g_nbhd1_s1 | E2 | reused | - | 4316 | 1700 | ok |
| restaurant_g_nbhd1_s2 | E2 | reused | - | 4316 | 1700 | ok |
| restaurant_g_nbhd2_s0 | E2 | reused | - | 3785 | 1445 | ok |
| restaurant_g_nbhd2_s1 | E2 | reused | - | 3785 | 1445 | ok |
| restaurant_g_nbhd2_s2 | E2 | reused | - | 3785 | 1445 | ok |

## Estimated calls and tokens per family

| family | calls | est. prompt tokens | est. output tokens |
|---|---|---|---|
| a_s2 | 3 | 31945 | 8753 |
| ae | 9 | 96123 | 26259 |
| f2 | 7 | 38389 | 13028 |
| oracle | 6 | 34764 | 9855 |
| g | 21 | 110205 | 31617 |
| total | 46 | 311426 | 89512 |

v3.5 batch: 28 calls, 158886 prompt, 45943 output tokens. Change: +18 calls, +152540 prompt, +43569 output tokens (the T8 rerun is dropped).

## F2 de-lexicalisation map

- F2 map: 276 strings (database names of hotel, restaurant, attraction, train stations, minus STOP, plus TR ids in the prompts).
- STOP (59): address, and, area, attraction, attractions, b and b, bar, bed and breakfast, bus, cab, cafe, cambridge, center, centre, church, cinema, city center, city centre, college, east, food, gallery, guest house, guest houses, guesthouse, guesthouses, hotel, hotels, house, lodge, museum, name, north, park, phone, place, pool, postcode, price, pub, restaurant, restaurants, road, room, south, station, street, swimming pool, taxi, taxis, the, theatre, time, town center, town centre, train, trains, travel time, west.
- v3.3 F map: 119 strings; 71 also in F2; 48 only in F (span strings, generic words, misspellings): abbey pool, alexander, astroturf pitch, barbecue restaurant, bishop stafford, bishop stortford, bishops stafford, british food, cafe uno, cambidge, cambridge, cambridge art theatre, cambridge leisure park, cambridge towninfo centre, cherry hinton, cherry hinton hall, cherry hinton road, cocum restaurant, college, don pasquale, finch bed and breakfast, gonville place, hotel, huntingdon road, king lynn, north part of cambridge, pizza hut, pool way, restaurant, restaurant 2 2, room, stansted, the acorn guest house, the ashley hotel, the cambridge art theatre, the cambridge arts theatre, the cineworld cinema, the finch bed and breakfast, the finches bed and breakfast, the huntingdon marriott, the restaurant, the tandoori palace, the whale of a time, travel time, traveller rest, university arm, university arm hotel, university arms.

## Byte check of A against v3.1 (LF text)

| entity | check | result |
|---|---|---|
| train | A order None vs v2.txt | identical |
| train | A order 1 vs v2_r2.txt | identical |
| hotel | A order None vs v2.txt | identical |
| hotel | A order 1 vs v2_r2.txt | identical |
| restaurant | A order None vs v2.txt | identical |
| restaurant | A order 1 vs v2_r2.txt | identical |
