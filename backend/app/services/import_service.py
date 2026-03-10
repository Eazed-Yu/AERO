from sqlalchemy.ext.asyncio import AsyncSession

from app.models.energy_meter import EnergyMeter
from app.schemas.energy_meter import EnergyMeterCreate, ImportResult


class ImportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def bulk_import_energy(
        self,
        records: list[EnergyMeterCreate],
        on_conflict: str = "skip",
    ) -> ImportResult:
        total = len(records)
        inserted = 0
        errors = 0
        error_details: list[str] = []

        for i, rec in enumerate(records):
            try:
                self.db.add(EnergyMeter(**rec.model_dump()))
                inserted += 1
            except Exception as e:
                errors += 1
                error_details.append(f"Record {i}: {str(e)}")

            if inserted % 500 == 0 and inserted > 0:
                await self.db.flush()

        if inserted > 0:
            await self.db.flush()

        return ImportResult(
            total=total,
            inserted=inserted,
            skipped=0,
            errors=errors,
            error_details=error_details[:50],
        )
