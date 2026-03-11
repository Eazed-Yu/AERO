from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.energy_meter import EnergyMeter
from app.schemas.energy_meter import (
    EnergyMeterCreate,
    EnergyMeterUpdate,
    ImportResult,
)
from app.schemas.query import EnergyQueryParams, PaginatedResponse


class EnergyMeterService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def query(self, params: EnergyQueryParams) -> PaginatedResponse:
        stmt = select(EnergyMeter)
        count_stmt = select(func.count(EnergyMeter.id))

        if params.region_id:
            stmt = stmt.where(EnergyMeter.region_id == params.region_id)
            count_stmt = count_stmt.where(EnergyMeter.region_id == params.region_id)
        if params.building_id:
            stmt = stmt.where(EnergyMeter.building_id == params.building_id)
            count_stmt = count_stmt.where(EnergyMeter.building_id == params.building_id)
        if params.start_time:
            stmt = stmt.where(EnergyMeter.timestamp >= params.start_time)
            count_stmt = count_stmt.where(EnergyMeter.timestamp >= params.start_time)
        if params.end_time:
            stmt = stmt.where(EnergyMeter.timestamp <= params.end_time)
            count_stmt = count_stmt.where(EnergyMeter.timestamp <= params.end_time)

        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        sort_col = getattr(EnergyMeter, params.sort_by, EnergyMeter.timestamp)
        if params.sort_order == "desc":
            stmt = stmt.order_by(sort_col.desc())
        else:
            stmt = stmt.order_by(sort_col.asc())

        offset = (params.page - 1) * params.page_size
        stmt = stmt.offset(offset).limit(params.page_size)

        result = await self.db.execute(stmt)
        items = list(result.scalars().all())
        pages = (total + params.page_size - 1) // params.page_size if total > 0 else 0

        return PaginatedResponse(
            items=items, total=total, page=params.page,
            page_size=params.page_size, pages=pages,
        )

    async def get_records(
        self, building_id: str, start_time: datetime, end_time: datetime
    ) -> list[EnergyMeter]:
        stmt = (
            select(EnergyMeter)
            .where(EnergyMeter.building_id == building_id)
            .where(EnergyMeter.timestamp >= start_time)
            .where(EnergyMeter.timestamp <= end_time)
            .order_by(EnergyMeter.timestamp)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_record(self, record_id: int) -> EnergyMeter | None:
        stmt = select(EnergyMeter).where(EnergyMeter.id == record_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_record(self, data: EnergyMeterCreate) -> EnergyMeter:
        record = EnergyMeter(**data.model_dump())
        self.db.add(record)
        await self.db.flush()
        return record

    async def update_record(
        self, record_id: int, data: EnergyMeterUpdate
    ) -> EnergyMeter | None:
        record = await self.get_record(record_id)
        if not record:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(record, key, value)
        await self.db.flush()
        return record

    async def delete_record(self, record_id: int) -> bool:
        record = await self.get_record(record_id)
        if not record:
            return False
        await self.db.delete(record)
        await self.db.flush()
        return True

    async def bulk_import(
        self, records: list[EnergyMeterCreate], on_conflict: str = "skip"
    ) -> ImportResult:
        total = len(records)
        inserted = 0
        errors = 0
        error_details: list[str] = []

        for i, rec in enumerate(records):
            try:
                self.db.add(EnergyMeter(**rec.model_dump()))
                inserted += 1
            except Exception as e:
                errors += 1
                error_details.append(f"Record {i}: {str(e)}")
            if inserted % 500 == 0 and inserted > 0:
                await self.db.flush()

        if inserted > 0:
            await self.db.flush()

        return ImportResult(
            total=total, inserted=inserted, skipped=0,
            errors=errors, error_details=error_details[:50],
        )
