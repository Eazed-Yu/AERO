from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.energy import EnergyRecordResponse
from app.schemas.query import EnergyQueryParams, PaginatedResponse
from app.services.energy_service import EnergyService

router = APIRouter()


@router.get("")
async def query_energy(
    building_id: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    metrics: str | None = Query(None, description="Comma-separated metrics"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    sort_by: str = "timestamp",
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    params = EnergyQueryParams(
        building_id=building_id,
        start_time=start_time,
        end_time=end_time,
        metrics=metrics.split(",") if metrics else None,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    svc = EnergyService(db)
    result = await svc.query(params)
    # Serialize items
    result.items = [
        EnergyRecordResponse.model_validate(item) for item in result.items
    ]
    return result
