from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.anomaly import AnomalyDetectRequest, AnomalyEventResponse
from app.services.anomaly_service import AnomalyService

router = APIRouter()


@router.get("", response_model=list[AnomalyEventResponse])
async def list_anomalies(
    building_id: str | None = None,
    severity: str | None = None,
    resolved: bool | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    svc = AnomalyService(db)
    return await svc.list_anomalies(
        building_id=building_id,
        severity=severity,
        resolved=resolved,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )


@router.post("/detect", response_model=list[AnomalyEventResponse])
async def detect_anomalies(
    data: AnomalyDetectRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = AnomalyService(db)
    return await svc.detect_anomalies(
        building_id=data.building_id,
        start_time=data.start_time,
        end_time=data.end_time,
    )


@router.patch("/{anomaly_id}/resolve")
async def resolve_anomaly(
    anomaly_id: str,
    db: AsyncSession = Depends(get_db),
):
    svc = AnomalyService(db)
    success = await svc.resolve_anomaly(anomaly_id)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Anomaly not found")
    return {"status": "resolved"}
