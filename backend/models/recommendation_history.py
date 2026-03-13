from datetime import datetime

from sqlalchemy import Integer, Float, String, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.db import Base


class RecommendationHistory(Base):
    __tablename__ = "recommendation_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, default=1)
    track_id: Mapped[int] = mapped_column(Integer, ForeignKey("tracks.id"))

    source: Mapped[str] = mapped_column(String(50))  # "queue" | "auto_discovery"
    explanation: Mapped[str] = mapped_column(Text)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    recommended_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
