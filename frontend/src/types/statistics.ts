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
  cop?: number
  cooling_output_kwh?: number
  energy_input_kwh?: number
  avg_supply_temp?: number
  avg_return_temp?: number
  rating: string
}

export interface AnomalyStatistics {
  total_count: number
  by_type: Record<string, number>
  by_severity: Record<string, number>
  unresolved_count: number
}
