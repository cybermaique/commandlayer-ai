from fastapi import APIRouter, Depends

from app.api.schemas.command import CommandRequest
from app.api.dependencies.auth import enforce_rate_limit
from app.domain.types.auth import AuthContext
from app.services.command_service import CommandService

router = APIRouter(prefix="/commands", tags=["commands"])


@router.post("")
def execute_command(
    command: CommandRequest,
    auth_context: AuthContext = Depends(enforce_rate_limit),
):
    service = CommandService()
    return service.execute(command, auth_context)
