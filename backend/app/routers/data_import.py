from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.energy_meter import ImportResult
from app.services.import_service import ImportService

router = APIRouter()


# ── Endpoints ──

@router.post("/device/{device_id}/upload", response_model=ImportResult)
async def upload_device_records(
    device_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a CSV/JSON file to import operation records for a device."""
    content = await file.read()
    svc = ImportService(db)

    try:
        records = svc.parse_upload_file(file.filename or "", content)
    except ValueError as e:
        return ImportResult(
            total=0, inserted=0, skipped=0, errors=1,
            error_details=[str(e)],
        )
    try:
        return await svc.import_device_records(device_id=device_id, records=records)
    except ValueError as e:
        return ImportResult(
            total=len(records), inserted=0, skipped=0, errors=1,
            error_details=[str(e)],
        )
    except Exception as e:
        return ImportResult(
            total=len(records), inserted=0, skipped=0, errors=1,
            error_details=[f"Import failed: {e}"],
        )


@router.get("/device/{device_id}/template")
async def download_device_template(
    device_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Download a CSV template for the device type."""
    svc = ImportService(db)
    eq = await svc._get_equipment(device_id)
    csv_text = svc.get_device_csv_template(eq.device_type)
    return PlainTextResponse(
        content=csv_text,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={eq.device_type}_template.csv",
        },
    )
