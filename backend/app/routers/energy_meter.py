from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.energy_meter import EnergyMeterCreate, EnergyMeterResponse, EnergyMeterUpdate
from app.schemas.query import EnergyQueryParams
from app.services.energy_meter_service import EnergyMeterService

router = APIRouter()


@router.get("")
async def query_energy_meters(
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
        building_id=building_id, start_time=start_time, end_time=end_time,
        metrics=metrics.split(",") if metrics else None,
        page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order,
    )
    svc = EnergyMeterService(db)
    result = await svc.query(params)
    result.items = [EnergyMeterResponse.model_validate(item) for item in result.items]
    return result


@router.get("/{record_id}", response_model=EnergyMeterResponse)
async def get_energy_meter(record_id: int, db: AsyncSession = Depends(get_db)):
    svc = EnergyMeterService(db)
    record = await svc.get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Energy meter record not found")
    return record


@router.post("", response_model=EnergyMeterResponse, status_code=201)
async def create_energy_meter(data: EnergyMeterCreate, db: AsyncSession = Depends(get_db)):
    svc = EnergyMeterService(db)
    return await svc.create_record(data)


@router.post("/batch")
async def batch_import_energy(records: list[EnergyMeterCreate], db: AsyncSession = Depends(get_db)):
    svc = EnergyMeterService(db)
    result = await svc.bulk_import(records)
    return result


@router.put("/{record_id}", response_model=EnergyMeterResponse)
async def update_energy_meter(record_id: int, data: EnergyMeterUpdate, db: AsyncSession = Depends(get_db)):
    svc = EnergyMeterService(db)
    record = await svc.update_record(record_id, data)
    if not record:
        raise HTTPException(status_code=404, detail="Energy meter record not found")
    return record


@router.delete("/{record_id}")
async def delete_energy_meter(record_id: int, db: AsyncSession = Depends(get_db)):
    svc = EnergyMeterService(db)
    success = await svc.delete_record(record_id)
    if not success:
        raise HTTPException(status_code=404, detail="Energy meter record not found")
    return {"status": "deleted"}
