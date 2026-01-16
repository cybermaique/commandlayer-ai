from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.api.schemas.command import CommandRequest
from app.services.command_service import CommandService
from app.services.intent_resolver import IntentResolutionError

router = APIRouter(prefix="/commands", tags=["commands"])


@router.post("")
def execute_command(command: CommandRequest):
    service = CommandService()
    try:
        return service.execute(command)
    except IntentResolutionError as exc:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error_code": "intent_resolution_failed",
                "errors": exc.errors,
                "raw_text": exc.raw_text,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))