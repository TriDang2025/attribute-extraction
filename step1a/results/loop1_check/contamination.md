# T4 contamination probe (2026-10-27)

Model Qwen/Qwen2.5-32B-Instruct-AWQ, vLLM 0.32.0, A100 80 GB, temperature 0. Raw answers: `contamination_raw.jsonl`.
Gold train attributes (7): arrive by, confirmed reference, day, departure, destination, leave at, requested people.

| Question | Answer (attributes listed) | Gold matched |
|---|---|---|
| Q1 "List the slots of the train domain in the MultiWOZ dataset." | train-IDs, departure, destination, day, leave-time, arrive-by, price | 5/7 (not reference, people) |
| Q2 "A train-booking assistant stores ... List the attributes." | 15 generic fields (user ID, origin, destination, travel date, class, passengers, seat, status, payment, ...) | 3/7 loosely (origin, destination, date, passengers), no arrive-by / leave-at |

Verdict: **contaminated**.
- When the dataset is named, the model gives the MultiWOZ slot list, including dataset-specific ones such as "arrive-by" and "train-IDs".
- Without the name it gives a generic list.
- So naming from the full prompt may draw on memory, and the no-context run is required. It was run as `nocontext_r1`.
- Uncertain: 2 questions only, so this shows the model knows the slot list. It does not show that the full-prompt names come from memory.
