"""M3: cross-encoder reranking with BGE reranker."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RERANK_TOP_K

RERANK_MODEL = "BAAI/bge-reranker-v2-m3"


@dataclass
class RerankResult:
    text: str
    score: float
    metadata: dict = field(default_factory=dict)


class CrossEncoderReranker:
    def __init__(self, model_name: str = RERANK_MODEL):
        import torch
        from sentence_transformers import CrossEncoder
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = CrossEncoder(model_name, device=device, max_length=512)
        if device == "cuda":
            self.model.model.half()

    def rerank(self, query: str, documents: list[dict], top_k: int = RERANK_TOP_K) -> list[RerankResult]:
        if not documents:
            return []
        scores = self.model.predict([(query, d["text"]) for d in documents], batch_size=16)
        ranked = sorted(zip(documents, scores), key=lambda p: float(p[1]), reverse=True)[:top_k]
        return [RerankResult(d["text"], float(s), d.get("metadata", {})) for d, s in ranked]
