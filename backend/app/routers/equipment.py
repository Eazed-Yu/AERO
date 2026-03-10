from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.equipment import EquipmentCreate, EquipmentResponse, EquipmentUpdate
from app.services.equipment_service import EquipmentService

router = APIRouter()


@router.get("", response_model=list[EquipmentResponse])
async def list_equipment(
    building_id: str | None = None,
    device_type: str | None = None,
    system_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    svc = EquipmentService(db)
    return await svc.list_equipment(
        building_id=building_id, device_type=device_type, system_type=system_type,
    )


@router.post("", response_model=EquipmentResponse, status_code=201)
async def create_equipment(data: EquipmentCreate, db: AsyncSession = Depends(get_db)):
    svc = EquipmentService(db)
    return await svc.create_equipment(data)


@router.get("/{device_id}", response_model=EquipmentResponse)
async def get_equipment(device_id: str, db: AsyncSession = Depends(get_db)):
    svc = EquipmentService(db)
    equipment = await svc.get_equipment(device_id)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return equipment


@router.put("/{device_id}", response_model=EquipmentResponse)
async def update_equipment(device_id: str, data: EquipmentUpdate, db: AsyncSession = Depends(get_db)):
    svc = EquipmentService(db)
    equipment = await svc.update_equipment(device_id, data)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return equipment


@router.delete("/{device_id}")
async def delete_equipment(device_id: str, db: AsyncSession = Depends(get_db)):
    svc = EquipmentService(db)
    success = await svc.delete_equipment(device_id)
    if not success:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return {"status": "deleted"}
