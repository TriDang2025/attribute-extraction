# Instructions for an agent running TEAR on Colab

You are on a Google Colab GPU VM, in `/content/attribute-extraction/tear`. This is a clone of the GitHub repo `TriDang2025/attribute-extraction`, which is shared with collaborators.
- Data and the surrogate come from Hugging Face.
- Results are committed back to GitHub.
- Background: `AGENTS.md` and `README.md` in this folder.
- Notebook cell 1 has already set up the logins: HF through `huggingface_hub.login`, and GitHub through the GH_TOKEN env var. If `hf auth whoami` or `git push` fails, ask the user to run cell 1 again.

Goal: rerun the TEAR reproduction on more Conversation test texts than the 20 done on the laptop. Use the same models and settings: Llama-3-8B Q4_K_M, SFR-Embedding-Mistral Q4_K_M, and an 8K context, now on the GPU.

- GitHub pushes use the `GH_TOKEN` environment variable that notebook cell 1 sets. Jobs started from notebook cells inherit it; the Colab Terminal does not. So start runs from the notebook cells (`run.sh` / `run_colab.sh`), and if a push from the Terminal fails with `could not read Username`, ask the user to run the push from a notebook cell instead.

## Rules
- Do not change the method code (`tear_reproduction/`, `eval/`, `surrogate/`) or the prompts without asking the user.
- Fixing Colab scripts (`colab/`) is fine, but **ask before committing or pushing code**. Result commits made by `colab/sync.sh` and `colab/run.sh` are allowed.
- Never delete, rewrite or force-push `results/` or git history. Never use `git push --force`.
- If `results/RUN_OWNER` shows someone else's run as `state=running`, stop and ask the user. Don't use `FORCE=1` unless they say to.
- Before any run likely to take more than 5 minutes, give the user a time estimate and wait for a go-ahead.
- Never print, echo or write tokens.

## Steps
1. `bash colab/setup.sh`. Expect `SETUP_DONE`, with 49 tests OK.
2. `bash colab/start_servers.sh`. Expect `SERVERS_UP`.
3. **Benchmark:** `bash colab/run.sh 25 1`. Check `bash colab/status.sh` every few minutes until `results/run_all.log` shows `RUN_ALL_DONE` or `RUN_ALL_FAILED`.
4. **Estimate.** Use the `new` column of `status.sh` (mean seconds per text for each step) to estimate the time for N=100 and N=700:
   - RAG ×3 seeds and TEAR ×3 seeds
   - then, for each level: TEAR, discovery, coherence and TEAR*

   Ask the user for the GPU type and the compute units per hour shown in Colab. Give hours and units for each size, and wait for their choice.
5. **Run the chosen size:** `bash colab/run.sh N 1`. Use the same command after a disconnect.
6. **Report.** When it's done, confirm the final results commit is on GitHub with `git log -1`. Then summarize Table 2 and Recall-AUC from `results/report.md`, compared with the 20-text laptop run (`git log` of `results/`) and the paper.

## Troubleshooting
- **Servers:** logs are in `results/colab_logs/server_*.log`. CUDA out of memory means the GPU is too small: the coherence step needs about 20 GB. Ask for an L4 or A100.
- **llama.cpp build:** see `results/colab_logs/llama_build.log`. If the tag fails, try a newer one with `TEAR_LLAMA_TAG=bNNNN bash colab/setup.sh` and tell the user.
- **Run errors:** see `results/colab_logs/run_all_N*.out`, and the traceback after `RUN_ALL_FAILED` in `results/run_all.log`.
- **Push failures (`PUSH_FAILED`):** run `git status` and `git log origin/main..` and report them. Don't resolve conflicts in result files by guessing; ask.
- **Expected differences:** outputs won't be bit-identical to the laptop run, because the arithmetic differs between GPU and CPU and the surrogate previews are regenerated on the GPU.
