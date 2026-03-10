from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.equipment import (
    EquipmentCreate,
    EquipmentResponse,
    EquipmentStatusCreate,
    EquipmentStatusResponse,
    EquipmentStatusUpdate,
    EquipmentUpdate,
)
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


@router.post("", response_model=EquipmentResponse, status_code=201)
async def create_equipment(
    data: EquipmentCreate,
    db: AsyncSession = Depends(get_db),
):
    svc = EquipmentService(db)
    return await svc.create_equipment(data)


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


@router.put("/{device_id}", response_model=EquipmentResponse)
async def update_equipment(
    device_id: str,
    data: EquipmentUpdate,
    db: AsyncSession = Depends(get_db),
):
    svc = EquipmentService(db)
    equipment = await svc.update_equipment(device_id, data)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return equipment


@router.delete("/{device_id}")
async def delete_equipment(
    device_id: str,
    db: AsyncSession = Depends(get_db),
):
    svc = EquipmentService(db)
    success = await svc.delete_equipment(device_id)
    if not success:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return {"status": "deleted"}


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


@router.post(
    "/status",
    response_model=EquipmentStatusResponse,
    status_code=201,
)
async def create_status(
    data: EquipmentStatusCreate,
    db: AsyncSession = Depends(get_db),
):
    svc = EquipmentService(db)
    return await svc.create_status(data)


@router.get("/status/{status_id}", response_model=EquipmentStatusResponse)
async def get_status(
    status_id: int,
    db: AsyncSession = Depends(get_db),
):
    svc = EquipmentService(db)
    status = await svc.get_status(status_id)
    if not status:
        raise HTTPException(status_code=404, detail="Status not found")
    return status


@router.put("/status/{status_id}", response_model=EquipmentStatusResponse)
async def update_status(
    status_id: int,
    data: EquipmentStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    svc = EquipmentService(db)
    status = await svc.update_status(status_id, data)
    if not status:
        raise HTTPException(status_code=404, detail="Status not found")
    return status


@router.delete("/status/{status_id}")
async def delete_status(
    status_id: int,
    db: AsyncSession = Depends(get_db),
):
    svc = EquipmentService(db)
    success = await svc.delete_status(status_id)
    if not success:
        raise HTTPException(status_code=404, detail="Status not found")
    return {"status": "deleted"}
