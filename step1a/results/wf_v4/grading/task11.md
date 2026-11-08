# wf_v4 task 11: grading agreement and controls

40 answers from claude, gemini, user.

## Judge agreement (first answers)

| pair | item | n | exact | within 1 |
|---|---|---|---|---|
| claude vs gemini | grouping | 16 | 0.688 | 1.000 |
| claude vs gemini | names | 16 | 0.562 | 0.938 |
| claude vs gemini | relationships | 16 | 0.312 | 1.000 |
| claude vs gemini | keys | 16 | 0.500 | 0.938 |
| claude vs gemini | design_quality | 16 | 0.562 | 1.000 |
| claude vs gemini | overall | 16 | 0.750 | 1.000 |
| claude vs gemini | answerability | 128 | 0.852 | - |
| claude vs user | grouping | 2 | 1.000 | 1.000 |
| claude vs user | names | 2 | 0.000 | 0.000 |
| claude vs user | relationships | 2 | 0.500 | 1.000 |
| claude vs user | keys | 2 | 0.000 | 1.000 |
| claude vs user | design_quality | 2 | 0.500 | 1.000 |
| claude vs user | overall | 2 | 0.500 | 1.000 |
| claude vs user | answerability | 16 | 0.562 | - |
| gemini vs user | grouping | 2 | 0.500 | 1.000 |
| gemini vs user | names | 2 | 0.000 | 0.500 |
| gemini vs user | relationships | 2 | 0.500 | 1.000 |
| gemini vs user | keys | 2 | 0.500 | 0.500 |
| gemini vs user | design_quality | 2 | 0.500 | 1.000 |
| gemini vs user | overall | 2 | 0.000 | 1.000 |
| gemini vs user | answerability | 16 | 0.688 | - |

## Self-agreement (answer 1 vs repeat)

| pair | item | n | exact | within 1 |
|---|---|---|---|---|
| claude | grouping | 3 | 1.000 | 1.000 |
| claude | names | 3 | 1.000 | 1.000 |
| claude | relationships | 3 | 0.667 | 1.000 |
| claude | keys | 3 | 0.667 | 1.000 |
| claude | design_quality | 3 | 1.000 | 1.000 |
| claude | overall | 3 | 1.000 | 1.000 |
| claude | answerability | 24 | 0.958 | - |
| gemini | grouping | 3 | 1.000 | 1.000 |
| gemini | names | 3 | 0.333 | 1.000 |
| gemini | relationships | 3 | 0.000 | 0.000 |
| gemini | keys | 3 | 0.333 | 1.000 |
| gemini | design_quality | 3 | 0.667 | 1.000 |
| gemini | overall | 3 | 1.000 | 1.000 |
| gemini | answerability | 24 | 0.833 | - |
| user | grouping | 0 | - | - |
| user | names | 0 | - | - |
| user | relationships | 0 | - | - |
| user | keys | 0 | - | - |
| user | design_quality | 0 | - | - |
| user | overall | 0 | - | - |
| user | answerability | 0 | - | - |

## Controls (rank by mean of the 6 scores, 1 = best)

| judge | set | n | GT rank | d rank | planted rank | GT top | d bottom | planted middle | GT > planted > d |
|---|---|---|---|---|---|---|---|---|---|
| claude | dev50 | 8 | 1 | 5 | 3 | True | False | True | True |
| claude | dev50b | 8 | 1 | 6 | 4 | True | False | True | True |
| gemini | dev50 | 8 | 1 | 5 | 2 | True | False | False | True |
| gemini | dev50b | 8 | 1 | 4 | 5 | True | False | True | False |
| user | dev50 | 1 | None | None | None | None | None | None | None |
| user | dev50b | 1 | None | None | None | None | None | None | None |

## Planted errors named in the reasons (merge, foreign key, moved column)

| judge | set | merge | fk removed | column moved |
|---|---|---|---|---|
| claude | dev50 | yes | yes | yes |
| claude | dev50b | yes | yes | yes |
| gemini | dev50 | yes | yes | yes |
| gemini | dev50b | yes | yes | yes |

## Spearman with the automatic scores (pooled over the graded candidates)

| judge | score | metric | rho | n |
|---|---|---|---|---|
| claude | overall | grouping_f1 | 0.396 | 16 |
| claude | overall | table_f1 | 0.870 | 16 |
| claude | overall | rel_recall | 0.081 | 10 |
| claude | overall | pk_right | 0.673 | 16 |
| claude | mean6 | grouping_f1 | 0.744 | 16 |
| claude | mean6 | table_f1 | 0.862 | 16 |
| claude | mean6 | rel_recall | 0.154 | 10 |
| claude | mean6 | pk_right | 0.214 | 16 |
| gemini | overall | grouping_f1 | 0.686 | 16 |
| gemini | overall | table_f1 | 0.710 | 16 |
| gemini | overall | rel_recall | 0.118 | 10 |
| gemini | overall | pk_right | 0.270 | 16 |
| gemini | mean6 | grouping_f1 | 0.715 | 16 |
| gemini | mean6 | table_f1 | 0.718 | 16 |
| gemini | mean6 | rel_recall | 0.038 | 10 |
| gemini | mean6 | pk_right | 0.203 | 16 |
| user | overall | grouping_f1 | - | 2 |
| user | overall | table_f1 | - | 2 |
| user | overall | rel_recall | - | 2 |
| user | overall | pk_right | - | 2 |
| user | mean6 | grouping_f1 | - | 2 |
| user | mean6 | table_f1 | - | 2 |
| user | mean6 | rel_recall | - | 2 |
| user | mean6 | pk_right | - | 2 |
| mean | overall | grouping_f1 | 0.618 | 16 |
| mean | overall | table_f1 | 0.789 | 16 |
| mean | overall | rel_recall | 0.115 | 10 |
| mean | overall | pk_right | 0.396 | 16 |
| mean | mean6 | grouping_f1 | 0.732 | 16 |
| mean | mean6 | table_f1 | 0.744 | 16 |
| mean | mean6 | rel_recall | 0.114 | 10 |
| mean | mean6 | pk_right | 0.189 | 16 |
