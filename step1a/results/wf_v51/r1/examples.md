# wf_v5.1 R1 examples: two mixed-role clusters (dev50)

Before = adopted clusters (alpha 0). After = alpha 0.3, t 0.25 (chosen on dev50). Snippets: 4 words left, [value], 2 words right (the vector sees the value masked as its type tag).

## 1. cluster E1#1 (train, 89 mentions): roles Train leave at / Train arrive by

- Train leave at (56 mentions)
  - `train that leaves at [20:45] from stevenage`
  - `trains, TR9448 leaves at [5:54] would that`
- Train arrive by (31 mentions)
  - `Stansted airport, arriving by [20:30] .`
  - `gets you there at [06:08] . Need`

After (alpha 0.3, t 0.25): the 89 mentions go to

| new cluster | mentions from this cluster | Train leave at | Train arrive by |
|---|---|---|---|
| E1#1 | 87 | 56 | 29 |
| E1#33 | 2 | 0 | 2 |

## 2. cluster E1#3 (train, 45 mentions): roles Train destination / Train departure

- Train destination (22 mentions)
  - `a train going to [cambridge] .`
  - `want to be in [Cambridge] by 11:30,`
- Train departure (21 mentions)
  - `I need to leave [Cambridge] on Friday.`
  - `It will arrive in [Cambridge] at 20:08`

After (alpha 0.3, t 0.25): the 45 mentions go to

| new cluster | mentions from this cluster | Train destination | Train departure |
|---|---|---|---|
| E1#3 | 44 | 22 | 20 |
| E1#32 | 1 | 0 | 1 |

