from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.statistics import (
    AggregationResult,
    AnomalyStatistics,
    COPResult,
    EUIResult,
    PlantEfficiencyResult,
)
from app.services.statistics_service import StatisticsService

router = APIRouter()


@router.get("/aggregate", response_model=list[AggregationResult])
async def aggregate(
    building_id: str,
    start_time: datetime,
    end_time: datetime,
    period: str = Query("day", pattern="^(hour|day|week|month)$"),
    metrics: str = Query("total_electricity_kwh", description="Comma-separated"),
    db: AsyncSession = Depends(get_db),
):
    svc = StatisticsService(db)
    return await svc.aggregate_by_period(
        building_id=building_id, start_time=start_time, end_time=end_time,
        period=period, metrics=metrics.split(","),
    )


@router.get("/cop", response_model=list[COPResult])
async def calculate_cop(
    start_time: datetime,
    end_time: datetime,
    device_id: str | None = None,
    building_id: str | None = None,
    period: str = Query("day", pattern="^(hour|day|week|month)$"),
    db: AsyncSession = Depends(get_db),
):
    svc = StatisticsService(db)
    return await svc.calculate_cop(
        start_time=start_time, end_time=end_time,
        device_id=device_id, building_id=building_id, period=period,
    )


@router.get("/eui", response_model=EUIResult)
async def calculate_eui(
    building_id: str,
    start_time: datetime,
    end_time: datetime,
    db: AsyncSession = Depends(get_db),
):
    svc = StatisticsService(db)
    result = await svc.calculate_eui(building_id, start_time, end_time)
    if not result:
        return {"error": "Building not found"}
    return result


@router.get("/plant-efficiency", response_model=list[PlantEfficiencyResult])
async def plant_efficiency(
    start_time: datetime,
    end_time: datetime,
    period: str = Query("day", pattern="^(hour|day|week|month)$"),
    db: AsyncSession = Depends(get_db),
):
    svc = StatisticsService(db)
    return await svc.plant_efficiency(start_time, end_time, period)


@router.get("/anomaly-summary", response_model=AnomalyStatistics)
async def anomaly_summary(
    start_time: datetime,
    end_time: datetime,
    building_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    svc = StatisticsService(db)
    return await svc.get_anomaly_statistics(building_id, start_time, end_time)
