import json

from app.api.schemas.command import CommandRequest
from app.infra.models.command_log_model import CommandLogModel
from app.infra.session import get_session
from app.services.command_executor import CommandExecutor
from app.services.command_validator import CommandValidator
from app.services.intent_resolver import IntentResolutionError, IntentResolver


class CommandService:
    def execute(self, command: CommandRequest):
        CommandValidator.validate(command)

        action = command.action
        payload = command.payload or {}
        confidence = 1.0
        used_raw_text = False

        if not action and command.raw_text:
            resolution = IntentResolver.resolve(
                raw_text=command.raw_text,
                fallback_payload=payload,
                requested_by=command.requested_by,
            )

            if resolution.intent == "unknown":
                raise IntentResolutionError(command.raw_text, resolution.errors)

            action = resolution.intent
            payload = resolution.payload
            confidence = resolution.confidence
            used_raw_text = True

        with get_session() as session:
            result = CommandExecutor.execute(
                session=session,
                action=action,
                payload=payload,
            )

            status = "noop" if result.get("already_exists") else "success"

            log = CommandLogModel(
                raw_text=command.raw_text if used_raw_text else action,
                intent_json=json.dumps(
                    {
                        "action": action,
                        "payload": payload,
                        "confidence": confidence,
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