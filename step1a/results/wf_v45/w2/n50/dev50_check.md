# W2 dev50 check

Step 4: v43

## Step 3 final columns vs frozen wf_v4.4 T4

| entity | columns (corpus) | columns (frozen) | same names | only corpus | only frozen |
|---|---|---|---|---|---|
| hotel | 22 | 23 | 19 | area, num stars, people | day, day of week, location part, postcode |
| train | 15 | 14 | 11 | day of week, departure location, location str, reference number | booking id, price, time int |
| restaurant | 23 | 21 | 20 | food type, num int, num str | price range |
| attraction | 15 | new | - | - | - |
| attraction_2 | 1 | new | - | - | - |

## Step 4 scored as dev50

# wf_v4.4 Step 4 (Llama-3.1-8B)

Scores with the v4.3 scorers (full GT; `scores.csv` has reachable-only too). Counts are summed over the finished chains of a row, F1 values are means. `vote` = the voted schema (one chain per input and set), `single` = the seed chains. GT columns in rest = GT columns held only in a "rest" column.

| input | set | schema | chains finished | table F1 | grouping F1 | GT columns placed | GT columns in rest | PK right (a) | PK right (b) | relationship recall | relationship precision | tables per chain | repairs per chain |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| a_llama44 | dev50 | single | 3/3 | 0.600 | 1.000 | 76/150 (0.507) | 0/150 (0.000) | 0/9 (0.000) | 9/9 (1.000) | n/a | n/a | 5-5 | 5.7 (3-7) |
| a_llama44 | all | single | 3/3 | 0.600 | 1.000 | 76/150 (0.507) | 0/150 (0.000) | 0/9 (0.000) | 9/9 (1.000) | n/a | n/a | 5-5 | 5.7 (3-7) |

Chains not finished: 0

| input | set | chains | calls | calls per chain | prompt tokens | output tokens | retried |
|---|---|---|---|---|---|---|---|
| a_llama44 | dev50 | 3 | 0 | 0.0 | 0 | 0 | 0 |
