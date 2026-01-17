import json

import httpx
from fastapi import HTTPException

from app.api.schemas.command import CommandRequest
from app.domain.types.auth import AuthContext
from app.infra.models.command_log_model import CommandLogModel
from app.infra.session import get_session
from app.infra.settings import settings
from app.services.command_executor import CommandExecutor
from app.services.command_validator import CommandValidator
from app.services.intent_resolver import IntentResolver


class CommandService:
    def execute(
        self,
        command: CommandRequest,
        auth_context: AuthContext | None = None,
    ):
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

        if settings.auth_mode == "api_key" and not auth_context:
            raise HTTPException(
                status_code=401,
                detail={
                    "error_code": "unauthorized",
                    "message": "Missing or invalid API key.",
                },
            )

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
                            "message": "Some required fields are missing in the request.",
                            "missing_fields": resolution.missing_fields,
                        },
                    )

            except httpx.TimeoutException as exc:
                raise HTTPException(
                    status_code=504,
                    detail={
                        "error_code": "provider_timeout",
                        "message": str(exc),
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

        if (
            settings.auth_mode == "api_key"
            and action == "assign_task"
            and auth_context
            and auth_context.role not in {"admin", "runner"}
        ):
            raise HTTPException(
                status_code=403,
                detail={
                    "error_code": "forbidden",
                    "message": "API key does not have permission for this action.",
                },
            )

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

            if settings.auth_mode == "api_key" and auth_context:
                resolution_metadata["auth"] = {
                    "mode": "api_key",
                    "api_key_name": auth_context.name,
                    "role": auth_context.role,
                }

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
                api_key_id=auth_context.api_key_id if auth_context else None,
            )

            session.add(log)
            session.commit()

        return {
            "status": status,
            "action": action,
            "result": result,
        }
