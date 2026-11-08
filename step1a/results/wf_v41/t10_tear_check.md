# wf_v4.1 task 10: TEAR baseline check (2026-11-07)

**Question:** do we have TEAR outputs for dev50 and dev50b? If not, does TEAR need a GPU?

**Answer: no outputs; yes, a GPU (an L4 is enough).**

- **dev50:** set up in wf_v3.6 (`tear/colab/DEV50_RUN.md`, dataset `conversation_dev50`, scorer `step1a/scripts/score_tear_v36.py`), never run. No `tear/results/conversation_dev50/` in any worktree or in git history.
- **dev50b:** not set up. dev50b = pool[50:100], so it also sits in TEAR's labeled pool. It needs a `conversation_dev50b` dataset that removes those 50 ids from the pool, the same way `conversation_dev50` does (`eval/reproduce.py` `HELD_OUT`, `data_build/dev50.py`). This is a small code change, not done yet.
- **GPU:** TEAR's LLM is Llama-3-8B. On the laptop CPU the discovery step takes about 300 s per text (`tear/README.md`), so 50 texts would take about 4 h for extraction plus discovery (estimate). On an L4:
  - extraction only (`te`, full schema): about 15 min per set (`DEV50_RUN.md`);
  - attribute recommendation (`te` → `discover` → `coherence` → `integrate`, needed for "new attributes" in task 9): about 100 s per text, so about 85 min per set (estimate from the 2026-10-18 benchmark).
- **Notebook:** TEAR does not need the A100 or Qwen, and it has its own notebook (`tear/colab/TEAR_colab.ipynb`). Task 6 therefore lists it as a separate optional L4 run, not inside the Qwen notebook.
- **Caveat (unchanged from v3.6):** the BART surrogate was trained on the full pool, so its previews saw the dev texts.

**Decision needed:** should TEAR run on Nov 16 (L4, about 2 × 15 min for extraction, or about 2 × 85 min for recommendation), and should the `conversation_dev50b` dataset be added?
