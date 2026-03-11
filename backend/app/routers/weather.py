from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.weather import WeatherRecordCreate, WeatherRecordResponse, WeatherRecordUpdate
from app.schemas.query import EnergyQueryParams
from app.services.weather_service import WeatherService

router = APIRouter()


@router.get("")
async def query_weather(
    region_id: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    sort_by: str = "timestamp",
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    params = EnergyQueryParams(
        region_id=region_id, start_time=start_time, end_time=end_time,
        page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order,
    )
    svc = WeatherService(db)
    result = await svc.query(params)
    result.items = [WeatherRecordResponse.model_validate(item) for item in result.items]
    return result


@router.get("/{record_id}", response_model=WeatherRecordResponse)
async def get_weather_record(record_id: int, db: AsyncSession = Depends(get_db)):
    svc = WeatherService(db)
    record = await svc.get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Weather record not found")
    return record


@router.post("", response_model=WeatherRecordResponse, status_code=201)
async def create_weather_record(data: WeatherRecordCreate, db: AsyncSession = Depends(get_db)):
    svc = WeatherService(db)
    return await svc.create_record(data)


@router.post("/batch")
async def batch_import_weather(records: list[WeatherRecordCreate], db: AsyncSession = Depends(get_db)):
    svc = WeatherService(db)
    count = await svc.bulk_import(records)
    return {"imported": count}


@router.put("/{record_id}", response_model=WeatherRecordResponse)
async def update_weather_record(record_id: int, data: WeatherRecordUpdate, db: AsyncSession = Depends(get_db)):
    svc = WeatherService(db)
    record = await svc.update_record(record_id, data)
    if not record:
        raise HTTPException(status_code=404, detail="Weather record not found")
    return record


@router.delete("/{record_id}")
async def delete_weather_record(record_id: int, db: AsyncSession = Depends(get_db)):
    svc = WeatherService(db)
    success = await svc.delete_record(record_id)
    if not success:
        raise HTTPException(status_code=404, detail="Weather record not found")
    return {"status": "deleted"}
