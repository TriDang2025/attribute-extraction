# wf_v4 task 11: grading agreement and controls

19 answers from claude.

## Judge agreement (first answers)

| pair | item | n | exact | within 1 |
|---|---|---|---|---|

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

## Controls (rank by mean of the 6 scores, 1 = best)

| judge | set | n | GT rank | d rank | planted rank | GT top | d bottom | planted middle | GT > planted > d |
|---|---|---|---|---|---|---|---|---|---|
| claude | dev50 | 8 | 1 | 5 | 3 | True | False | True | True |
| claude | dev50b | 8 | 1 | 6 | 4 | True | False | True | True |

## Planted errors named in the reasons (merge, foreign key, moved column)

| judge | set | merge | fk removed | column moved |
|---|---|---|---|---|
| claude | dev50 | yes | yes | yes |
| claude | dev50b | yes | yes | yes |

## Spearman with the automatic scores (pooled over the graded candidates)

| judge | score | metric | rho | n |
|---|---|---|---|---|
| claude | overall | grouping_f1 | 0.271 | 14 |
| claude | overall | table_f1 | 0.394 | 16 |
| claude | overall | rel_recall | -0.127 | 10 |
| claude | overall | pk_right | 0.817 | 14 |
| claude | mean6 | grouping_f1 | 0.695 | 14 |
| claude | mean6 | table_f1 | 0.359 | 16 |
| claude | mean6 | rel_recall | -0.240 | 10 |
| claude | mean6 | pk_right | 0.289 | 14 |
