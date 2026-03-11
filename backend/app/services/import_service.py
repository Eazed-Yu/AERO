import csv
import io
import json
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.sqltypes import Boolean, Date, DateTime, Float, Integer, Numeric

from app.models.equipment import Equipment
from app.schemas.energy_meter import ImportResult
from app.services.hvac_data_service import MODEL_MAP


# CSV template columns per device type (excludes id; device_id is auto-filled)
TEMPLATE_COLUMNS: dict[str, list[str]] = {
    "chiller": [
        "timestamp", "chw_supply_temp", "chw_return_temp", "chw_flow_rate",
        "cw_supply_temp", "cw_return_temp", "cw_flow_rate", "power_kw",
        "cooling_capacity_kw", "load_ratio", "cop", "evaporator_approach",
        "condenser_approach", "compressor_rla_pct", "running_status",
    ],
    "ahu": [
        "timestamp", "supply_air_temp", "return_air_temp", "mixed_air_temp",
        "outdoor_air_temp", "supply_air_humidity", "return_air_humidity",
        "supply_fan_speed", "supply_fan_power_kw", "supply_air_flow",
        "return_fan_speed", "chw_valve_pos", "hw_valve_pos", "oa_damper_pos",
        "ra_damper_pos", "duct_static_pressure", "filter_dp",
        "operating_mode", "sat_setpoint", "dsp_setpoint", "running_status",
    ],
    "boiler": [
        "timestamp", "hw_supply_temp", "hw_return_temp", "hw_flow_rate",
        "firing_rate", "power_kw", "fuel_consumption", "heating_capacity_kw",
        "efficiency", "flue_gas_temp", "running_status",
    ],
    "vav": [
        "timestamp", "zone_temp", "zone_temp_setpoint_clg",
        "zone_temp_setpoint_htg", "airflow", "airflow_setpoint", "damper_pos",
        "discharge_air_temp", "reheat_valve_pos", "zone_co2",
        "occupancy_status", "operating_mode",
    ],
    "pump": [
        "timestamp", "speed", "power_kw", "flow_rate",
        "inlet_pressure", "outlet_pressure", "differential_pressure",
        "running_status",
    ],
    "cooling_tower": [
        "timestamp", "fan_speed", "fan_power_kw", "cw_inlet_temp",
        "cw_outlet_temp", "wet_bulb_temp", "approach", "range",
        "running_status",
    ],
}

# Pump aliases share the same template
for _alias in ("chw_pump", "cw_pump", "hw_pump"):
    TEMPLATE_COLUMNS[_alias] = TEMPLATE_COLUMNS["pump"]


class ImportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── helpers ──

    async def _get_equipment(self, device_id: str) -> Equipment:
        stmt = select(Equipment).where(Equipment.device_id == device_id)
        result = await self.db.execute(stmt)
        eq = result.scalar_one_or_none()
        if eq is None:
            raise ValueError(f"Device not found: {device_id}")
        return eq

    @staticmethod
    def _resolve_model(device_type: str):
        model = MODEL_MAP.get(device_type)
        if model is None:
            raise ValueError(f"Unknown device type: {device_type}")
        return model

    @staticmethod
    def _coerce_value(value, column):
        if value is None:
            return None

        if isinstance(value, str):
            value = value.strip()
            if value == "" or value.lower() in {"null", "none"}:
                return None

        col_type = column.type

        if isinstance(col_type, DateTime):
            if isinstance(value, datetime):
                return value
            if isinstance(value, date):
                return datetime.combine(value, datetime.min.time())
            if isinstance(value, str):
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            raise ValueError(f"Invalid datetime value: {value}")

        if isinstance(col_type, Date):
            if isinstance(value, date):
                return value
            if isinstance(value, datetime):
                return value.date()
            if isinstance(value, str):
                return date.fromisoformat(value)
            raise ValueError(f"Invalid date value: {value}")

        if isinstance(col_type, Boolean):
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(value)
            if isinstance(value, str):
                lowered = value.lower()
                if lowered in {"1", "true", "yes", "y"}:
                    return True
                if lowered in {"0", "false", "no", "n"}:
                    return False
            raise ValueError(f"Invalid boolean value: {value}")

        if isinstance(col_type, Integer):
            if isinstance(value, int):
                return value
            return int(float(value))

        if isinstance(col_type, (Float, Numeric)):
            if isinstance(value, (int, float)):
                return value
            return float(value)

        return value

    @classmethod
    def _coerce_record_for_model(cls, model, rec: dict) -> dict:
        columns = model.__table__.columns
        coerced: dict = {}
        for k, v in rec.items():
            col = columns.get(k)
            if col is None:
                continue
            coerced[k] = cls._coerce_value(v, col)
        return coerced

    # ── import device records ──

    async def import_device_records(
        self, device_id: str, records: list[dict],
    ) -> ImportResult:
        eq = await self._get_equipment(device_id)
        model = self._resolve_model(eq.device_type)

        total = len(records)
        inserted = 0
        errors = 0
        error_details: list[str] = []

        for i, rec in enumerate(records):
            try:
                rec["device_id"] = device_id
                # Remove keys not in model to avoid errors
                if "id" in rec:
                    del rec["id"]
                normalized = self._coerce_record_for_model(model, rec)
                self.db.add(model(**normalized))
                inserted += 1
            except Exception as e:
                errors += 1
                if len(error_details) < 50:
                    error_details.append(f"Row {i}: {e}")

            if inserted % 500 == 0 and inserted > 0:
                await self.db.flush()

        if inserted > 0:
            await self.db.flush()

        return ImportResult(
            total=total, inserted=inserted, skipped=0,
            errors=errors, error_details=error_details,
        )

    # ── CSV template ──

    @staticmethod
    def get_device_csv_template(device_type: str) -> str:
        # Normalise pump aliases
        cols = TEMPLATE_COLUMNS.get(device_type)
        if cols is None:
            raise ValueError(f"No template for device type: {device_type}")

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(cols)
        return output.getvalue()

    # ── file parsing helpers ──

    @staticmethod
    def parse_upload_file(filename: str, content: bytes) -> list[dict]:
        text = content.decode("utf-8-sig")

        if filename.endswith(".json"):
            payload = json.loads(text)
            if isinstance(payload, dict):
                raw = payload.get("records") or payload.get("data") or []
            else:
                raw = payload
        elif filename.endswith(".csv"):
            reader = csv.DictReader(io.StringIO(text))
            raw = list(reader)
        else:
            raise ValueError("Unsupported file format. Use .csv or .json")

        if not isinstance(raw, list):
            raise ValueError("Invalid payload: expected a list of records")

        # Normalise keys (strip BOM/whitespace)
        cleaned: list[dict] = []
        for row in raw:
            cleaned.append({
                k.lstrip("\ufeff").strip(): v
                for k, v in row.items() if k is not None
            })
        return cleaned
