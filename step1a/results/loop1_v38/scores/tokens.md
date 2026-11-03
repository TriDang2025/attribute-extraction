# wf_v3.8 batch tokens (exact, from the responses)

| family | calls | prompt tokens | per call | output tokens | per call | est. prompt (chars/3.5) |
|---|---|---|---|---|---|---|
| dupcheck | 12 | 7,796 | 649 | 349 | 29 | 7,895 |
| example | 122 | 65,229 | 534 | 10,791 | 88 | 66,344 |
| neighbour | 122 | 77,720 | 637 | 13,924 | 114 | 80,038 |
| total | 256 | 150,745 | 588 | 25,064 | 97 | 154,277 |

v3.7 batch: 124 calls, 565,921 prompt, 109,867 output (4,563 / 886 per call).
v3.8 vs v3.7: +132 calls, -415,176 prompt (-73.4%), -84,803 output (-77.2%); per call -3,975 prompt, -789 output.
