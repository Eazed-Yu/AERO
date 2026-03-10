export interface AHURecord {
  id: number
  device_id: string
  timestamp: string
  supply_air_temp?: number
  return_air_temp?: number
  mixed_air_temp?: number
  outdoor_air_temp?: number
  supply_air_humidity?: number
  return_air_humidity?: number
  supply_fan_speed?: number
  supply_fan_power_kw?: number
  supply_air_flow?: number
  return_fan_speed?: number
  chw_valve_pos?: number
  hw_valve_pos?: number
  oa_damper_pos?: number
  ra_damper_pos?: number
  duct_static_pressure?: number
  filter_dp?: number
  operating_mode?: string
  sat_setpoint?: number
  dsp_setpoint?: number
  running_status?: string
}
