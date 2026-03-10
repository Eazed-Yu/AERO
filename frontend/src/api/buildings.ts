import api from '.'
import type { Building } from '@/types/building'

export const buildingsApi = {
  list: (type?: string) =>
    api.get<Building[]>('/buildings', { params: { building_type: type } }),
  get: (id: string) => api.get<Building>(`/buildings/${id}`),
  create: (data: Partial<Building>) => api.post<Building>('/buildings', data),
}
