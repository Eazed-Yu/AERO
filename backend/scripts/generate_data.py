"""
Generate realistic synthetic building energy CSV files.
Usage: uv run python -m scripts.generate_data --days 7 --anomaly-rate 0.04
"""

import argparse
import csv
import json
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

BUILDINGS = [
    {
        "building_id": "BLD-001",
        "name": "绿地办公大厦",
        "building_type": "office",
        "area": 15000,
        "address": "济南市历下区经十路88号",
        "floors": 20,
        "year_built": 2018,
    },
    {
        "building_id": "BLD-002",
        "name": "中央商业广场",
        "building_type": "commercial",
        "area": 25000,
        "address": "济南市市中区泉城路168号",
        "floors": 6,
        "year_built": 2015,
    },
    {
        "building_id": "BLD-003",
        "name": "滨河花园小区",
        "building_type": "residential",
        "area": 8000,
        "address": "临沂市兰山区滨河大道56号",
        "floors": 18,
        "year_built": 2020,
    },
    {
        "building_id": "BLD-004",
        "name": "临朐县人民医院",
        "building_type": "hospital",
        "area": 20000,
        "address": "潍坊市临朐县民主路100号",
        "floors": 12,
        "year_built": 2012,
    },
    {
        "building_id": "BLD-005",
        "name": "临沂大学教学楼A",
        "building_type": "school",
        "area": 5000,
        "address": "临沂市兰山区双岭路中段",
        "floors": 5,
        "year_built": 2010,
    },
]

EQUIPMENT_TEMPLATES = {
    "office": [
        ("chiller", "中央空调主机", 500),
        ("ahu", "空气处理机组-1F", 50),
        ("ahu", "空气处理机组-10F", 50),
        ("pump", "冷冻水泵", 30),
        ("lighting", "照明系统", 100),
    ],
    "commercial": [
        ("chiller", "中央空调主机A", 800),
        ("chiller", "中央空调主机B", 800),
        ("ahu", "新风机组", 60),
        ("pump", "冷却水泵", 45),
        ("lighting", "商场照明", 200),
    ],
    "residential": [
        ("boiler", "供暖锅炉", 200),
        ("pump", "循环水泵", 15),
        ("lighting", "公共照明", 20),
    ],
    "hospital": [
        ("chiller", "中央空调主机A", 600),
        ("chiller", "中央空调主机B", 600),
        ("ahu", "手术室新风", 80),
        ("boiler", "蒸汽锅炉", 300),
        ("pump", "冷冻水泵", 40),
        ("lighting", "照明系统", 150),
    ],
    "school": [
        ("chiller", "教学楼空调", 300),
        ("ahu", "教室新风", 30),
        ("pump", "水泵", 10),
        ("lighting", "教室照明", 60),
    ],
}

# Building-type specific electricity baselines (kWh per hour per 1000m²)
ELECTRICITY_BASELINES = {
    "office": 8.0,
    "commercial": 12.0,
    "residential": 3.0,
    "hospital": 15.0,
    "school": 6.0,
}

# Canonical energy import columns expected by backend import endpoints.
ENERGY_IMPORT_FIELDS = [
    "building_id",
    "timestamp",
    "electricity_kwh",
    "water_m3",
    "gas_m3",
    "hvac_kwh",
    "hvac_supply_temp",
    "hvac_return_temp",
    "hvac_flow_rate",
    "outdoor_temp",
    "outdoor_humidity",
    "occupancy_density",
]


def _hour_factor(hour: int, btype: str) -> float:
    """Time-of-day multiplier for electricity usage."""
    if btype == "office":
        if 8 <= hour <= 18:
            return 1.0 + 0.3 * math.sin(math.pi * (hour - 8) / 10)
        return 0.3
    elif btype == "commercial":
        if 10 <= hour <= 21:
            return 0.8 + 0.4 * math.sin(math.pi * (hour - 10) / 11)
        return 0.2
    elif btype == "residential":
        if 6 <= hour <= 8:
            return 0.8
        elif 18 <= hour <= 22:
            return 1.2
        elif 22 <= hour or hour < 6:
            return 0.4
        return 0.5
    elif btype == "hospital":
        return 0.8 + 0.2 * math.sin(math.pi * hour / 12)
    elif btype == "school":
        if 7 <= hour <= 17:
            return 1.0
        return 0.2
    return 0.5


def _weekday_factor(weekday: int, btype: str) -> float:
    """Weekday vs weekend factor (0=Monday, 6=Sunday)."""
    if btype in ("office", "school"):
        return 1.0 if weekday < 5 else 0.2
    elif btype == "commercial":
        return 1.0 if weekday < 5 else 1.3
    return 1.0


def _seasonal_temp(day_of_year: int) -> float:
    """Simulate outdoor temperature based on day of year (济南气候)."""
    # Annual average ~14°C, amplitude ~18°C, peak in July (day 200)
    return 14 + 18 * math.sin(2 * math.pi * (day_of_year - 100) / 365)


def _current_hour() -> datetime:
    now = datetime.now()
    return now.replace(minute=0, second=0, microsecond=0)


def generate_data(
    days: int = 7,
    anomaly_rate: float = 0.05,
    seed: int = 42,
):
    random.seed(seed)
    np.random.seed(seed)

    if days <= 0:
        raise ValueError("days must be greater than 0")
    if not 0 <= anomaly_rate <= 1:
        raise ValueError("anomaly_rate must be between 0 and 1")

    end_hour = _current_hour()
    start_hour = end_hour - timedelta(days=days)

    energy_records = []
    equipment_list = []
    equipment_status_records = []
    anomaly_events = []

    # Generate equipment
    dev_counter = 0
    for bld in BUILDINGS:
        btype = bld["building_type"]
        templates = EQUIPMENT_TEMPLATES.get(btype, [])
        for dtype, dname, power in templates:
            dev_counter += 1
            device_id = f"DEV-{dev_counter:04d}"
            equipment_list.append(
                {
                    "building_id": bld["building_id"],
                    "device_id": device_id,
                    "device_name": f"{bld['name']}-{dname}",
                    "device_type": dtype,
                    "rated_power_kw": power,
                }
            )

    # Generate hourly energy records concentrated in the previous N days.
    for bld in BUILDINGS:
        btype = bld["building_type"]
        area = bld["area"]
        baseline = ELECTRICITY_BASELINES[btype] * (area / 1000)

        ts = start_hour
        while ts <= end_hour:
            day_of_year = ts.timetuple().tm_yday
            weekday = ts.weekday()
            hour = ts.hour

            outdoor_base = _seasonal_temp(day_of_year)
            wd_factor = _weekday_factor(weekday, btype)
            hr_factor = _hour_factor(hour, btype)

            # Outdoor conditions
            outdoor_temp = outdoor_base + 3 * math.sin(
                2 * math.pi * (hour - 6) / 24
            ) + np.random.normal(0, 1.5)
            outdoor_humidity = max(
                20,
                min(95, 60 + 15 * math.sin(2 * math.pi * (hour - 3) / 24)
                    + np.random.normal(0, 8)),
            )

            # Electricity
            noise = np.random.normal(1.0, 0.08)
            electricity = baseline * hr_factor * wd_factor * noise

            # HVAC depends on outdoor temp
            temp_diff = abs(outdoor_temp - 22)
            hvac_factor = max(0.1, min(1.5, temp_diff / 20))
            hvac_kwh = electricity * 0.45 * hvac_factor * np.random.normal(1, 0.05)

            # HVAC temps
            if outdoor_temp > 22:  # Cooling mode
                supply_temp = 7 + np.random.normal(0, 0.5)
                return_temp = 12 + np.random.normal(0, 0.5)
            else:  # Heating mode
                supply_temp = 45 + np.random.normal(0, 1)
                return_temp = 38 + np.random.normal(0, 1)

            flow_rate = max(5, 30 + 20 * hvac_factor + np.random.normal(0, 3))

            # Water
            water = (area / 1000) * 0.3 * hr_factor * wd_factor * np.random.normal(1, 0.1)

            # Occupancy
            if btype in ("office", "school"):
                occ = 5.0 * hr_factor * wd_factor + np.random.normal(0, 0.5)
            elif btype == "hospital":
                occ = 3.0 + np.random.normal(0, 0.3)
            elif btype == "commercial":
                occ = 8.0 * hr_factor * wd_factor + np.random.normal(0, 1)
            else:
                occ = 2.0 + np.random.normal(0, 0.3)
            occ = max(0, occ)

            # Inject obvious but DB-valid anomalies for testing.
            is_anomaly = random.random() < anomaly_rate
            if is_anomaly:
                anomaly_choice = random.choice([
                    "electricity_spike",
                    "temperature_offset",
                    "flow_loss",
                ])
                if anomaly_choice == "electricity_spike":
                    electricity *= random.uniform(3.0, 6.0)
                    metric_name = "electricity_kwh"
                    metric_value = electricity
                    threshold_value = baseline * 2.0
                    description = "Electricity spike much higher than baseline."
                elif anomaly_choice == "temperature_offset":
                    # Cooling mode should have low supply temp; this introduces clear drift.
                    supply_temp += random.uniform(10, 18)
                    metric_name = "hvac_supply_temp"
                    metric_value = supply_temp
                    threshold_value = 18.0
                    description = "HVAC supply temperature abnormally high."
                else:
                    flow_rate = max(0, flow_rate * random.uniform(0.03, 0.12))
                    hvac_kwh *= random.uniform(1.4, 2.0)
                    metric_name = "hvac_flow_rate"
                    metric_value = flow_rate
                    threshold_value = 5.0
                    description = "HVAC flow rate collapse with elevated HVAC load."

                severity = random.choice(["high", "critical"])
                anomaly_events.append(
                    {
                        "building_id": bld["building_id"],
                        "device_id": "",
                        "timestamp": ts.isoformat(),
                        "anomaly_type": anomaly_choice,
                        "severity": severity,
                        "metric_name": metric_name,
                        "metric_value": round(float(metric_value), 3),
                        "threshold_value": round(float(threshold_value), 3),
                        "description": description,
                        "resolved": False,
                        "detection_method": "synthetic_rule",
                    }
                )

            record = {
                "building_id": bld["building_id"],
                "timestamp": ts.isoformat(),
                "electricity_kwh": round(max(0, electricity), 2),
                "water_m3": round(max(0, water), 3),
                "gas_m3": round(max(0, (area / 1000) * 0.1 * hvac_factor * np.random.normal(1, 0.05)), 3),
                "hvac_kwh": round(max(0, hvac_kwh), 2),
                "hvac_supply_temp": round(supply_temp, 1),
                "hvac_return_temp": round(return_temp, 1),
                "hvac_flow_rate": round(max(0, flow_rate), 1),
                "outdoor_temp": round(outdoor_temp, 1),
                "outdoor_humidity": round(outdoor_humidity, 1),
                "occupancy_density": round(occ, 1),
            }
            energy_records.append(record)

            ts += timedelta(hours=1)

    # Generate equipment status (daily snapshots)
    for equip in equipment_list:
        for day in range(days + 1):
            dt = (start_hour + timedelta(days=day)).replace(
                minute=0,
                second=0,
                microsecond=0,
            )
            ts = dt.replace(hour=12, minute=0, second=0)

            is_abnormal = random.random() < 0.03
            status = "abnormal" if is_abnormal else "normal"
            error_code = f"E{random.randint(100,999)}" if is_abnormal else None

            equipment_status_records.append(
                {
                    "device_id": equip["device_id"],
                    "timestamp": ts.isoformat(),
                    "status": status,
                    "power_consumption_kw": round(
                        equip["rated_power_kw"] * np.random.uniform(0.3, 0.95), 1
                    ),
                    "runtime_hours": round(day * 8 + np.random.uniform(0, 8), 1),
                    "error_code": error_code,
                    "notes": "" if not is_abnormal else "Synthetic abnormal event for testing",
                }
            )

    return {
        "buildings": BUILDINGS,
        "energy_records": energy_records,
        "equipment": equipment_list,
        "equipment_status": equipment_status_records,
        "anomaly_events": anomaly_events,
    }


def _save_csv(filepath: Path, records: list[dict]):
    if not records:
        return

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)


def _save_csv_with_fields(filepath: Path, records: list[dict], fieldnames: list[str]):
    if not records:
        return

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            writer.writerow({key: rec.get(key) for key in fieldnames})


def _save_json(filepath: Path, payload: dict):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic building energy CSV files for manual import."
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Generate data distributed in the previous N days (default: 7)",
    )
    parser.add_argument(
        "--anomaly-rate",
        type=float,
        default=0.05,
        help="Probability of hourly record anomaly injection (default: 0.05)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible synthetic data (default: 42)",
    )
    args = parser.parse_args()

    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    print("Generating synthetic CSV data for manual import...")
    data = generate_data(days=args.days, anomaly_rate=args.anomaly_rate, seed=args.seed)

    print(f"  Buildings: {len(data['buildings'])}")
    print(f"  Energy records: {len(data['energy_records'])}")
    print(f"  Equipment: {len(data['equipment'])}")
    print(f"  Equipment status: {len(data['equipment_status'])}")

    for key, records in data.items():
        filepath = data_dir / f"{key}.csv"
        _save_csv(filepath, records)
        print(f"  Saved {filepath}")

    # Single-file bundle for one-shot sharing/import workflows.
    bundle_json = data_dir / "dataset_bundle.json"
    _save_json(bundle_json, data)
    print(f"  Saved {bundle_json} (single-file bundle)")

    # Import-ready files for the two import endpoints:
    # 1) /api/v1/import/upload: CSV with canonical header order.
    upload_csv = data_dir / "energy_records_import.csv"
    _save_csv_with_fields(upload_csv, data["energy_records"], ENERGY_IMPORT_FIELDS)
    print(f"  Saved {upload_csv} (for POST /api/v1/import/upload)")

    # 2) /api/v1/import/energy: JSON request body with records list.
    import_payload = {
        "records": [
            {field: rec.get(field) for field in ENERGY_IMPORT_FIELDS}
            for rec in data["energy_records"]
        ],
        "validate": True,
        "on_conflict": "skip",
    }
    import_json = data_dir / "energy_import_request.json"
    _save_json(import_json, import_payload)
    print(f"  Saved {import_json} (for POST /api/v1/import/energy)")

    print("Done. You can manually import these CSV files into database tables.")


if __name__ == "__main__":
    main()
