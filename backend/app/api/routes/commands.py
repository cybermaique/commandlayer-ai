from fastapi import APIRouter, HTTPException
from app.api.schemas.command import CommandRequest
from app.services.command_service import CommandService

router = APIRouter(prefix="/commands", tags=["commands"])

@router.post("")
def execute_command(command: CommandRequest):
    service = CommandService()
    try:
        return service.execute(command)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
