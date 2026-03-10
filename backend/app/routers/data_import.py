import json

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.energy import EnergyImportRequest, EnergyRecordCreate, ImportResult
from app.services.import_service import ImportService

router = APIRouter()


@router.post("/energy", response_model=ImportResult)
async def import_energy_records(
    data: EnergyImportRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = ImportService(db)
    return await svc.bulk_import_energy(
        records=data.records,
        on_conflict=data.on_conflict,
    )


@router.post("/upload", response_model=ImportResult)
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    text = content.decode("utf-8")

    if file.filename and file.filename.endswith(".json"):
        raw_records = json.loads(text)
    elif file.filename and file.filename.endswith(".csv"):
        import csv
        import io

        reader = csv.DictReader(io.StringIO(text))
        raw_records = list(reader)
    else:
        raw_records = json.loads(text)

    records = []
    errors = []
    for i, raw in enumerate(raw_records):
        try:
            records.append(EnergyRecordCreate(**raw))
        except Exception as e:
            errors.append(f"Row {i}: {str(e)}")

    svc = ImportService(db)
    result = await svc.bulk_import_energy(records=records)
    result.errors += len(errors)
    result.error_details.extend(errors[:20])
    return result
