from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.energy import EnergyRecordResponse
from app.services.energy_service import EnergyService
from app.services.export_service import ExportService

router = APIRouter()


@router.post("/csv")
async def export_csv(
    building_id: str,
    start_time: datetime,
    end_time: datetime,
    db: AsyncSession = Depends(get_db),
):
    svc = EnergyService(db)
    records = await svc.get_records(building_id, start_time, end_time)

    columns = [
        "building_id", "timestamp", "electricity_kwh", "water_m3",
        "gas_m3", "hvac_kwh", "hvac_supply_temp", "hvac_return_temp",
        "outdoor_temp", "outdoor_humidity",
    ]
    data = [
        {k: getattr(r, k, None) for k in columns} for r in records
    ]
    # Convert datetime for serialization
    for row in data:
        if row.get("timestamp"):
            row["timestamp"] = row["timestamp"].isoformat()

    export_svc = ExportService()
    return await export_svc.export_csv(
        data=data,
        columns=columns,
        filename=f"energy_{building_id}_{start_time.date()}_{end_time.date()}.csv",
    )


@router.post("/excel")
async def export_excel(
    building_id: str,
    start_time: datetime,
    end_time: datetime,
    db: AsyncSession = Depends(get_db),
):
    svc = EnergyService(db)
    records = await svc.get_records(building_id, start_time, end_time)

    columns = [
        "building_id", "timestamp", "electricity_kwh", "water_m3",
        "gas_m3", "hvac_kwh", "hvac_supply_temp", "hvac_return_temp",
        "outdoor_temp", "outdoor_humidity",
    ]
    data = [
        {k: getattr(r, k, None) for k in columns} for r in records
    ]

    export_svc = ExportService()
    return await export_svc.export_excel(
        data=data,
        columns=columns,
        sheet_name="能耗数据",
        filename=f"energy_{building_id}_{start_time.date()}_{end_time.date()}.xlsx",
    )
