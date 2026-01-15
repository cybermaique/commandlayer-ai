from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.types.enums import AssetType


@dataclass(frozen=True)
class Asset:
    id: str
    type: AssetType
    name: str
    active: bool = True
    created_at: Optional[datetime] = None
