from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.statistics import AggregationResult, AnomalyStatistics, COPResult
from app.services.statistics_service import StatisticsService

router = APIRouter()


@router.get("/aggregate", response_model=list[AggregationResult])
async def aggregate(
    building_id: str,
    start_time: datetime,
    end_time: datetime,
    period: str = Query("day", pattern="^(hour|day|week|month)$"),
    metrics: str = Query("electricity_kwh", description="Comma-separated"),
    db: AsyncSession = Depends(get_db),
):
    svc = StatisticsService(db)
    return await svc.aggregate_by_period(
        building_id=building_id,
        start_time=start_time,
        end_time=end_time,
        period=period,
        metrics=metrics.split(","),
    )


@router.get("/cop", response_model=list[COPResult])
async def calculate_cop(
    building_id: str,
    start_time: datetime,
    end_time: datetime,
    period: str = Query("day", pattern="^(hour|day|week|month)$"),
    db: AsyncSession = Depends(get_db),
):
    svc = StatisticsService(db)
    return await svc.calculate_cop(
        building_id=building_id,
        start_time=start_time,
        end_time=end_time,
        period=period,
    )


@router.get("/anomaly-summary", response_model=AnomalyStatistics)
async def anomaly_summary(
    start_time: datetime,
    end_time: datetime,
    building_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    svc = StatisticsService(db)
    return await svc.get_anomaly_statistics(
        building_id=building_id,
        start_time=start_time,
        end_time=end_time,
    )
