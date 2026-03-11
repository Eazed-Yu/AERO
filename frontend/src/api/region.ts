import api from '.'
import type { Region } from '@/types/region'

export const regionsApi = {
  list: () => api.get<Region[]>('/regions'),
  get: (id: string) => api.get<Region>(`/regions/${id}`),
  create: (data: Partial<Region>) => api.post<Region>('/regions', data),
  update: (id: string, data: Partial<Region>) =>
    api.put<Region>(`/regions/${id}`, data),
  remove: (id: string) => api.delete(`/regions/${id}`),
}
