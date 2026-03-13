from datetime import date

from sqlalchemy import Integer, Float, Date
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.db import Base


class EvaluationMetrics(Base):
    __tablename__ = "evaluation_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_date: Mapped[date] = mapped_column(Date, unique=True)

    # Engagement
    total_recommendations: Mapped[int] = mapped_column(Integer, default=0)
    like_rate: Mapped[float] = mapped_column(Float, default=0.0)
    dislike_rate: Mapped[float] = mapped_column(Float, default=0.0)
    skip_rate: Mapped[float] = mapped_column(Float, default=0.0)

    # Discovery quality
    new_artist_rate: Mapped[float] = mapped_column(Float, default=0.0)
    genre_diversity: Mapped[float] = mapped_column(Float, default=0.0)
