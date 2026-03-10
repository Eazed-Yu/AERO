export interface CoolingTowerRecord {
  id: number
  device_id: string
  timestamp: string
  fan_speed?: number
  fan_power_kw?: number
  cw_inlet_temp?: number
  cw_outlet_temp?: number
  wet_bulb_temp?: number
  approach?: number
  range?: number
  running_status?: string
}
