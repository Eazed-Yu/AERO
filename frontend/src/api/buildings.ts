import api from '.'
import type { Building } from '@/types/building'

export const buildingsApi = {
  list: (params?: { region_id?: string; building_type?: string }) =>
    api.get<Building[]>('/buildings', { params }),
  get: (id: string) => api.get<Building>(`/buildings/${id}`),
  create: (data: Partial<Building>) => api.post<Building>('/buildings', data),
  update: (id: string, data: Partial<Building>) =>
    api.put<Building>(`/buildings/${id}`, data),
  remove: (id: string) => api.delete(`/buildings/${id}`),
}
