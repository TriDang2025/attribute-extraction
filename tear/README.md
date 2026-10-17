# TEAR reproduction

This project reproduces TEAR (Li et al., "TEAR: Table Extraction with Attribute Recommendation from Texts via Large Language Models", `../source_paper/TEAR.pdf`). TEAR extracts a table from free text (Table Extraction Workflow) and recommends missing schema attributes (Attribute Recommendation Workflow).

Every paper component is implemented. A first run on a CPU laptop used 20 test texts. This README tells you how to set the project up on a new machine and continue with more test texts. It assumes no prior context.

- Results so far: `results/report.md` (tables).
- Running on Google Colab with data on Hugging Face and results committed to this repo: `colab/README.md`.
- Project notes for agents: `AGENTS.md`.
- Paths in this README are relative to this `tear/` folder. Run all commands from here.

## 1. What is in the package

| Path | Content |
|---|---|
| `tear_reproduction/` | Method code: schema, prompts, retrieval, pipeline, integration, coherence score, LLM client |
| `surrogate/` | BART-Large preview model ("surrogate"): training, prediction, table serialization |
| `eval/metrics.py`, `eval/reproduce.py` | Metrics (Eq. 20-22) and every experiment step as a CLI |
| `tools/run_all.py` | Runs all steps in order and writes the report. Resumable |
| `data/conversation/` | Main benchmark, built from MultiWOZ 2.4: `pool.jsonl` (300 labeled texts), `test.jsonl` (700 test texts with gold tables), `input.jsonl` (same texts without gold), `levels.json`, `previews.jsonl`, cached embeddings |
| `data/incidents_small/`, `data/weather_small/` | Tiny hand-labeled sets (smoke tests only) |
| `results/` | Outputs of the first run (20 texts). New runs append here |
| `models/surrogate_conversation_cont2/` | Trained surrogate (1.6 GB). Only in the zip, not in the original folder |
| `tools/llama.cpp/bin/` | llama.cpp b11139 for **Windows, CPU only** |
| `downloads/multiwoz/MULTIWOZ2.4.zip` | Raw source data. Needed only to rebuild `data/conversation` |
| `tests/` | 49 unit tests |
| `backup/` | Old versions of replaced scripts |

The package does **not** include these. Get them in step 2:
- Meta-Llama-3-8B-Instruct Q4_K_M GGUF (4.9 GB): the LLM for extraction, discovery and judging.
- SFR-Embedding-Mistral Q4_K_M GGUF (4.4 GB): the embedder for retrieval.
- roberta-large (1.4 GB): BERTScore downloads it automatically the first time a report is written.

## 2. Setup

Run all commands from the project root.

### 2.1 Python

Python 3.14 was used for the original run. A recent 3.12+ will probably work, but it was not tested.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

On an NVIDIA GPU, install the CUDA build of torch from https://pytorch.org first. The surrogate code runs on CPU either way, at about 26 s per text. The GPU matters mainly for llama.cpp.

### 2.2 llama.cpp

All three model servers use `llama-server` from llama.cpp.
- **Windows without a GPU:** use the included `tools/llama.cpp/bin/llama-server.exe`.
- **Anything else:** download a release from https://github.com/ggml-org/llama.cpp/releases (b11139 or newer; use the CUDA build if there is an NVIDIA GPU). Unpack it and point `TEAR_LLAMA_SERVER` at the `llama-server` binary.

### 2.3 Model files

Put both GGUFs in `models/gguf/`. Use `curl -L -C -` so an interrupted download resumes.

```bash
mkdir -p models/gguf
curl -L -C - -o models/gguf/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf https://huggingface.co/lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF/resolve/main/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf
curl -L -C - -o models/gguf/ggml-sfr-embedding-mistral-q4_k_m.gguf https://huggingface.co/dranger003/SFR-Embedding-Mistral-GGUF/resolve/main/ggml-sfr-embedding-mistral-q4_k_m.gguf
```

Check the file sizes: 4,920,733,888 bytes (Llama) and 4,368,439,008 bytes (SFR).

### 2.4 Environment variables

`tools/run_all.py` and `tools/start_scoring_server.sh` read these:

| Variable | Meaning | Default |
|---|---|---|
| `TEAR_N` | Number of Conversation test texts (the first N of `test.jsonl`) | `20` |
| `TEAR_ALL_LEVELS` | Set to `1` to also run exploratory levels 1 and 3 | unset (only level 2) |
| `TEAR_MODELS` | Folder with `surrogate_conversation_cont2/` and `gguf/` | `<project>/models` |
| `TEAR_LLAMA_SERVER` | Path to the `llama-server` binary | `tools/llama.cpp/bin/llama-server[.exe]` |
| `TEAR_LLAMA_GGUF` | Llama GGUF for the coherence-score server | `<TEAR_MODELS>/gguf/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf` |
| `TEAR_LLAMA_ARGS` | Extra `llama-server` arguments for the coherence-score server | `-t 10`; use `-ngl 99` on a GPU |

### 2.5 Start the model servers

Two servers must keep running during a run. `run_all.py` starts a third one itself.

| Port | Role | Started by |
|---|---|---|
| 1234 | Chat LLM (OpenAI-compatible `/v1/chat/completions`) | you |
| 8082 | SFR embedder (`/tokenize`, `/embeddings`) | you |
| 8081 | Coherence scorer: same Llama GGUF, scores forced tokens | `run_all.py`, only during the coherence step |

```bash
# Set SERVER to the llama-server path. Add -ngl 99 on a GPU; leave it out on CPU.
SERVER=tools/llama.cpp/bin/llama-server
$SERVER -m models/gguf/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf --port 1234 -c 8192 -np 1 --no-webui -ngl 99
$SERVER -m models/gguf/ggml-sfr-embedding-mistral-q4_k_m.gguf --port 8082 -c 4096 -np 1 --embedding --pooling last --no-webui -ngl 99
```

Run each server in its own terminal, or in the background. Check them with:

```bash
curl http://localhost:1234/health
curl http://localhost:8082/health
```

**Notes**
- The original run served the chat model with LM Studio on port 1234: `lms load meta-llama-3-8b-instruct --context-length 8192 --ttl 259200`. Either server works. The client sends the model name `meta-llama-3-8b-instruct`, which llama-server ignores. Outputs will not be bit-identical to the first run.
- With LM Studio, keep the long `--ttl`. Its default 1-hour idle TTL unloads the model, and on the original laptop the automatic reload went to the iGPU and crashed.
- The 8K context matches the original run. The pipeline's prompt cap assumes it.

### 2.6 Check the setup

```bash
python -m unittest tests.test_metrics tests.test_retrieval tests.test_pipeline tests.test_surrogate tests.test_reproduce tests.test_client
```

All 49 tests should pass. They need no servers.

## 3. Run

### 3.1 Everything, with more test texts (recommended)

```bash
# Linux/macOS
TEAR_N=100 TEAR_ALL_LEVELS=1 TEAR_LLAMA_ARGS="-ngl 99" python tools/run_all.py
```

```powershell
# Windows PowerShell
$env:TEAR_N = "100"; $env:TEAR_ALL_LEVELS = "1"; $env:TEAR_LLAMA_ARGS = "-ngl 99"; python tools/run_all.py
```

`run_all.py` runs these steps:
1. Embeds the pool plus the first N test texts. 320 are already cached, so only the new ones are embedded.
2. Table 2 RAG, seeds 0-2.
3. Surrogate previews for the first N test texts. It rewrites `data/conversation/previews.jsonl` when that file has fewer than N rows.
4. Table 2 TEAR, seed 0.
5. Level 2: TEAR extraction, discovery, coherence score, integration, TEAR\*.
6. Table 2 TEAR, seeds 1 and 2, then the report (`CORE_DONE` in the log).
7. With `TEAR_ALL_LEVELS=1`: levels 1 and 3, then the report again (`RUN_ALL_DONE`).

**Resuming**
- Every step skips texts already in its result file. The 20 texts from the first run are reused.
- If the run stops, run the same command again.
- The coherence and integration outputs are recomputed when discovery added new texts, because they are older than `disc_L*_s0.jsonl`.

**Progress and results**
- Progress goes to `results/run_all.log`.
- The report goes to `results/report.md` and `results/report.json`.

### 3.2 Single steps

Use this for a Table 2-only run, for example. `--n` is the number of test texts. TEAR needs previews for those texts first.

```bash
head -n 100 data/conversation/input.jsonl > results/conversation_input_first100.jsonl
python -m surrogate.predict --model models/surrogate_conversation_cont2 --input results/conversation_input_first100.jsonl --out data/conversation/previews.jsonl
python -m eval.reproduce embed --dataset conversation --n 100
python -m eval.reproduce te --dataset conversation --methods rag tear --seeds 0 1 2 --n 100
python -m eval.reproduce report
```

Per exploratory level L (1, 2, 3):

```bash
python -m eval.reproduce te        --dataset conversation --methods tear --level L --seeds 0 --n 100
python -m eval.reproduce discover  --dataset conversation --level L --seed 0 --n 100
python -m eval.reproduce coherence --dataset conversation --level L --seed 0     # needs the port-8081 server (tools/start_scoring_server.sh)
python -m eval.reproduce integrate --dataset conversation --level L --seed 0
python -m eval.reproduce tearstar  --dataset conversation --level L --seed 0 --n 100
```

`python -m eval.reproduce -h` lists all options, such as `--base-url` and `--embedding-url` for other server addresses.

### 3.3 Expected time

Measured on the original CPU laptop (i7-1265U):

| Step | Time |
|---|---|
| Embedding | about 30-50 s per text |
| Surrogate preview | 26 s per text |
| RAG extraction | about 70 s per text and seed |
| TEAR extraction | about 300 s per text and seed |
| Discovery | about 300 s per text and level |
| Coherence | 15-20 min per level at 20 texts. It grows with the number of proposals |

Totals on that CPU:
- 100 texts, Table 2 only: about 33 h.
- 100 texts, full run with all levels: about 4-5 days.

A GPU should make this many times faster, but that was not measured.

### 3.4 Output files (`results/conversation/`)

| File | Content |
|---|---|
| `te_{rag,tear}_Lfull_s{seed}.jsonl` | Table 2 extractions: one row per text, with the table, prompts/calls, retries and seconds |
| `te_tear_L{1,2,3}_s0.jsonl` | TEAR extraction with the reduced schema at each level |
| `disc_L*_s0.jsonl` | Attributes proposed by discovery for each text |
| `coh_L*_s0.json` | Schema Coherence Scores |
| `ar_L*_s0.json` | Integrated, ranked recommendations |
| `tearstar_L*_s0.json`, `te_tearstar_L*_s0.jsonl` | TEAR\*: accepted attributes and the re-extraction |

## 4. Rebuild from scratch (optional)

```bash
python -I data_build/multiwoz.py      # data/conversation from downloads/multiwoz/MULTIWOZ2.4.zip (seed 0)
python -m data_build.small_sets       # data/incidents_small, data/weather_small
# Base model: facebook/bart-large in a local folder
python -m surrogate.train --pool data/conversation/pool.jsonl --out models/surrogate_conversation_cont2 --base-model <bart-large dir> --epochs 10 --patience 1 --lr 5e-5
```

The shipped surrogate trained for 10 epochs in total. Early stopping kept epoch 9, with validation loss 0.54. See `results/surrogate_conversation_train*.log`.

## 5. Open items

- Run more Conversation test texts (all 700 if time allows) with 3 seeds. This matters most for Figure 4.
- Log more evaluation detail for larger runs: per-text precision, recall and F1, plus debugging statistics to diagnose failures.
- Train one surrogate per exploratory level, so hidden attributes are also hidden from training.
- Optional: the TRE, MapMake, DIRECT and MSS baselines, and other backbones (Qwen2.5-14B, Llama-70B).

## 6. Paper sections and code

| Paper | Code |
|---|---|
| Table 6 schemas, entity-grouped JSON tables | `tear_reproduction/schema.py` |
| Surrogate preview model: BART-Large, ⟨m⟩⟨s⟩⟨n⟩ serialization (4.2.1) | `surrogate/` |
| Header, value and semantic utilities, union of top-k_te (Eq. 7-11) | `tear_reproduction/retrieval.py` |
| EI, DI, SP, JI and definition prompts (A.1, A.4) | `tear_reproduction/prompts.py` |
| Table Extraction Workflow and Discovery Mechanism (Eq. 12-14) | `tear_reproduction/pipeline.py` |
| Hybrid Integration: Vendi score, Algorithms 1 and 2 (Eq. 15-17) | `tear_reproduction/integration.py` |
| Schema Coherence Score, 10 orderings (Eq. 18-19) | `tear_reproduction/coherence.py` |
| header-F1, structured-F1 with DF1, recall-AUC, EM / chrF / BERTScore (Eq. 20-22) | `eval/metrics.py` |
| Conversation benchmark, splits, exploratory levels (5.1) | `data_build/multiwoz.py` |
| Table 2, Figure 4 and TEAR\* experiments | `eval/reproduce.py` |

## 7. Differences from the paper

- **Data:** the Incidents and Weather annotations are not public. Conversation is rebuilt from MultiWOZ 2.4 following Section 5.1. Only 2 attributes fall below the 15% coverage rule, so the levels also hide the next-lowest-coverage attributes. The paper's counts (7 / 12 / 17 hidden) require this.
- **Test size and seeds:** the first run used 20 test texts instead of about 700. Table extraction used 3 seeds; attribute recommendation and TEAR\* used 1 seed.
- **Preview model at exploratory levels:** one surrogate is trained on the full-schema pool, and hidden columns are removed from its previews. The paper hides them from training as well.
- **Embedder:** SFR-Embedding-Mistral Q4_K_M served by llama.cpp (`--embedding --pooling last`). EOS is appended, as the model card's last-token pooling expects, and its semantic-similarity instruction is applied to both texts.
- **Preview decoding:** the surrogate often writes ⟨s⟩ where the single ⟨n⟩ after the header row belongs. When a sequence has no ⟨n⟩, the header row is taken as the leading run of cells that are attribute names (`surrogate/serialize.py`).
- **Placeholder names:** Llama-3-8B sometimes copies the DI template's `<new attribute 1>` names. Such a reply is retried with that error stated, and any placeholder left is dropped.
- **TEAR\*:** when no recommended attribute matches a hidden one exactly, the schema does not change, so TEAR\* is recorded as the TEAR run instead of being re-run.
- **Robustness additions:**
  - an unparseable reply is retried with the error appended (up to 3 calls)
  - copied template artifacts and unclosed braces are repaired
  - the longest demonstrations are dropped only when a prompt would not fit in the 8K context

  Each case is logged in the result files.
- **Algorithm 1:** proposals that are in no low-diversity set are kept, and spent single-element sets are retired so the loop ends. The printed algorithm leaves both implicit.
- **Definitions (A.4):** at most 3 source texts per proposal.
- **Example 5.2:** the paper's own recall (0.71) and structured-F1 (0.73) conflict with its Figure 3 matrix. Eq. 20 gives 0.9 and 0.82, and the code follows the equations.
- **Not reproduced:** the paper's baselines other than RAG (TRE, MapMake, DIRECT, MSS), and the Qwen and Llama-70B backbones. CFR is reported as a cheap reference for recommendation.
