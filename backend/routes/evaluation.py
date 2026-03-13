from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_session
from backend.evaluation.metrics import MetricsCalculator

router = APIRouter(tags=["evaluation"])


@router.get("/evaluation/metrics")
async def get_metrics(
    days: int = 30,
    session: AsyncSession = Depends(get_session),
):
    """
    Get evaluation metrics for the specified period.

    Query params:
    - days: rolling window size (default 30)
    """
    calculator = MetricsCalculator()
    return await calculator.calculate_metrics(session, days=days)
