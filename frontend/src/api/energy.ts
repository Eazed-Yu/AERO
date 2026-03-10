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
  get: (id: number) => api.get<EnergyRecord>(`/energy/${id}`),
  create: (data: Partial<EnergyRecord>) => api.post<EnergyRecord>('/energy', data),
  update: (id: number, data: Partial<EnergyRecord>) =>
    api.put<EnergyRecord>(`/energy/${id}`, data),
  remove: (id: number) => api.delete(`/energy/${id}`),
}
