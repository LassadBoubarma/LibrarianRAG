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

TOKEN_RE = re.compile(r"[a-z0-9_]+")
RRF_WEIGHTS = [1.0 / (60 + rank + 1) for rank in range(30)]


def tokens(text):
    return TOKEN_RE.findall(text.lower())


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
        # Precomputed index mappings and candidate strings to eliminate redundant allocations
        self.all_ids = np.arange(len(self.chunks), dtype=int)
        self.doc_ids = {}
        for i, c in enumerate(self.chunks):
            self.doc_ids.setdefault(c["document"], []).append(i)
        self.doc_ids = {doc: np.array(indices, dtype=int) for doc, indices in self.doc_ids.items()}
        self.chunk_texts = [c["section"] + "\n" + c["text"] for c in self.chunks]

    def retrieve(self, question, mode="rerank", k=5, document=None):
        if mode not in {"keyword", "vector", "hybrid", "rerank"}:
            raise ValueError("Unknown retrieval mode")
        started = perf_counter()
        if document:
            ids = self.doc_ids.get(document)
            if ids is None or len(ids) == 0:
                return [], (perf_counter() - started) * 1000
        else:
            ids = self.all_ids

        ranks = []
        if mode != "vector":
            scores = self.bm25.get_scores(tokens(question))
            sub_scores = scores if document is None else scores[ids]
            top_idx = np.argsort(-sub_scores, kind="stable")[:30]
            ranks.append(top_idx if document is None else ids[top_idx])
        if mode != "keyword":
            query = self.embedder.encode(question, normalize_embeddings=True)
            scores = self.vectors @ query
            sub_scores = scores if document is None else scores[ids]
            top_idx = np.argsort(-sub_scores, kind="stable")[:30]
            ranks.append(top_idx if document is None else ids[top_idx])
        if mode in {"keyword", "vector"}:
            selected = list(ranks[0][:k])
        else:
            combined = {}
            for ranking in ranks:
                for rank, i in enumerate(ranking):
                    idx = int(i)
                    combined[idx] = combined.get(idx, 0.0) + RRF_WEIGHTS[rank]
            selected = sorted(combined, key=combined.get, reverse=True)[:20]
        if mode == "rerank":
            pairs = [(question, self.chunk_texts[i]) for i in selected]
            scores = self.reranker.predict(pairs, show_progress_bar=False)
            ranked_pairs = sorted(zip(selected, scores), key=lambda item: float(item[1]), reverse=True)[:k]
            found = [{**self.chunks[i], "score": float(score)} for i, score in ranked_pairs]
        else:
            found = [{**self.chunks[i], "score": None} for i in selected[:k]]
        return found, (perf_counter() - started) * 1000
