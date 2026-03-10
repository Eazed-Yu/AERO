from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EnergyRecord
from app.schemas.energy import EnergyRecordCreate, ImportResult


class ImportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def bulk_import_energy(
        self,
        records: list[EnergyRecordCreate],
        on_conflict: str = "skip",
    ) -> ImportResult:
        total = len(records)
        inserted = 0
        skipped = 0
        errors = 0
        error_details: list[str] = []

        for i, rec in enumerate(records):
            try:
                energy = EnergyRecord(**rec.model_dump())
                self.db.add(energy)
                inserted += 1
            except Exception as e:
                errors += 1
                error_details.append(f"Record {i}: {str(e)}")

            # Flush in batches
            if inserted % 500 == 0 and inserted > 0:
                await self.db.flush()

        if inserted > 0:
            await self.db.flush()

        return ImportResult(
            total=total,
            inserted=inserted,
            skipped=skipped,
            errors=errors,
            error_details=error_details[:50],
        )
