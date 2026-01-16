import re
from typing import Any, Dict, Optional

from app.infra.settings import settings
from app.services.intent_types import ResolvedIntent, ResolvedIntentResult
from app.services.llm.llm_intent_resolver import LLMIntentResolver
from app.services.rag.retriever import RagContext, Retriever

UUID_PATTERN = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"

ASSET_ID_REGEX = re.compile(
    rf"asset_id\s*[:=]\s*(?P<asset_id>{UUID_PATTERN})",
    re.IGNORECASE,
)
TASK_ID_REGEX = re.compile(
    rf"task_id\s*[:=]\s*(?P<task_id>{UUID_PATTERN})",
    re.IGNORECASE,
)
ASSIGN_TASK_REGEX = re.compile(
    rf"(?:assign|atribuir)\s+task\s+(?P<task_id>{UUID_PATTERN}).*?(?:to|ao)\s+asset\s+(?P<asset_id>{UUID_PATTERN})",
    re.IGNORECASE,
)


class PreAIIntentResolver:
    @staticmethod
    def resolve(
        raw_text: str,
        fallback_payload: Optional[Dict[str, Any]] = None,
    ) -> ResolvedIntent:
        payload: Dict[str, Any] = {}
        fallback_payload = fallback_payload or {}

        used_fallback = False
        used_weak_match = False

        asset_id = None
        task_id = None

        assign_match = ASSIGN_TASK_REGEX.search(raw_text)
        if assign_match:
            asset_id = assign_match.group("asset_id")
            task_id = assign_match.group("task_id")
        else:
            asset_match = ASSET_ID_REGEX.search(raw_text)
            task_match = TASK_ID_REGEX.search(raw_text)

            if asset_match:
                asset_id = asset_match.group("asset_id")
            if task_match:
                task_id = task_match.group("task_id")

        if not asset_id and "asset_id" in fallback_payload:
            asset_id = fallback_payload.get("asset_id")
            used_fallback = True

        if not task_id and "task_id" in fallback_payload:
            task_id = fallback_payload.get("task_id")
            used_fallback = True

        if not asset_id or not task_id:
            return ResolvedIntent(
                action=None,
                payload={},
                confidence=0.0,
                provider="pre_ai",
                model="regex",
                error="missing_fields",
            )

        payload = {
            "asset_id": asset_id,
            "task_id": task_id,
        }

        confidence = 0.7 if used_fallback or used_weak_match else 1.0

        return ResolvedIntent(
            action="assign_task",
            payload=payload,
            confidence=confidence,
            provider="pre_ai",
            model="regex",
        )


class IntentResolver:
    @staticmethod
    def resolve(
        raw_text: str,
        fallback_payload: Optional[Dict[str, Any]] = None,
    ) -> ResolvedIntentResult:
        mode = settings.intent_resolution_mode
        empty_rag = RagContext(enabled=False, sources=[], context_text="")

        if mode == "llm":
            rag = Retriever.get_context(raw_text)
            intent = LLMIntentResolver().resolve(
                raw_text,
                context=rag.context_text,
            )
            return ResolvedIntentResult(intent=intent, rag=rag)

        if mode == "hybrid":
            pre = PreAIIntentResolver.resolve(
                raw_text,
                fallback_payload=fallback_payload,
            )

            if pre.error:
                rag = Retriever.get_context(raw_text)
                intent = LLMIntentResolver().resolve(
                    raw_text,
                    context=rag.context_text,
                )
                return ResolvedIntentResult(intent=intent, rag=rag)

            return ResolvedIntentResult(intent=pre, rag=empty_rag)

        pre = PreAIIntentResolver.resolve(
            raw_text,
            fallback_payload=fallback_payload,
        )
        return ResolvedIntentResult(intent=pre, rag=empty_rag)
