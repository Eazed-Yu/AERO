export interface EnergyMeter {
  id: number
  region_id: string
  building_id: string
  timestamp: string
  total_electricity_kwh?: number
  hvac_electricity_kwh?: number
  lighting_kwh?: number
  plug_load_kwh?: number
  peak_demand_kw?: number
  gas_m3?: number
  water_m3?: number
  cooling_kwh?: number
  heating_kwh?: number
}

export interface ImportResult {
  total: number
  inserted: number
  skipped: number
  errors: number
  error_details: string[]
}
