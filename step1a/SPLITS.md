# Splits (from wf_v3, 2026-10-27)

`s1a/split.py`: ids = `chunking/data/conversation_ids.txt`, TEAR pool (300) first, then TEAR test (700).

| name | ids | role |
|---|---|---|
| dev50 | pool[0:50] (`--split dev --limit 50`) | development; all tuning |
| dev2 (old test50) | test[0:50] (`--split test --limit 50`) | second development set; it was seen while choosing wf_v2.x settings |
| dev50b (wf_v3.7) | pool[50:100] (`--split dev50b`; `split.dialogues("dev50b")`), 50 dialogues, SSNG0262 .. SNG0935; no overlap with dev50 or fresh (checked) | confirm decisions only, never tune |
| dev50c (wf_v5.0 G0) | 50 dialogues of pool[100:300] drawn with seed 0 (`split.dev50c`); sealed like fresh (`unseal=True`). Gold built 2026-11-22 in `results/wf_v50/g0/` (`run_g0.sh`: `export_mentions.py --split dev50c --unseal`, `gt_v35.py --auto-entities`), never read | final check of the wf_v5.0 fixes only |
| fresh | test[350:450] (`split.dialogues("fresh", unseal=True)`), 100 dialogues, first PMUL0532, last PMUL0297 | sealed test; open only for the final numbers |

The fresh split raises `PermissionError` unless `unseal=True`; no script passes it yet.
