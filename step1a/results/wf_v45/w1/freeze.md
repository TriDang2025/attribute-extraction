# wf_v4.5 W1: Step 4 freeze check

Single seed chains, means of F1, counts summed; full GT; corrected scorer. v4.3 values from the wf_v4.4 report (T6 table).

| check | v4.3 (corrected) | v4.4 other off | pass |
|---|---|---|---|
| GT columns placed, a_llama44 | 0.536 | 0.573 | yes |
| table F1, c1 | 0.753 | 0.652 | no |
| table F1, a_llama44 | 0.672 | 0.658 | no |

**Freeze: v4.3.**

- a_llama44: 6 chains, table F1 0.658, grouping F1 0.757, GT placed 173/302 (0.573)
- c1: 6 chains, table F1 0.652, grouping F1 0.743, GT placed 197/300 (0.657)
