# wf_v4 blind grading (task 9)

Each file in `packets/` is one complete prompt. Grade it with a judge model (Claude, ChatGPT) and save its JSON answer.

## How to grade
1. For every packet, open a **new temporary chat** (memory off, no earlier messages, no files attached). Paste the whole packet file as the first and only message.
2. Write down the model name and version shown by the app (put it in the answer file as an extra top-level field `"model": "..."`, the reader keeps it).
3. The judge must answer with JSON only. Save the JSON as `answers/<judge>_<code>.json` (judge = `claude` or `chatgpt`; code = the 4 letters in the packet file name). If the JSON is wrapped in a code fence, that is fine; the reader strips it.
4. Repeats: the rows marked "repeat" below are graded a second time in another new chat; save them as `answers/<judge>_<code>_r2.json`.
5. Do not open `key.json` before all 38 answers are saved. Then run `python scripts/read_grades_v4.py` (writes `grades.csv` and `task11.md`).

## Checklist (38 answers: 16 x claude, 16 x chatgpt, 3 repeats each)
| done | judge | code | set | save as | repeat |
|---|---|---|---|---|---|
| [ ] | claude | GBQB | dev50 | answers/claude_GBQB.json |  |
| [ ] | claude | JBJH | dev50 | answers/claude_JBJH.json |  |
| [ ] | claude | KXVZ | dev50 | answers/claude_KXVZ.json |  |
| [ ] | claude | MGTK | dev50 | answers/claude_MGTK.json |  |
| [ ] | claude | RPGV | dev50 | answers/claude_RPGV.json |  |
| [ ] | claude | RRSK | dev50 | answers/claude_RRSK.json |  |
| [ ] | claude | VCJR | dev50 | answers/claude_VCJR.json |  |
| [ ] | claude | WWPH | dev50 | answers/claude_WWPH.json |  |
| [ ] | claude | CXJS | dev50b | answers/claude_CXJS.json |  |
| [ ] | claude | FHMV | dev50b | answers/claude_FHMV.json |  |
| [ ] | claude | MKNR | dev50b | answers/claude_MKNR.json |  |
| [ ] | claude | PXBM | dev50b | answers/claude_PXBM.json |  |
| [ ] | claude | RFFT | dev50b | answers/claude_RFFT.json |  |
| [ ] | claude | VBGV | dev50b | answers/claude_VBGV.json |  |
| [ ] | claude | VPRG | dev50b | answers/claude_VPRG.json |  |
| [ ] | claude | ZHHK | dev50b | answers/claude_ZHHK.json |  |
| [ ] | claude | GBQB | dev50 | answers/claude_GBQB_r2.json | yes |
| [ ] | claude | CXJS | dev50b | answers/claude_CXJS_r2.json | yes |
| [ ] | claude | JBJH | dev50 | answers/claude_JBJH_r2.json | yes |
| [ ] | chatgpt | GBQB | dev50 | answers/chatgpt_GBQB.json |  |
| [ ] | chatgpt | JBJH | dev50 | answers/chatgpt_JBJH.json |  |
| [ ] | chatgpt | KXVZ | dev50 | answers/chatgpt_KXVZ.json |  |
| [ ] | chatgpt | MGTK | dev50 | answers/chatgpt_MGTK.json |  |
| [ ] | chatgpt | RPGV | dev50 | answers/chatgpt_RPGV.json |  |
| [ ] | chatgpt | RRSK | dev50 | answers/chatgpt_RRSK.json |  |
| [ ] | chatgpt | VCJR | dev50 | answers/chatgpt_VCJR.json |  |
| [ ] | chatgpt | WWPH | dev50 | answers/chatgpt_WWPH.json |  |
| [ ] | chatgpt | CXJS | dev50b | answers/chatgpt_CXJS.json |  |
| [ ] | chatgpt | FHMV | dev50b | answers/chatgpt_FHMV.json |  |
| [ ] | chatgpt | MKNR | dev50b | answers/chatgpt_MKNR.json |  |
| [ ] | chatgpt | PXBM | dev50b | answers/chatgpt_PXBM.json |  |
| [ ] | chatgpt | RFFT | dev50b | answers/chatgpt_RFFT.json |  |
| [ ] | chatgpt | VBGV | dev50b | answers/chatgpt_VBGV.json |  |
| [ ] | chatgpt | VPRG | dev50b | answers/chatgpt_VPRG.json |  |
| [ ] | chatgpt | ZHHK | dev50b | answers/chatgpt_ZHHK.json |  |
| [ ] | chatgpt | MKNR | dev50b | answers/chatgpt_MKNR_r2.json | yes |
| [ ] | chatgpt | VCJR | dev50 | answers/chatgpt_VCJR_r2.json | yes |
| [ ] | chatgpt | RFFT | dev50b | answers/chatgpt_RFFT_r2.json | yes |
