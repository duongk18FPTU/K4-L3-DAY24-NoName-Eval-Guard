"""M2: hybrid search = BM25 + dense (BGE-M3 in Qdrant), fused with Reciprocal Rank Fusion."""
from __future__ import annotations

import os
import re
import sys
import uuid
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (BM25_TOP_K, COLLECTION_NAME, DENSE_TOP_K, EMBEDDING_DIM, EMBEDDING_MODEL,
                    HYBRID_TOP_K, QDRANT_HOST, QDRANT_PORT)

RRF_K = 60


@dataclass
class SearchResult:
    text: str
    score: float
    metadata: dict = field(default_factory=dict)


def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


_MODEL = None


def get_embedder():
    global _MODEL
    if _MODEL is None:
        import torch
        from sentence_transformers import SentenceTransformer
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _MODEL = SentenceTransformer(EMBEDDING_MODEL, device=device)
        if device == "cuda":
            _MODEL.half()
        _MODEL.max_seq_length = 512
    return _MODEL


class HybridSearch:
    def __init__(self, collection: str = COLLECTION_NAME):
        from qdrant_client import QdrantClient
        self.collection = collection
        self.client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=60)
        self.chunks: list[dict] = []
        self.bm25 = None

    def index(self, chunks: list[dict]) -> None:
        from qdrant_client.models import Distance, PointStruct, VectorParams
        from rank_bm25 import BM25Okapi

        self.chunks = list(chunks)
        self.bm25 = BM25Okapi([tokenize(c["text"]) for c in self.chunks])

        embedder = get_embedder()
        vectors = embedder.encode([c["text"] for c in self.chunks], batch_size=32,
                                  normalize_embeddings=True, show_progress_bar=True)
        if self.client.collection_exists(self.collection):
            self.client.delete_collection(self.collection)
        self.client.create_collection(
            self.collection, vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE))
        for start in range(0, len(self.chunks), 256):
            batch = range(start, min(start + 256, len(self.chunks)))
            self.client.upsert(self.collection, points=[
                PointStruct(id=i, vector=vectors[i].tolist(),
                            payload={"text": self.chunks[i]["text"],
                                     "metadata": self.chunks[i].get("metadata", {})})
                for i in batch])

    def _bm25_ranking(self, query: str) -> list[int]:
        scores = self.bm25.get_scores(tokenize(query))
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        return [i for i in order[:BM25_TOP_K] if scores[i] > 0]

    def _dense_ranking(self, query: str) -> list[int]:
        vector = get_embedder().encode([query], normalize_embeddings=True)[0].tolist()
        hits = self.client.search(self.collection, query_vector=vector, limit=DENSE_TOP_K)
        return [int(h.id) for h in hits]

    def search(self, query: str, top_k: int = HYBRID_TOP_K) -> list[SearchResult]:
        if self.bm25 is None:
            raise RuntimeError("Call index(chunks) before search().")
        fused: dict[int, float] = {}
        for ranking in (self._bm25_ranking(query), self._dense_ranking(query)):
            for rank, idx in enumerate(ranking):
                fused[idx] = fused.get(idx, 0.0) + 1.0 / (RRF_K + rank + 1)
        top = sorted(fused, key=fused.get, reverse=True)[:top_k]
        return [SearchResult(self.chunks[i]["text"], fused[i], self.chunks[i].get("metadata", {}))
                for i in top]
