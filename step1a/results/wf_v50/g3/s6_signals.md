# wf_v5.0 G3 (S6): gold-free signals for blocking wrong group joins

Unit: every pair of clusters inside one final group (wf_v4.6 Y3 run), both with a gold label; "diff" = different majority gold label.
dev50: 393 pairs (207 diff, 186 same); dev50b: 367 pairs (227 diff, 140 same). Gold used only to score the signal.

| signal | best cut | dev50 block diff / same | dev50b block diff / same | verdict |
|---|---|---|---|---|
| value disagreement in shared dialogues | any | 30/30 vs 12/15 (co-dialogue pairs only) | 41/44 vs 12/12 | no signal, support 1 dialogue |
| left-word cosine (idf) | < 0.2 | 118/147 vs 125/183 | 166/182 vs 112/137 | no signal |
| name refinement (token subset), >= 2 of 3 orders | | 23 vs 16 | 38 vs 25 | at base rate |
| value-centroid cosine (bge-m3 vectors.npz) | < 0.5 | 156 vs 147 | 182 vs 119 | no signal |

Upper bound with no blocker at all (each cluster its own group, loop 1 span found, scorer rules v1.3):
- dev50: 30 -> 32 found (+ Hotel address, Taxi departure, Taxi destination; - Train departure), groups 84 -> 138.
- dev50b: 26 -> 30 found (+ Restaurant address, Taxi departure, Train departure, Train destination), groups 74 -> 117.

Probe scripts and pair tables: probe/ (run from step1a/ with the chunking venv).
