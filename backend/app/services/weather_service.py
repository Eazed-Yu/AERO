from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.weather import WeatherRecord
from app.schemas.query import EnergyQueryParams, PaginatedResponse
from app.schemas.weather import WeatherRecordCreate, WeatherRecordUpdate


class WeatherService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def query(self, params: EnergyQueryParams) -> PaginatedResponse:
        stmt = select(WeatherRecord)
        count_stmt = select(func.count(WeatherRecord.id))

        if params.building_id:
            stmt = stmt.where(WeatherRecord.building_id == params.building_id)
            count_stmt = count_stmt.where(WeatherRecord.building_id == params.building_id)
        if params.start_time:
            stmt = stmt.where(WeatherRecord.timestamp >= params.start_time)
            count_stmt = count_stmt.where(WeatherRecord.timestamp >= params.start_time)
        if params.end_time:
            stmt = stmt.where(WeatherRecord.timestamp <= params.end_time)
            count_stmt = count_stmt.where(WeatherRecord.timestamp <= params.end_time)

        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        sort_col = getattr(WeatherRecord, params.sort_by, WeatherRecord.timestamp)
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

    async def get_record(self, record_id: int) -> WeatherRecord | None:
        stmt = select(WeatherRecord).where(WeatherRecord.id == record_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_record(self, data: WeatherRecordCreate) -> WeatherRecord:
        record = WeatherRecord(**data.model_dump())
        self.db.add(record)
        await self.db.flush()
        return record

    async def update_record(
        self, record_id: int, data: WeatherRecordUpdate
    ) -> WeatherRecord | None:
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

    async def bulk_import(self, records: list[WeatherRecordCreate]) -> int:
        count = 0
        for rec in records:
            self.db.add(WeatherRecord(**rec.model_dump()))
            count += 1
            if count % 500 == 0:
                await self.db.flush()
        if count > 0:
            await self.db.flush()
        return count
