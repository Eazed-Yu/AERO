export interface AggregationResult {
  period_start: string
  period_end?: string
  metric_name: string
  avg?: number
  min?: number
  max?: number
  sum?: number
  count: number
}

export interface COPResult {
  period_start: string
  device_id?: string
  cop?: number
  cooling_capacity_kwh?: number
  power_kwh?: number
  chw_supply_temp_avg?: number
  chw_return_temp_avg?: number
  cw_supply_temp_avg?: number
  cw_return_temp_avg?: number
  load_ratio_avg?: number
  rating: string
}

export interface EUIResult {
  building_id: string
  building_name: string
  period_start: string
  period_end: string
  total_electricity_kwh: number
  area: number
  eui: number
  hvac_eui?: number
}

export interface PlantEfficiencyResult {
  period_start: string
  total_cooling_kwh?: number
  chiller_power_kwh?: number
  pump_power_kwh?: number
  tower_power_kwh?: number
  total_power_kwh?: number
  system_cop?: number
}

export interface AnomalyStatistics {
  total_count: number
  by_type: Record<string, number>
  by_severity: Record<string, number>
  by_equipment_type: Record<string, number>
  unresolved_count: number
}
