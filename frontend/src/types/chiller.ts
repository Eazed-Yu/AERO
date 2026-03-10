export interface ChillerRecord {
  id: number
  device_id: string
  timestamp: string
  chw_supply_temp?: number
  chw_return_temp?: number
  chw_flow_rate?: number
  cw_supply_temp?: number
  cw_return_temp?: number
  cw_flow_rate?: number
  power_kw?: number
  cooling_capacity_kw?: number
  load_ratio?: number
  cop?: number
  evaporator_approach?: number
  condenser_approach?: number
  compressor_rla_pct?: number
  running_status?: string
}
