import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.api.dependencies.auth import enforce_rate_limit
from app.api.schemas.logs import AssetSummary, CommandLogItem, TaskSummary
from app.domain.types.auth import AuthContext
from app.infra.models.asset_model import AssetModel
from app.infra.models.command_log_model import CommandLogModel
from app.infra.models.task_model import TaskModel
from app.infra.session import get_session
from app.infra.settings import settings

router = APIRouter()

ALLOWED_READONLY_ROLES = {"admin", "runner", "readonly"}


def _ensure_readonly_access(auth_context: AuthContext) -> None:
    if settings.auth_mode != "api_key":
        return
    if auth_context.role not in ALLOWED_READONLY_ROLES:
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "forbidden",
                "message": "API key does not have permission for this resource.",
            },
        )


@router.get("/command-logs", response_model=list[CommandLogItem], tags=["logs"])
def list_command_logs(
    limit: int = 50,
    offset: int = 0,
    auth_context: AuthContext = Depends(enforce_rate_limit),
):
    _ensure_readonly_access(auth_context)

    with get_session() as session:
        logs = (
            session.execute(
                select(CommandLogModel)
                .order_by(CommandLogModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            .scalars()
            .all()
        )

    results: list[CommandLogItem] = []
    for log in logs:
        try:
            intent_json = json.loads(log.intent_json)
        except json.JSONDecodeError:
            intent_json = {}

        auth_metadata = {}
        if isinstance(intent_json, dict):
            resolution = intent_json.get("resolution")
            if isinstance(resolution, dict):
                auth_metadata = resolution.get("auth") or {}

        results.append(
            CommandLogItem(
                id=log.id,
                raw_text=log.raw_text,
                status=log.status,
                created_at=log.created_at,
                api_key_id=log.api_key_id,
                intent_json=intent_json if isinstance(intent_json, dict) else {},
                api_key_name=auth_metadata.get("api_key_name"),
                role=auth_metadata.get("role"),
            )
        )

    return results


@router.get("/assets", response_model=list[AssetSummary], tags=["assets"])
def list_assets(
    auth_context: AuthContext = Depends(enforce_rate_limit),
):
    _ensure_readonly_access(auth_context)
    with get_session() as session:
        assets = (
            session.execute(select(AssetModel).order_by(AssetModel.name.asc()))
            .scalars()
            .all()
        )

    return [AssetSummary(id=asset.id, name=asset.name) for asset in assets]


@router.get("/tasks", response_model=list[TaskSummary], tags=["tasks"])
def list_tasks(
    auth_context: AuthContext = Depends(enforce_rate_limit),
):
    _ensure_readonly_access(auth_context)
    with get_session() as session:
        tasks = (
            session.execute(select(TaskModel).order_by(TaskModel.created_at.desc()))
            .scalars()
            .all()
        )

    return [TaskSummary(id=task.id, title=task.title) for task in tasks]
