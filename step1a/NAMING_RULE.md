# Naming rule (name rubric, wf_v3.1)

One category per attribute row of `name_rubric.csv` (`category`; two raters fill `rater1`, `rater2`; `final` after
they agree). Judge the generated `name` (and its `description` only to see what the model meant) against what the
cluster really holds: its majority gold attribute (`majority_gold_attr`) and its top values (`top_values`). Judge the
name alone; do not reward a good description.

A cluster with `label` = `valid_new` (a real attribute that TEAR has no gold for) has no gold attribute: judge the
name against the top values only, with the same categories.

Real clusters (`label` gold or valid_new):
- `exact`: the name says the gold attribute (or, for valid_new, what the values are) with the right role.
  Wording differences in case, plural or `_` do not matter.
  - `departure_station` for `Train departure` (values: cambridge, london kings cross).
  - `restaurant_food_type` for `Restaurant food` (values: italian, chinese).
- `synonym`: a different word for the same thing, same role.
  - `price_range` for `Hotel price range` (cheap, moderate); `eat_time` for `Restaurant requested time`.
  - `number_of_guests` for `Hotel requested people` (2, 5).
- `too_general`: true for the values but does not separate this attribute from its siblings (a role or slot is
  missing).
  - `time` for `Train arrive by` while `Train leave at` exists (values 16:30, 17:15).
  - `station` for `Train destination` (values: london liverpool street, cambridge).
- `wrong_role`: the right kind of thing but the opposite or another role of a pair (departure/destination,
  leave at/arrive by).
  - `destination_station` for a cluster whose majority is `Train departure`.
  - `arrive_by_time` for `Taxi leave at`.
- `wrong`: names something else (another slot or entity, or a value class that does not fit).
  - `hotel_area` for `Hotel stars` (values: 3, 4, 5).
  - `reference_number` for `Train day` (values: monday, friday).

Noise clusters (`label` noise: chit-chat, yes/no, booking words, values that are not database values):
- `noise_marked`: the response marked it `not_attribute` (no name). This is the right outcome.
  - a cluster of `yes`, `ok`, `thank you` marked `not_attribute`.
  - a cluster of `booking`, `reservation` words marked `not_attribute`.
- `noise_named`: the response gave the noise cluster a name as an attribute (kept or merged), whatever the name.
  - a cluster of `yes`, `sure` named `confirmation`.
  - a cluster of `please`, `thanks` named `politeness_marker`.

Rules for borderline cases:
- A merged attribute is judged on its name against the majority gold attribute of the merged mentions. If the
  merge mixes two gold classes the name can be at best `too_general`.
- A split part is judged like any other attribute on its own mentions.
- Unsure rows (no name, not marked as `not_attribute` by the model) on a real cluster: `wrong`; on a noise
  cluster: `noise_marked`.
- When two categories fit, take the one lower in the list above (exact > synonym > too_general > wrong_role > wrong).

Scores (`s1a/pilot_score.rubric_accuracy`, rows with a `final` only):
- name accuracy on real clusters = (exact + synonym) / all real rows;
- on noise clusters = noise_marked / all noise rows (noise_named is the miss);
- role accuracy: real rows whose majority gold slot is departure, destination, leave at or arrive by (in any gold
  entity): (exact + synonym) / all of them; the `wrong_role` count is reported next to it.
