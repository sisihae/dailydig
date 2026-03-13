from datetime import datetime

from sqlalchemy import Integer, Float, String, DateTime, func, JSON
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.db import Base


class TasteProfile(Base):
    __tablename__ = "taste_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, default=1)

    genre_preferences: Mapped[dict] = mapped_column(JSON, default=dict)
    energy_preference: Mapped[float] = mapped_column(Float, default=0.5)
    era_preference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    favorite_artists: Mapped[list] = mapped_column(JSON, default=list)
    recent_likes: Mapped[list] = mapped_column(JSON, default=list)
    recent_dislikes: Mapped[list] = mapped_column(JSON, default=list)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
