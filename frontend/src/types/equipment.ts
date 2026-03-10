export interface Equipment {
  id: string
  building_id: string
  device_id: string
  device_name: string
  device_type: string
  system_type?: string
  model?: string
  manufacturer?: string
  rated_power_kw?: number
  rated_capacity?: number
  rated_cop?: number
  location?: string
  install_date?: string
  status?: string
  created_at: string
  updated_at: string
}
