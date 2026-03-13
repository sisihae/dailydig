from datetime import datetime

from sqlalchemy import Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.db import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, default=1)
    track_id: Mapped[int] = mapped_column(Integer, ForeignKey("tracks.id"))

    feedback_type: Mapped[str] = mapped_column(String(20))  # "like" | "dislike" | "skip"

    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
