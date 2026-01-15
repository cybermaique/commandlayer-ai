from datetime import datetime
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.models.base import Base


class CommandLogModel(Base):
    __tablename__ = "command_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    intent_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
