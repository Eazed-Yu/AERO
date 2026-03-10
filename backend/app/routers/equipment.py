from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.equipment import EquipmentResponse, EquipmentStatusResponse
from app.services.equipment_service import EquipmentService

router = APIRouter()


@router.get("", response_model=list[EquipmentResponse])
async def list_equipment(
    building_id: str | None = None,
    device_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    svc = EquipmentService(db)
    return await svc.list_equipment(
        building_id=building_id, device_type=device_type
    )


@router.get("/{device_id}")
async def get_equipment(
    device_id: str,
    db: AsyncSession = Depends(get_db),
):
    svc = EquipmentService(db)
    equipment = await svc.get_equipment(device_id)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    latest_status = await svc.get_latest_status(device_id)
    return {
        "equipment": EquipmentResponse.model_validate(equipment),
        "latest_status": (
            EquipmentStatusResponse.model_validate(latest_status)
            if latest_status
            else None
        ),
    }


@router.get(
    "/{device_id}/status-history",
    response_model=list[EquipmentStatusResponse],
)
async def get_status_history(
    device_id: str,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    svc = EquipmentService(db)
    return await svc.get_status_history(
        device_id=device_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )
