"""BM25 + vector search, combined by rank, then scored by a cross-encoder."""
import json
import hashlib
import re
from time import perf_counter

import numpy as np
import torch
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder, SentenceTransformer

from settings import DATA, EMBED_MODEL, INDEX, RERANK_MODEL


def tokens(text):
    return re.findall(r"[a-z0-9_]+", text.lower())


class Search:
    def __init__(self, index=INDEX):
        torch.set_num_threads(4)
        self.chunks = json.loads((index / "chunks.json").read_text(encoding="utf-8"))
        self.vectors = np.load(index / "vectors.npy", allow_pickle=False)
        config = json.loads((index / "config.json").read_text(encoding="utf-8"))
        if config["corpus_sha256"] != hashlib.sha256((DATA / "documents.jsonl").read_bytes()).hexdigest():
            raise ValueError("The documents changed. Run build_index.py again.")
        if len(self.chunks) != len(self.vectors) or config["model"] != EMBED_MODEL:
            raise ValueError("The index does not match the model. Run build_index.py again.")
        self.embedder = SentenceTransformer(EMBED_MODEL, device="cpu")
        self.reranker = CrossEncoder(RERANK_MODEL, device="cpu", max_length=512)
        self.bm25 = BM25Okapi([tokens(c["section"] + " " + c["text"]) for c in self.chunks])
        self.documents = sorted({c["document"] for c in self.chunks})

    def retrieve(self, question, mode="rerank", k=5, document=None):
        if mode not in {"keyword", "vector", "hybrid", "rerank"}:
            raise ValueError("Unknown retrieval mode")
        started = perf_counter()
        ids = np.array([i for i, c in enumerate(self.chunks) if not document or c["document"] == document], dtype=int)
        if len(ids) == 0:
            return [], (perf_counter() - started) * 1000
        ranks = []
        if mode != "vector":
            scores = self.bm25.get_scores(tokens(question))
            ranks.append(ids[np.argsort(-scores[ids], kind="stable")[:30]])
        if mode != "keyword":
            query = self.embedder.encode(question, normalize_embeddings=True)
            scores = self.vectors @ query
            ranks.append(ids[np.argsort(-scores[ids], kind="stable")[:30]])
        if mode in {"keyword", "vector"}:
            selected = list(ranks[0][:k])
        else:
            combined = {}
            for ranking in ranks:
                for rank, i in enumerate(ranking):
                    combined[int(i)] = combined.get(int(i), 0) + 1 / (60 + rank + 1)
            selected = sorted(combined, key=combined.get, reverse=True)[:20]
        if mode == "rerank":
            scores = self.reranker.predict([(question, self.chunks[i]["section"] + "\n" + self.chunks[i]["text"]) for i in selected])
            pairs = sorted(zip(selected, scores), key=lambda item: float(item[1]), reverse=True)[:k]
            found = [{**self.chunks[i], "score": float(score)} for i, score in pairs]
        else:
            found = [{**self.chunks[i], "score": None} for i in selected[:k]]
        return found, (perf_counter() - started) * 1000
