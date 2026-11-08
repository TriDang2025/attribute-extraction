# Loop 2 named probe, dev50

Labels: `results/wf_v41/step1b/labels_dev50.json`; run 127 s. Config: k=40, threshold=0.3, min_dialogues=3, min_support=0.05, max_overlap=0.5.
Keep rule: n_dialogues >= min_dialogues and support >= min_support and overlap < max_overlap.

| entity | labels | kept | dropped |
|---|---|---|---|
| train | 9 | 1 | 8 |
| hotel | 8 | 2 | 6 |
| restaurant | 8 | 0 | 8 |

| id | label | keep | mentions | dialogues | support | cohesion | overlap (column) | top values | reason |
|---|---|---|---|---|---|---|---|---|---|
| L2:train#0 | ticket class | drop | 1 | 1 | 0.034 | - | 1.00 (train id) | tr7610 | n_dialogues 1 < 3; support 0.034 < 0.05; overlap 1.000 >= 0.5 (mostly column 'train id') |
| L2:train#1 | seating preference | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2:train#2 | train operator | drop | 6 | 5 | 0.172 | 0.631 | 0.83 (train id) | tr1719, tr6193, tr7604 | overlap 0.833 >= 0.5 (mostly column 'train id') |
| L2:train#3 | return date | drop | 9 | 7 | 0.241 | 0.637 | 0.89 (travel date) | what day, 21:29, friday | overlap 0.889 >= 0.5 (mostly column 'travel date') |
| L2:train#4 | return time | drop | 20 | 13 | 0.448 | 0.670 | 0.90 (departure time) | 105 minute, 05:01, 06:40 | overlap 0.900 >= 0.5 (mostly column 'departure time') |
| L2:train#5 | ticket type | drop | 6 | 5 | 0.172 | 0.487 | 0.50 (train id) | ticket, gj3062pe, tr1110 | overlap 0.500 >= 0.5 (mostly column 'train id') |
| L2:train#6 | passenger type | keep | 3 | 3 | 0.103 | 0.667 | 0.33 (reference number) | i, rjoua7e1 | all checks passed |
| L2:train#7 | discount card | drop | 7 | 6 | 0.207 | 0.472 | 0.86 (reference number) | 1r61po9r, ji5o0vtt, tr7610 | overlap 0.857 >= 0.5 (mostly column 'reference number') |
| L2:train#8 | route type | drop | 11 | 8 | 0.276 | 0.617 | 0.55 (train id) | train, friday train, the train | overlap 0.545 >= 0.5 (mostly column 'train id') |
| L2:hotel#0 | room type | drop | 9 | 6 | 0.304 | 0.665 | 0.67 (star rating) | guesthouse, 4 star, 4 star guesthouse | overlap 0.667 >= 0.5 (mostly column 'star rating') |
| L2:hotel#1 | bed type | drop | 2 | 2 | 0.087 | 0.443 | 1.00 (star rating) | 4 star, cityroomz | n_dialogues 2 < 3; overlap 1.000 >= 0.5 (mostly column 'star rating') |
| L2:hotel#2 | internet access | keep | 16 | 10 | 0.478 | 0.944 | 0.00 (-) | free wifi, free internet, free wi-fi | all checks passed |
| L2:hotel#3 | parking available | keep | 10 | 7 | 0.304 | 0.943 | 0.00 (-) | free parking, parking | all checks passed |
| L2:hotel#4 | breakfast included | drop | 1 | 1 | 0.043 | - | 1.00 (hotel name) | alexander bed and breakfast | n_dialogues 1 < 3; support 0.043 < 0.05; overlap 1.000 >= 0.5 (mostly column 'hotel name') |
| L2:hotel#5 | pet friendly | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2:hotel#6 | wheelchair accessible | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2:hotel#7 | smoking allowed | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2:restaurant#0 | dietary restriction | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2:restaurant#1 | outdoor seating | drop | 1 | 1 | 0.029 | - | 1.00 (restaurant address) | 4 - 6 rose crescent | n_dialogues 1 < 3; support 0.029 < 0.05; overlap 1.000 >= 0.5 (mostly column 'restaurant address') |
| L2:restaurant#2 | alcohol served | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2:restaurant#3 | dress code | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2:restaurant#4 | wheelchair accessible | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2:restaurant#5 | kid friendly | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2:restaurant#6 | takeout available | drop | 5 | 4 | 0.114 | 0.524 | 0.80 (restaurant name) | 2 available restaurant, good luck chinese food takeaway, lucky star | overlap 0.800 >= 0.5 (mostly column 'restaurant name') |
| L2:restaurant#7 | accepted payment | drop | 1 | 1 | 0.029 | - | 1.00 (restaurant name) | pizza express | n_dialogues 1 < 3; support 0.029 < 0.05; overlap 1.000 >= 0.5 (mostly column 'restaurant name') |
