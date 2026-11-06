# Signals summary: dev50b

Entity | columns | instances | same-entity pairs (>=1) | cross pairs with it | FD holds | trivial | too few
---|---|---|---|---|---|---|---
train | 12 | 18 | 57 | 237 | 7 | 55 | 24
hotel | 17 | 25 | 111 | 262 | 9 | 37 | 112
restaurant | 18 | 28 | 120 | 279 | 17 | 51 | 98

Cross-entity FDs (columns of different entities, dialogues with one instance each side): 17 hold, 127 trivial, 562 too few, 64 fail.

Name test: name_score = coverage x mean(distinct ratio capped at 1, 1 - repeated share, first share); rank 1 per entity:

- train: 'departure time' (0.611, 17 instances)
- hotel: 'generic accommodation type' (0.483, 19 instances)
- restaurant: 'restaurant name' (0.430, 18 instances)

FD: holds = n >= 3 and share >= 0.9; trivial = no X value occurs twice; too_few = n < 3.
