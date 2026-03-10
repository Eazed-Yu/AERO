export interface Building {
  id: string
  building_id: string
  name: string
  building_type: string
  area: number
  address?: string
  floors?: number
  year_built?: number
  climate_zone?: string
  cooling_area?: number
  design_cooling_load?: number
  design_heating_load?: number
  created_at: string
  updated_at: string
}
