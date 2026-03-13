from datetime import datetime

from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.db import Base


class DigQueue(Base):
    __tablename__ = "dig_queue"

    id: Mapped[int] = mapped_column(primary_key=True)
    track_id: Mapped[int] = mapped_column(Integer, ForeignKey("tracks.id"))
    user_id: Mapped[int] = mapped_column(Integer, default=1)

    source: Mapped[str] = mapped_column(String(50))  # "playlist_import" | "auto_fetch"
    status: Mapped[str] = mapped_column(String(20), default="pending")  # "pending" | "delivered"
    playlist_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    added_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
