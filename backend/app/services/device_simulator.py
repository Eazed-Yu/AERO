"""
Device simulator — generates realistic synthetic HVAC device records.

Extracted from backend/scripts/generate_data.py for runtime use by import_service.
"""

import math
import random
from datetime import datetime, timedelta

import numpy as np


# ── Environment helpers ──

def _seasonal_temp(day_of_year: int) -> float:
    return 14 + 18 * math.sin(2 * math.pi * (day_of_year - 100) / 365)


def _hour_temp_offset(hour: int) -> float:
    return 3 * math.sin(2 * math.pi * (hour - 6) / 24)


def _outdoor_conditions(ts: datetime) -> dict:
    """Compute outdoor temperature, humidity and wet-bulb for a timestamp."""
    doy = ts.timetuple().tm_yday
    hr = ts.hour
    oat_base = _seasonal_temp(doy)
    oat = oat_base + _hour_temp_offset(hr) + np.random.normal(0, 1.5)
    rh = max(20, min(95, 60 + 15 * math.sin(2 * math.pi * (hr - 3) / 24) + np.random.normal(0, 8)))
    wbt = oat - (100 - rh) / 5
    cooling = oat > 22
    heating = oat < 10
    return {"oat": oat, "rh": rh, "wbt": wbt, "cooling": cooling, "heating": heating}


def _hour_factor(hour: int) -> float:
    """Generic occupancy factor (office-like)."""
    return (1.0 + 0.3 * math.sin(math.pi * (hour - 8) / 10)) if 8 <= hour <= 18 else 0.3


# ── Per-device-type generators ──

def _gen_chiller(device_id: str, ts: datetime, hvac_factor: float, oat: float) -> dict:
    load_ratio = min(100, max(20, 50 * hvac_factor + np.random.normal(0, 8)))
    rated_power = 500
    rated_capacity = 800
    power = rated_power * (load_ratio / 100) * np.random.normal(1, 0.03)
    chwst = 7 + np.random.normal(0, 0.3)
    chwrt = chwst + 4 + np.random.normal(0, 0.5)
    chw_flow = max(5, rated_capacity * 0.043 * (load_ratio / 100) * np.random.normal(1, 0.05))
    cwst = chwst + 7 + np.random.normal(0, 0.5)
    cwrt = cwst + 5 + np.random.normal(0, 0.5)
    cooling_cap = chw_flow * 4.186 * abs(chwrt - chwst)
    cop = cooling_cap / power if power > 0 else 0

    # ~5% anomaly: low COP
    if random.random() < 0.05:
        cop *= random.uniform(0.3, 0.5)
        cooling_cap *= 0.4

    return {
        "device_id": device_id, "timestamp": ts.isoformat(),
        "chw_supply_temp": round(chwst, 1), "chw_return_temp": round(chwrt, 1),
        "chw_flow_rate": round(chw_flow, 1),
        "cw_supply_temp": round(cwst, 1), "cw_return_temp": round(cwrt, 1),
        "cw_flow_rate": round(chw_flow * 1.2, 1),
        "power_kw": round(max(0, power), 1),
        "cooling_capacity_kw": round(max(0, cooling_cap), 1),
        "load_ratio": round(load_ratio, 1), "cop": round(max(0, cop), 2),
        "evaporator_approach": round(abs(chwst - 3) + np.random.normal(0, 0.2), 1),
        "condenser_approach": round(abs(cwrt - oat) * 0.3 + np.random.normal(0, 0.3), 1),
        "compressor_rla_pct": round(min(100, load_ratio * 0.9 + np.random.normal(0, 3)), 1),
        "running_status": "running",
    }


def _gen_ahu(device_id: str, ts: datetime, cooling: bool, heating: bool,
             hvac_factor: float, oat: float, hr_f: float) -> dict:
    mode = "cooling" if cooling else ("heating" if heating else "ventilation")
    sat_sp = 14 if cooling else (30 if heating else 22)
    sat = sat_sp + np.random.normal(0, 0.8)
    rat = 24 + np.random.normal(0, 1)
    mat = oat * 0.3 + rat * 0.7 + np.random.normal(0, 0.5)
    fan_speed = min(100, max(20, 50 * hr_f + np.random.normal(0, 5)))
    chw_v = min(100, max(0, 60 * hvac_factor + np.random.normal(0, 8))) if cooling else 0
    hw_v = min(100, max(0, 60 * (1.5 - hvac_factor) + np.random.normal(0, 8))) if heating else 0
    oa_d = min(100, max(10, 30 + np.random.normal(0, 5)))
    rated_power = 50
    rated_capacity = 30000

    # ~5% anomaly: simultaneous heating/cooling
    if random.random() < 0.05 and cooling:
        hw_v = random.uniform(35, 60)

    return {
        "device_id": device_id, "timestamp": ts.isoformat(),
        "supply_air_temp": round(sat, 1), "return_air_temp": round(rat, 1),
        "mixed_air_temp": round(mat, 1), "outdoor_air_temp": round(oat, 1),
        "supply_air_humidity": round(max(30, min(80, 55 + np.random.normal(0, 5))), 1),
        "return_air_humidity": round(max(30, min(70, 50 + np.random.normal(0, 5))), 1),
        "supply_fan_speed": round(fan_speed, 1),
        "supply_fan_power_kw": round(rated_power * fan_speed / 100 * np.random.normal(1, 0.03), 1),
        "supply_air_flow": round(rated_capacity * fan_speed / 100, 0),
        "return_fan_speed": round(max(0, fan_speed - 5 + np.random.normal(0, 2)), 1),
        "chw_valve_pos": round(max(0, min(100, chw_v)), 1),
        "hw_valve_pos": round(max(0, min(100, hw_v)), 1),
        "oa_damper_pos": round(oa_d, 1),
        "ra_damper_pos": round(100 - oa_d, 1),
        "duct_static_pressure": round(max(50, 250 * fan_speed / 100 + np.random.normal(0, 15)), 0),
        "filter_dp": round(max(30, 80 + np.random.normal(0, 10)), 0),
        "operating_mode": mode, "sat_setpoint": sat_sp,
        "dsp_setpoint": 250, "running_status": "running",
    }


def _gen_boiler(device_id: str, ts: datetime, hvac_factor: float) -> dict:
    firing = min(100, max(10, 50 * (1.5 - hvac_factor) + np.random.normal(0, 8)))
    hw_st = 45 + np.random.normal(0, 1)
    hw_rt = 38 + np.random.normal(0, 1)
    rated_power = 50
    rated_capacity = 800
    hw_flow = max(2, rated_capacity * 0.02 * (firing / 100) * np.random.normal(1, 0.05))
    heat_cap = hw_flow * 4.186 * abs(hw_st - hw_rt)
    pw = rated_power * (firing / 100) * np.random.normal(1, 0.03)
    eff = min(98, max(70, 92 + np.random.normal(0, 2)))
    return {
        "device_id": device_id, "timestamp": ts.isoformat(),
        "hw_supply_temp": round(hw_st, 1), "hw_return_temp": round(hw_rt, 1),
        "hw_flow_rate": round(hw_flow, 1), "firing_rate": round(firing, 1),
        "power_kw": round(max(0, pw), 1),
        "fuel_consumption": round(max(0, pw * 0.1), 2),
        "heating_capacity_kw": round(max(0, heat_cap), 1),
        "efficiency": round(eff, 1),
        "flue_gas_temp": round(120 + firing * 0.5 + np.random.normal(0, 5), 0),
        "running_status": "running",
    }


def _gen_vav(device_id: str, ts: datetime, cooling: bool, heating: bool,
             hr_f: float) -> dict:
    clg_sp = 24
    htg_sp = 20
    zone_t = 22 + np.random.normal(0, 1.5)
    mode = "cooling" if zone_t > clg_sp else ("heating" if zone_t < htg_sp else "deadband")
    damper = min(100, max(10, 50 + (zone_t - 22) * 10 + np.random.normal(0, 5)))
    rated_capacity = 2000
    airflow_sp = rated_capacity * (damper / 100)
    occ = "occupied" if hr_f > 0.5 else "unoccupied"

    # ~5% anomaly: zone overheating
    if random.random() < 0.05 and cooling:
        zone_t = clg_sp + random.uniform(3, 6)

    return {
        "device_id": device_id, "timestamp": ts.isoformat(),
        "zone_temp": round(zone_t, 1),
        "zone_temp_setpoint_clg": clg_sp, "zone_temp_setpoint_htg": htg_sp,
        "airflow": round(airflow_sp * np.random.normal(1, 0.05), 0),
        "airflow_setpoint": round(airflow_sp, 0),
        "damper_pos": round(max(0, min(100, damper)), 1),
        "discharge_air_temp": round(14 + np.random.normal(0, 1) if cooling else 28 + np.random.normal(0, 1), 1),
        "reheat_valve_pos": round(max(0, min(100, (htg_sp - zone_t) * 20 + np.random.normal(0, 5))) if heating else 0, 1),
        "zone_co2": round(max(350, 500 + 200 * hr_f + np.random.normal(0, 50)), 0),
        "occupancy_status": occ, "operating_mode": mode,
    }


def _gen_pump(device_id: str, ts: datetime, hvac_factor: float) -> dict:
    rated_power = 30
    rated_capacity = 120
    spd = min(100, max(30, 60 * hvac_factor + np.random.normal(0, 5)))
    pw = rated_power * (spd / 100) ** 3 * np.random.normal(1, 0.03)
    flow = rated_capacity * (spd / 100) * np.random.normal(1, 0.05)
    dp = max(50, 300 * (spd / 100) ** 2 + np.random.normal(0, 20))
    return {
        "device_id": device_id, "timestamp": ts.isoformat(),
        "speed": round(spd, 1), "power_kw": round(max(0, pw), 1),
        "flow_rate": round(max(0, flow), 1),
        "inlet_pressure": round(200 + np.random.normal(0, 10), 0),
        "outlet_pressure": round(200 + dp + np.random.normal(0, 10), 0),
        "differential_pressure": round(dp, 0),
        "running_status": "running",
    }


def _gen_cooling_tower(device_id: str, ts: datetime, hvac_factor: float,
                       wbt: float) -> dict:
    rated_power = 15
    fan_spd = min(100, max(20, 50 * hvac_factor + np.random.normal(0, 8)))
    cw_in = 32 + np.random.normal(0, 1)
    cw_out = cw_in - 5 - np.random.normal(0, 0.5)
    approach = cw_out - wbt
    rng = cw_in - cw_out
    return {
        "device_id": device_id, "timestamp": ts.isoformat(),
        "fan_speed": round(fan_spd, 1),
        "fan_power_kw": round(rated_power * (fan_spd / 100) ** 3, 1),
        "cw_inlet_temp": round(cw_in, 1), "cw_outlet_temp": round(cw_out, 1),
        "wet_bulb_temp": round(wbt, 1),
        "approach": round(max(0, approach), 1), "range": round(max(0, rng), 1),
        "running_status": "running",
    }


# ── Generator dispatch ──

_GENERATORS = {
    "chiller": lambda did, ts, hf, cond: _gen_chiller(did, ts, hf, cond["oat"]),
    "ahu": lambda did, ts, hf, cond: _gen_ahu(
        did, ts, cond["cooling"], cond["heating"], hf, cond["oat"], _hour_factor(ts.hour)),
    "boiler": lambda did, ts, hf, cond: _gen_boiler(did, ts, hf),
    "vav": lambda did, ts, hf, cond: _gen_vav(
        did, ts, cond["cooling"], cond["heating"], _hour_factor(ts.hour)),
    "chw_pump": lambda did, ts, hf, cond: _gen_pump(did, ts, hf),
    "cw_pump": lambda did, ts, hf, cond: _gen_pump(did, ts, hf),
    "hw_pump": lambda did, ts, hf, cond: _gen_pump(did, ts, hf),
    "pump": lambda did, ts, hf, cond: _gen_pump(did, ts, hf),
    "cooling_tower": lambda did, ts, hf, cond: _gen_cooling_tower(did, ts, hf, cond["wbt"]),
}


def simulate_device_records(
    device_type: str,
    device_id: str,
    start_time: datetime,
    end_time: datetime,
    interval_minutes: int = 60,
) -> list[dict]:
    """Generate simulated time-series records for a single device.

    Returns a list of dicts suitable for ORM insertion (each dict has
    device_id, timestamp, and all metric columns).
    """
    gen_fn = _GENERATORS.get(device_type)
    if gen_fn is None:
        raise ValueError(f"Unsupported device type for simulation: {device_type}")

    records: list[dict] = []
    ts = start_time
    while ts <= end_time:
        cond = _outdoor_conditions(ts)
        temp_diff = abs(cond["oat"] - 22)
        hvac_factor = max(0.1, min(1.5, temp_diff / 20))
        rec = gen_fn(device_id, ts, hvac_factor, cond)
        records.append(rec)
        ts += timedelta(minutes=interval_minutes)

    return records
