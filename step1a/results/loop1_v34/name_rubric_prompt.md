# Name rating prompt (wf_v3.4, blind raters)

Task: for each row of `names_to_rate.csv`, rate the generated attribute `name` against what the cluster really holds. Use `majority_gold_attr` (the TEAR gold attribute most mentions belong to; empty = no gold), `role`, `cluster_label` (real / mixed / noise) and `top_values`. Judge the name alone; ignore how good the description is (it only shows what the model meant). Domain: MultiWOZ train, hotel, restaurant.

Output format: CSV with one line per input row, `row,label` (header `row,label`), label one of the five below.

## Labels
- `right`: the name says the gold attribute (or, with no gold, what the values are) with the right role. Wording, plural, case and `_` do not matter.
  - `departure_station` for `Train departure` (values: cambridge, london kings cross).
  - `price_range` for `Hotel price range` (values: cheap, moderate).
- `too_general`: true for the values but does not tell this attribute from its siblings (a slot or role is missing).
  - `time` for `Train arrive by` while `Train leave at` exists (values: 16:30, 17:15).
  - `station` for `Train destination` (values: london liverpool street, cambridge).
- `wrong_role`: the right kind of thing but the opposite or another role of a pair (departure/destination, leave at/arrive by).
  - `destination_station` for a cluster whose majority is `Train departure`.
  - `arrive_by_time` for a cluster whose majority is `Train leave at`.
- `valid_extra`: the cluster has no gold attribute but the name correctly describes a real database-style value that TEAR has no gold for.
  - `train_id` for values tr1234, tr5678 (majority gold empty).
  - `ticket_price` for values 23.60 pounds, 9.40 pounds (majority gold empty).
- `wrong`: names something else (another slot or entity, or a value class that does not fit), or a named attribute for chit-chat.
  - `hotel_area` for `Hotel stars` (values: 3, 4, 5).
  - `reference_number` for `Train day` (values: monday, friday).

## Rules
- Mixed cluster (`cluster_label` = mixed): the name is `right` only if it matches a part of the cluster that holds at least 60% of the mentions; otherwise it is at best `too_general`.
- Empty name = the model marked the cluster as not a column: `right` if the cluster is noise or a cue, else `wrong`. (Such rows are not in `names_to_rate.csv`; the scorer applies this rule itself.)
- When two labels fit, the lower one wins: right > too_general > wrong_role > valid_extra > wrong (right is best, wrong is lowest).
