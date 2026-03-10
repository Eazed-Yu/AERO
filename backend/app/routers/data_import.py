import json

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.energy_meter import EnergyImportRequest, EnergyMeterCreate, ImportResult
from app.services.import_service import ImportService

router = APIRouter()


@router.post("/energy", response_model=ImportResult)
async def import_energy_records(
    data: EnergyImportRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = ImportService(db)
    return await svc.bulk_import_energy(
        records=data.records, on_conflict=data.on_conflict,
    )


@router.post("/upload", response_model=ImportResult)
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    text = content.decode("utf-8-sig")

    if file.filename and file.filename.endswith(".json"):
        payload = json.loads(text)
        if isinstance(payload, dict):
            if isinstance(payload.get("records"), list):
                raw_records = payload["records"]
            elif isinstance(payload.get("energy_meters"), list):
                raw_records = payload["energy_meters"]
            else:
                raw_records = []
        else:
            raw_records = payload
    elif file.filename and file.filename.endswith(".csv"):
        import csv
        import io

        reader = csv.DictReader(io.StringIO(text))
        raw_records = list(reader)
    else:
        payload = json.loads(text)
        if isinstance(payload, dict) and isinstance(payload.get("energy_meters"), list):
            raw_records = payload["energy_meters"]
        elif isinstance(payload, dict) and isinstance(payload.get("records"), list):
            raw_records = payload["records"]
        else:
            raw_records = payload

    if not isinstance(raw_records, list):
        return ImportResult(
            total=0, inserted=0, skipped=0, errors=1,
            error_details=["Invalid payload. Expected a JSON array or {'records': [...]}."],
        )

    def _normalize_row(raw: dict) -> dict:
        normalized = {}
        for key, value in raw.items():
            if key is None:
                continue
            cleaned_key = key.lstrip("\ufeff").strip()
            normalized[cleaned_key] = value
        return normalized

    records = []
    errors = []
    required_fields = {"building_id", "timestamp"}

    if raw_records:
        first_row = _normalize_row(raw_records[0])
        missing = required_fields - set(first_row.keys())
        if missing:
            return ImportResult(
                total=len(raw_records), inserted=0, skipped=0, errors=len(raw_records),
                error_details=[
                    "CSV header does not match import format. Required: building_id, timestamp."
                ],
            )

    for i, raw in enumerate(raw_records):
        try:
            normalized = _normalize_row(raw)
            records.append(EnergyMeterCreate(**normalized))
        except Exception as e:
            errors.append(f"Row {i}: {str(e)}")

    svc = ImportService(db)
    result = await svc.bulk_import_energy(records=records)
    result.errors += len(errors)
    result.error_details.extend(errors[:20])
    return result
