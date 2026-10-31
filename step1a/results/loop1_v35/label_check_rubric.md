# MultiWOZ label check rubric (T7, wf_v3.5)

Each row: a value said by the system in a hotel / train / restaurant dialogue, the full turn, and a MultiWOZ label `<domain>-<slot>`. Domain "booking" means a booking of the dialogue's current entity.

Judge only whether the label is right for that value in that turn. Answer exactly one of:
- **right**: the value is that slot (for example "TR6210" → train-trainid; "105 minutes" → train-duration).
- **wrong_slot**: the value is a real attribute value, but of another slot (for example "City Centre" labelled restaurant-address when it is the area).
- **wrong_domain**: the slot is right but it belongs to another entity (for example a hotel name labelled restaurant-name).
- **not_value**: the span is not an attribute value at all (a count of results, a general word, a broken span).

When unsure, pick the stricter label (any wrong label over right). Use no outside knowledge beyond the turn.
