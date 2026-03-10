import api from './index'
import type { Equipment } from '@/types/equipment'

export const equipmentApi = {
  list: (params?: { building_id?: string; device_type?: string; system_type?: string }) =>
    api.get<Equipment[]>('/equipment', { params }),

  getById: (deviceId: string) =>
    api.get<Equipment>(`/equipment/${deviceId}`),

  create: (data: Partial<Equipment>) =>
    api.post<Equipment>('/equipment', data),

  update: (deviceId: string, data: Partial<Equipment>) =>
    api.put<Equipment>(`/equipment/${deviceId}`, data),

  remove: (deviceId: string) =>
    api.delete(`/equipment/${deviceId}`),
}
