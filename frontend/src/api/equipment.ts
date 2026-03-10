import api from '.'
import type { Equipment, EquipmentStatus } from '@/types/equipment'

export const equipmentApi = {
  list: (params?: { building_id?: string; device_type?: string }) =>
    api.get<Equipment[]>('/equipment', { params }),

  create: (data: Partial<Equipment>) => api.post<Equipment>('/equipment', data),

  update: (deviceId: string, data: Partial<Equipment>) =>
    api.put<Equipment>(`/equipment/${deviceId}`, data),

  remove: (deviceId: string) => api.delete(`/equipment/${deviceId}`),

  get: (deviceId: string) =>
    api.get<{ equipment: Equipment; latest_status: EquipmentStatus | null }>(
      `/equipment/${deviceId}`
    ),

  statusHistory: (
    deviceId: string,
    params?: { start_time?: string; end_time?: string; limit?: number }
  ) => api.get<EquipmentStatus[]>(`/equipment/${deviceId}/status-history`, { params }),

  createStatus: (data: Partial<EquipmentStatus>) =>
    api.post<EquipmentStatus>('/equipment/status', data),

  getStatus: (statusId: number) =>
    api.get<EquipmentStatus>(`/equipment/status/${statusId}`),

  updateStatus: (statusId: number, data: Partial<EquipmentStatus>) =>
    api.put<EquipmentStatus>(`/equipment/status/${statusId}`, data),

  removeStatus: (statusId: number) => api.delete(`/equipment/status/${statusId}`),
}
