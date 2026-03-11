"""
Generate realistic synthetic HVAC full-chain data and seed into PostgreSQL.

Usage:
  uv run python -m scripts.generate_data --days 30 --seed 42
  uv run python -m scripts.generate_data --days 7 --anomaly-rate 0.08 --json-only
"""

import argparse
import csv
import json
import math
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import psycopg2
import psycopg2.extras

from app.config import settings

# ───────── Region definitions ─────────
REGIONS = [
    {
        "region_id": "REG-JN",
        "name": "济南片区",
        "description": "济南市辖区内建筑群",
        "address": "山东省济南市",
    },
    {
        "region_id": "REG-LY",
        "name": "临沂片区",
        "description": "临沂市辖区内建筑群",
        "address": "山东省临沂市",
    },
    {
        "region_id": "REG-WF",
        "name": "潍坊片区",
        "description": "潍坊市辖区内建筑群",
        "address": "山东省潍坊市",
    },
]

# ───────── Building definitions ─────────
BUILDINGS = [
    {
        "building_id": "BLD-001", "region_id": "REG-JN",
        "name": "绿地办公大厦", "building_type": "office",
        "area": 15000, "address": "济南市历下区经十路88号", "floors": 20, "year_built": 2018,
        "climate_zone": "夏热冬冷", "cooling_area": 12000,
        "design_cooling_load": 1800, "design_heating_load": 1200,
    },
    {
        "building_id": "BLD-002", "region_id": "REG-JN",
        "name": "中央商业广场", "building_type": "commercial",
        "area": 25000, "address": "济南市市中区泉城路168号", "floors": 6, "year_built": 2015,
        "climate_zone": "夏热冬冷", "cooling_area": 22000,
        "design_cooling_load": 3200, "design_heating_load": 2000,
    },
    {
        "building_id": "BLD-003", "region_id": "REG-LY",
        "name": "滨河花园小区", "building_type": "residential",
        "area": 8000, "address": "临沂市兰山区滨河大道56号", "floors": 18, "year_built": 2020,
        "climate_zone": "夏热冬冷", "cooling_area": 6000,
        "design_cooling_load": 800, "design_heating_load": 600,
    },
    {
        "building_id": "BLD-004", "region_id": "REG-WF",
        "name": "临朐县人民医院", "building_type": "hospital",
        "area": 20000, "address": "潍坊市临朐县民主路100号", "floors": 12, "year_built": 2012,
        "climate_zone": "夏热冬冷", "cooling_area": 16000,
        "design_cooling_load": 2400, "design_heating_load": 1800,
    },
    {
        "building_id": "BLD-005", "region_id": "REG-LY",
        "name": "临沂大学教学楼A", "building_type": "school",
        "area": 5000, "address": "临沂市兰山区双岭路中段", "floors": 5, "year_built": 2010,
        "climate_zone": "夏热冬冷", "cooling_area": 4000,
        "design_cooling_load": 600, "design_heating_load": 400,
    },
]

# ───────── Equipment templates per building type ─────────
EQUIPMENT_TEMPLATES = {
    "office": [
        ("chiller", "cooling_plant", "离心式冷水机组", "开利", "30XA-0802", 500, 800, 5.5),
        ("chw_pump", "cooling_plant", "冷冻水泵", "格兰富", "CR-64-3", 30, 120, None),
        ("cw_pump", "cooling_plant", "冷却水泵", "格兰富", "CR-80-4", 37, 150, None),
        ("cooling_tower", "cooling_plant", "横流冷却塔", "良机", "LBC-200", 15, 200, None),
        ("ahu", "air_system", "组合式空调机组-1F", "约克", "YAH-30", 50, 30000, None),
        ("ahu", "air_system", "组合式空调机组-10F", "约克", "YAH-25", 45, 25000, None),
        ("vav", "terminal", "VAV末端-3F-A区", None, None, 0.5, 2000, None),
        ("vav", "terminal", "VAV末端-3F-B区", None, None, 0.5, 2000, None),
        ("boiler", "heating_plant", "燃气热水锅炉", "威能", "WN-800", 50, 800, None),
        ("hw_pump", "heating_plant", "热水循环泵", "格兰富", "CR-40-2", 15, 80, None),
    ],
    "commercial": [
        ("chiller", "cooling_plant", "螺杆式冷水机组-A", "约克", "YVWA-1200", 800, 1200, 5.8),
        ("chiller", "cooling_plant", "螺杆式冷水机组-B", "约克", "YVWA-1200", 800, 1200, 5.8),
        ("chw_pump", "cooling_plant", "冷冻水泵-A", "格兰富", "CR-96-5", 55, 200, None),
        ("cw_pump", "cooling_plant", "冷却水泵-A", "格兰富", "CR-120-4", 75, 280, None),
        ("cooling_tower", "cooling_plant", "横流冷却塔-A", "良机", "LBC-400", 30, 400, None),
        ("ahu", "air_system", "组合式空调机组-B1", "开利", "39CQ-50", 60, 50000, None),
        ("ahu", "air_system", "组合式空调机组-2F", "开利", "39CQ-40", 50, 40000, None),
        ("vav", "terminal", "VAV末端-1F-中庭", None, None, 1.0, 5000, None),
        ("boiler", "heating_plant", "燃气热水锅炉", "威能", "WN-1200", 80, 1200, None),
        ("hw_pump", "heating_plant", "热水循环泵", "格兰富", "CR-50-3", 22, 100, None),
    ],
    "residential": [
        ("boiler", "heating_plant", "燃气供暖锅炉-A", "博世", "GB-500", 35, 500, None),
        ("boiler", "heating_plant", "燃气供暖锅炉-B", "博世", "GB-500", 35, 500, None),
        ("hw_pump", "heating_plant", "热水循环泵", "格兰富", "CR-32-2", 11, 60, None),
    ],
    "hospital": [
        ("chiller", "cooling_plant", "离心式冷水机组-A", "麦克维尔", "WMC-600", 600, 900, 5.2),
        ("chiller", "cooling_plant", "离心式冷水机组-B", "麦克维尔", "WMC-600", 600, 900, 5.2),
        ("chw_pump", "cooling_plant", "冷冻水泵", "格兰富", "CR-80-4", 45, 160, None),
        ("cw_pump", "cooling_plant", "冷却水泵", "格兰富", "CR-96-3", 55, 200, None),
        ("cooling_tower", "cooling_plant", "横流冷却塔", "良机", "LBC-300", 22, 300, None),
        ("ahu", "air_system", "手术室净化空调", "约克", "YAH-40", 80, 40000, None),
        ("ahu", "air_system", "门诊大厅空调", "约克", "YAH-30", 50, 30000, None),
        ("vav", "terminal", "VAV末端-ICU", None, None, 0.8, 3000, None),
        ("boiler", "heating_plant", "蒸汽锅炉", "威索", "WS-1000", 70, 1000, None),
        ("hw_pump", "heating_plant", "热水循环泵", "格兰富", "CR-50-2", 18, 90, None),
    ],
    "school": [
        ("chiller", "cooling_plant", "风冷螺杆机组", "格力", "LSBLGP-300", 300, 450, 3.2),
        ("ahu", "air_system", "教室新风机组", "远大", "YD-20", 30, 20000, None),
        ("vav", "terminal", "VAV末端-阶梯教室", None, None, 0.5, 3000, None),
        ("boiler", "heating_plant", "电热水锅炉", "海尔", "HR-200", 200, 200, None),
        ("hw_pump", "heating_plant", "热水循环泵", "格兰富", "CR-20-1", 7, 40, None),
    ],
}

ELECTRICITY_BASELINES = {
    "office": 8.0, "commercial": 12.0, "residential": 3.0, "hospital": 15.0, "school": 6.0,
}


UPLOAD_COLUMNS: dict[str, list[str]] = {
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
        "timestamp", "zone_temp", "zone_temp_setpoint_clg", "zone_temp_setpoint_htg",
        "airflow", "airflow_setpoint", "damper_pos", "discharge_air_temp",
        "reheat_valve_pos", "zone_co2", "occupancy_status", "operating_mode",
    ],
    "pump": [
        "timestamp", "speed", "power_kw", "flow_rate", "inlet_pressure",
        "outlet_pressure", "differential_pressure", "running_status",
    ],
    "cooling_tower": [
        "timestamp", "fan_speed", "fan_power_kw", "cw_inlet_temp", "cw_outlet_temp",
        "wet_bulb_temp", "approach", "range", "running_status",
    ],
}

# Different file formats for different device types to match demo upload scenarios.
UPLOAD_FILE_FORMAT: dict[str, str] = {
    "chiller": "csv",
    "ahu": "json_records",
    "boiler": "csv",
    "vav": "json_data",
    "pump": "csv",
    "cooling_tower": "json_array",
}


def _hour_factor(hour: int, btype: str) -> float:
    if btype == "office":
        return (1.0 + 0.3 * math.sin(math.pi * (hour - 8) / 10)) if 8 <= hour <= 18 else 0.3
    elif btype == "commercial":
        return (0.8 + 0.4 * math.sin(math.pi * (hour - 10) / 11)) if 10 <= hour <= 21 else 0.2
    elif btype == "residential":
        if 18 <= hour <= 22: return 1.2
        if 6 <= hour <= 8: return 0.8
        if 22 <= hour or hour < 6: return 0.4
        return 0.5
    elif btype == "hospital":
        return 0.8 + 0.2 * math.sin(math.pi * hour / 12)
    elif btype == "school":
        return 1.0 if 7 <= hour <= 17 else 0.2
    return 0.5


def _weekday_factor(weekday: int, btype: str) -> float:
    if btype in ("office", "school"):
        return 1.0 if weekday < 5 else 0.2
    elif btype == "commercial":
        return 1.0 if weekday < 5 else 1.3
    return 1.0


def _seasonal_temp(day_of_year: int) -> float:
    return 14 + 18 * math.sin(2 * math.pi * (day_of_year - 100) / 365)


def _is_cooling_season(outdoor_temp: float) -> bool:
    return outdoor_temp > 22


def _is_heating_season(outdoor_temp: float) -> bool:
    return outdoor_temp < 10


def _current_hour() -> datetime:
    return datetime.now().replace(minute=0, second=0, microsecond=0)


# ═══════════════════════════════════════════════════════════
# Per-device-type record generators
# ═══════════════════════════════════════════════════════════

def _gen_chiller_record(ch, ts, hvac_factor, oat, anomaly_rate, anomaly_events, region_id, building_id):
    load_ratio = min(100, max(20, 50 * hvac_factor + np.random.normal(0, 8)))
    power = ch["rated_power_kw"] * (load_ratio / 100) * np.random.normal(1, 0.03)
    chwst = 7 + np.random.normal(0, 0.3)
    chwrt = chwst + 4 + np.random.normal(0, 0.5)
    chw_flow = max(5, ch["rated_capacity"] * 0.043 * (load_ratio / 100) * np.random.normal(1, 0.05))
    cwst = chwst + 7 + np.random.normal(0, 0.5)
    cwrt = cwst + 5 + np.random.normal(0, 0.5)
    cooling_cap = chw_flow * 4.186 * abs(chwrt - chwst)
    cop = cooling_cap / power if power > 0 else 0

    if random.random() < anomaly_rate * 0.5:
        cop *= random.uniform(0.3, 0.5)
        cooling_cap *= 0.4
        anomaly_events.append({
            "region_id": region_id, "building_id": building_id,
            "device_id": ch["device_id"],
            "timestamp": ts.isoformat(), "anomaly_type": "low_cop",
            "severity": "high", "metric_name": "cop",
            "metric_value": round(cop, 2), "threshold_value": 2.0,
            "description": f"冷机 {ch['device_id']} COP异常偏低",
            "resolved": False, "detection_method": "synthetic_rule",
            "equipment_type": "chiller", "fault_code": "CH-COP-LOW",
            "recommended_action": "检查冷冻水/冷却水流量及温差",
        })

    return {
        "device_id": ch["device_id"], "timestamp": ts.isoformat(),
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


def _gen_ahu_record(ahu, ts, cooling, heating, hvac_factor, oat, hr_f, anomaly_rate, anomaly_events, region_id, building_id):
    mode = "cooling" if cooling else ("heating" if heating else "ventilation")
    sat_sp = 14 if cooling else (30 if heating else 22)
    sat = sat_sp + np.random.normal(0, 0.8)
    rat = 24 + np.random.normal(0, 1)
    mat = oat * 0.3 + rat * 0.7 + np.random.normal(0, 0.5)
    fan_speed = min(100, max(20, 50 * hr_f + np.random.normal(0, 5)))
    chw_v = min(100, max(0, 60 * hvac_factor + np.random.normal(0, 8))) if cooling else 0
    hw_v = min(100, max(0, 60 * (1.5 - hvac_factor) + np.random.normal(0, 8))) if heating else 0
    oa_d = min(100, max(10, 30 + np.random.normal(0, 5)))

    if random.random() < anomaly_rate * 0.3 and cooling:
        hw_v = random.uniform(35, 60)
        anomaly_events.append({
            "region_id": region_id, "building_id": building_id,
            "device_id": ahu["device_id"],
            "timestamp": ts.isoformat(), "anomaly_type": "simultaneous_clg_htg",
            "severity": "high", "metric_name": "chw_valve_pos",
            "metric_value": round(chw_v, 1), "threshold_value": 30,
            "description": f"AHU {ahu['device_id']} 冷热水阀同时开启",
            "resolved": False, "detection_method": "synthetic_rule",
            "equipment_type": "ahu", "fault_code": "AHU-SIM-CLG-HTG",
            "recommended_action": "检查控制逻辑",
        })

    return {
        "device_id": ahu["device_id"], "timestamp": ts.isoformat(),
        "supply_air_temp": round(sat, 1), "return_air_temp": round(rat, 1),
        "mixed_air_temp": round(mat, 1), "outdoor_air_temp": round(oat, 1),
        "supply_air_humidity": round(max(30, min(80, 55 + np.random.normal(0, 5))), 1),
        "return_air_humidity": round(max(30, min(70, 50 + np.random.normal(0, 5))), 1),
        "supply_fan_speed": round(fan_speed, 1),
        "supply_fan_power_kw": round(ahu["rated_power_kw"] * fan_speed / 100 * np.random.normal(1, 0.03), 1),
        "supply_air_flow": round(ahu["rated_capacity"] * fan_speed / 100, 0),
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


def _gen_boiler_record(bl, ts, hvac_factor):
    firing = min(100, max(10, 50 * (1.5 - hvac_factor) + np.random.normal(0, 8)))
    hw_st = 45 + np.random.normal(0, 1)
    hw_rt = 38 + np.random.normal(0, 1)
    hw_flow = max(2, bl["rated_capacity"] * 0.02 * (firing / 100) * np.random.normal(1, 0.05))
    heat_cap = hw_flow * 4.186 * abs(hw_st - hw_rt)
    pw = bl["rated_power_kw"] * (firing / 100) * np.random.normal(1, 0.03)
    eff = min(98, max(70, 92 + np.random.normal(0, 2)))
    return {
        "device_id": bl["device_id"], "timestamp": ts.isoformat(),
        "hw_supply_temp": round(hw_st, 1), "hw_return_temp": round(hw_rt, 1),
        "hw_flow_rate": round(hw_flow, 1), "firing_rate": round(firing, 1),
        "power_kw": round(max(0, pw), 1),
        "fuel_consumption": round(max(0, pw * 0.1), 2),
        "heating_capacity_kw": round(max(0, heat_cap), 1),
        "efficiency": round(eff, 1),
        "flue_gas_temp": round(120 + firing * 0.5 + np.random.normal(0, 5), 0),
        "running_status": "running",
    }


def _gen_vav_record(vav, ts, cooling, heating, hr_f, anomaly_rate, anomaly_events, region_id, building_id):
    clg_sp = 24
    htg_sp = 20
    zone_t = 22 + np.random.normal(0, 1.5)
    mode = "cooling" if zone_t > clg_sp else ("heating" if zone_t < htg_sp else "deadband")
    damper = min(100, max(10, 50 + (zone_t - 22) * 10 + np.random.normal(0, 5)))
    airflow_sp = vav["rated_capacity"] * (damper / 100)
    occ = "occupied" if hr_f > 0.5 else "unoccupied"

    if random.random() < anomaly_rate * 0.3 and cooling:
        zone_t = clg_sp + random.uniform(3, 6)
        anomaly_events.append({
            "region_id": region_id, "building_id": building_id,
            "device_id": vav["device_id"],
            "timestamp": ts.isoformat(), "anomaly_type": "zone_overheating",
            "severity": "medium", "metric_name": "zone_temp",
            "metric_value": round(zone_t, 1), "threshold_value": clg_sp,
            "description": f"VAV {vav['device_id']} 区域过热",
            "resolved": False, "detection_method": "synthetic_rule",
            "equipment_type": "vav", "fault_code": "VAV-ZONE-HOT",
            "recommended_action": "检查风阀及上游AHU送风温度",
        })

    return {
        "device_id": vav["device_id"], "timestamp": ts.isoformat(),
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


def _gen_pump_record(pm, ts, hvac_factor):
    spd = min(100, max(30, 60 * hvac_factor + np.random.normal(0, 5)))
    pw = pm["rated_power_kw"] * (spd / 100) ** 3 * np.random.normal(1, 0.03)
    flow = pm["rated_capacity"] * (spd / 100) * np.random.normal(1, 0.05)
    dp = max(50, 300 * (spd / 100) ** 2 + np.random.normal(0, 20))
    return {
        "device_id": pm["device_id"], "timestamp": ts.isoformat(),
        "speed": round(spd, 1), "power_kw": round(max(0, pw), 1),
        "flow_rate": round(max(0, flow), 1),
        "inlet_pressure": round(200 + np.random.normal(0, 10), 0),
        "outlet_pressure": round(200 + dp + np.random.normal(0, 10), 0),
        "differential_pressure": round(dp, 0),
        "running_status": "running",
    }


def _gen_cooling_tower_record(ct, ts, hvac_factor, wbt):
    fan_spd = min(100, max(20, 50 * hvac_factor + np.random.normal(0, 8)))
    cw_in = 32 + np.random.normal(0, 1)
    cw_out = cw_in - 5 - np.random.normal(0, 0.5)
    approach = cw_out - wbt
    rng = cw_in - cw_out
    return {
        "device_id": ct["device_id"], "timestamp": ts.isoformat(),
        "fan_speed": round(fan_spd, 1),
        "fan_power_kw": round(ct["rated_power_kw"] * (fan_spd / 100) ** 3, 1),
        "cw_inlet_temp": round(cw_in, 1), "cw_outlet_temp": round(cw_out, 1),
        "wet_bulb_temp": round(wbt, 1),
        "approach": round(max(0, approach), 1), "range": round(max(0, rng), 1),
        "running_status": "running",
    }


# ═══════════════════════════════════════════════════════════
# Data generation (pure in-memory, no DB dependency)
# ═══════════════════════════════════════════════════════════

def generate_data(days: int = 7, anomaly_rate: float = 0.05, seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    end_hour = _current_hour()
    start_hour = end_hour - timedelta(days=days)

    weather_records = []
    energy_meters = []
    equipment_list = []
    chiller_records = []
    ahu_records = []
    boiler_records = []
    vav_records = []
    pump_records = []
    cooling_tower_records = []
    anomaly_events = []

    # ── Generate equipment ──
    dev_counter = 0
    building_devices: dict[str, list[dict]] = {b["building_id"]: [] for b in BUILDINGS}

    for bld in BUILDINGS:
        btype = bld["building_type"]
        region_id = bld["region_id"]
        for dtype, stype, dname, mfr, model, power, capacity, cop in EQUIPMENT_TEMPLATES.get(btype, []):
            dev_counter += 1
            device_id = f"DEV-{dev_counter:04d}"
            eq = {
                "region_id": region_id,
                "building_id": bld["building_id"], "device_id": device_id,
                "device_name": f"{bld['name']}-{dname}", "device_type": dtype,
                "system_type": stype, "model": model, "manufacturer": mfr,
                "rated_power_kw": power, "rated_capacity": capacity,
                "rated_cop": cop, "location": f"{bld['name']} 机房",
                "install_date": f"{bld['year_built']}-06-01", "status": "active",
            }
            equipment_list.append(eq)
            building_devices[bld["building_id"]].append(eq)

    # ── Weather data per region ──
    region_weather_cache: dict[str, dict[str, list]] = {}
    for region in REGIONS:
        region_weather_cache[region["region_id"]] = {}

    # ── Hourly data generation ──
    # First, generate weather per region
    region_ids = list({r["region_id"] for r in REGIONS})
    region_hourly_conditions: dict[str, dict[str, dict]] = {rid: {} for rid in region_ids}

    ts = start_hour
    while ts <= end_hour:
        doy = ts.timetuple().tm_yday
        hr = ts.hour
        ts_key = ts.isoformat()

        for rid in region_ids:
            oat_base = _seasonal_temp(doy)
            oat = oat_base + 3 * math.sin(2 * math.pi * (hr - 6) / 24) + np.random.normal(0, 1.5)
            rh = max(20, min(95, 60 + 15 * math.sin(2 * math.pi * (hr - 3) / 24) + np.random.normal(0, 8)))
            wbt = oat - (100 - rh) / 5

            weather_records.append({
                "region_id": rid, "timestamp": ts_key,
                "dry_bulb_temp": round(oat, 1), "wet_bulb_temp": round(wbt, 1),
                "relative_humidity": round(rh, 1),
                "wind_speed": round(max(0, 2 + np.random.normal(0, 1.5)), 1),
                "solar_radiation": round(max(0, 400 * max(0, math.sin(math.pi * (hr - 6) / 12)) + np.random.normal(0, 50)), 0) if 6 <= hr <= 18 else 0,
                "atmospheric_pressure": round(1013 + np.random.normal(0, 3), 1),
            })

            region_hourly_conditions[rid][ts_key] = {
                "oat": oat, "rh": rh, "wbt": wbt,
                "cooling": _is_cooling_season(oat),
                "heating": _is_heating_season(oat),
            }

        ts += timedelta(hours=1)

    # ── Building-level data ──
    for bld in BUILDINGS:
        btype = bld["building_type"]
        area = bld["area"]
        region_id = bld["region_id"]
        baseline = ELECTRICITY_BASELINES[btype] * (area / 1000)
        devices = building_devices[bld["building_id"]]

        chillers = [d for d in devices if d["device_type"] == "chiller"]
        ahus = [d for d in devices if d["device_type"] == "ahu"]
        boilers = [d for d in devices if d["device_type"] == "boiler"]
        vavs = [d for d in devices if d["device_type"] == "vav"]
        chw_pumps = [d for d in devices if d["device_type"] == "chw_pump"]
        cw_pumps = [d for d in devices if d["device_type"] == "cw_pump"]
        hw_pumps = [d for d in devices if d["device_type"] == "hw_pump"]
        towers = [d for d in devices if d["device_type"] == "cooling_tower"]

        ts = start_hour
        while ts <= end_hour:
            wd = ts.weekday()
            hr = ts.hour
            ts_key = ts.isoformat()
            wd_f = _weekday_factor(wd, btype)
            hr_f = _hour_factor(hr, btype)

            cond = region_hourly_conditions[region_id][ts_key]
            oat = cond["oat"]
            wbt = cond["wbt"]
            cooling = cond["cooling"]
            heating = cond["heating"]

            temp_diff = abs(oat - 22)
            hvac_factor = max(0.1, min(1.5, temp_diff / 20))

            # Energy meter
            noise = np.random.normal(1.0, 0.08)
            total_elec = baseline * hr_f * wd_f * noise
            hvac_elec = total_elec * 0.45 * hvac_factor * np.random.normal(1, 0.05)
            lighting = total_elec * 0.25 * np.random.normal(1, 0.03)
            plug = total_elec * 0.20 * np.random.normal(1, 0.04)
            gas = max(0, (area / 1000) * 0.1 * (1.5 if heating else 0.1) * np.random.normal(1, 0.05))
            water = max(0, (area / 1000) * 0.3 * hr_f * wd_f * np.random.normal(1, 0.1))

            is_energy_anomaly = random.random() < anomaly_rate * 0.3
            if is_energy_anomaly:
                total_elec *= random.uniform(3.0, 5.0)

            energy_meters.append({
                "region_id": region_id,
                "building_id": bld["building_id"], "timestamp": ts_key,
                "total_electricity_kwh": round(max(0, total_elec), 2),
                "hvac_electricity_kwh": round(max(0, hvac_elec), 2),
                "lighting_kwh": round(max(0, lighting), 2),
                "plug_load_kwh": round(max(0, plug), 2),
                "peak_demand_kw": round(max(0, total_elec * 1.2), 1),
                "gas_m3": round(max(0, gas), 3),
                "water_m3": round(max(0, water), 3),
                "cooling_kwh": round(max(0, hvac_elec * 3.5 if cooling else 0), 2),
                "heating_kwh": round(max(0, hvac_elec * 0.85 if heating else 0), 2),
            })

            # Chiller records (cooling season only)
            if cooling and hr_f > 0.3:
                for ch in chillers:
                    chiller_records.append(_gen_chiller_record(
                        ch, ts, hvac_factor, oat, anomaly_rate, anomaly_events, region_id, bld["building_id"]))

            # AHU records
            if hr_f > 0.2:
                for ahu in ahus:
                    ahu_records.append(_gen_ahu_record(
                        ahu, ts, cooling, heating, hvac_factor, oat, hr_f, anomaly_rate, anomaly_events, region_id, bld["building_id"]))

            # Boiler records (heating season)
            if heating and hr_f > 0.3:
                for bl in boilers:
                    boiler_records.append(_gen_boiler_record(bl, ts, hvac_factor))

            # VAV records (working hours)
            if hr_f > 0.3:
                for vav in vavs:
                    vav_records.append(_gen_vav_record(
                        vav, ts, cooling, heating, hr_f, anomaly_rate, anomaly_events, region_id, bld["building_id"]))

            # Pump records
            all_pumps = chw_pumps + cw_pumps + hw_pumps
            for pm in all_pumps:
                is_chw = pm["device_type"] == "chw_pump"
                is_cw = pm["device_type"] == "cw_pump"
                should_run = (cooling and (is_chw or is_cw)) or (heating and pm["device_type"] == "hw_pump")
                if should_run and hr_f > 0.3:
                    pump_records.append(_gen_pump_record(pm, ts, hvac_factor))

            # Cooling tower records
            if cooling and hr_f > 0.3:
                for ct in towers:
                    cooling_tower_records.append(_gen_cooling_tower_record(ct, ts, hvac_factor, wbt))

            ts += timedelta(hours=1)

    return {
        "regions": REGIONS,
        "buildings": BUILDINGS,
        "weather_records": weather_records,
        "energy_meters": energy_meters,
        "equipment": equipment_list,
        "chiller_records": chiller_records,
        "ahu_records": ahu_records,
        "boiler_records": boiler_records,
        "vav_records": vav_records,
        "pump_records": pump_records,
        "cooling_tower_records": cooling_tower_records,
        "anomaly_events": anomaly_events,
    }


def _canonical_device_type(device_type: str) -> str:
    if device_type in ("chw_pump", "cw_pump", "hw_pump"):
        return "pump"
    return device_type


def _device_records_key(device_type: str) -> str | None:
    mapping = {
        "chiller": "chiller_records",
        "ahu": "ahu_records",
        "boiler": "boiler_records",
        "vav": "vav_records",
        "pump": "pump_records",
        "cooling_tower": "cooling_tower_records",
    }
    return mapping.get(_canonical_device_type(device_type))


def _project_upload_row(device_type: str, row: dict) -> dict:
    cols = UPLOAD_COLUMNS[_canonical_device_type(device_type)]
    return {k: row.get(k) for k in cols}


def export_upload_files(
    data: dict,
    output_dir: Path,
    days: int,
):
    output_dir.mkdir(parents=True, exist_ok=True)

    equipment = data.get("equipment", [])
    anomaly_events = data.get("anomaly_events", [])

    anomaly_count_by_device: dict[str, int] = {}
    for event in anomaly_events:
        did = event.get("device_id")
        if not did:
            continue
        anomaly_count_by_device[did] = anomaly_count_by_device.get(did, 0) + 1

    generated_files = []
    for eq in equipment:
        device_id = eq["device_id"]
        device_type = eq["device_type"]
        canonical_type = _canonical_device_type(device_type)
        records_key = _device_records_key(device_type)
        if not records_key:
            continue

        raw_records = [
            r for r in data.get(records_key, [])
            if r.get("device_id") == device_id
        ]
        upload_rows = [_project_upload_row(device_type, r) for r in raw_records]
        fmt = UPLOAD_FILE_FORMAT[canonical_type]

        if fmt == "csv":
            filename = f"{device_id}_{canonical_type}.csv"
            file_path = output_dir / filename
            cols = UPLOAD_COLUMNS[canonical_type]
            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=cols)
                writer.writeheader()
                writer.writerows(upload_rows)
        elif fmt == "json_records":
            filename = f"{device_id}_{canonical_type}.json"
            file_path = output_dir / filename
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({"records": upload_rows}, f, ensure_ascii=False, indent=2)
        elif fmt == "json_data":
            filename = f"{device_id}_{canonical_type}.json"
            file_path = output_dir / filename
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({"data": upload_rows}, f, ensure_ascii=False, indent=2)
        else:
            filename = f"{device_id}_{canonical_type}.json"
            file_path = output_dir / filename
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(upload_rows, f, ensure_ascii=False, indent=2)

        generated_files.append({
            "device_id": device_id,
            "device_type": device_type,
            "canonical_device_type": canonical_type,
            "filename": filename,
            "format": fmt,
            "record_count": len(upload_rows),
            "anomaly_count": anomaly_count_by_device.get(device_id, 0),
            "upload_endpoint": f"/api/v1/import/device/{device_id}/upload",
        })

    manifest = {
        "generated_at": datetime.now().isoformat(),
        "days": days,
        "note": "Each file can be uploaded in UI by selecting the corresponding device_id.",
        "total_files": len(generated_files),
        "total_anomalies": len(anomaly_events),
        "files": generated_files,
    }
    manifest_path = output_dir / "upload_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    return generated_files, manifest_path


def _generate_type_samples(days: int, anomaly_rate: float, seed: int) -> dict[str, list[dict]]:
    random.seed(seed)
    np.random.seed(seed)

    end_hour = _current_hour()
    start_hour = end_hour - timedelta(days=days)

    rows: dict[str, list[dict]] = {
        "chiller": [],
        "ahu": [],
        "boiler": [],
        "vav": [],
        "pump": [],
        "cooling_tower": [],
    }

    ts = start_hour
    while ts <= end_hour:
        hr = ts.hour
        ts_key = ts.isoformat()
        daytime = 8 <= hr <= 20
        hvac_factor = 0.6 + 0.4 * math.sin(2 * math.pi * (hr - 8) / 24)
        hvac_factor = max(0.2, min(1.2, hvac_factor + np.random.normal(0, 0.05)))

        # chiller
        if daytime:
            load_ratio = min(100, max(25, 45 + 35 * hvac_factor + np.random.normal(0, 6)))
            power_kw = max(20, 8 + load_ratio * 0.9 + np.random.normal(0, 2))
            cooling_kw = max(50, power_kw * (4.2 + np.random.normal(0, 0.3)))
            cop = cooling_kw / power_kw
            if random.random() < anomaly_rate * 0.5:
                cop = max(1.2, cop * random.uniform(0.45, 0.65))
                cooling_kw = power_kw * cop

            rows["chiller"].append({
                "timestamp": ts_key,
                "chw_supply_temp": round(7 + np.random.normal(0, 0.3), 1),
                "chw_return_temp": round(12 + np.random.normal(0, 0.5), 1),
                "chw_flow_rate": round(max(20, 60 + 35 * hvac_factor + np.random.normal(0, 4)), 1),
                "cw_supply_temp": round(30 + np.random.normal(0, 0.7), 1),
                "cw_return_temp": round(35 + np.random.normal(0, 0.7), 1),
                "cw_flow_rate": round(max(30, 85 + 40 * hvac_factor + np.random.normal(0, 5)), 1),
                "power_kw": round(power_kw, 1),
                "cooling_capacity_kw": round(cooling_kw, 1),
                "load_ratio": round(load_ratio, 1),
                "cop": round(cop, 2),
                "evaporator_approach": round(max(1, 2.5 + np.random.normal(0, 0.3)), 1),
                "condenser_approach": round(max(1, 3.0 + np.random.normal(0, 0.4)), 1),
                "compressor_rla_pct": round(min(100, load_ratio * 0.92 + np.random.normal(0, 3)), 1),
                "running_status": "running",
            })

        # ahu
        sat_sp = 14 if daytime else 18
        sat = sat_sp + np.random.normal(0, 0.8)
        chw_valve = max(0, min(100, 35 + 40 * hvac_factor + np.random.normal(0, 8)))
        hw_valve = max(0, min(100, 20 + np.random.normal(0, 6))) if not daytime else 0
        if random.random() < anomaly_rate * 0.25 and daytime:
            hw_valve = random.uniform(35, 60)

        rows["ahu"].append({
            "timestamp": ts_key,
            "supply_air_temp": round(sat, 1),
            "return_air_temp": round(24 + np.random.normal(0, 1.2), 1),
            "mixed_air_temp": round(20 + np.random.normal(0, 1.4), 1),
            "outdoor_air_temp": round(12 + 8 * math.sin(2 * math.pi * (hr - 6) / 24) + np.random.normal(0, 1), 1),
            "supply_air_humidity": round(max(30, min(80, 52 + np.random.normal(0, 6))), 1),
            "return_air_humidity": round(max(30, min(75, 48 + np.random.normal(0, 6))), 1),
            "supply_fan_speed": round(max(20, min(100, 35 + 50 * hvac_factor + np.random.normal(0, 5))), 1),
            "supply_fan_power_kw": round(max(2, 8 + 8 * hvac_factor + np.random.normal(0, 1.2)), 1),
            "supply_air_flow": round(max(3000, 12000 + 7000 * hvac_factor + np.random.normal(0, 800)), 0),
            "return_fan_speed": round(max(10, min(100, 30 + 46 * hvac_factor + np.random.normal(0, 5))), 1),
            "chw_valve_pos": round(chw_valve, 1),
            "hw_valve_pos": round(hw_valve, 1),
            "oa_damper_pos": round(max(10, min(100, 25 + np.random.normal(0, 5))), 1),
            "ra_damper_pos": round(max(0, min(90, 75 + np.random.normal(0, 5))), 1),
            "duct_static_pressure": round(max(60, 180 + 80 * hvac_factor + np.random.normal(0, 20)), 0),
            "filter_dp": round(max(30, 75 + np.random.normal(0, 10)), 0),
            "operating_mode": "cooling" if daytime else "ventilation",
            "sat_setpoint": sat_sp,
            "dsp_setpoint": 250,
            "running_status": "running",
        })

        # boiler
        firing = max(5, min(100, 30 + (1.2 - hvac_factor) * 40 + np.random.normal(0, 8)))
        eff = max(70, min(97, 91 + np.random.normal(0, 2)))
        rows["boiler"].append({
            "timestamp": ts_key,
            "hw_supply_temp": round(48 + np.random.normal(0, 1.5), 1),
            "hw_return_temp": round(40 + np.random.normal(0, 1.5), 1),
            "hw_flow_rate": round(max(3, 20 + firing * 0.2 + np.random.normal(0, 1.8)), 1),
            "firing_rate": round(firing, 1),
            "power_kw": round(max(8, 12 + firing * 0.45 + np.random.normal(0, 2)), 1),
            "fuel_consumption": round(max(0.4, 1.0 + firing * 0.04 + np.random.normal(0, 0.2)), 2),
            "heating_capacity_kw": round(max(15, 30 + firing * 0.9 + np.random.normal(0, 4)), 1),
            "efficiency": round(eff, 1),
            "flue_gas_temp": round(max(90, 120 + firing * 0.4 + np.random.normal(0, 6)), 0),
            "running_status": "running",
        })

        # vav
        zone_temp = 23 + np.random.normal(0, 1.0)
        if random.random() < anomaly_rate * 0.3:
            zone_temp += random.uniform(2.5, 4.5)
        rows["vav"].append({
            "timestamp": ts_key,
            "zone_temp": round(zone_temp, 1),
            "zone_temp_setpoint_clg": 24,
            "zone_temp_setpoint_htg": 20,
            "airflow": round(max(300, 1200 + 600 * hvac_factor + np.random.normal(0, 120)), 0),
            "airflow_setpoint": round(max(300, 1300 + 550 * hvac_factor), 0),
            "damper_pos": round(max(5, min(100, 40 + 25 * hvac_factor + np.random.normal(0, 6))), 1),
            "discharge_air_temp": round(15 + np.random.normal(0, 1.2), 1),
            "reheat_valve_pos": round(max(0, min(100, (20 - zone_temp) * 18 + np.random.normal(0, 4))), 1),
            "zone_co2": round(max(350, 500 + 220 * hvac_factor + np.random.normal(0, 60)), 0),
            "occupancy_status": "occupied" if daytime else "unoccupied",
            "operating_mode": "cooling" if zone_temp > 24 else ("heating" if zone_temp < 20 else "deadband"),
        })

        # pump
        speed = max(25, min(100, 45 + 45 * hvac_factor + np.random.normal(0, 5)))
        flow = max(10, 60 + speed * 1.3 + np.random.normal(0, 8))
        dp = max(40, 80 + (speed / 100) ** 2 * 260 + np.random.normal(0, 15))
        rows["pump"].append({
            "timestamp": ts_key,
            "speed": round(speed, 1),
            "power_kw": round(max(1, 3 + (speed / 100) ** 3 * 35 + np.random.normal(0, 0.8)), 1),
            "flow_rate": round(flow, 1),
            "inlet_pressure": round(max(120, 180 + np.random.normal(0, 10)), 0),
            "outlet_pressure": round(max(180, 180 + dp + np.random.normal(0, 12)), 0),
            "differential_pressure": round(dp, 0),
            "running_status": "running",
        })

        # cooling tower
        fan_speed = max(20, min(100, 35 + 40 * hvac_factor + np.random.normal(0, 7)))
        cw_in = 31 + np.random.normal(0, 1)
        cw_out = cw_in - 4.5 + np.random.normal(0, 0.6)
        rows["cooling_tower"].append({
            "timestamp": ts_key,
            "fan_speed": round(fan_speed, 1),
            "fan_power_kw": round(max(1, (fan_speed / 100) ** 3 * 25), 1),
            "cw_inlet_temp": round(cw_in, 1),
            "cw_outlet_temp": round(cw_out, 1),
            "wet_bulb_temp": round(22 + np.random.normal(0, 1.2), 1),
            "approach": round(max(1, cw_out - 22 + np.random.normal(0, 0.5)), 1),
            "range": round(max(1, cw_in - cw_out), 1),
            "running_status": "running",
        })

        ts += timedelta(hours=1)

    return rows


def export_upload_files_by_type(
    output_dir: Path,
    days: int,
    anomaly_rate: float,
    seed: int,
):
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = _generate_type_samples(days=days, anomaly_rate=anomaly_rate, seed=seed)

    generated_files = []
    for canonical_type, records in rows.items():
        fmt = UPLOAD_FILE_FORMAT[canonical_type]
        if fmt == "csv":
            filename = f"sample_{canonical_type}.csv"
            file_path = output_dir / filename
            cols = UPLOAD_COLUMNS[canonical_type]
            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=cols)
                writer.writeheader()
                writer.writerows(records)
        elif fmt == "json_records":
            filename = f"sample_{canonical_type}.json"
            file_path = output_dir / filename
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({"records": records}, f, ensure_ascii=False, indent=2)
        elif fmt == "json_data":
            filename = f"sample_{canonical_type}.json"
            file_path = output_dir / filename
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({"data": records}, f, ensure_ascii=False, indent=2)
        else:
            filename = f"sample_{canonical_type}.json"
            file_path = output_dir / filename
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)

        generated_files.append({
            "canonical_device_type": canonical_type,
            "filename": filename,
            "format": fmt,
            "record_count": len(records),
            "upload_hint": f"Upload to any device whose type is {canonical_type} (pump includes chw_pump/cw_pump/hw_pump)",
        })

    manifest = {
        "generated_at": datetime.now().isoformat(),
        "days": days,
        "mode": "by_device_type",
        "note": "Create region/building/device in UI first, then upload matching type file on device upload page.",
        "total_files": len(generated_files),
        "files": generated_files,
    }
    manifest_path = output_dir / "type_upload_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    return generated_files, manifest_path


# ═══════════════════════════════════════════════════════════
# Database seeding (psycopg2 synchronous)
# ═══════════════════════════════════════════════════════════

BATCH_SIZE = 1000


def _connect():
    return psycopg2.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        dbname=settings.POSTGRES_DATABASE,
    )


def _batch_insert(cur, sql: str, rows: list[dict], label: str):
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        psycopg2.extras.execute_batch(cur, sql, batch, page_size=500)
        done = min(i + BATCH_SIZE, len(rows))
        print(f"  {label}: {done}/{len(rows)}")


def seed_database(data: dict, reset: bool = False):
    conn = _connect()
    conn.autocommit = False
    cur = conn.cursor()

    try:
        if reset:
            print("Clearing existing data...")
            for table in [
                "cooling_tower_records", "pump_records", "vav_records",
                "boiler_records", "ahu_records", "chiller_records",
                "anomaly_events", "energy_meters", "weather_records",
                "equipment", "buildings", "regions",
            ]:
                cur.execute(f"DELETE FROM {table}")
            print("  All tables cleared.")

        # Check if regions already exist
        cur.execute("SELECT COUNT(*) FROM regions")
        count = cur.fetchone()[0]
        if count > 0 and not reset:
            print(f"Database already has {count} regions. Use --reset to clear first.")
            return

        # 0. Regions
        for r in data["regions"]:
            cur.execute(
                """INSERT INTO regions
                (id, region_id, name, description, address)
                VALUES (%(id)s, %(region_id)s, %(name)s, %(description)s, %(address)s)""",
                {**r, "id": str(uuid.uuid4())},
            )
        print(f"  regions: {len(data['regions'])}")

        # 1. Buildings
        for b in data["buildings"]:
            cur.execute(
                """INSERT INTO buildings
                (id, building_id, region_id, name, building_type, area, address, floors, year_built,
                 climate_zone, cooling_area, design_cooling_load, design_heating_load)
                VALUES (%(id)s, %(building_id)s, %(region_id)s, %(name)s, %(building_type)s, %(area)s,
                 %(address)s, %(floors)s, %(year_built)s,
                 %(climate_zone)s, %(cooling_area)s, %(design_cooling_load)s, %(design_heating_load)s)""",
                {**b, "id": str(uuid.uuid4())},
            )
        print(f"  buildings: {len(data['buildings'])}")

        # 2. Equipment
        for e in data["equipment"]:
            cur.execute(
                """INSERT INTO equipment
                (id, region_id, building_id, device_id, device_name, device_type, system_type,
                 model, manufacturer, rated_power_kw, rated_capacity, rated_cop,
                 location, install_date, status)
                VALUES (%(id)s, %(region_id)s, %(building_id)s, %(device_id)s, %(device_name)s, %(device_type)s,
                 %(system_type)s, %(model)s, %(manufacturer)s, %(rated_power_kw)s, %(rated_capacity)s,
                 %(rated_cop)s, %(location)s, %(install_date)s, %(status)s)""",
                {**e, "id": str(uuid.uuid4())},
            )
        print(f"  equipment: {len(data['equipment'])}")

        # 3. Weather records (per region)
        _batch_insert(cur,
            """INSERT INTO weather_records
            (region_id, timestamp, dry_bulb_temp, wet_bulb_temp, relative_humidity,
             wind_speed, solar_radiation, atmospheric_pressure)
            VALUES (%(region_id)s, %(timestamp)s, %(dry_bulb_temp)s, %(wet_bulb_temp)s,
             %(relative_humidity)s, %(wind_speed)s, %(solar_radiation)s, %(atmospheric_pressure)s)""",
            data["weather_records"], "weather_records")

        # 4. Energy meters
        _batch_insert(cur,
            """INSERT INTO energy_meters
            (region_id, building_id, timestamp, total_electricity_kwh, hvac_electricity_kwh,
             lighting_kwh, plug_load_kwh, peak_demand_kw, gas_m3, water_m3,
             cooling_kwh, heating_kwh)
            VALUES (%(region_id)s, %(building_id)s, %(timestamp)s, %(total_electricity_kwh)s,
             %(hvac_electricity_kwh)s, %(lighting_kwh)s, %(plug_load_kwh)s,
             %(peak_demand_kw)s, %(gas_m3)s, %(water_m3)s,
             %(cooling_kwh)s, %(heating_kwh)s)""",
            data["energy_meters"], "energy_meters")

        # 5. Chiller records
        _batch_insert(cur,
            """INSERT INTO chiller_records
            (device_id, timestamp, chw_supply_temp, chw_return_temp, chw_flow_rate,
             cw_supply_temp, cw_return_temp, cw_flow_rate, power_kw, cooling_capacity_kw,
             load_ratio, cop, evaporator_approach, condenser_approach,
             compressor_rla_pct, running_status)
            VALUES (%(device_id)s, %(timestamp)s, %(chw_supply_temp)s, %(chw_return_temp)s,
             %(chw_flow_rate)s, %(cw_supply_temp)s, %(cw_return_temp)s, %(cw_flow_rate)s,
             %(power_kw)s, %(cooling_capacity_kw)s, %(load_ratio)s, %(cop)s,
             %(evaporator_approach)s, %(condenser_approach)s,
             %(compressor_rla_pct)s, %(running_status)s)""",
            data["chiller_records"], "chiller_records")

        # 6. AHU records
        _batch_insert(cur,
            """INSERT INTO ahu_records
            (device_id, timestamp, supply_air_temp, return_air_temp, mixed_air_temp,
             outdoor_air_temp, supply_air_humidity, return_air_humidity,
             supply_fan_speed, supply_fan_power_kw, supply_air_flow, return_fan_speed,
             chw_valve_pos, hw_valve_pos, oa_damper_pos, ra_damper_pos,
             duct_static_pressure, filter_dp, operating_mode, sat_setpoint,
             dsp_setpoint, running_status)
            VALUES (%(device_id)s, %(timestamp)s, %(supply_air_temp)s, %(return_air_temp)s,
             %(mixed_air_temp)s, %(outdoor_air_temp)s, %(supply_air_humidity)s,
             %(return_air_humidity)s, %(supply_fan_speed)s, %(supply_fan_power_kw)s,
             %(supply_air_flow)s, %(return_fan_speed)s, %(chw_valve_pos)s, %(hw_valve_pos)s,
             %(oa_damper_pos)s, %(ra_damper_pos)s, %(duct_static_pressure)s, %(filter_dp)s,
             %(operating_mode)s, %(sat_setpoint)s, %(dsp_setpoint)s, %(running_status)s)""",
            data["ahu_records"], "ahu_records")

        # 7. Boiler records
        _batch_insert(cur,
            """INSERT INTO boiler_records
            (device_id, timestamp, hw_supply_temp, hw_return_temp, hw_flow_rate,
             firing_rate, power_kw, fuel_consumption, heating_capacity_kw,
             efficiency, flue_gas_temp, running_status)
            VALUES (%(device_id)s, %(timestamp)s, %(hw_supply_temp)s, %(hw_return_temp)s,
             %(hw_flow_rate)s, %(firing_rate)s, %(power_kw)s, %(fuel_consumption)s,
             %(heating_capacity_kw)s, %(efficiency)s, %(flue_gas_temp)s, %(running_status)s)""",
            data["boiler_records"], "boiler_records")

        # 8. VAV records
        _batch_insert(cur,
            """INSERT INTO vav_records
            (device_id, timestamp, zone_temp, zone_temp_setpoint_clg, zone_temp_setpoint_htg,
             airflow, airflow_setpoint, damper_pos, discharge_air_temp, reheat_valve_pos,
             zone_co2, occupancy_status, operating_mode)
            VALUES (%(device_id)s, %(timestamp)s, %(zone_temp)s, %(zone_temp_setpoint_clg)s,
             %(zone_temp_setpoint_htg)s, %(airflow)s, %(airflow_setpoint)s, %(damper_pos)s,
             %(discharge_air_temp)s, %(reheat_valve_pos)s, %(zone_co2)s,
             %(occupancy_status)s, %(operating_mode)s)""",
            data["vav_records"], "vav_records")

        # 9. Pump records
        _batch_insert(cur,
            """INSERT INTO pump_records
            (device_id, timestamp, speed, power_kw, flow_rate,
             inlet_pressure, outlet_pressure, differential_pressure, running_status)
            VALUES (%(device_id)s, %(timestamp)s, %(speed)s, %(power_kw)s, %(flow_rate)s,
             %(inlet_pressure)s, %(outlet_pressure)s, %(differential_pressure)s,
             %(running_status)s)""",
            data["pump_records"], "pump_records")

        # 10. Cooling tower records
        _batch_insert(cur,
            """INSERT INTO cooling_tower_records
            (device_id, timestamp, fan_speed, fan_power_kw, cw_inlet_temp, cw_outlet_temp,
             wet_bulb_temp, approach, range, running_status)
            VALUES (%(device_id)s, %(timestamp)s, %(fan_speed)s, %(fan_power_kw)s,
             %(cw_inlet_temp)s, %(cw_outlet_temp)s, %(wet_bulb_temp)s,
             %(approach)s, %(range)s, %(running_status)s)""",
            data["cooling_tower_records"], "cooling_tower_records")

        # 11. Anomaly events
        for ae in data["anomaly_events"]:
            cur.execute(
                """INSERT INTO anomaly_events
                (id, region_id, building_id, device_id, timestamp, anomaly_type, severity,
                 metric_name, metric_value, threshold_value, description, resolved,
                 detection_method, equipment_type, fault_code, recommended_action)
                VALUES (%(id)s, %(region_id)s, %(building_id)s, %(device_id)s, %(timestamp)s,
                 %(anomaly_type)s, %(severity)s, %(metric_name)s, %(metric_value)s,
                 %(threshold_value)s, %(description)s, %(resolved)s, %(detection_method)s,
                 %(equipment_type)s, %(fault_code)s, %(recommended_action)s)""",
                {**ae, "id": str(uuid.uuid4())},
            )
        print(f"  anomaly_events: {len(data['anomaly_events'])}")

        conn.commit()
        print("Database seeded successfully!")

    except Exception as e:
        conn.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        cur.close()
        conn.close()


# ═══════════════════════════════════════════════════════════
# CLI entry point
# ═══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Generate HVAC full-chain synthetic data and seed database.")
    parser.add_argument("--days", type=int, default=7, help="Number of days of data to generate")
    parser.add_argument("--anomaly-rate", type=float, default=0.05, help="Anomaly injection rate (0-1)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--reset", action="store_true", help="Clear all existing data before seeding")
    parser.add_argument("--json-only", action="store_true", help="Only save JSON file, skip database seeding")
    parser.add_argument("--upload-files", action="store_true", help="Export per-device upload files for UI demo")
    parser.add_argument("--upload-files-by-type", action="store_true", help="Export per-device-type upload files (no device_id binding)")
    parser.add_argument("--upload-output-dir", type=str, default="upload_files", help="Output directory for per-device upload files")
    parser.add_argument("--output", type=str, default="dataset_bundle.json", help="JSON output filename")
    args = parser.parse_args()

    print(f"Generating {args.days} days of HVAC data (seed={args.seed}, anomaly_rate={args.anomaly_rate})...")
    data = generate_data(days=args.days, anomaly_rate=args.anomaly_rate, seed=args.seed)

    print("\nGenerated records:")
    for key, val in data.items():
        if isinstance(val, list):
            print(f"  {key}: {len(val)}")

    if args.json_only:
        data_dir = Path(__file__).parent.parent / "data"
        data_dir.mkdir(exist_ok=True)
        output_path = data_dir / args.output
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\nSaved to {output_path}")
    else:
        print(f"\nSeeding database ({settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DATABASE})...")
        seed_database(data, reset=args.reset)

    if args.upload_files:
        data_dir = Path(__file__).parent.parent / "data"
        upload_dir = data_dir / args.upload_output_dir
        generated_files, manifest_path = export_upload_files(data, upload_dir, args.days)
        print(f"\nGenerated upload files: {len(generated_files)}")
        print(f"Manifest: {manifest_path}")
        print("Per-device format overview:")
        for item in generated_files:
            print(
                f"  {item['device_id']} ({item['device_type']}) -> {item['filename']} "
                f"[{item['format']}] records={item['record_count']} anomalies={item['anomaly_count']}"
            )

    if args.upload_files_by_type:
        data_dir = Path(__file__).parent.parent / "data"
        upload_dir = data_dir / args.upload_output_dir
        generated_files, manifest_path = export_upload_files_by_type(
            output_dir=upload_dir,
            days=args.days,
            anomaly_rate=args.anomaly_rate,
            seed=args.seed,
        )
        print(f"\nGenerated type-based upload files: {len(generated_files)}")
        print(f"Manifest: {manifest_path}")
        for item in generated_files:
            print(
                f"  {item['canonical_device_type']} -> {item['filename']} "
                f"[{item['format']}] records={item['record_count']}"
            )

    print("Done.")


if __name__ == "__main__":
    main()
