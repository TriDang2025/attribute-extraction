# Names against L2 slot names: rubric (wf_v3.6)

Each row is one attribute group that a system proposed for a dialogue entity (hotel, restaurant, train). You see the
group's name and description, its most frequent values, and the MultiWOZ slot (name and schema description) that most
of the group's values carry. Judge only whether the group's name fits that slot. Answer with exactly one label:

- **right**: the name means the slot (for example "arrival_time" for train-arriveby; "reference_number" for a
  booking reference). Wording may differ.
- **partly**: the name is related but too general, too specific, or mixes the slot with another (for example
  "time" for train-arriveby, or "location" for train-destination).
- **wrong**: the name means something else (for example "departure" for train-destination, or "price" for
  hotel-stars).

Rules:
- Use the values to understand the group; judge the name, not the values.
- If unsure between right and partly, pick partly; if unsure between partly and wrong, pick wrong.
- Use no outside knowledge beyond this row.

Answer file: `row,label` (one line per row, labels right / partly / wrong).
