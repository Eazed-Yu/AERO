import api from '.'
import type { AnomalyEvent } from '@/types/anomaly'

export const anomalyApi = {
  list: (params?: {
    building_id?: string
    severity?: string
    resolved?: boolean
    start_time?: string
    end_time?: string
    limit?: number
  }) => api.get<AnomalyEvent[]>('/anomaly', { params }),

  detect: (data: { building_id: string; start_time: string; end_time: string }) =>
    api.post<AnomalyEvent[]>('/anomaly/detect', data),

  create: (data: Partial<AnomalyEvent>) =>
    api.post<AnomalyEvent>('/anomaly', data),

  get: (id: string) => api.get<AnomalyEvent>(`/anomaly/${id}`),

  update: (id: string, data: Partial<AnomalyEvent>) =>
    api.put<AnomalyEvent>(`/anomaly/${id}`, data),

  resolve: (id: string) => api.patch(`/anomaly/${id}/resolve`),

  remove: (id: string) => api.delete(`/anomaly/${id}`),
}
