from fastapi import APIRouter

from app.api.schemas.command import CommandRequest
from app.services.command_service import CommandService

router = APIRouter(prefix="/commands", tags=["commands"])


@router.post("")
def execute_command(command: CommandRequest):
    service = CommandService()
    return service.execute(command)
