def calculate_cop(
    hvac_kwh: float,
    supply_temp: float,
    return_temp: float,
    flow_rate_m3h: float,
    hours: float = 1.0,
) -> float | None:
    """
    Calculate Coefficient of Performance.

    COP = Q_cooling / W_input
    Q_cooling = flow_rate × 4.186 × |return_temp - supply_temp| [kW]
    W_input = hvac_kwh / hours [kW]

    4.186 kJ/(kg·°C) is the specific heat of water.
    Water density ≈ 1000 kg/m³, so flow_rate in m³/h × 1000 = kg/h.
    Q = flow_rate_m3h × 1000 × 4.186 × ΔT / 3600 = flow_rate × 1.163 × ΔT [kW]
    """
    if not hvac_kwh or hvac_kwh <= 0:
        return None
    if flow_rate_m3h is None or flow_rate_m3h <= 0:
        return None
    if supply_temp is None or return_temp is None:
        return None

    delta_t = abs(return_temp - supply_temp)
    if delta_t < 0.1:
        return None

    # Q in kW
    q_kw = flow_rate_m3h * 1.163 * delta_t
    # W in kW
    w_kw = hvac_kwh / hours if hours > 0 else hvac_kwh

    if w_kw <= 0:
        return None

    return q_kw / w_kw


def cop_rating(cop: float | None) -> str:
    if cop is None:
        return "N/A"
    if cop > 4.0:
        return "excellent"
    if cop > 3.0:
        return "good"
    if cop > 2.0:
        return "fair"
    return "poor"
