# Signals summary: dev50

Entity | columns | instances | same-entity pairs (>=1) | cross pairs with it | FD holds | trivial | too few
---|---|---|---|---|---|---|---
train | 16 | 29 | 98 | 327 | 20 | 55 | 58
hotel | 19 | 22 | 115 | 319 | 15 | 26 | 130
restaurant | 20 | 35 | 127 | 346 | 12 | 59 | 112

Cross-entity FDs (columns of different entities, dialogues with one instance each side): 4 hold, 224 trivial, 596 too few, 112 fail.

Name test: name_score = coverage x mean(distinct ratio capped at 1, 1 - repeated share, first share); rank 1 per entity:

- train: 'departure time' (0.518, 23 instances)
- hotel: 'hotel name' (0.544, 18 instances)
- restaurant: 'restaurant name' (0.533, 29 instances)

FD: holds = n >= 3 and share >= 0.9; trivial = no X value occurs twice; too_few = n < 3.
