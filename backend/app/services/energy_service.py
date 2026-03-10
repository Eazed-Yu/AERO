from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EnergyRecord
from app.schemas.query import EnergyQueryParams, PaginatedResponse


class EnergyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def query(self, params: EnergyQueryParams) -> PaginatedResponse:
        # Base query
        stmt = select(EnergyRecord)
        count_stmt = select(func.count(EnergyRecord.id))

        # Apply filters
        if params.building_id:
            stmt = stmt.where(EnergyRecord.building_id == params.building_id)
            count_stmt = count_stmt.where(
                EnergyRecord.building_id == params.building_id
            )
        if params.start_time:
            stmt = stmt.where(EnergyRecord.timestamp >= params.start_time)
            count_stmt = count_stmt.where(
                EnergyRecord.timestamp >= params.start_time
            )
        if params.end_time:
            stmt = stmt.where(EnergyRecord.timestamp <= params.end_time)
            count_stmt = count_stmt.where(
                EnergyRecord.timestamp <= params.end_time
            )

        # Count total
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Sort
        sort_col = getattr(EnergyRecord, params.sort_by, EnergyRecord.timestamp)
        if params.sort_order == "desc":
            stmt = stmt.order_by(sort_col.desc())
        else:
            stmt = stmt.order_by(sort_col.asc())

        # Pagination
        offset = (params.page - 1) * params.page_size
        stmt = stmt.offset(offset).limit(params.page_size)

        result = await self.db.execute(stmt)
        items = list(result.scalars().all())

        pages = (total + params.page_size - 1) // params.page_size if total > 0 else 0

        return PaginatedResponse(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            pages=pages,
        )

    async def get_records(
        self,
        building_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> list[EnergyRecord]:
        stmt = (
            select(EnergyRecord)
            .where(EnergyRecord.building_id == building_id)
            .where(EnergyRecord.timestamp >= start_time)
            .where(EnergyRecord.timestamp <= end_time)
            .order_by(EnergyRecord.timestamp)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
