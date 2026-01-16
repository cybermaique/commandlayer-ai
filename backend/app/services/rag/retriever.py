import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from app.infra.settings import settings

UUID_PATTERN = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)


@dataclass(frozen=True)
class RagContext:
    enabled: bool
    sources: List[str]
    context_text: str


class Retriever:
    @staticmethod
    def get_context(raw_text: str) -> RagContext:
        if settings.rag_mode != "lite":
            return RagContext(enabled=False, sources=[], context_text="")

        base_path = Path(settings.knowledge_base_path)
        if not base_path.exists() or not base_path.is_dir():
            return RagContext(enabled=True, sources=[], context_text="")

        files = sorted(base_path.glob("*.md"))
        if not files:
            return RagContext(enabled=True, sources=[], context_text="")

        content_map: Dict[str, str] = {}
        for file_path in files:
            try:
                content_map[file_path.name] = file_path.read_text(encoding="utf-8")
            except OSError:
                continue

        if not content_map:
            return RagContext(enabled=True, sources=[], context_text="")

        selected_files = Retriever._select_files(raw_text, content_map)
        context_text, sources = Retriever._build_context(selected_files, content_map)

        return RagContext(
            enabled=True,
            sources=sources,
            context_text=context_text,
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
