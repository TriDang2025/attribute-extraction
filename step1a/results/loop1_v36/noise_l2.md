# wf_v3.6 noise at L2 (model-free noise set)

Noise clusters = clusters with >= 60% noise mentions under noise_kind=mwoz at L2 (see noise_mwoz.md). Marked = decision not_attribute / unsure / attribute_cue. Pooled over the 3 entities. noise marked = noise clusters that are marked; precision = marked clusters that are noise; real marked = marked clusters labelled real (an attribute at L2); mixed marked = marked clusters labelled mixed (neither).

Left out (invalid runs): restaurant A r2

| variant | noise marked | precision of marks | real marked as noise | mixed marked |
|---|---|---|---|---|
| A r1 | 9/13 (0.692) | 9/14 (0.643) | 2 | 3 |
| A r2 | 8/10 (0.800) | 8/13 (0.615) | 1 | 4 |
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
