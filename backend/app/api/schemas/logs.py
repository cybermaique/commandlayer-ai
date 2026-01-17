from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class CommandLogItem(BaseModel):
    id: str
    raw_text: str
    status: str
    created_at: datetime
    api_key_id: Optional[str] = None
    intent_json: dict[str, Any]
    api_key_name: Optional[str] = None
    role: Optional[str] = None


class AssetSummary(BaseModel):
    id: str
    name: str


class TaskSummary(BaseModel):
    id: str
    title: str
