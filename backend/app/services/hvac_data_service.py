from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ahu import AHURecord
from app.models.boiler import BoilerRecord
from app.models.chiller import ChillerRecord
from app.models.cooling_tower import CoolingTowerRecord
from app.models.pump import PumpRecord
from app.models.vav import VAVRecord
from app.schemas.query import HVACDataQueryParams, PaginatedResponse

# Map equipment type to model class
MODEL_MAP = {
    "chiller": ChillerRecord,
    "ahu": AHURecord,
    "boiler": BoilerRecord,
    "vav": VAVRecord,
    "pump": PumpRecord,
    "chw_pump": PumpRecord,
    "cw_pump": PumpRecord,
    "hw_pump": PumpRecord,
    "cooling_tower": CoolingTowerRecord,
}


class HVACDataService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _get_model(self, equipment_type: str):
        model = MODEL_MAP.get(equipment_type)
        if not model:
            raise ValueError(f"Unknown equipment type: {equipment_type}")
        return model

    async def query_records(
        self, equipment_type: str, params: HVACDataQueryParams
    ) -> PaginatedResponse:
        model = self._get_model(equipment_type)
        stmt = select(model)
        count_stmt = select(func.count(model.id))

        if params.device_id:
            stmt = stmt.where(model.device_id == params.device_id)
            count_stmt = count_stmt.where(model.device_id == params.device_id)
        if params.start_time:
            stmt = stmt.where(model.timestamp >= params.start_time)
            count_stmt = count_stmt.where(model.timestamp >= params.start_time)
        if params.end_time:
            stmt = stmt.where(model.timestamp <= params.end_time)
            count_stmt = count_stmt.where(model.timestamp <= params.end_time)
        if params.running_status and hasattr(model, "running_status"):
            stmt = stmt.where(model.running_status == params.running_status)
            count_stmt = count_stmt.where(model.running_status == params.running_status)

        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        sort_col = getattr(model, params.sort_by, model.timestamp)
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

    async def get_record(self, equipment_type: str, record_id: int):
        model = self._get_model(equipment_type)
        stmt = select(model).where(model.id == record_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_record(self, equipment_type: str, data: dict):
        model = self._get_model(equipment_type)
        record = model(**data)
        self.db.add(record)
        await self.db.flush()
        return record

    async def update_record(
        self, equipment_type: str, record_id: int, data: dict
    ):
        record = await self.get_record(equipment_type, record_id)
        if not record:
            return None
        for key, value in data.items():
            setattr(record, key, value)
        await self.db.flush()
        return record

    async def delete_record(self, equipment_type: str, record_id: int) -> bool:
        record = await self.get_record(equipment_type, record_id)
        if not record:
            return False
        await self.db.delete(record)
        await self.db.flush()
        return True

    async def get_latest_records(
        self, equipment_type: str, device_ids: list[str] | None = None
    ) -> list:
        """Get latest record for each device of given type."""
        model = self._get_model(equipment_type)

        # Subquery for max timestamp per device
        sub = (
            select(
                model.device_id,
                func.max(model.timestamp).label("max_ts"),
            )
            .group_by(model.device_id)
        )
        if device_ids:
            sub = sub.where(model.device_id.in_(device_ids))
        sub = sub.subquery()

        stmt = select(model).join(
            sub,
            (model.device_id == sub.c.device_id)
            & (model.timestamp == sub.c.max_ts),
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_overview(self) -> dict[str, list]:
        """Get latest status for all equipment types (dashboard use)."""
        overview: dict[str, list] = {}
        for eq_type in ["chiller", "ahu", "boiler", "vav", "pump", "cooling_tower"]:
            try:
                records = await self.get_latest_records(eq_type)
                overview[eq_type] = records
            except Exception:
                overview[eq_type] = []
        return overview

    async def bulk_import(
        self, equipment_type: str, records: list[dict]
    ) -> int:
        model = self._get_model(equipment_type)
        count = 0
        for rec_data in records:
            self.db.add(model(**rec_data))
            count += 1
            if count % 500 == 0:
                await self.db.flush()
        if count > 0:
            await self.db.flush()
        return count
