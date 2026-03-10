from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.ahu import AHURecordCreate, AHURecordResponse, AHURecordUpdate
from app.schemas.boiler import BoilerRecordCreate, BoilerRecordResponse, BoilerRecordUpdate
from app.schemas.chiller import ChillerRecordCreate, ChillerRecordResponse, ChillerRecordUpdate
from app.schemas.cooling_tower import CoolingTowerRecordCreate, CoolingTowerRecordResponse, CoolingTowerRecordUpdate
from app.schemas.pump import PumpRecordCreate, PumpRecordResponse, PumpRecordUpdate
from app.schemas.query import HVACDataQueryParams
from app.schemas.vav import VAVRecordCreate, VAVRecordResponse, VAVRecordUpdate
from app.services.hvac_data_service import HVACDataService

router = APIRouter()

# Schema mappings
RESPONSE_MAP = {
    "chiller": ChillerRecordResponse,
    "ahu": AHURecordResponse,
    "boiler": BoilerRecordResponse,
    "vav": VAVRecordResponse,
    "pump": PumpRecordResponse,
    "chw_pump": PumpRecordResponse,
    "cw_pump": PumpRecordResponse,
    "hw_pump": PumpRecordResponse,
    "cooling_tower": CoolingTowerRecordResponse,
}

CREATE_MAP: dict[str, type] = {
    "chiller": ChillerRecordCreate,
    "ahu": AHURecordCreate,
    "boiler": BoilerRecordCreate,
    "vav": VAVRecordCreate,
    "pump": PumpRecordCreate,
    "chw_pump": PumpRecordCreate,
    "cw_pump": PumpRecordCreate,
    "hw_pump": PumpRecordCreate,
    "cooling_tower": CoolingTowerRecordCreate,
}


def _get_response_schema(eq_type: str):
    schema = RESPONSE_MAP.get(eq_type)
    if not schema:
        raise HTTPException(400, f"Unknown equipment type: {eq_type}")
    return schema


# --- Overview ---
@router.get("/overview")
async def hvac_overview(db: AsyncSession = Depends(get_db)):
    svc = HVACDataService(db)
    overview = await svc.get_overview()
    result: dict[str, list] = {}
    for eq_type, records in overview.items():
        schema = RESPONSE_MAP.get(eq_type)
        if schema:
            result[eq_type] = [schema.model_validate(r) for r in records]
        else:
            result[eq_type] = []
    return result


# --- Generic HVAC endpoints ---
def _build_query_params(
    device_id: str | None, start_time, end_time, running_status, page, page_size, sort_by, sort_order
) -> HVACDataQueryParams:
    return HVACDataQueryParams(
        device_id=device_id, start_time=start_time, end_time=end_time,
        running_status=running_status, page=page, page_size=page_size,
        sort_by=sort_by, sort_order=sort_order,
    )


# ---- Chillers ----
@router.get("/chillers/{device_id}/records")
async def query_chiller_records(
    device_id: str,
    start_time: datetime | None = None, end_time: datetime | None = None,
    running_status: str | None = None,
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=1000),
    sort_by: str = "timestamp", sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    params = _build_query_params(device_id, start_time, end_time, running_status, page, page_size, sort_by, sort_order)
    svc = HVACDataService(db)
    result = await svc.query_records("chiller", params)
    result.items = [ChillerRecordResponse.model_validate(i) for i in result.items]
    return result


@router.post("/chillers/{device_id}/records", status_code=201)
async def create_chiller_record(device_id: str, data: ChillerRecordCreate, db: AsyncSession = Depends(get_db)):
    svc = HVACDataService(db)
    record = await svc.create_record("chiller", {**data.model_dump(), "device_id": device_id})
    return ChillerRecordResponse.model_validate(record)


@router.put("/chillers/records/{record_id}")
async def update_chiller_record(record_id: int, data: ChillerRecordUpdate, db: AsyncSession = Depends(get_db)):
    svc = HVACDataService(db)
    record = await svc.update_record("chiller", record_id, data.model_dump(exclude_unset=True))
    if not record:
        raise HTTPException(404, "Record not found")
    return ChillerRecordResponse.model_validate(record)


@router.delete("/chillers/records/{record_id}")
async def delete_chiller_record(record_id: int, db: AsyncSession = Depends(get_db)):
    svc = HVACDataService(db)
    if not await svc.delete_record("chiller", record_id):
        raise HTTPException(404, "Record not found")
    return {"status": "deleted"}


# ---- AHUs ----
@router.get("/ahus/{device_id}/records")
async def query_ahu_records(
    device_id: str,
    start_time: datetime | None = None, end_time: datetime | None = None,
    running_status: str | None = None,
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=1000),
    sort_by: str = "timestamp", sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    params = _build_query_params(device_id, start_time, end_time, running_status, page, page_size, sort_by, sort_order)
    svc = HVACDataService(db)
    result = await svc.query_records("ahu", params)
    result.items = [AHURecordResponse.model_validate(i) for i in result.items]
    return result


@router.post("/ahus/{device_id}/records", status_code=201)
async def create_ahu_record(device_id: str, data: AHURecordCreate, db: AsyncSession = Depends(get_db)):
    svc = HVACDataService(db)
    record = await svc.create_record("ahu", {**data.model_dump(), "device_id": device_id})
    return AHURecordResponse.model_validate(record)


@router.put("/ahus/records/{record_id}")
async def update_ahu_record(record_id: int, data: AHURecordUpdate, db: AsyncSession = Depends(get_db)):
    svc = HVACDataService(db)
    record = await svc.update_record("ahu", record_id, data.model_dump(exclude_unset=True))
    if not record:
        raise HTTPException(404, "Record not found")
    return AHURecordResponse.model_validate(record)


@router.delete("/ahus/records/{record_id}")
async def delete_ahu_record(record_id: int, db: AsyncSession = Depends(get_db)):
    svc = HVACDataService(db)
    if not await svc.delete_record("ahu", record_id):
        raise HTTPException(404, "Record not found")
    return {"status": "deleted"}


# ---- Boilers ----
@router.get("/boilers/{device_id}/records")
async def query_boiler_records(
    device_id: str,
    start_time: datetime | None = None, end_time: datetime | None = None,
    running_status: str | None = None,
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=1000),
    sort_by: str = "timestamp", sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    params = _build_query_params(device_id, start_time, end_time, running_status, page, page_size, sort_by, sort_order)
    svc = HVACDataService(db)
    result = await svc.query_records("boiler", params)
    result.items = [BoilerRecordResponse.model_validate(i) for i in result.items]
    return result


@router.post("/boilers/{device_id}/records", status_code=201)
async def create_boiler_record(device_id: str, data: BoilerRecordCreate, db: AsyncSession = Depends(get_db)):
    svc = HVACDataService(db)
    record = await svc.create_record("boiler", {**data.model_dump(), "device_id": device_id})
    return BoilerRecordResponse.model_validate(record)


@router.put("/boilers/records/{record_id}")
async def update_boiler_record(record_id: int, data: BoilerRecordUpdate, db: AsyncSession = Depends(get_db)):
    svc = HVACDataService(db)
    record = await svc.update_record("boiler", record_id, data.model_dump(exclude_unset=True))
    if not record:
        raise HTTPException(404, "Record not found")
    return BoilerRecordResponse.model_validate(record)


@router.delete("/boilers/records/{record_id}")
async def delete_boiler_record(record_id: int, db: AsyncSession = Depends(get_db)):
    svc = HVACDataService(db)
    if not await svc.delete_record("boiler", record_id):
        raise HTTPException(404, "Record not found")
    return {"status": "deleted"}


# ---- VAVs ----
@router.get("/vavs/{device_id}/records")
async def query_vav_records(
    device_id: str,
    start_time: datetime | None = None, end_time: datetime | None = None,
    running_status: str | None = None,
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=1000),
    sort_by: str = "timestamp", sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    params = _build_query_params(device_id, start_time, end_time, running_status, page, page_size, sort_by, sort_order)
    svc = HVACDataService(db)
    result = await svc.query_records("vav", params)
    result.items = [VAVRecordResponse.model_validate(i) for i in result.items]
    return result


@router.post("/vavs/{device_id}/records", status_code=201)
async def create_vav_record(device_id: str, data: VAVRecordCreate, db: AsyncSession = Depends(get_db)):
    svc = HVACDataService(db)
    record = await svc.create_record("vav", {**data.model_dump(), "device_id": device_id})
    return VAVRecordResponse.model_validate(record)


@router.put("/vavs/records/{record_id}")
async def update_vav_record(record_id: int, data: VAVRecordUpdate, db: AsyncSession = Depends(get_db)):
    svc = HVACDataService(db)
    record = await svc.update_record("vav", record_id, data.model_dump(exclude_unset=True))
    if not record:
        raise HTTPException(404, "Record not found")
    return VAVRecordResponse.model_validate(record)


@router.delete("/vavs/records/{record_id}")
async def delete_vav_record(record_id: int, db: AsyncSession = Depends(get_db)):
    svc = HVACDataService(db)
    if not await svc.delete_record("vav", record_id):
        raise HTTPException(404, "Record not found")
    return {"status": "deleted"}


# ---- Pumps ----
@router.get("/pumps/{device_id}/records")
async def query_pump_records(
    device_id: str,
    start_time: datetime | None = None, end_time: datetime | None = None,
    running_status: str | None = None,
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=1000),
    sort_by: str = "timestamp", sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    params = _build_query_params(device_id, start_time, end_time, running_status, page, page_size, sort_by, sort_order)
    svc = HVACDataService(db)
    result = await svc.query_records("pump", params)
    result.items = [PumpRecordResponse.model_validate(i) for i in result.items]
    return result


@router.post("/pumps/{device_id}/records", status_code=201)
async def create_pump_record(device_id: str, data: PumpRecordCreate, db: AsyncSession = Depends(get_db)):
    svc = HVACDataService(db)
    record = await svc.create_record("pump", {**data.model_dump(), "device_id": device_id})
    return PumpRecordResponse.model_validate(record)


@router.put("/pumps/records/{record_id}")
async def update_pump_record(record_id: int, data: PumpRecordUpdate, db: AsyncSession = Depends(get_db)):
    svc = HVACDataService(db)
    record = await svc.update_record("pump", record_id, data.model_dump(exclude_unset=True))
    if not record:
        raise HTTPException(404, "Record not found")
    return PumpRecordResponse.model_validate(record)


@router.delete("/pumps/records/{record_id}")
async def delete_pump_record(record_id: int, db: AsyncSession = Depends(get_db)):
    svc = HVACDataService(db)
    if not await svc.delete_record("pump", record_id):
        raise HTTPException(404, "Record not found")
    return {"status": "deleted"}


# ---- Cooling Towers ----
@router.get("/cooling-towers/{device_id}/records")
async def query_ct_records(
    device_id: str,
    start_time: datetime | None = None, end_time: datetime | None = None,
    running_status: str | None = None,
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=1000),
    sort_by: str = "timestamp", sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    params = _build_query_params(device_id, start_time, end_time, running_status, page, page_size, sort_by, sort_order)
    svc = HVACDataService(db)
    result = await svc.query_records("cooling_tower", params)
    result.items = [CoolingTowerRecordResponse.model_validate(i) for i in result.items]
    return result


@router.post("/cooling-towers/{device_id}/records", status_code=201)
async def create_ct_record(device_id: str, data: CoolingTowerRecordCreate, db: AsyncSession = Depends(get_db)):
    svc = HVACDataService(db)
    record = await svc.create_record("cooling_tower", {**data.model_dump(), "device_id": device_id})
    return CoolingTowerRecordResponse.model_validate(record)


@router.put("/cooling-towers/records/{record_id}")
async def update_ct_record(record_id: int, data: CoolingTowerRecordUpdate, db: AsyncSession = Depends(get_db)):
    svc = HVACDataService(db)
    record = await svc.update_record("cooling_tower", record_id, data.model_dump(exclude_unset=True))
    if not record:
        raise HTTPException(404, "Record not found")
    return CoolingTowerRecordResponse.model_validate(record)


@router.delete("/cooling-towers/records/{record_id}")
async def delete_ct_record(record_id: int, db: AsyncSession = Depends(get_db)):
    svc = HVACDataService(db)
    if not await svc.delete_record("cooling_tower", record_id):
        raise HTTPException(404, "Record not found")
    return {"status": "deleted"}
