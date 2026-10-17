# Reproduction results (Llama-3-8B-Instruct, CPU)

## Table 2: table extraction, full schema

| Dataset | Metric | sim. | Paper RAG | Ours RAG | Paper TEAR | Ours TEAR |
|---|---|---|---|---|---|---|
| Conversation | header-F1 | EM | 84.6 | 87.8±0.5 | 88.7 | 84.4±0.5 |
| Conversation | header-F1 | chrf | 91.9 | 93.6±0.2 | 94.5 | 92.3±0.3 |
| Conversation | header-F1 | BS | 91.3 | 96.5±0.1 | 93.9 | 95.4±0.3 |
| Conversation | structured-F1 | EM | 76.9 | 68.2±1.0 | 82.4 | 71.5±0.4 |
| Conversation | structured-F1 | chrf | 81.2 | 79.9±0.7 | 86.1 | 80.8±0.5 |
| Conversation | structured-F1 | BS | 83.8 | 81.5±0.7 | 88.4 | 81.5±0.6 |
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

- Conversation RAG s0: 20 texts, 0 failed
- Conversation RAG s1: 20 texts, 0 failed
- Conversation RAG s2: 20 texts, 0 failed
- Conversation TEAR s0: 20 texts, 0 failed
- Conversation TEAR s1: 20 texts, 0 failed
- Conversation TEAR s2: 20 texts, 0 failed
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
| Conversation | 1 (seed 0) | 7 | 24 | 0 | 0 | 24 | 7 | 0 | 32.8 | 58.6 | 25.3 | 37.2 |
| Conversation | 2 (seed 0) | 12 | 26 | 0 | 0 | 26 | 6 | 0 | 27.1 | 46.6 | 23.6 | 35.3 |
| Conversation | 3 (seed 0) | 17 | 39 | 1 | 1 | 39 | 6 | 1 | 38.8 | 61.7 | 33.5 | 50.4 |

The paper reports Figure 4 as bars only (roughly 40-80% for Llama-3-8B).

## Figure 5/17: TEAR vs TEAR* under exploratory schemas (scored against the full-schema gold)

| Dataset | Level | Method | header-F1 EM | header-F1 chrf | structured-F1 EM | structured-F1 chrf |
|---|---|---|---|---|---|---|
| Conversation | 1 | TEAR | 80.0±0.0 | 89.1±0.0 | 68.8±0.0 | 77.3±0.0 |
| Conversation | 1 | TEAR* | 80.0±0.0 | 89.1±0.0 | 68.8±0.0 | 77.3±0.0 |
| Conversation | 2 | TEAR | 76.9±0.0 | 86.9±0.0 | 60.9±0.0 | 74.4±0.0 |
| Conversation | 2 | TEAR* | 76.9±0.0 | 86.9±0.0 | 60.9±0.0 | 74.4±0.0 |
| Conversation | 3 | TEAR | 68.0±0.0 | 80.2±0.0 | 52.2±0.0 | 64.2±0.0 |
| Conversation | 3 | TEAR* | 68.6±0.0 | 79.3±0.0 | 50.7±0.0 | 63.5±0.0 |
