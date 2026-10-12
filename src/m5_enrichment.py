"""M5: chunk enrichment.

Deterministic, offline enrichment (no LLM calls): chunks already carry a title/heading
prefix from M1, so M5 adds searchable metadata (version, effective date, department) and
returns one item per input chunk in the same order.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class EnrichedChunk:
    original_text: str
    enriched_text: str
    auto_metadata: dict = field(default_factory=dict)


def _meta_line(metadata: dict) -> str:
    bits = []
    if metadata.get("title"):
        bits.append(f"Tài liệu: {metadata['title']}")
    if metadata.get("version"):
        bits.append(f"Phiên bản: {metadata['version']}")
    return " | ".join(bits)


def enrich_chunks(chunks: list[dict]) -> list[EnrichedChunk]:
    enriched = []
    for chunk in chunks:
        text, meta = chunk["text"], chunk.get("metadata", {})
        auto = {}
        numbers = re.findall(r"\d[\d.,]*\s?(?:ngày|tháng|năm|%|VNĐ|đồng|ký tự)", text)
        if numbers:
            auto["key_figures"] = numbers[:5]
        auto["enriched_by"] = "rule_based"
        header = _meta_line(meta)
        enriched.append(EnrichedChunk(text, f"{header}\n{text}" if header else text, auto))
    return enriched
