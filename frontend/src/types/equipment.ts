export interface Equipment {
  id: string
  building_id: string
  device_id: string
  device_name: string
  device_type: string
  rated_power_kw?: number
  created_at: string
  updated_at: string
}

export interface EquipmentStatus {
  id: number
  device_id: string
  timestamp: string
  status: string
  power_consumption_kw?: number
  runtime_hours?: number
  error_code?: string
  notes?: string
  created_at: string
}
