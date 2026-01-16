import re
from typing import Any, Dict, Optional

from app.infra.settings import settings
from app.services.intent_types import ResolvedIntent
from app.services.llm.llm_intent_resolver import LLMIntentResolver

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

        if not raw_text or not raw_text.strip():
            return ResolvedIntent(
                action=None,
                payload=None,
                confidence=0.0,
                provider="pre_ai",
                model="regex",
                error="raw_text_required",
            )

        asset_match = ASSET_ID_REGEX.search(raw_text)
        task_match = TASK_ID_REGEX.search(raw_text)

        asset_id = asset_match.group("asset_id") if asset_match else None
        task_id = task_match.group("task_id") if task_match else None

        used_weak_match = False

        if not asset_id or not task_id:
            assign_match = ASSIGN_TASK_REGEX.search(raw_text)
            if assign_match:
                asset_id = asset_id or assign_match.group("asset_id")
                task_id = task_id or assign_match.group("task_id")
                used_weak_match = True

        used_fallback = False
        if not asset_id and fallback_payload.get("asset_id"):
            asset_id = fallback_payload.get("asset_id")
            used_fallback = True

        if not task_id and fallback_payload.get("task_id"):
            task_id = fallback_payload.get("task_id")
            used_fallback = True

        if not asset_id or not task_id:
            return ResolvedIntent(
                action=None,
                payload=None,
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
    ) -> ResolvedIntent:
        mode = settings.intent_resolution_mode

        if mode == "llm":
            return LLMIntentResolver().resolve(raw_text)

        if mode == "hybrid":
            pre = PreAIIntentResolver.resolve(
                raw_text,
                fallback_payload=fallback_payload,
            )
            if pre.error:
                return LLMIntentResolver().resolve(raw_text)
            return pre

        return PreAIIntentResolver.resolve(
            raw_text,
            fallback_payload=fallback_payload,
        )
