import api from '.'
import type { Equipment, EquipmentStatus } from '@/types/equipment'

export const equipmentApi = {
  list: (params?: { building_id?: string; device_type?: string }) =>
    api.get<Equipment[]>('/equipment', { params }),

  get: (deviceId: string) =>
    api.get<{ equipment: Equipment; latest_status: EquipmentStatus | null }>(
      `/equipment/${deviceId}`
    ),

  statusHistory: (
    deviceId: string,
    params?: { start_time?: string; end_time?: string; limit?: number }
  ) => api.get<EquipmentStatus[]>(`/equipment/${deviceId}/status-history`, { params }),
}
