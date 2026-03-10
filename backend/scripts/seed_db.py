"""
Seed database with generated data (synchronous, using psycopg2).
Usage: uv run python -m scripts.seed_db
"""

import json
from datetime import datetime
from pathlib import Path

import psycopg2
import psycopg2.extras

from app.config import settings

DATA_DIR = Path(__file__).parent.parent / "data"


def seed():
    conn = psycopg2.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        dbname=settings.POSTGRES_DATABASE,
    )
    conn.autocommit = False
    cur = conn.cursor()

    try:
        # Check if data exists
        cur.execute("SELECT COUNT(*) FROM buildings")
        count = cur.fetchone()[0]
        if count > 0:
            print(f"Database already has {count} buildings. Skipping seed.")
            return

        # Load buildings
        with open(DATA_DIR / "buildings.json", encoding="utf-8") as f:
            buildings = json.load(f)
        for b in buildings:
            cur.execute(
                """INSERT INTO buildings (id, building_id, name, building_type, area, address, floors, year_built)
                VALUES (gen_random_uuid(), %(building_id)s, %(name)s, %(building_type)s, %(area)s, %(address)s, %(floors)s, %(year_built)s)""",
                b,
            )
        print(f"  Inserted {len(buildings)} buildings")

        # Load energy records
        with open(DATA_DIR / "energy_records.json", encoding="utf-8") as f:
            energy_data = json.load(f)

        batch_size = 1000
        for i in range(0, len(energy_data), batch_size):
            batch = energy_data[i : i + batch_size]
            psycopg2.extras.execute_batch(
                cur,
                """INSERT INTO energy_records
                (building_id, timestamp, electricity_kwh, water_m3, gas_m3,
                 hvac_kwh, hvac_supply_temp, hvac_return_temp, hvac_flow_rate,
                 outdoor_temp, outdoor_humidity, occupancy_density)
                VALUES (%(building_id)s, %(timestamp)s, %(electricity_kwh)s, %(water_m3)s, %(gas_m3)s,
                 %(hvac_kwh)s, %(hvac_supply_temp)s, %(hvac_return_temp)s, %(hvac_flow_rate)s,
                 %(outdoor_temp)s, %(outdoor_humidity)s, %(occupancy_density)s)""",
                batch,
                page_size=500,
            )
            print(f"  Energy records: {min(i + batch_size, len(energy_data))}/{len(energy_data)}")

        # Load equipment
        with open(DATA_DIR / "equipment.json", encoding="utf-8") as f:
            equip_data = json.load(f)
        for e in equip_data:
            cur.execute(
                """INSERT INTO equipment (id, building_id, device_id, device_name, device_type, rated_power_kw)
                VALUES (gen_random_uuid(), %(building_id)s, %(device_id)s, %(device_name)s, %(device_type)s, %(rated_power_kw)s)""",
                e,
            )
        print(f"  Inserted {len(equip_data)} equipment")

        # Load equipment status
        with open(DATA_DIR / "equipment_status.json", encoding="utf-8") as f:
            status_data = json.load(f)
        for i in range(0, len(status_data), batch_size):
            batch = status_data[i : i + batch_size]
            psycopg2.extras.execute_batch(
                cur,
                """INSERT INTO equipment_status
                (device_id, timestamp, status, power_consumption_kw, runtime_hours, error_code)
                VALUES (%(device_id)s, %(timestamp)s, %(status)s, %(power_consumption_kw)s, %(runtime_hours)s, %(error_code)s)""",
                batch,
                page_size=500,
            )
            print(f"  Equipment status: {min(i + batch_size, len(status_data))}/{len(status_data)}")

        conn.commit()
        print("Seed completed!")

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def main():
    if not DATA_DIR.exists():
        print("Data directory not found. Run generate_data.py first.")
        return
    seed()


if __name__ == "__main__":
    main()
