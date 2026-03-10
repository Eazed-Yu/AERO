import api from './index'
import type { PaginatedResponse } from '@/types/api'
import type { ChillerRecord } from '@/types/chiller'
import type { AHURecord } from '@/types/ahu'
import type { BoilerRecord } from '@/types/boiler'
import type { VAVRecord } from '@/types/vav'
import type { PumpRecord } from '@/types/pump'
import type { CoolingTowerRecord } from '@/types/cooling_tower'

export interface HVACQueryParams {
  start_time?: string
  end_time?: string
  running_status?: string
  page?: number
  page_size?: number
  sort_by?: string
  sort_order?: string
}

export interface HVACOverview {
  chiller: ChillerRecord[]
  ahu: AHURecord[]
  boiler: BoilerRecord[]
  vav: VAVRecord[]
  pump: PumpRecord[]
  cooling_tower: CoolingTowerRecord[]
}

export const hvacApi = {
  getOverview: () =>
    api.get<HVACOverview>('/hvac/overview'),

  // Chillers
  queryChillerRecords: (deviceId: string, params: HVACQueryParams) =>
    api.get<PaginatedResponse<ChillerRecord>>(`/hvac/chillers/${deviceId}/records`, { params }),

  createChillerRecord: (deviceId: string, data: Partial<ChillerRecord>) =>
    api.post(`/hvac/chillers/${deviceId}/records`, data),

  updateChillerRecord: (recordId: number, data: Partial<ChillerRecord>) =>
    api.put(`/hvac/chillers/records/${recordId}`, data),

  deleteChillerRecord: (recordId: number) =>
    api.delete(`/hvac/chillers/records/${recordId}`),

  // AHUs
  queryAHURecords: (deviceId: string, params: HVACQueryParams) =>
    api.get<PaginatedResponse<AHURecord>>(`/hvac/ahus/${deviceId}/records`, { params }),

  createAHURecord: (deviceId: string, data: Partial<AHURecord>) =>
    api.post(`/hvac/ahus/${deviceId}/records`, data),

  updateAHURecord: (recordId: number, data: Partial<AHURecord>) =>
    api.put(`/hvac/ahus/records/${recordId}`, data),

  deleteAHURecord: (recordId: number) =>
    api.delete(`/hvac/ahus/records/${recordId}`),

  // Boilers
  queryBoilerRecords: (deviceId: string, params: HVACQueryParams) =>
    api.get<PaginatedResponse<BoilerRecord>>(`/hvac/boilers/${deviceId}/records`, { params }),

  createBoilerRecord: (deviceId: string, data: Partial<BoilerRecord>) =>
    api.post(`/hvac/boilers/${deviceId}/records`, data),

  updateBoilerRecord: (recordId: number, data: Partial<BoilerRecord>) =>
    api.put(`/hvac/boilers/records/${recordId}`, data),

  deleteBoilerRecord: (recordId: number) =>
    api.delete(`/hvac/boilers/records/${recordId}`),

  // VAVs
  queryVAVRecords: (deviceId: string, params: HVACQueryParams) =>
    api.get<PaginatedResponse<VAVRecord>>(`/hvac/vavs/${deviceId}/records`, { params }),

  createVAVRecord: (deviceId: string, data: Partial<VAVRecord>) =>
    api.post(`/hvac/vavs/${deviceId}/records`, data),

  updateVAVRecord: (recordId: number, data: Partial<VAVRecord>) =>
    api.put(`/hvac/vavs/records/${recordId}`, data),

  deleteVAVRecord: (recordId: number) =>
    api.delete(`/hvac/vavs/records/${recordId}`),

  // Pumps
  queryPumpRecords: (deviceId: string, params: HVACQueryParams) =>
    api.get<PaginatedResponse<PumpRecord>>(`/hvac/pumps/${deviceId}/records`, { params }),

  createPumpRecord: (deviceId: string, data: Partial<PumpRecord>) =>
    api.post(`/hvac/pumps/${deviceId}/records`, data),

  updatePumpRecord: (recordId: number, data: Partial<PumpRecord>) =>
    api.put(`/hvac/pumps/records/${recordId}`, data),

  deletePumpRecord: (recordId: number) =>
    api.delete(`/hvac/pumps/records/${recordId}`),

  // Cooling Towers
  queryCTRecords: (deviceId: string, params: HVACQueryParams) =>
    api.get<PaginatedResponse<CoolingTowerRecord>>(`/hvac/cooling-towers/${deviceId}/records`, { params }),

  createCTRecord: (deviceId: string, data: Partial<CoolingTowerRecord>) =>
    api.post(`/hvac/cooling-towers/${deviceId}/records`, data),

  updateCTRecord: (recordId: number, data: Partial<CoolingTowerRecord>) =>
    api.put(`/hvac/cooling-towers/records/${recordId}`, data),

  deleteCTRecord: (recordId: number) =>
    api.delete(`/hvac/cooling-towers/records/${recordId}`),
}
