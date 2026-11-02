# wf_v3.6 noise at L2, with the Colab batch (model-free noise set)

Noise clusters = clusters with >= 60% noise mentions under noise_kind=mwoz at L2 (see noise_mwoz.md). Marked = decision not_attribute / unsure / attribute_cue. Pooled over the 3 entities. noise marked = noise clusters that are marked; precision = marked clusters that are noise; real marked = marked clusters labelled real (an attribute at L2); mixed marked = marked clusters labelled mixed (neither).

| variant | noise marked | precision of marks | real marked as noise | mixed marked |
|---|---|---|---|---|
| A r1 (order 0) | 9/13 (0.692) | 9/14 (0.643) | 2 | 3 |
| A r2 (order 1) | 9/13 (0.692) | 9/14 (0.643) | 1 | 4 |
| A s2 (order 2) | 3/13 (0.231) | 3/8 (0.375) | 3 | 2 |
| B s0 | 10/13 (0.769) | 10/18 (0.556) | 4 | 4 |
| C s0 | 10/13 (0.769) | 10/18 (0.556) | 4 | 4 |
| C s1 | 8/13 (0.615) | 8/17 (0.471) | 4 | 5 |
| C s2 | 7/13 (0.538) | 7/21 (0.333) | 7 | 7 |
| C s012 | 9/13 (0.692) | 9/20 (0.450) | 6 | 5 |
| D s012 | 1/13 (0.077) | 1/3 (0.333) | 1 | 1 |
| C33 s012 | 9/13 (0.692) | 9/20 (0.450) | 6 | 5 |
| E s012 | 13/13 (1.000) | 13/31 (0.419) | 7 | 11 |
| E1 s012 | 13/13 (1.000) | 13/27 (0.481) | 4 | 10 |
| E2 s012 | 10/13 (0.769) | 10/21 (0.476) | 6 | 5 |
| E s0 | 12/13 (0.923) | 12/31 (0.387) | 7 | 12 |
| F2 s0 | 12/13 (0.923) | 12/30 (0.400) | 8 | 10 |
| AE s0 | 9/13 (0.692) | 9/13 (0.692) | 1 | 3 |
| AE s1 | 11/13 (0.846) | 11/20 (0.550) | 2 | 7 |
| AE s2 | 5/13 (0.385) | 5/10 (0.500) | 3 | 2 |
| AE s012 | 11/13 (0.846) | 11/16 (0.688) | 3 | 2 |
| Oracle s0 | 10/13 (0.769) | 10/20 (0.500) | 5 | 5 |
| Oracle s1 | 10/13 (0.769) | 10/22 (0.455) | 5 | 7 |
| Oracle s2 | 9/13 (0.692) | 9/21 (0.429) | 6 | 6 |
| Oracle s012 | 10/13 (0.769) | 10/23 (0.435) | 7 | 6 |
| g s0 | 11/13 (0.846) | 11/25 (0.440) | 8 | 6 |
| g s1 | 9/13 (0.692) | 9/21 (0.429) | 5 | 7 |
| g s2 | 12/13 (0.923) | 12/27 (0.444) | 8 | 7 |
| g s012 | 11/13 (0.846) | 11/22 (0.500) | 6 | 5 |
