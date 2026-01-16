from typing import Any, Dict, Optional
from pydantic import BaseModel


class CommandRequest(BaseModel):
    action: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    requested_by: str
    raw_text: Optional[str] = None
