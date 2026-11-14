# T3: L2 attributes Qwen found and Llama v4.3 missed

Qwen = frozen Step 3 v3.9 (found 31/40 | 29/41), Llama = v4.3 (`results/wf_v43/u2`, found 30/40 | 27/41); same scorer (`rules_groups.found`, L2, rules v1.1) on the final columns of both. Types come from `classify` in `scripts/t3_missed_v44.py` (deterministic; rules in its docstring). The clusters of a miss are those of the Qwen column that found it; (n) = mentions of the attribute in the cluster.

## Counts per type

| | not_attribute | bad batch | merged | other | all |
|---|---|---|---|---|---|
| all | 2 | 0 | 2 | 1 | 5 |
| dev50 | 1 | 0 | 1 | 0 | 2 |
| dev50b | 1 | 0 | 1 | 1 | 3 |

## Misses

| set | entity | attribute | type | clusters | batches (order, batch) | Llama names (s0 / s1 / s2) | vote | Llama column | why |
|---|---|---|---|---|---|---|---|---|---|
| dev50 | train | Train requested people | **not_attribute** | E1#14(6) | E1#14: s0b3, s1b5, s2b3 | E1#14: not_attribute / not_attribute / not_attribute | E1#14: not_attribute | E1#5/0 (total fee), purity 0.15, coverage 0.2 | 100% of its mentions are in clusters Llama voted not_attribute (names: E1#14: not_attribute/not_attribute/not_attribute) |
| dev50 | hotel | Hotel address | **merged** | E0#30(1) | E0#30: s0b7, s1b3, s2b4 | E0#30: location / address / location | E0#30: merge | E0#10|E0#21|E0#22|E0#30|E0#7 (location), purity 0.15, coverage 1.0 | its clusters sit in a column of purity 0.15 that holds Hotel area 6, Hotel name 3, Hotel address 2; the clashing names came from different batches; orders disagree on E0#30 |
| dev50b | train | Train arrive by | **other** | E0#3(25) | E0#3: s0b1, s1b3, s2b4 | E0#3: arrival_time / arrival_time / arrival_time | E0#3: split | E0#3/1 (time str), purity 0.67, coverage 0.08 | the attribute is spread over several columns (best part purity 0.67, coverage 0.08); split pass E0#3: ran (2 parts) |
| dev50b | train | Train destination | **merged** | E0#1(4) E0#12(1) E0#13(5) E0#8(2) | E0#1: s0b1, s1b1, s2b4; E0#12: s0b3, s1b2, s2b3; E0#13: s0b3, s1b4, s2b3; E0#8: s0b2, s1b3, s2b4 | E0#1: destination / departure_station / departure_station; E0#12: destination / destination / destination; E0#13: destination / destination / departure_station; E0#8: destination / destination / destination | E0#1: merge; E0#12: merge; E0#13: merge; E0#8: merge | E0#11|E0#12|E0#13|E0#17|E0#8|E0#9 (destination), purity 0.55, coverage 0.8 | its clusters sit in a column of purity 0.55 that holds Train destination 24, Train departure 17; same batch and same name as E0#11, E0#12, E0#13, E0#16, E0#17, E0#9; orders disagree on E0#1, E0#13 |
| dev50b | restaurant | Restaurant postcode | **not_attribute** | E3#42(1) E3#8(2) | E3#42: s0b9, s1b7, s2b8; E3#8: s0b2, s1b9, s2b10 | E3#42: address / address_component / not_attribute; E3#8: not_attribute / not_attribute / not_attribute | E3#42: merge; E3#8: not_attribute | E3#13/1 (location str), purity 0.5, coverage 0.25 | 67% of its mentions are in clusters Llama voted not_attribute (names: E3#42: address/address_component/not_attribute; E3#8: not_attribute/not_attribute/not_attribute) |

## Found by Llama but not by Qwen (2)

- dev50 train: Train destination
- dev50b hotel: Hotel address
