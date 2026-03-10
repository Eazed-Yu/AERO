import api from '.'
import type { EnergyRecord } from '@/types/energy'
import type { PaginatedResponse } from '@/types/api'

export interface EnergyQueryParams {
  building_id?: string
  start_time?: string
  end_time?: string
  metrics?: string
  page?: number
  page_size?: number
  sort_by?: string
  sort_order?: string
}

export const energyApi = {
  query: (params: EnergyQueryParams) =>
    api.get<PaginatedResponse<EnergyRecord>>('/energy', { params }),
}
