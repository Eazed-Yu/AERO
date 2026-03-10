from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.building import BuildingCreate, BuildingResponse, BuildingUpdate
from app.services.building_service import BuildingService

router = APIRouter()


@router.get("", response_model=list[BuildingResponse])
async def list_buildings(
    building_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    svc = BuildingService(db)
    return await svc.list_buildings(building_type=building_type)


@router.get("/{building_id}", response_model=BuildingResponse)
async def get_building(
    building_id: str,
    db: AsyncSession = Depends(get_db),
):
    svc = BuildingService(db)
    building = await svc.get_building(building_id)
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    return building


@router.post("", response_model=BuildingResponse, status_code=201)
async def create_building(
    data: BuildingCreate,
    db: AsyncSession = Depends(get_db),
):
    svc = BuildingService(db)
    return await svc.create_building(data)


@router.put("/{building_id}", response_model=BuildingResponse)
async def update_building(
    building_id: str,
    data: BuildingUpdate,
    db: AsyncSession = Depends(get_db),
):
    svc = BuildingService(db)
    building = await svc.update_building(building_id, data)
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    return building


@router.delete("/{building_id}")
async def delete_building(
    building_id: str,
    db: AsyncSession = Depends(get_db),
):
    svc = BuildingService(db)
    success = await svc.delete_building(building_id)
    if not success:
        raise HTTPException(status_code=404, detail="Building not found")
    return {"status": "deleted"}
