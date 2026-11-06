# wf_v4 Colab batch: calls and estimated tokens (dry run with a fake model)

Tokens estimated as chars / 3.5; the notebook counts exact tokens (stop above 20,000 for first prompts, 30,000 for any). Prompts of stages 2+ come from fake answers (lower bounds); output tokens: see scripts/dry_run_v4.py.

| stage | family | calls | est. prompt tokens | per call | largest prompt | est. output tokens |
|---|---|---|---|---|---|---|
| 1 | s4_41 | 25 | 209,805 | 8,392 | 13,512 | 18,160 |
| 1 | s4_e | 6 | 100,728 | 16,788 | 17,825 | 15,000 |
| 2 | s4_42 | 25 | 163,425 | 6,537 | 11,454 | 12,500 |
| 3 | s4_43 | 25 | 167,688 | 6,707 | 11,633 | 15,000 |
| 4 | s4_44 | 25 | 172,597 | 6,903 | 11,830 | 46,390 |
| 5 | s4_place | 2 | 2,271 | 1,135 | 1,176 | 240 |
| 6 | s4_place | 2 | 2,311 | 1,155 | 1,198 | 240 |
| 7 | s4_place | 2 | 2,276 | 1,138 | 1,172 | 240 |
| 8 | s4_place | 2 | 2,371 | 1,185 | 1,219 | 240 |
| 9 | s4_place | 2 | 2,300 | 1,150 | 1,174 | 240 |
| total | | 116 | 825,772 | 7,118 | 17,825 | 108,250 |
