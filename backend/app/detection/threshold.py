import numpy as np

from app.detection.base import AbstractDetector, DetectionContext
from app.utils.cop import calculate_cop


class ThresholdDetector(AbstractDetector):
    """Simple threshold-based anomaly detection."""

    DEFAULT_THRESHOLDS = {
        "electricity_spike_factor": 2.0,
        "min_cop": 2.0,
        "temp_deviation_celsius": 5.0,
    }

    def __init__(self, thresholds: dict | None = None):
        self.thresholds = {**self.DEFAULT_THRESHOLDS, **(thresholds or {})}

    async def detect(
        self, records: list, context: DetectionContext
    ) -> list[dict]:
        if not records:
            return []

        # Merge context thresholds
        th = {**self.thresholds, **context.thresholds}
        candidates = []

        # Compute rolling average for electricity
        electricity_values = [
            r.electricity_kwh for r in records if r.electricity_kwh is not None
        ]
        if electricity_values:
            rolling_avg = float(np.mean(electricity_values))
            spike_threshold = rolling_avg * th["electricity_spike_factor"]
        else:
            rolling_avg = None
            spike_threshold = None

        for rec in records:
            # Check electricity spike
            if (
                spike_threshold
                and rec.electricity_kwh
                and rec.electricity_kwh > spike_threshold
            ):
                candidates.append(
                    {
                        "timestamp": rec.timestamp,
                        "anomaly_type": "energy_spike",
                        "severity": self._severity(
                            rec.electricity_kwh, spike_threshold
                        ),
                        "metric_name": "electricity_kwh",
                        "metric_value": rec.electricity_kwh,
                        "threshold_value": spike_threshold,
                        "description": (
                            f"电力能耗 {rec.electricity_kwh:.1f} kWh "
                            f"超过阈值 {spike_threshold:.1f} kWh "
                            f"(均值 {rolling_avg:.1f} 的 {th['electricity_spike_factor']}倍)"
                        ),
                        "detection_method": "threshold",
                    }
                )

            # Check COP
            if (
                rec.hvac_kwh
                and rec.hvac_supply_temp is not None
                and rec.hvac_return_temp is not None
                and rec.hvac_flow_rate
            ):
                cop = calculate_cop(
                    rec.hvac_kwh,
                    rec.hvac_supply_temp,
                    rec.hvac_return_temp,
                    rec.hvac_flow_rate,
                )
                if cop is not None and cop < th["min_cop"]:
                    candidates.append(
                        {
                            "timestamp": rec.timestamp,
                            "anomaly_type": "low_cop",
                            "severity": "high" if cop < 1.0 else "medium",
                            "metric_name": "cop",
                            "metric_value": round(cop, 2),
                            "threshold_value": th["min_cop"],
                            "description": (
                                f"COP值 {cop:.2f} 低于最低阈值 {th['min_cop']}"
                            ),
                            "detection_method": "threshold",
                        }
                    )

            # Check temperature deviation
            if rec.hvac_supply_temp is not None:
                # Expected supply temp: ~7°C for cooling, ~45°C for heating
                if rec.outdoor_temp is not None and rec.outdoor_temp > 22:
                    expected = 7.0
                else:
                    expected = 45.0
                deviation = abs(rec.hvac_supply_temp - expected)
                if deviation > th["temp_deviation_celsius"]:
                    candidates.append(
                        {
                            "timestamp": rec.timestamp,
                            "anomaly_type": "temp_deviation",
                            "severity": "high" if deviation > 10 else "medium",
                            "metric_name": "hvac_supply_temp",
                            "metric_value": rec.hvac_supply_temp,
                            "threshold_value": expected,
                            "description": (
                                f"出水温度 {rec.hvac_supply_temp:.1f}°C "
                                f"偏离期望值 {expected:.1f}°C "
                                f"达 {deviation:.1f}°C"
                            ),
                            "detection_method": "threshold",
                        }
                    )

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
