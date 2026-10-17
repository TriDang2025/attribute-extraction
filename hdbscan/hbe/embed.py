"""bge-m3 embeddings with the repo's settings (generate_bge_m3_embeddings.ipynb).

The repo encodes per year with batch_size=1, so every text is encoded alone and
order does not affect the result. We encode in length order (faster, same output
for batch_size=1) and write rows back in input order. Partial results are saved
every `chunk` texts so a run can resume.
"""

from pathlib import Path

import numpy as np

from . import config


def load_model(model_path=None, device=None):
    import torch
    from sentence_transformers import SentenceTransformer
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    path = model_path or (config.MODELS / "bge-m3")
    model = SentenceTransformer(str(path), device=device)
    model.max_seq_length = config.MAX_SEQ_LEN
    return model


def encode(model, texts, out_path, chunk=500, batch_size=config.BATCH_SIZE, progress=True):
    out_path = Path(out_path)
    part = out_path.with_suffix(".partial.npy")
    done_path = out_path.with_suffix(".done.npy")
    n = len(texts)
    order = np.argsort([-len(t) for t in texts], kind="stable")  # longest first: OOM shows early
    dim = model.get_sentence_embedding_dimension()
    if part.exists() and done_path.exists():
        emb, done = np.load(part), np.load(done_path)
        assert emb.shape == (n, dim) and done.shape == (n,), "partial file does not match input"
    else:
        emb, done = np.zeros((n, dim), dtype=np.float32), np.zeros(n, dtype=bool)
    todo = [i for i in order if not done[i]]
    for start in range(0, len(todo), chunk):
        idx = todo[start:start + chunk]
        vec = model.encode([texts[i] for i in idx], batch_size=batch_size,
                           show_progress_bar=progress, convert_to_numpy=True,
                           normalize_embeddings=config.NORMALIZE)
        emb[idx], done[idx] = vec, True
        np.save(part, emb)
        np.save(done_path, done)
        print(f"  {int(done.sum())}/{n} encoded", flush=True)
    np.save(out_path, emb)
    part.unlink(missing_ok=True)
    done_path.unlink(missing_ok=True)
    return emb
