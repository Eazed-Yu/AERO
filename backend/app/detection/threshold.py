import numpy as np

from app.detection.base import AbstractDetector, DetectionContext


class ThresholdDetector(AbstractDetector):
    """Enhanced threshold-based anomaly detection for HVAC systems."""

    DEFAULT_THRESHOLDS = {
        "electricity_spike_factor": 2.0,
        "chiller_cop_warning": 0.6,   # ratio of rated COP
        "chiller_cop_critical": 0.4,
        "chw_delta_t_min": 2.0,       # min ΔT for chilled water (°C)
        "ct_approach_max": 5.0,        # max cooling tower approach (°C)
        "ahu_sat_deviation": 3.0,      # max SAT deviation from setpoint (°C)
        "ahu_simultaneous_clg_htg": 30.0,  # valve % threshold
        "vav_zone_deviation": 2.0,     # zone temp deviation from setpoint (°C)
    }

    def __init__(self, thresholds: dict | None = None):
        self.thresholds = {**self.DEFAULT_THRESHOLDS, **(thresholds or {})}

    async def detect(
        self, records: list | dict, context: DetectionContext
    ) -> list[dict]:
        # Accept both old-style list and new-style dict
        if isinstance(records, list):
            # Legacy fallback
            return []

        th = {**self.thresholds, **context.thresholds}
        candidates: list[dict] = []

        # 1. Energy spike detection
        energy_records = records.get("energy", [])
        candidates.extend(self._detect_energy_spikes(energy_records, th))

        # 2. Chiller anomalies
        chiller_records = records.get("chiller", [])
        candidates.extend(self._detect_chiller_anomalies(chiller_records, th))

        # 3. AHU anomalies
        ahu_records = records.get("ahu", [])
        candidates.extend(self._detect_ahu_anomalies(ahu_records, th))

        # 4. VAV anomalies
        vav_records = records.get("vav", [])
        candidates.extend(self._detect_vav_anomalies(vav_records, th))

        return candidates

    def _detect_energy_spikes(self, records: list, th: dict) -> list[dict]:
        candidates = []
        values = [r.total_electricity_kwh for r in records if r.total_electricity_kwh]
        if not values:
            return candidates

        rolling_avg = float(np.mean(values))
        spike_threshold = rolling_avg * th["electricity_spike_factor"]

        for rec in records:
            if rec.total_electricity_kwh and rec.total_electricity_kwh > spike_threshold:
                candidates.append({
                    "timestamp": rec.timestamp,
                    "anomaly_type": "energy_spike",
                    "severity": self._severity(rec.total_electricity_kwh, spike_threshold),
                    "metric_name": "total_electricity_kwh",
                    "metric_value": rec.total_electricity_kwh,
                    "threshold_value": spike_threshold,
                    "description": (
                        f"电力能耗 {rec.total_electricity_kwh:.1f} kWh "
                        f"超过阈值 {spike_threshold:.1f} kWh "
                        f"(均值 {rolling_avg:.1f} 的 {th['electricity_spike_factor']}倍)"
                    ),
                    "detection_method": "threshold",
                    "equipment_type": None,
                })
        return candidates

    def _detect_chiller_anomalies(self, records: list, th: dict) -> list[dict]:
        candidates = []
        for rec in records:
            if rec.running_status != "running":
                continue

            # COP anomaly
            if rec.cop is not None and rec.cop < 2.0:
                sev = "critical" if rec.cop < 1.0 else "high" if rec.cop < 1.5 else "medium"
                candidates.append({
                    "timestamp": rec.timestamp,
                    "device_id": rec.device_id,
                    "anomaly_type": "low_cop",
                    "severity": sev,
                    "metric_name": "cop",
                    "metric_value": round(rec.cop, 2),
                    "threshold_value": 2.0,
                    "description": f"冷机 {rec.device_id} COP值 {rec.cop:.2f} 低于阈值 2.0",
                    "detection_method": "threshold",
                    "equipment_type": "chiller",
                    "fault_code": "CH-COP-LOW",
                    "recommended_action": "检查冷冻水/冷却水流量及温差，清洗换热器",
                })

            # CHW ΔT too small
            if (
                rec.chw_supply_temp is not None
                and rec.chw_return_temp is not None
            ):
                delta_t = abs(rec.chw_return_temp - rec.chw_supply_temp)
                if delta_t < th["chw_delta_t_min"]:
                    candidates.append({
                        "timestamp": rec.timestamp,
                        "device_id": rec.device_id,
                        "anomaly_type": "chw_low_delta_t",
                        "severity": "medium",
                        "metric_name": "chw_delta_t",
                        "metric_value": round(delta_t, 2),
                        "threshold_value": th["chw_delta_t_min"],
                        "description": (
                            f"冷机 {rec.device_id} 冷冻水温差 {delta_t:.1f}°C "
                            f"低于阈值 {th['chw_delta_t_min']}°C，可能流量过大或效率低"
                        ),
                        "detection_method": "threshold",
                        "equipment_type": "chiller",
                        "fault_code": "CH-DT-LOW",
                        "recommended_action": "检查冷冻水流量设定，考虑降低水泵频率",
                    })
        return candidates

    def _detect_ahu_anomalies(self, records: list, th: dict) -> list[dict]:
        candidates = []
        for rec in records:
            if rec.running_status != "running":
                continue

            # SAT deviation
            if (
                rec.supply_air_temp is not None
                and rec.sat_setpoint is not None
            ):
                dev = abs(rec.supply_air_temp - rec.sat_setpoint)
                if dev > th["ahu_sat_deviation"]:
                    candidates.append({
                        "timestamp": rec.timestamp,
                        "device_id": rec.device_id,
                        "anomaly_type": "sat_deviation",
                        "severity": "high" if dev > 5 else "medium",
                        "metric_name": "supply_air_temp",
                        "metric_value": round(rec.supply_air_temp, 1),
                        "threshold_value": rec.sat_setpoint,
                        "description": (
                            f"AHU {rec.device_id} 送风温度 {rec.supply_air_temp:.1f}°C "
                            f"偏离设定值 {rec.sat_setpoint:.1f}°C 达 {dev:.1f}°C"
                        ),
                        "detection_method": "threshold",
                        "equipment_type": "ahu",
                        "fault_code": "AHU-SAT-DEV",
                        "recommended_action": "检查冷/热水阀及风机运行状态",
                    })

            # Simultaneous heating and cooling
            clg_limit = th["ahu_simultaneous_clg_htg"]
            if (
                rec.chw_valve_pos is not None
                and rec.hw_valve_pos is not None
                and rec.chw_valve_pos > clg_limit
                and rec.hw_valve_pos > clg_limit
            ):
                candidates.append({
                    "timestamp": rec.timestamp,
                    "device_id": rec.device_id,
                    "anomaly_type": "simultaneous_clg_htg",
                    "severity": "high",
                    "metric_name": "chw_valve_pos",
                    "metric_value": round(rec.chw_valve_pos, 1),
                    "threshold_value": clg_limit,
                    "description": (
                        f"AHU {rec.device_id} 冷水阀 {rec.chw_valve_pos:.0f}% "
                        f"和热水阀 {rec.hw_valve_pos:.0f}% 同时开启，存在能源浪费"
                    ),
                    "detection_method": "threshold",
                    "equipment_type": "ahu",
                    "fault_code": "AHU-SIM-CLG-HTG",
                    "recommended_action": "检查控制逻辑，确认冷热水阀不应同时大幅开启",
                })
        return candidates

    def _detect_vav_anomalies(self, records: list, th: dict) -> list[dict]:
        candidates = []
        for rec in records:
            if rec.zone_temp is None:
                continue

            # Check overcooling/overheating
            if rec.operating_mode == "cooling" and rec.zone_temp_setpoint_clg is not None:
                dev = rec.zone_temp - rec.zone_temp_setpoint_clg
                if dev > th["vav_zone_deviation"]:
                    candidates.append({
                        "timestamp": rec.timestamp,
                        "device_id": rec.device_id,
                        "anomaly_type": "zone_overheating",
                        "severity": "high" if dev > 4 else "medium",
                        "metric_name": "zone_temp",
                        "metric_value": round(rec.zone_temp, 1),
                        "threshold_value": rec.zone_temp_setpoint_clg,
                        "description": (
                            f"VAV {rec.device_id} 区域温度 {rec.zone_temp:.1f}°C "
                            f"高于制冷设定 {rec.zone_temp_setpoint_clg:.1f}°C 达 {dev:.1f}°C"
                        ),
                        "detection_method": "threshold",
                        "equipment_type": "vav",
                        "fault_code": "VAV-ZONE-HOT",
                        "recommended_action": "检查VAV风阀及上游AHU送风温度",
                    })

            if rec.operating_mode == "heating" and rec.zone_temp_setpoint_htg is not None:
                dev = rec.zone_temp_setpoint_htg - rec.zone_temp
                if dev > th["vav_zone_deviation"]:
                    candidates.append({
                        "timestamp": rec.timestamp,
                        "device_id": rec.device_id,
                        "anomaly_type": "zone_overcooling",
                        "severity": "high" if dev > 4 else "medium",
                        "metric_name": "zone_temp",
                        "metric_value": round(rec.zone_temp, 1),
                        "threshold_value": rec.zone_temp_setpoint_htg,
                        "description": (
                            f"VAV {rec.device_id} 区域温度 {rec.zone_temp:.1f}°C "
                            f"低于制热设定 {rec.zone_temp_setpoint_htg:.1f}°C 达 {dev:.1f}°C"
                        ),
                        "detection_method": "threshold",
                        "equipment_type": "vav",
                        "fault_code": "VAV-ZONE-COLD",
                        "recommended_action": "检查再热阀及热水供应",
                    })
        return candidates

    def _severity(self, value: float, threshold: float) -> str:
        ratio = value / threshold if threshold > 0 else 0
        if ratio > 3.0:
            return "critical"
        if ratio > 2.0:
            return "high"
        if ratio > 1.5:
            return "medium"
        return "low"
