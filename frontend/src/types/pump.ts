export interface PumpRecord {
  id: number
  device_id: string
  timestamp: string
  speed?: number
  power_kw?: number
  flow_rate?: number
  inlet_pressure?: number
  outlet_pressure?: number
  differential_pressure?: number
  running_status?: string
}
