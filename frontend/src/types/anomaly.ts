export interface AnomalyEvent {
  id: string
  building_id: string
  device_id?: string
  timestamp: string
  anomaly_type: string
  severity: string
  metric_name: string
  metric_value: number
  threshold_value?: number
  description: string
  resolved: boolean
  detection_method: string
  created_at: string
}
