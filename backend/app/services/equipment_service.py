from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Equipment, EquipmentStatus
from app.schemas.equipment import (
    EquipmentCreate,
    EquipmentStatusCreate,
    EquipmentStatusUpdate,
    EquipmentUpdate,
)


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

    async def create_equipment(self, data: EquipmentCreate) -> Equipment:
        equipment = Equipment(**data.model_dump())
        self.db.add(equipment)
        await self.db.flush()
        return equipment

    async def update_equipment(
        self, device_id: str, data: EquipmentUpdate
    ) -> Equipment | None:
        equipment = await self.get_equipment(device_id)
        if not equipment:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(equipment, key, value)
        await self.db.flush()
        return equipment

    async def delete_equipment(self, device_id: str) -> bool:
        equipment = await self.get_equipment(device_id)
        if not equipment:
            return False
        await self.db.delete(equipment)
        await self.db.flush()
        return True

    async def get_status(self, status_id: int) -> EquipmentStatus | None:
        stmt = select(EquipmentStatus).where(EquipmentStatus.id == status_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_status(
        self, data: EquipmentStatusCreate
    ) -> EquipmentStatus:
        status = EquipmentStatus(**data.model_dump())
        self.db.add(status)
        await self.db.flush()
        return status

    async def update_status(
        self, status_id: int, data: EquipmentStatusUpdate
    ) -> EquipmentStatus | None:
        status = await self.get_status(status_id)
        if not status:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(status, key, value)
        await self.db.flush()
        return status

    async def delete_status(self, status_id: int) -> bool:
        status = await self.get_status(status_id)
        if not status:
            return False
        await self.db.delete(status)
        await self.db.flush()
        return True
