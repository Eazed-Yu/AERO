import api from './index'
import type { WeatherRecord } from '@/types/weather'
import type { PaginatedResponse } from '@/types/api'

export interface WeatherQueryParams {
  building_id?: string
  start_time?: string
  end_time?: string
  page?: number
  page_size?: number
  sort_by?: string
  sort_order?: string
}

export const weatherApi = {
  query: (params: WeatherQueryParams) =>
    api.get<PaginatedResponse<WeatherRecord>>('/weather', { params }),

  getById: (id: number) =>
    api.get<WeatherRecord>(`/weather/${id}`),

  create: (data: Partial<WeatherRecord>) =>
    api.post<WeatherRecord>('/weather', data),

  update: (id: number, data: Partial<WeatherRecord>) =>
    api.put<WeatherRecord>(`/weather/${id}`, data),

  remove: (id: number) =>
    api.delete(`/weather/${id}`),

  batchImport: (records: Partial<WeatherRecord>[]) =>
    api.post('/weather/batch', records),
}
