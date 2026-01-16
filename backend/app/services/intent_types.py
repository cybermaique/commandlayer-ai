from dataclasses import dataclass
from typing import Any, Dict, Optional

from app.services.rag.retriever import RagContext


@dataclass(frozen=True)
class ResolvedIntent:
    action: Optional[str]
    payload: Optional[Dict[str, Any]]
    confidence: float
    provider: str
    model: str
    raw_output: Optional[str] = None
    error: Optional[str] = None


@dataclass(frozen=True)
class ResolvedIntentResult:
    intent: ResolvedIntent
    rag: RagContext
