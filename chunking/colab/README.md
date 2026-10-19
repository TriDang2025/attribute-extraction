# Running the chunking comparison on Google Colab (GitHub + Hugging Face)

- **Code:** this repo, folder `chunking/`. It is separate from `tear/` and `hdbscan/`.
- **Data:** the HF dataset `database-lab/attribute-extraction-data`, folder `chunking/`, which holds `MULTIWOZ2.4.zip` and `conversation_ids.txt`.
- **Results:** committed back to this repo under `chunking/results/`.

Steps marked **YOU** need a person.

## What runs
`scripts/run.py` runs 6 chunkers over two settings:
- **Chunkers:** RSC, Chroma ClusterSemanticChunker, Chonkie with potion, Chonkie with bge-m3, fixed 400-token chunks, and TextTiling.
- **Setting S:** 1,000 single dialogues.
- **Setting T:** 50 stitched documents of 20 dialogues each, for seeds 42, 0 and 1.

It is resumable: each method's chunks are appended to `results/<run>/chunks/*.jsonl`, and documents already there are skipped.

## One-time setup
Tokens and Colab Secrets work the same way as for TEAR (`tear/colab/README.md`):
- `HF_TOKEN`: a token with read access to the dataset
- `GH_TOKEN`: a classic token with the `public_repo` scope

**Never put a token in a notebook cell or a file.**

## Each session
1. **YOU: open the notebook.** In Colab, File > Open notebook > GitHub, pick `chunking/colab/CHK_colab.ipynb`, and choose a GPU (an L4 is best).
2. **YOU: fill in your git name and email** in cell 1, then run cell 1.
3. **Run cell 2.** It works in the background and takes about 30–60 min on an L4.
4. **Cell 3 shows progress.** The log ends with `CHK_DONE`.
5. **YOU: keep the tab open.** After a disconnect, run cells 1 and 2 again; the run resumes.
6. **Results:** `git pull` on any machine. Each run writes `results/<run>/metrics.csv`.
