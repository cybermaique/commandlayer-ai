from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from app.infra.settings import settings


@dataclass(frozen=True)
class KnowledgeChunk:
    source: str
    chunk_index: int
    content: str
    content_hash: str


def load_markdown_chunks(base_path: Path) -> list[KnowledgeChunk]:
    if not base_path.exists() or not base_path.is_dir():
        return []

    chunk_size = settings.kb_chunk_size
    chunk_overlap = settings.kb_chunk_overlap
    chunks: list[KnowledgeChunk] = []

    for file_path in sorted(base_path.glob("*.md")):
        try:
            content = file_path.read_text(encoding="utf-8")
        except OSError:
            continue

        for index, chunk in enumerate(
            _split_text(content, chunk_size, chunk_overlap)
        ):
            chunk_hash = sha256(chunk.encode("utf-8")).hexdigest()
            chunks.append(
                KnowledgeChunk(
                    source=file_path.name,
                    chunk_index=index,
                    content=chunk,
                    content_hash=chunk_hash,
                )
            )

    return chunks


def _split_text(text: str, size: int, overlap: int) -> list[str]:
    if size <= 0:
        return []

    normalized = text.strip()
    if not normalized:
        return []

    overlap = max(0, min(overlap, size - 1))
    chunks: list[str] = []
    start = 0
    length = len(normalized)

    while start < length:
        end = min(start + size, length)
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= length:
            break
        start = end - overlap

    return chunks
