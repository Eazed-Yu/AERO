from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Equipment, EquipmentStatus


class EquipmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_equipment(
        self,
        building_id: str | None = None,
        device_type: str | None = None,
    ) -> list[Equipment]:
        stmt = select(Equipment)
        if building_id:
            stmt = stmt.where(Equipment.building_id == building_id)
        if device_type:
            stmt = stmt.where(Equipment.device_type == device_type)
        stmt = stmt.order_by(Equipment.device_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_equipment(self, device_id: str) -> Equipment | None:
        stmt = select(Equipment).where(Equipment.device_id == device_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_status(self, device_id: str) -> EquipmentStatus | None:
        stmt = (
            select(EquipmentStatus)
            .where(EquipmentStatus.device_id == device_id)
            .order_by(EquipmentStatus.timestamp.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_status_history(
        self,
        device_id: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[EquipmentStatus]:
        stmt = select(EquipmentStatus).where(
            EquipmentStatus.device_id == device_id
        )
        if start_time:
            stmt = stmt.where(EquipmentStatus.timestamp >= start_time)
        if end_time:
            stmt = stmt.where(EquipmentStatus.timestamp <= end_time)
        stmt = stmt.order_by(EquipmentStatus.timestamp.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
