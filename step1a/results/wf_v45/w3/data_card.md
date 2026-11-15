# wf_v4.5 W3: cost-test corpora (data card)

- **Use:** cost test only (no labels, nothing tuned on them).
- **Sizes:** 50, 100, 200, 300, 500, 1000; each smaller set is the start of the bigger one.
- **50-300:** TEAR's non-test pool (`tear/data/conversation/pool.jsonl`) in its own order: n50 = dev50, n100 = dev50 + dev50b.
- **500, 1000:** n300 plus raw MultiWOZ 2.2 dialogues (`C:/Users/nguye/data/MultiWOZ_2.2`, train + dev + test files), shuffled with seed 0. Text built as TEAR does: `User:` / `System:` lines, space before . , ! ? removed.
- **Overlap check** against TEAR's test set (700) and the pool (300), by dialogue id and by text hash (sha1 of lowercase letters and digits):

| count | value |
|---|---|
| multiwoz dialogues | 10437 |
| removed by id | 1000 |
| removed by text hash | 3 |
| kept candidates | 9434 |
| extra used | 700 |
| tear test ids in mwoz | 700 |
| pool format match | 257 |

Format check: rebuilding the pool from MultiWOZ this way gives TEAR's exact text for 257/300 dialogues; the rest differ only in TEAR's other small clean-ups, so the extra texts are close to, not identical with, TEAR's format.

| corpus | dialogues | from pool | from MultiWOZ | characters |
|---|---|---|---|---|
| n50 | 50 | 50 | 0 | 60,596 |
| n100 | 100 | 100 | 0 | 113,931 |
| n200 | 200 | 200 | 0 | 220,087 |
| n300 | 300 | 300 | 0 | 332,840 |
| n500 | 500 | 300 | 200 | 542,626 |
| n1000 | 1000 | 300 | 700 | 1,070,881 |

Files: `data/wf_v45_corpora/n<size>.jsonl` (gitignored; rebuild with `python scripts/w3_corpora_v45.py`), ids in `results/wf_v45/w3/ids.json`.
