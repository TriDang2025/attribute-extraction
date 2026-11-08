# Loop 2 sensitivity check (diary Nov 7, task 3)

Report only: the keep rule is unchanged (n_dialogues >= 3, support >= 0.05, overlap < 0.5). Labels: the Step 1b dry-run labels. Cell = clusters kept / labels. **Bold** = the frozen default (k 40, threshold 0.3).

## dev50 (25 labels)

| threshold \ k | 20 | 40 | 80 |
|---|---|---|---|
| 0.2 | 5/25 | 5/25 | 5/25 |
| 0.3 | 2/25 | **3/25** | 2/25 |
| 0.4 | 2/25 | 2/25 | 2/25 |

Which clusters are kept (K = kept) and support at the default threshold 0.3:

| cluster | label | k20/t0.2 | k40/t0.2 | k80/t0.2 | k20/t0.3 | k40/t0.3 | k80/t0.3 | k20/t0.4 | k40/t0.4 | k80/t0.4 | support k40 | support all turns | entity turns |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L2_train#0 | ticket class | - | - | - | - | - | - | - | - | - | 0.035 | 0.103 | 243 |
| L2_train#1 | seating preference | K | K | K | - | - | - | - | - | - | 0.000 | 0.138 | 243 |
| L2_train#2 | train operator | - | - | - | - | - | - | - | - | - | 0.172 | 0.759 | 243 |
| L2_train#3 | return date | - | - | - | - | - | - | - | - | - | 0.241 | 0.966 | 243 |
| L2_train#4 | return time | - | - | - | - | - | - | - | - | - | 0.448 | 0.966 | 243 |
| L2_train#5 | ticket type | K | - | - | - | - | - | - | - | - | 0.172 | 0.483 | 243 |
| L2_train#6 | passenger type | - | K | K | - | K | - | - | - | - | 0.103 | 0.414 | 243 |
| L2_train#7 | discount card | - | - | - | - | - | - | - | - | - | 0.207 | 0.690 | 243 |
| L2_train#8 | route type | K | K | K | - | - | - | - | - | - | 0.276 | 0.862 | 243 |
| L2_hotel#0 | room type | - | - | - | - | - | - | - | - | - | 0.304 | 0.652 | 187 |
| L2_hotel#1 | bed type | - | - | - | - | - | - | - | - | - | 0.087 | 0.217 | 187 |
| L2_hotel#2 | internet access | K | K | K | K | K | K | K | K | K | 0.478 | 0.522 | 187 |
| L2_hotel#3 | parking available | K | K | K | K | K | K | K | K | K | 0.304 | 0.391 | 187 |
| L2_hotel#4 | breakfast included | - | - | - | - | - | - | - | - | - | 0.043 | 0.043 | 187 |
| L2_hotel#5 | pet friendly | - | - | - | - | - | - | - | - | - | 0.000 | 0.000 | 187 |
| L2_hotel#6 | wheelchair accessible | - | - | - | - | - | - | - | - | - | 0.000 | 0.087 | 187 |
| L2_hotel#7 | smoking allowed | - | - | - | - | - | - | - | - | - | 0.000 | 0.000 | 187 |
| L2_restaurant#0 | dietary restriction | - | - | - | - | - | - | - | - | - | 0.000 | 0.057 | 245 |
| L2_restaurant#1 | outdoor seating | - | - | - | - | - | - | - | - | - | 0.029 | 0.314 | 245 |
| L2_restaurant#2 | alcohol served | - | - | - | - | - | - | - | - | - | 0.000 | 0.000 | 245 |
| L2_restaurant#3 | dress code | - | - | - | - | - | - | - | - | - | 0.000 | 0.029 | 245 |
| L2_restaurant#4 | wheelchair accessible | - | - | - | - | - | - | - | - | - | 0.000 | 0.029 | 245 |
| L2_restaurant#5 | kid friendly | - | - | - | - | - | - | - | - | - | 0.000 | 0.000 | 245 |
| L2_restaurant#6 | takeout available | - | - | - | - | - | - | - | - | - | 0.114 | 0.514 | 245 |
| L2_restaurant#7 | accepted payment | - | - | - | - | - | - | - | - | - | 0.029 | 0.057 | 245 |

## dev50b (5 labels)

| threshold \ k | 20 | 40 | 80 |
|---|---|---|---|
| 0.2 | 2/5 | 2/5 | 2/5 |
| 0.3 | 2/5 | **2/5** | 2/5 |
| 0.4 | 2/5 | 2/5 | 2/5 |

Which clusters are kept (K = kept) and support at the default threshold 0.3:

| cluster | label | k20/t0.2 | k40/t0.2 | k80/t0.2 | k20/t0.3 | k40/t0.3 | k80/t0.3 | k20/t0.4 | k40/t0.4 | k80/t0.4 | support k40 | support all turns | entity turns |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L2_train#0 | ticket class | - | - | - | - | - | - | - | - | - | 0.000 | 0.000 | 117 |
| L2_train#1 | return ticket | - | - | - | - | - | - | - | - | - | 0.278 | 0.722 | 117 |
| L2_hotel#0 | free parking | K | K | K | K | K | K | K | K | K | 0.560 | 0.600 | 232 |
| L2_hotel#1 | free wifi | K | K | K | K | K | K | K | K | K | 0.400 | 0.400 | 232 |
| L2_restaurant#0 | vegetarian options | - | - | - | - | - | - | - | - | - | 0.000 | 0.000 | 191 |
