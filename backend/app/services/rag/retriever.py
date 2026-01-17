import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy import select

from app.infra.models.knowledge_chunk_model import KnowledgeChunkModel
from app.infra.session import get_session
from app.infra.settings import settings
from app.services.llm.openai_embeddings_client import OpenAIEmbeddingsClient

UUID_PATTERN = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)


@dataclass(frozen=True)
class RagContext:
    enabled: bool
    sources: List[str]
    context_text: str
    mode: Optional[str] = None
    top_k: Optional[int] = None
    retrieved_chunks: Optional[int] = None


class Retriever:
    @staticmethod
    def get_context(raw_text: str) -> RagContext:
        raw_text = (raw_text or "").strip()

        if settings.rag_mode == "off":
            return RagContext(
                enabled=False,
                sources=[],
                context_text="",
                mode="off",
                top_k=None,
                retrieved_chunks=None,
            )

        if settings.rag_mode == "lite":
            return Retriever._get_lite_context(raw_text)

        if settings.rag_mode == "vector":
            return Retriever._get_vector_context(raw_text)

        # Unknown mode -> behave like off (safe default) but expose mode
        return RagContext(
            enabled=False,
            sources=[],
            context_text="",
            mode=settings.rag_mode,
            top_k=None,
            retrieved_chunks=None,
        )

    @staticmethod
    def _get_lite_context(raw_text: str) -> RagContext:
        base_path = Path(settings.knowledge_base_path)
        if not base_path.exists() or not base_path.is_dir():
            return RagContext(enabled=True, sources=[], context_text="", mode="lite")

        files = sorted(base_path.glob("*.md"))
        if not files:
            return RagContext(enabled=True, sources=[], context_text="", mode="lite")

        content_map: Dict[str, str] = {}
        for file_path in files:
            try:
                content_map[file_path.name] = file_path.read_text(encoding="utf-8")
            except OSError:
                continue

        if not content_map:
            return RagContext(enabled=True, sources=[], context_text="", mode="lite")

        selected_files = Retriever._select_files(raw_text, content_map)
        context_text, sources = Retriever._build_context(selected_files, content_map)

        return RagContext(
            enabled=True,
            sources=sources,
            context_text=context_text,
            mode="lite",
            top_k=None,
            retrieved_chunks=len(sources),
        )

    @staticmethod
    def _get_vector_context(raw_text: str) -> RagContext:
        # If raw_text is empty, avoid embedding call
        if not raw_text:
            return RagContext(
                enabled=True,
                sources=[],
                context_text="",
                mode="vector",
                top_k=settings.rag_top_k,
                retrieved_chunks=0,
            )

        embeddings_client = OpenAIEmbeddingsClient()
        embeddings = embeddings_client.embed_texts([raw_text])
        if not embeddings:
            return RagContext(
                enabled=True,
                sources=[],
                context_text="",
                mode="vector",
                top_k=settings.rag_top_k,
                retrieved_chunks=0,
            )

        with get_session() as session:
            has_rows = session.execute(select(KnowledgeChunkModel.id).limit(1)).first()
            if not has_rows:
                return RagContext(
                    enabled=True,
                    sources=[],
                    context_text="",
                    mode="vector",
                    top_k=settings.rag_top_k,
                    retrieved_chunks=0,
                )

            embedding = embeddings[0]
            stmt = (
                select(KnowledgeChunkModel)
                .order_by(KnowledgeChunkModel.embedding.cosine_distance(embedding))
                .limit(settings.rag_top_k)
            )
            results = session.execute(stmt).scalars().all()

        context_text, sources = Retriever._build_vector_context(results)

        return RagContext(
            enabled=True,
            sources=sources,
            context_text=context_text,
            mode="vector",
            top_k=settings.rag_top_k,
            retrieved_chunks=len(results),
        )

    @staticmethod
    def _select_files(raw_text: str, content_map: Dict[str, str]) -> List[str]:
        filenames = list(content_map.keys())
        policies_name = "policies.md" if "policies.md" in content_map else None
        found_uuids = set(UUID_PATTERN.findall(raw_text or ""))

        if found_uuids:
            matched = []
            for name in filenames:
                if any(uuid in content_map[name] for uuid in found_uuids):
                    matched.append(name)
            if policies_name and policies_name not in matched:
                matched.append(policies_name)
            return matched

        selected = []
        if policies_name:
            selected.append(policies_name)

        for name in filenames:
            if name == policies_name:
                continue
            selected.append(name)

        return selected

    @staticmethod
    def _build_context(
        selected_files: List[str],
        content_map: Dict[str, str],
    ) -> tuple[str, List[str]]:
        max_chars = settings.rag_max_chars
        chunks: List[str] = []
        sources: List[str] = []
        total_chars = 0

        for name in selected_files:
            content = content_map.get(name)
            if not content:
                continue

            header = f"SOURCE: {name}\n"
            candidate = f"{header}{content.strip()}\n"
            candidate_len = len(candidate)

            if total_chars + candidate_len > max_chars:
                remaining = max_chars - total_chars
                if remaining <= len(header):
                    break
                trimmed_content = content.strip()[: max(0, remaining - len(header) - 1)]
                candidate = f"{header}{trimmed_content}\n"
                chunks.append(candidate)
                sources.append(name)
                total_chars += len(candidate)
                break

            chunks.append(candidate)
            sources.append(name)
            total_chars += candidate_len

        return "\n".join(chunks).strip(), sources

    @staticmethod
    def _build_vector_context(
        chunks: List[KnowledgeChunkModel],
    ) -> tuple[str, List[str]]:
        max_chars = settings.rag_max_chars
        pieces: List[str] = []
        sources: List[str] = []
        total_chars = 0

        for chunk in chunks:
            header = f"SOURCE: {chunk.source}\n"
            body = chunk.content.strip()
            candidate = f"{header}{body}\n"
            candidate_len = len(candidate)

            if total_chars + candidate_len > max_chars:
                remaining = max_chars - total_chars
                if remaining <= len(header):
                    break
                trimmed_body = body[: max(0, remaining - len(header) - 1)]
                candidate = f"{header}{trimmed_body}\n"
                pieces.append(candidate)
                if chunk.source not in sources:
                    sources.append(chunk.source)
                total_chars += len(candidate)
                break

            pieces.append(candidate)
            if chunk.source not in sources:
                sources.append(chunk.source)
            total_chars += candidate_len

        return "\n".join(pieces).strip(), sources
