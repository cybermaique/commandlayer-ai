from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Assignment:
    id: str
    asset_id: str
    task_id: str
    assigned_at: Optional[datetime] = None
