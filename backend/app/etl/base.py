from abc import ABC, abstractmethod

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession


class AbstractETLAdapter(ABC):
    """
    Abstract base for dataset-specific ETL importers.
    Implementations will handle specific public dataset formats
    and transform them into the canonical AERO schema.

    Planned implementations:
    - University of Michigan Campus Dataset
    - AlphaBuilding Synthetic Dataset
    - Building Data Genome Project 2
    """

    @abstractmethod
    async def extract(self, source: str) -> pd.DataFrame:
        """Extract data from source (file path, URL, etc.)."""
        ...

    @abstractmethod
    async def transform(self, raw_data: pd.DataFrame) -> list[dict]:
        """Transform into canonical AERO format."""
        ...

    @abstractmethod
    async def load(self, records: list[dict], db: AsyncSession) -> int:
        """Load into database. Returns number of records inserted."""
        ...

    async def run(self, source: str, db: AsyncSession) -> int:
        """Full ETL pipeline."""
        raw = await self.extract(source)
        transformed = await self.transform(raw)
        return await self.load(transformed, db)
