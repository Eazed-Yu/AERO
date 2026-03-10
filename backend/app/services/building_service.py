from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Building
from app.schemas.building import BuildingCreate, BuildingUpdate


class BuildingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_buildings(self, building_type: str | None = None) -> list[Building]:
        stmt = select(Building)
        if building_type:
            stmt = stmt.where(Building.building_type == building_type)
        stmt = stmt.order_by(Building.building_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_building(self, building_id: str) -> Building | None:
        stmt = select(Building).where(Building.building_id == building_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_building(self, data: BuildingCreate) -> Building:
        building = Building(**data.model_dump())
        self.db.add(building)
        await self.db.flush()
        return building

    async def update_building(
        self, building_id: str, data: BuildingUpdate
    ) -> Building | None:
        building = await self.get_building(building_id)
        if not building:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(building, key, value)
        await self.db.flush()
        return building

    async def delete_building(self, building_id: str) -> bool:
        building = await self.get_building(building_id)
        if not building:
            return False
        await self.db.delete(building)
        await self.db.flush()
        return True
