import api from './index'
import type { EnergyMeter, ImportResult } from '@/types/energy_meter'
import type { PaginatedResponse } from '@/types/api'

export interface EnergyMeterQueryParams {
  region_id?: string
  building_id?: string
  start_time?: string
  end_time?: string
  metrics?: string
  page?: number
  page_size?: number
  sort_by?: string
  sort_order?: string
}

export const energyMeterApi = {
  query: (params: EnergyMeterQueryParams) =>
    api.get<PaginatedResponse<EnergyMeter>>('/energy-meters', { params }),

  getById: (id: number) =>
    api.get<EnergyMeter>(`/energy-meters/${id}`),

  create: (data: Partial<EnergyMeter>) =>
    api.post<EnergyMeter>('/energy-meters', data),

  update: (id: number, data: Partial<EnergyMeter>) =>
    api.put<EnergyMeter>(`/energy-meters/${id}`, data),

  remove: (id: number) =>
    api.delete(`/energy-meters/${id}`),

  batchImport: (records: Partial<EnergyMeter>[]) =>
    api.post<ImportResult>('/energy-meters/batch', records),
}
