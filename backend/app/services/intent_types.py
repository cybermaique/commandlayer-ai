from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ResolvedIntent:
    action: Optional[str]
    payload: Optional[Dict[str, Any]]
    confidence: float
    provider: str
    model: str
    raw_output: Optional[str] = None
    error: Optional[str] = None