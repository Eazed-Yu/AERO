export interface Building {
  id: string
  building_id: string
  name: string
  building_type: string
  area: number
  address?: string
  floors?: number
  year_built?: number
  created_at: string
  updated_at: string
}
