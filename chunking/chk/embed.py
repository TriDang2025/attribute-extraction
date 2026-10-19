"""One cached bge-m3 encoder plus adapters for the three libraries' embedding APIs."""

import hashlib
import pickle

import numpy as np

from . import config


class Encoder:
    """sentence-transformers model with an on-disk cache keyed by text hash (normalized vectors)."""

    def __init__(self, name=config.BGE_M3, tag="bge-m3"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(name, device="cpu" if not _cuda() else "cuda")
        self.model.max_seq_length = config.BGE_MAX_LEN
        self.tag = tag
        self.path = config.CACHE / f"{tag}.pkl"
        self.cache = pickle.load(open(self.path, "rb")) if self.path.exists() else {}
        self.n_new = 0

    @staticmethod
    def key(text):
        return hashlib.sha1(text.encode("utf-8")).hexdigest()

    def encode(self, texts):
        keys = [self.key(t) for t in texts]
        todo = sorted({k: t for k, t in zip(keys, texts) if k not in self.cache}.items(),
                      key=lambda kv: len(kv[1]))  # length-sorted batches pad less
        if todo:
            vecs = self.model.encode([t for _, t in todo], batch_size=config.BGE_BATCH,
                                     normalize_embeddings=True, convert_to_numpy=True)
            for (k, _), v in zip(todo, vecs):
                self.cache[k] = v.astype(np.float32)
            self.n_new += len(todo)
        return np.stack([self.cache[k] for k in keys]) if keys else np.zeros((0, self.dim))

    @property
    def dim(self):
        return self.model.get_sentence_embedding_dimension()

    def save(self):
        if self.n_new:
            config.CACHE.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            pickle.dump(self.cache, open(tmp, "wb"))
            tmp.replace(self.path)
            self.n_new = 0


def _cuda():
    try:
        import torch
        return torch.cuda.is_available()
    except Exception:
        return False


def langchain_embeddings(enc):
    from langchain_core.embeddings import Embeddings

    class LCEmb(Embeddings):
        def embed_documents(self, texts):
            return enc.encode(list(texts)).tolist()

        def embed_query(self, text):
            return enc.encode([text])[0].tolist()

    return LCEmb()


def chroma_embedding_function(enc):
    """ClusterSemanticChunker calls embedding_function(list_of_str) -> list of vectors."""
    def ef(input):
        return [v for v in enc.encode(list(input))]
    return ef


def chonkie_embeddings(enc):
    from chonkie.embeddings import SentenceTransformerEmbeddings

    class Cached(SentenceTransformerEmbeddings):
        def embed(self, text):
            return enc.encode([text])[0]

        def embed_batch(self, texts):
            return list(enc.encode(list(texts)))

    return Cached(enc.model)


def chonkie_potion():
    from chonkie.embeddings import Model2VecEmbeddings
    return Model2VecEmbeddings(config.POTION)
