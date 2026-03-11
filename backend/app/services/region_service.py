from sqlalchemy import select, func, cast, Integer
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.region import Region
from app.schemas.region import RegionCreate, RegionUpdate


class RegionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _next_id(self) -> str:
        stmt = select(func.max(cast(Region.region_id, Integer)))
        result = await self.db.execute(stmt)
        max_id = result.scalar() or 0
        return str(max_id + 1)

    async def list_regions(self) -> list[Region]:
        stmt = select(Region).order_by(Region.region_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_region(self, region_id: str) -> Region | None:
        stmt = select(Region).where(Region.region_id == region_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_region(self, data: RegionCreate) -> Region:
        region_id = await self._next_id()
        region = Region(region_id=region_id, **data.model_dump())
        self.db.add(region)
        await self.db.flush()
        return region

    async def update_region(
        self, region_id: str, data: RegionUpdate
    ) -> Region | None:
        region = await self.get_region(region_id)
        if not region:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(region, key, value)
        await self.db.flush()
        return region

    async def delete_region(self, region_id: str) -> bool:
        region = await self.get_region(region_id)
        if not region:
            return False
        await self.db.delete(region)
        await self.db.flush()
        return True
