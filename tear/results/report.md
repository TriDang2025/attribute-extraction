# Reproduction results (Llama-3-8B-Instruct, CPU)

## Table 2: table extraction, full schema

| Dataset | Metric | sim. | Paper RAG | Ours RAG | Paper TEAR | Ours TEAR |
|---|---|---|---|---|---|---|
| Conversation | header-F1 | EM | 84.6 | 83.0±0.2 | 88.7 | 81.7±0.6 |
| Conversation | header-F1 | chrf | 91.9 | 91.2±0.3 | 94.5 | 89.4±0.5 |
| Conversation | header-F1 | BS | 91.3 | 94.9±0.2 | 93.9 | 92.9±0.5 |
| Conversation | structured-F1 | EM | 76.9 | 65.9±0.5 | 82.4 | 67.1±0.3 |
| Conversation | structured-F1 | chrf | 81.2 | 76.7±0.5 | 86.1 | 77.3±0.3 |
| Conversation | structured-F1 | BS | 83.8 | 77.8±0.4 | 88.4 | 78.6±0.4 |
| Incidents | header-F1 | EM | 81.5 | 100.0±0.0 | 87.8 | 100.0±0.0 |
| Incidents | header-F1 | chrf | 87.9 | 100.0±0.0 | 92.5 | 100.0±0.0 |
| Incidents | header-F1 | BS | 88.5 | 100.0±0.0 | 93.1 | 100.0±0.0 |
| Incidents | structured-F1 | EM | 61.2 | 82.6±0.0 | 69.1 | 82.6±0.0 |
| Incidents | structured-F1 | chrf | 73.6 | 99.9±0.0 | 79.4 | 99.9±0.0 |
| Incidents | structured-F1 | BS | 76.8 | 95.2±0.0 | 82.9 | 95.2±0.0 |
| Weather | header-F1 | EM | 77.3 | 76.9±0.0 | 80.3 | 83.3±0.0 |
| Weather | header-F1 | chrf | 83.5 | 80.2±0.0 | 85.6 | 86.9±0.0 |
| Weather | header-F1 | BS | 88.7 | 87.4±0.0 | 90.1 | 87.2±0.0 |
| Weather | structured-F1 | EM | 46.2 | 83.3±0.0 | 51.0 | 83.3±0.0 |
| Weather | structured-F1 | chrf | 65.4 | 77.3±0.0 | 70.1 | 91.4±0.0 |
| Weather | structured-F1 | BS | 64.3 | 84.2±0.0 | 67.9 | 83.8±0.0 |

- Conversation RAG s0: 200 texts, 1 failed
- Conversation RAG s1: 200 texts, 0 failed
- Conversation RAG s2: 200 texts, 0 failed
- Conversation TEAR s0: 200 texts, 0 failed
- Conversation TEAR s1: 200 texts, 0 failed
- Conversation TEAR s2: 200 texts, 0 failed
- Incidents RAG s0: 2 texts, 0 failed
- Incidents RAG s1: 2 texts, 0 failed
- Incidents RAG s2: 2 texts, 0 failed
- Incidents TEAR s0: 2 texts, 0 failed
- Incidents TEAR s1: 2 texts, 0 failed
- Incidents TEAR s2: 2 texts, 0 failed
- Weather RAG s0: 1 texts, 0 failed
- Weather RAG s1: 1 texts, 0 failed
- Weather RAG s2: 1 texts, 0 failed
- Weather TEAR s0: 1 texts, 0 failed
- Weather TEAR s1: 1 texts, 0 failed
- Weather TEAR s2: 1 texts, 0 failed

## Figure 4: attribute recommendation recall-AUC (%)

| Dataset | Level | Hidden | Z | P* | Judge calls | Z' | elbow k | Accepted | TEAR chrf | TEAR BS | CFR chrf | CFR BS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Conversation | 1 (seed 0) | 7 | 132 | 8 | 8 | 132 | 11 | 1 | 64.4 | 76.2 | 64.9 | 72.2 |
| Conversation | 2 (seed 0) | 12 | 137 | 4 | 4 | 137 | 20 | 2 | 66.5 | 73.6 | 63.5 | 73.6 |
| Conversation | 3 (seed 0) | 17 | 207 | 6 | 6 | 207 | 19 | 6 | 74.6 | 79.9 | 65.2 | 75.2 |

The paper reports Figure 4 as bars only (roughly 40-80% for Llama-3-8B).

## Figure 5/17: TEAR vs TEAR* under exploratory schemas (scored against the full-schema gold)

| Dataset | Level | Method | header-F1 EM | header-F1 chrf | structured-F1 EM | structured-F1 chrf |
|---|---|---|---|---|---|---|
| Conversation | 1 | TEAR | 76.4±0.0 | 86.2±0.0 | 65.8±0.0 | 75.4±0.0 |
| Conversation | 1 | TEAR* | 77.5±0.0 | 86.5±0.0 | 65.3±0.0 | 75.0±0.0 |
| Conversation | 2 | TEAR | 70.3±0.0 | 82.3±0.0 | 59.1±0.0 | 71.2±0.0 |
| Conversation | 2 | TEAR* | 71.4±0.0 | 82.6±0.0 | 60.4±0.0 | 71.7±0.0 |
| Conversation | 3 | TEAR | 58.3±0.0 | 70.6±0.0 | 47.8±0.0 | 58.5±0.0 |
| Conversation | 3 | TEAR* | 69.6±0.0 | 81.0±0.0 | 56.8±0.0 | 67.6±0.0 |
