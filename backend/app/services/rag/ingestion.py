from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from sqlalchemy import delete, select, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.infra.models.knowledge_chunk_model import KnowledgeChunkModel
from app.infra.settings import settings
from app.services.llm.openai_embeddings_client import OpenAIEmbeddingsClient
from app.services.rag.chunker import KnowledgeChunk, load_markdown_chunks


@dataclass(frozen=True)
class IngestionSummary:
    inserted: int
    updated: int
    deleted: int
    skipped: int
    total: int


def ingest_knowledge_base(session: Session) -> IngestionSummary:
    base_path = Path(settings.knowledge_base_path)
    chunks = load_markdown_chunks(base_path)

    if not chunks:
        return IngestionSummary(inserted=0, updated=0, deleted=0, skipped=0, total=0)

    sources = sorted({chunk.source for chunk in chunks})
    existing_rows = session.execute(
        select(KnowledgeChunkModel).where(KnowledgeChunkModel.source.in_(sources))
    ).scalars().all()

    existing_map = {
        (row.source, row.chunk_index): row for row in existing_rows
    }
    incoming_map = {
        (chunk.source, chunk.chunk_index): chunk for chunk in chunks
    }

    to_embed: list[KnowledgeChunk] = []
    skipped = 0
    inserted = 0
    updated = 0
    for chunk in chunks:
        existing = existing_map.get((chunk.source, chunk.chunk_index))
        if existing and existing.content_hash == chunk.content_hash:
            skipped += 1
            continue
        if existing:
            updated += 1
        else:
            inserted += 1
        to_embed.append(chunk)

    embeddings_client = OpenAIEmbeddingsClient()
    embeddings = _embed_chunks(embeddings_client, to_embed)

    if embeddings or not to_embed:
        deleted = 0
        to_delete = [
            (source, chunk_index)
            for (source, chunk_index) in existing_map.keys()
            if (source, chunk_index) not in incoming_map
        ]
        if to_delete:
            delete_stmt = delete(KnowledgeChunkModel).where(
                tuple_(KnowledgeChunkModel.source, KnowledgeChunkModel.chunk_index).in_(
                    to_delete
                )
            )
            deleted = session.execute(delete_stmt).rowcount or 0

        now = datetime.utcnow()
        rows = []
        for chunk, embedding in zip(to_embed, embeddings):
            rows.append(
                {
                    "id": str(uuid4()),
                    "source": chunk.source,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "content_hash": chunk.content_hash,
                    "embedding": embedding,
                    "created_at": now,
                    "updated_at": now,
                }
            )

        if rows:
            stmt = insert(KnowledgeChunkModel).values(rows)
            stmt = stmt.on_conflict_do_update(
                index_elements=["source", "chunk_index"],
                set_={
                    "content": stmt.excluded.content,
                    "content_hash": stmt.excluded.content_hash,
                    "embedding": stmt.excluded.embedding,
                    "updated_at": stmt.excluded.updated_at,
                },
            )
            session.execute(stmt)

        session.commit()
    else:
        deleted = 0

    return IngestionSummary(
        inserted=inserted if embeddings else 0,
        updated=updated if embeddings else 0,
        deleted=deleted,
        skipped=skipped if embeddings else skipped + len(to_embed),
        total=len(chunks),
    )


def _embed_chunks(
    client: OpenAIEmbeddingsClient,
    chunks: Iterable[KnowledgeChunk],
) -> list[list[float]]:
    chunk_list = list(chunks)
    if not chunk_list:
        return []

    texts = [chunk.content for chunk in chunk_list]
    embeddings = client.embed_texts(texts)
    if len(embeddings) != len(chunk_list):
        return []
    return embeddings
