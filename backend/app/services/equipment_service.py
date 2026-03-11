from sqlalchemy import select, func, cast, Integer
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.equipment import Equipment
from app.schemas.equipment import EquipmentCreate, EquipmentUpdate


class EquipmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _next_id(self) -> str:
        stmt = select(func.max(cast(Equipment.device_id, Integer)))
        result = await self.db.execute(stmt)
        max_id = result.scalar() or 0
        return str(max_id + 1)

    async def list_equipment(
        self,
        region_id: str | None = None,
        building_id: str | None = None,
        device_type: str | None = None,
        system_type: str | None = None,
    ) -> list[Equipment]:
        stmt = select(Equipment)
        if region_id:
            stmt = stmt.where(Equipment.region_id == region_id)
        if building_id:
            stmt = stmt.where(Equipment.building_id == building_id)
        if device_type:
            stmt = stmt.where(Equipment.device_type == device_type)
        if system_type:
            stmt = stmt.where(Equipment.system_type == system_type)
        stmt = stmt.order_by(Equipment.device_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_equipment(self, device_id: str) -> Equipment | None:
        stmt = select(Equipment).where(Equipment.device_id == device_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_equipment(self, data: EquipmentCreate) -> Equipment:
        device_id = await self._next_id()
        equipment = Equipment(device_id=device_id, **data.model_dump())
        self.db.add(equipment)
        await self.db.flush()
        return equipment

    async def update_equipment(
        self, device_id: str, data: EquipmentUpdate
    ) -> Equipment | None:
        equipment = await self.get_equipment(device_id)
        if not equipment:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
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

    async def get_devices_by_type(self, device_type: str) -> list[str]:
        """Return list of device_ids for a given type."""
        stmt = (
            select(Equipment.device_id)
            .where(Equipment.device_type == device_type)
            .order_by(Equipment.device_id)
        )
        result = await self.db.execute(stmt)
        return [row[0] for row in result.all()]
