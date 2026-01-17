from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AuthContext:
    mode: str
    api_key_id: Optional[str]
    name: Optional[str]
    role: Optional[str]
    rate_limit_key: str
