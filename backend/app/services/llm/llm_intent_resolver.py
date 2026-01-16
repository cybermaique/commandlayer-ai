import json

from app.infra.settings import settings
from app.services.intent_types import ResolvedIntent
from app.services.llm.openai_client import OpenAIClient

SYSTEM_PROMPT = """
You are an intent extraction engine for a deterministic command execution API.

Return ONLY valid JSON (no markdown).
Schema:
{
  "action": string|null,
  "payload": object|null,
  "confidence": number,
  "error": string|null
}

Supported actions:
- "assign_task" with payload:
  { "asset_id": "<uuid>", "task_id": "<uuid>" }

Rules:
- If missing required fields, set action=null, payload=null, confidence=0, error="missing_fields"
- Never invent ids. Extract only from user text.
""".strip()


class LLMIntentResolver:
    def __init__(self) -> None:
        self.client = OpenAIClient()

    def resolve(self, raw_text: str) -> ResolvedIntent:
        content = self.client.chat(SYSTEM_PROMPT, raw_text)

        try:
            data = json.loads(content)
        except Exception:
            return ResolvedIntent(
                action=None,
                payload=None,
                confidence=0.0,
                provider="openai",
                model=settings.openai_model,
                raw_output=content,
                error="invalid_json_from_llm",
            )

        return ResolvedIntent(
            action=data.get("action"),
            payload=data.get("payload"),
            confidence=float(data.get("confidence") or 0.0),
            provider="openai",
            model=settings.openai_model,
            raw_output=content,
            error=data.get("error"),
        )