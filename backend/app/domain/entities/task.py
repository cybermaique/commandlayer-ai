from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.types.enums import TaskStatus


@dataclass(frozen=True)
class Task:
    id: str
    title: str
    scheduled_for: datetime
    status: TaskStatus = TaskStatus.SCHEDULED
    created_at: Optional[datetime] = None
