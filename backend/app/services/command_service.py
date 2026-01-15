import json
from app.api.schemas.command import CommandRequest
from app.services.command_validator import CommandValidator
from app.services.command_executor import CommandExecutor
from app.infra.session import get_session
from app.infra.models.command_log_model import CommandLogModel


class CommandService:
    def execute(self, command: CommandRequest):
        CommandValidator.validate(command)

        with get_session() as session:
            result = CommandExecutor.execute(
                session=session,
                action=command.action,
                payload=command.payload,
            )

            # status mais “real”
            status = "noop" if result.get("already_exists") else "success"

            log = CommandLogModel(
                raw_text=command.raw_text or "",  # futuro chat entra aqui
                intent_json=json.dumps(
                    {
                        "action": command.action,
                        "payload": command.payload,
                        "requested_by": command.requested_by,
                    },
                    ensure_ascii=False,
                ),
                status=status,
            )

            session.add(log)
            session.commit()

        return {
            "status": status,
            "action": command.action,
            "result": result,
        }
