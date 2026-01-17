import json

import httpx
from fastapi import HTTPException

from app.api.schemas.command import CommandRequest
from app.infra.models.command_log_model import CommandLogModel
from app.infra.session import get_session
from app.infra.settings import settings
from app.services.command_executor import CommandExecutor
from app.services.command_validator import CommandValidator
from app.services.intent_resolver import IntentResolver


class CommandService:
    def execute(self, command: CommandRequest):
        try:
            CommandValidator.validate_request(command)
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "invalid_request",
                    "message": str(exc),
                },
            ) from exc

        action = command.action
        payload = command.payload or {}
        used_raw_text = False
        resolution = None
        rag = None

        if not action and command.raw_text:
            try:
                resolution_result = IntentResolver.resolve(
                    raw_text=command.raw_text,
                    fallback_payload=payload,
                )
                resolution = resolution_result.intent
                rag = resolution_result.rag
                used_raw_text = True

                # IMPORTANT: apply resolved intent to the execution variables
                action = resolution.action
                payload = resolution.payload or {}

                # Friendly, deterministic error for the most common LLM failure mode
                if resolution.error == "missing_fields":
                    raise HTTPException(
                        status_code=422,
                        detail={
                            "error_code": "missing_fields",
                            "message": (
                                "Unable to resolve asset_id and task_id. "
                                "Enable RAG or provide explicit IDs."
                            ),
                            "rag": {
                                "enabled": rag.enabled if rag else False,
                                "sources": rag.sources if rag else [],
                            },
                        },
                    )

            except RuntimeError as exc:
                if "OPENAI_API_KEY" in str(exc):
                    raise HTTPException(
                        status_code=503,
                        detail={
                            "error_code": "provider_unavailable",
                            "message": str(exc),
                        },
                    ) from exc

                raise HTTPException(
                    status_code=503,
                    detail={
                        "error_code": "provider_error",
                        "message": str(exc),
                    },
                ) from exc

            except httpx.TimeoutException as exc:
                raise HTTPException(
                    status_code=504,
                    detail={
                        "error_code": "provider_timeout",
                        "message": "LLM provider timeout",
                    },
                ) from exc

            except httpx.HTTPStatusError as exc:
                raise HTTPException(
                    status_code=503,
                    detail={
                        "error_code": "provider_http_error",
                        "message": str(exc),
                    },
                ) from exc

        try:
            action, payload = CommandValidator.validate_action_and_payload(
                action=action,
                payload=payload,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "invalid_payload",
                    "message": str(exc),
                },
            ) from exc

        with get_session() as session:
            result = CommandExecutor.execute(
                session=session,
                action=action,
                payload=payload,
            )

            status = "noop" if result.get("already_exists") else "success"

            resolution_metadata = {
                "mode": settings.intent_resolution_mode if used_raw_text else "direct",
                "provider": resolution.provider if resolution else "direct",
                "model": resolution.model if resolution else "direct",
                "confidence": resolution.confidence if resolution else 1.0,
            }

            if resolution and resolution.raw_output:
                resolution_metadata["raw_output"] = resolution.raw_output

            if used_raw_text and rag:
                rag_metadata = {
                    "enabled": rag.enabled,
                    "sources": rag.sources,
                    "context_chars": len(rag.context_text),
                }
                if rag.mode:
                    rag_metadata["mode"] = rag.mode
                if rag.top_k is not None:
                    rag_metadata["top_k"] = rag.top_k
                if rag.retrieved_chunks is not None:
                    rag_metadata["retrieved_chunks"] = rag.retrieved_chunks
                resolution_metadata["rag"] = rag_metadata

            log = CommandLogModel(
                raw_text=command.raw_text if used_raw_text else action,
                intent_json=json.dumps(
                    {
                        "action": action,
                        "payload": payload,
                        "resolution": resolution_metadata,
                    },
                    ensure_ascii=False,
                ),
                status=status,
            )

            session.add(log)
            session.commit()

        return {
            "status": status,
            "action": action,
            "result": result,
        }
