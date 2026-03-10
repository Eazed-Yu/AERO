export interface BoilerRecord {
  id: number
  device_id: string
  timestamp: string
  hw_supply_temp?: number
  hw_return_temp?: number
  hw_flow_rate?: number
  firing_rate?: number
  power_kw?: number
  fuel_consumption?: number
  heating_capacity_kw?: number
  efficiency?: number
  flue_gas_temp?: number
  running_status?: string
}
