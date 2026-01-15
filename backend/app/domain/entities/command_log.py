from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class CommandLog:
    id: str
    raw_text: str
    intent_json: str
    status: str
    created_at: Optional[datetime] = None
