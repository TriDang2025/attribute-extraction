"""The three chunkers (and two baselines). Each returns a list of chunk strings, in text order.

1. rsc      - Recursive Semantic Chunking, rebuilt from Latif et al. (ICNLSP 2025) Algorithm 1
2. chroma   - ClusterSemanticChunker, official code (chunking_evaluation @ e708410)
3. chonkie  - chonkie.SemanticChunker 1.7.0, official code
Baselines: fixed (400 cl100k tokens) and texttiling (NLTK, lexical).
"""

import re

import numpy as np

from . import config

SENT_END = re.compile(r"(?<=[.?!])\s+")


# ------------------------------------------------------------------ 1. RSC
def _semantic(lc_emb, text, percentile):
    from langchain_experimental.text_splitter import SemanticChunker
    sc = SemanticChunker(lc_emb, breakpoint_threshold_type="percentile",
                         breakpoint_threshold_amount=percentile)
    return [c for c in sc.split_text(text) if c.strip()]


def _presplit(text, t_max):
    """Split at the nearest sentence boundary so that every segment is <= t_max chars."""
    if len(text) <= t_max:
        return [text]
    out, cur = [], ""
    for s in SENT_END.split(text):
        if cur and len(cur) + 1 + len(s) > t_max:
            out.append(cur)
            cur = s
        else:
            cur = f"{cur} {s}" if cur else s
    if cur:
        out.append(cur)
    return out


def _recurse(lc_emb, chunk, percentile, p):
    """R(c, T): re-run the semantic chunker on chunks > T_chunk with a lower breakpoint percentile."""
    if len(chunk) <= p["t_chunk"]:
        return [chunk]
    nxt = percentile - p["delta"]
    if nxt < p["floor_percentile"]:
        return [chunk]
    parts = _semantic(lc_emb, chunk, nxt)
    out = []
    for part in parts:
        out += _recurse(lc_emb, part, nxt, p)
    return out


def _merge_short(enc, chunks, t_merge):
    """Merge each chunk shorter than T_merge into the more similar neighbour (S_prev >= S_next -> prev)."""
    chunks = list(chunks)
    i = 0
    while i < len(chunks) and len(chunks) > 1:
        if len(chunks[i]) >= t_merge:
            i += 1
            continue
        v = enc.encode([c for c in chunks[max(0, i - 1):i + 2]])
        me = v[1] if i > 0 else v[0]
        s_prev = float(me @ v[0]) if i > 0 else -np.inf
        s_next = float(me @ v[-1]) if i + 1 < len(chunks) else -np.inf
        if s_prev >= s_next:
            chunks[i - 1] = chunks[i - 1] + " " + chunks[i]
            del chunks[i]
        else:
            chunks[i + 1] = chunks[i] + " " + chunks[i + 1]
            del chunks[i]
    return chunks


def rsc(text, enc, lc_emb, p=config.RSC):
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    c0 = []
    for seg in _presplit(text, p["t_max"]):
        c0 += _semantic(lc_emb, seg, p["start_percentile"])
    c1 = []
    for c in c0:
        c1 += _recurse(lc_emb, c, p["start_percentile"], p)
    c2 = _merge_short(enc, c1, p["t_merge"])
    rec = RecursiveCharacterTextSplitter(chunk_size=p["t_final"], chunk_overlap=0)
    out = []
    for c in c2:
        out += rec.split_text(c) if len(c) > p["t_final"] else [c]
    return out


# ------------------------------------------------------------------ 2. Chroma
def chroma(text, ef, p=config.CHROMA):
    from chunking_evaluation.chunking import ClusterSemanticChunker
    return ClusterSemanticChunker(embedding_function=ef, **p).split_text(text)


# ------------------------------------------------------------------ 3. Chonkie
def chonkie(text, emb, p=config.CHONKIE):
    from chonkie import SemanticChunker
    return [c.text for c in SemanticChunker(embedding_model=emb, **p).chunk(text)]


# ------------------------------------------------------------------ baselines
def fixed(text, p=config.FIXED):
    from chunking_evaluation.chunking import FixedTokenChunker
    return FixedTokenChunker(**p).split_text(text)


def texttiling(text, p=config.TEXTTILING):
    """Classic TextTiling; one turn per pseudo-paragraph (NLTK cuts only at paragraph breaks)."""
    from nltk.tokenize import TextTilingTokenizer
    para = text.replace("\n", "\n\n")
    try:
        tiles = TextTilingTokenizer(**p).tokenize(para)
    except ValueError:  # text shorter than the window
        return [text]
    return [t.strip("\n").replace("\n\n", "\n") for t in tiles if t.strip()]
