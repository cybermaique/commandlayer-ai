from sqlalchemy import select
from app.infra.models import AssignmentModel


class CommandExecutor:
    @staticmethod
    def execute(session, action: str, payload: dict):
        if action == "assign_task":
            asset_id = payload["asset_id"]
            task_id = payload["task_id"]

            # 1) Verifica se já existe (idempotência)
            existing = session.execute(
                select(AssignmentModel).where(
                    AssignmentModel.asset_id == asset_id,
                    AssignmentModel.task_id == task_id,
                )
            ).scalar_one_or_none()

            if existing:
                return {"assignment_id": existing.id, "already_exists": True}

            # 2) Se não existe, cria
            assignment = AssignmentModel(
                asset_id=asset_id,
                task_id=task_id,
            )
            session.add(assignment)

            # flush garante que o ID seja gerado antes do commit
            session.flush()

            return {"assignment_id": assignment.id, "already_exists": False}

        raise ValueError(f"Unsupported action: {action}")
