from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

class CommandRequest(BaseModel):
    action: Optional[str] = None
    payload: Optional[Dict[str, Any]] = Field(default_factory=dict)
    requested_by: str
    raw_text: Optional[str] = None