from pydantic import BaseModel
from typing import Dict, Any, Optional


class CommandRequest(BaseModel):
    action: str
    payload: Dict[str, Any]
    requested_by: str
    raw_text: Optional[str] = None
