export interface EnergyRecord {
  id: number
  building_id: string
  timestamp: string
  electricity_kwh?: number
  water_m3?: number
  gas_m3?: number
  hvac_kwh?: number
  hvac_supply_temp?: number
  hvac_return_temp?: number
  hvac_flow_rate?: number
  outdoor_temp?: number
  outdoor_humidity?: number
  occupancy_density?: number
  created_at: string
}

export interface ImportResult {
  total: number
  inserted: number
  skipped: number
  errors: number
  error_details: string[]
}
