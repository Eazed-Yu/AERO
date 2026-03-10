export interface VAVRecord {
  id: number
  device_id: string
  timestamp: string
  zone_temp?: number
  zone_temp_setpoint_clg?: number
  zone_temp_setpoint_htg?: number
  airflow?: number
  airflow_setpoint?: number
  damper_pos?: number
  discharge_air_temp?: number
  reheat_valve_pos?: number
  zone_co2?: number
  occupancy_status?: string
  operating_mode?: string
}
