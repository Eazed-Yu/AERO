from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.region import RegionCreate, RegionResponse, RegionUpdate
from app.services.region_service import RegionService

router = APIRouter()


@router.get("", response_model=list[RegionResponse])
async def list_regions(db: AsyncSession = Depends(get_db)):
    svc = RegionService(db)
    return await svc.list_regions()


@router.get("/{region_id}", response_model=RegionResponse)
async def get_region(region_id: str, db: AsyncSession = Depends(get_db)):
    svc = RegionService(db)
    region = await svc.get_region(region_id)
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    return region


@router.post("", response_model=RegionResponse, status_code=201)
async def create_region(data: RegionCreate, db: AsyncSession = Depends(get_db)):
    svc = RegionService(db)
    try:
        return await svc.create_region(data)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="创建区域失败，请重试")


@router.put("/{region_id}", response_model=RegionResponse)
async def update_region(
    region_id: str, data: RegionUpdate, db: AsyncSession = Depends(get_db)
):
    svc = RegionService(db)
    region = await svc.update_region(region_id, data)
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    return region


@router.delete("/{region_id}")
async def delete_region(region_id: str, db: AsyncSession = Depends(get_db)):
    svc = RegionService(db)
    success = await svc.delete_region(region_id)
    if not success:
        raise HTTPException(status_code=404, detail="Region not found")
    return {"status": "deleted"}
