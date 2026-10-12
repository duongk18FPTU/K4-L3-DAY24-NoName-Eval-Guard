"""M1: load corpus and hierarchical (parent/child) chunking."""
from __future__ import annotations

import os
import re
import sys
import uuid
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATA_DIR, HIERARCHICAL_CHILD_SIZE, HIERARCHICAL_PARENT_SIZE


@dataclass
class Chunk:
    text: str
    metadata: dict = field(default_factory=dict)
    parent_id: str | None = None
    chunk_id: str = field(default_factory=lambda: uuid.uuid4().hex)


def _read_pdf(path: str) -> str:
    from pypdf import PdfReader
    reader = PdfReader(path)
    return "\n\n".join((page.extract_text() or "").strip() for page in reader.pages)


def _title_of(text: str, fallback: str) -> str:
    m = re.search(r"^#\s+(.+)$", text, flags=re.M)
    return m.group(1).strip() if m else fallback


def load_documents(data_dir: str = DATA_DIR) -> list[dict]:
    """Read every .md/.pdf in the corpus. Old policy versions are kept on purpose."""
    docs = []
    for name in sorted(os.listdir(data_dir)):
        path = os.path.join(data_dir, name)
        stem, ext = os.path.splitext(name)
        if ext.lower() == ".md":
            with open(path, encoding="utf-8") as f:
                text = f.read()
        elif ext.lower() == ".pdf":
            text = _read_pdf(path)
        else:
            continue
        if not text.strip():
            print(f"[m1] skip {name}: no extractable text (scanned PDF?)")
            continue
        version = re.search(r"Phiên bản:\s*([^|\n]+)", text)
        docs.append({"text": text, "metadata": {
            "source": name, "doc_id": stem, "doc_type": ext.lower().lstrip("."),
            "title": _title_of(text, stem),
            "version": version.group(1).strip() if version else None,
        }})
    return docs


def _split_sections(text: str) -> list[tuple[str, str]]:
    """Split markdown by headings -> [(heading, body)]; plain text is one section."""
    parts = re.split(r"(?m)^(#{1,4}\s+.+)$", text)
    sections = []
    if parts[0].strip():
        sections.append(("", parts[0].strip()))
    for i in range(1, len(parts), 2):
        sections.append((parts[i].lstrip("# ").strip(), parts[i + 1].strip()))
    return [(h, b) for h, b in sections if h or b]


def _split_sentences(text: str) -> list[str]:
    pieces = re.split(r"(?<=[.!?;:])\s+|\n+", text)
    return [p.strip() for p in pieces if p and p.strip()]


def _pack(units: list[str], limit: int) -> list[str]:
    """Greedily pack units into pieces <= limit chars; hard-split oversize units."""
    out, cur = [], ""
    for unit in units:
        while len(unit) > limit:
            if cur:
                out.append(cur)
                cur = ""
            out.append(unit[:limit])
            unit = unit[limit:]
        if cur and len(cur) + 1 + len(unit) > limit:
            out.append(cur)
            cur = unit
        else:
            cur = f"{cur} {unit}".strip()
    if cur:
        out.append(cur)
    return out


def chunk_hierarchical(text: str, metadata: dict | None = None,
                       parent_size: int = HIERARCHICAL_PARENT_SIZE,
                       child_size: int = HIERARCHICAL_CHILD_SIZE) -> tuple[list[Chunk], list[Chunk]]:
    """Return (parents, children). Children carry parent_id and the title/heading as a prefix
    so that a child stays attributable to its policy version when retrieved alone."""
    metadata = dict(metadata or {})
    title = metadata.get("title", "")
    parents: list[Chunk] = []
    children: list[Chunk] = []

    for heading, body in _split_sections(text):
        for piece in _pack(_split_sentences(body), parent_size):
            parent = Chunk(f"{heading}\n{piece}".strip(), {**metadata, "heading": heading})
            parents.append(parent)
            prefix = " > ".join(dict.fromkeys(p for p in (title, heading) if p))
            budget = max(child_size - len(prefix) - 3, 64)
            for child_piece in _pack(_split_sentences(piece), budget):
                child_text = f"[{prefix}] {child_piece}" if prefix else child_piece
                children.append(Chunk(child_text, {**metadata, "heading": heading},
                                      parent_id=parent.chunk_id))
    return parents, children
