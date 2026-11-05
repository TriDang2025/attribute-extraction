# wf_v3.9 prompt samples (verbatim)

## reconcile_dev50b_hotel_E1-0p0_o0

```text
Below is one part of a cluster of values taken from dialogue turns, and a list of other columns of the same table. Each
column has a name, a description (when there is one) and example values. The examples of the part are marked with [[ ]]
inside the turn they come from. Values that play different roles (where something starts and where it ends, the
earliest and the latest time) are different attributes. If unsure, answer none.

Part E1#0/0: name: specific guesthouse | description: names of specific guesthouses or hotels
Examples:
- 1 [system] previous turn, user: Thank you! I'm looking for a place to stay in the moderate price range. | turn: [[A and B guest house]] might fit your needs. Would you like me to book it?
- 2 [system] previous turn, user: Hi, I am planning my upcoming trip and am looking for a place to stay. Can you recommend something for me? | turn: Sure, I am fond of the [[acorn guest house]] personally. Did you have a price range that you'd like to stick to?
- 3 [system] previous turn, user: How about just 1 night? | turn: Okay, you are booked at the [[bridge guest house]] for 1 night (Saturday). Your reference number is NVYYU4ML. Can I help with anything else?
- 4 [system] previous turn, user: That is great. Can you provide me the phone number and price range of the best guest house? | turn: Yes the phone number to the [[acorn guest house]] 01223353888 with a price range of moderate
- 5 [system] previous turn, user: The location does not matter but I need a 3 star hotel. | turn: [[bridge guest house]] is a 3 star and a nice place.Do you want the address ?

Columns (5):
- name: number of accommodations | examples: 3 guesthouse; 29 hotel; 3 hotel
- name: generic accommodation type | examples: guesthouse; hotel; guest house
- name: accommodation type | description: type of accommodation, such as hotel or guesthouse | examples: alexander bed and breakfast; hobson house; el shaddai
- name: amenities | description: amenities provided by the accommodation | examples: room; city; cityroomz
- name: hotel name | examples: allenbell; the allenbell; the lensfield hotel

Question: Is this part the same attribute, with the same role, as one of these columns? Answer that column's name, or none.

Return ONLY one JSON object, nothing before or after it, with a reason of at most 25 words written before the answer: {"unit_id": "E1#0/0", "reason": "str", "same_as": "<column name or none>"}
```

## train_acue_dev50_s0 (first 2,600 chars of the instruction part, then the rest is as the v3.7 A prompt)

```text
You help design a database schema from a dialogue corpus. Below is ONE entity (a candidate table) found
by clustering text spans. Each cluster of the entity is a candidate attribute (column). Work in two steps.
1. Write the list of the entity's distinct attributes, each once: a snake_case name, a one-sentence
   description and a short role. Use role-specific names: when values play different roles (where
   something starts vs where it ends, the earliest vs the latest time allowed), give each role its own
   attribute and put the role in the name; do not use one general name for both.
2. Assign EVERY cluster to one listed attribute by name. Several clusters may share one attribute (then they
   are the same attribute). Use "not_attribute" for noise. Noise is common: yes, ok, thanks, booking words,
   and values that a database would not store. Use "attribute_cue" for clusters whose examples are questions or requests about an attribute rather than its values (what day, how many tickets, which area); it means an attribute exists but this cluster is not a column. If a cluster holds two attributes (two roles), assign its
   most frequent attribute and set "mixed" to true.
Also choose where each cluster belongs: pick ONE placement from the listed options and copy its text
exactly. Quote one example span as evidence. Examples are marked with [[...]] inside the turn they come from.
Lines labelled "automatic suggestion" are weak hints and can be wrong; decide from the examples.
Return ONLY one JSON object, nothing before or after it. Example of the shape (other names and values):
{"attributes": [{"name": "graduation_year", "description": "year the degree was finished", "role": "end of the studies"}],
 "clusters": [{"cluster_id": "E9#0", "attribute": "graduation_year", "evidence": "I finished in [[2019]]",
               "mixed": false, "placement": "current entity E9"},
              {"cluster_id": "E9#1", "attribute": "not_attribute", "evidence": "[[ok]] thanks",
               "mixed": false, "placement": "current entity E9"}]}

Entity E1: 29 clusters.

Placement options (copy one exactly into "placement"):
- current entity E1: the attribute belongs to E1
- sub-entity of E1: a part of E1 that has attributes of its own
- other entity E0: the attribute belongs to E0
- other entity E2: the attribute belongs to E2
- other entity E3: the attribute belongs to E3
- other entity E4: the attribute belongs to E4
- relationship(E1, E0): links E1 and E0
- relationship(E1, E2): links E1 and E2
- relationship(E1, E3): links E1 and E3
- relationship(E1, E4): links E1 and E4
...```

## dupcheck on reconciled columns (stage 2; shape shown on the unchanged dev50 train columns)

```text
Below is a list of columns proposed for one table. Each column has an id, a name, a description and example values.
Some columns are the same attribute listed twice (the same kind of value, with the same role, under two names or in two parts).
Find them: list every group of two or more columns that are the same attribute with the same role. Do not join columns that
are different attributes, and do not join columns whose values play different roles (for example where something starts
and where it ends). Leave a column out when it has no twin.

Columns (20):
1. name: arrival location | description: the location where the train arrives | examples: stansted airport; leicester; broxbourne
2. name: arrival time | examples: 19:30; 18:15; 18:24
3. name: day query | examples: what day
4. name: departure location | description: the location from which the train departs | examples: ely; norwich; peterborough
5. name: departure time | description: the time at which the train departs | examples: 12:00; 13:15; 15:45
6. name: destination city | examples: cambridge
7. name: local information center | examples: cambridge towninfo centre
8. name: number of people | examples: 1 child; 2 adult; 3 people
9. name: number of tickets | description: the number of tickets booked | examples: how many ticket; 16; 10
10. name: number of trains | examples: 1 train; 12; 19 train
11. name: origin city | examples: cambridge; cambidge
12. name: price per ticket | description: the cost of a single train ticket | examples: 10.10 pound; 12.80 pound; 14.08 pound
13. name: reference number | description: the reference number for the booking | examples: 1r61po9r; 64uq7m3g; 698re4w1
14. name: stay duration days | examples: 2 day
15. name: time query | examples: what time
16. name: total fee | examples: 66 gbp; 10.56 gbp; 40.4 gbp
17. name: train id | description: the unique identifier for the train | examples: tr9016; tr5713; tr5921
18. name: travel date | description: the date of the train journey | examples: saturday; friday; wednesday
19. name: travel time | description: the duration of the train journey | examples: 28-minute
20. name: travel time minutes | examples: 105 minute; 49 minute; 38 minute

Return ONLY one JSON object, nothing before or after it, in this shape (other ids): {"joins": [{"columns": [3, 7], "reason": "same value, same role"}]}. Use [] when nothing is joined.
```
