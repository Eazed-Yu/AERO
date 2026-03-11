import api from './index'
import type { AggregationResult, AnomalyStatistics, COPResult, EUIResult, PlantEfficiencyResult } from '@/types/statistics'

export const statisticsApi = {
  aggregate: (params: {
    region_id?: string
    building_id?: string
    start_time: string
    end_time: string
    period?: string
    metrics?: string
  }) => api.get<AggregationResult[]>('/statistics/aggregate', { params }),

  cop: (params: {
    start_time: string
    end_time: string
    device_id?: string
    region_id?: string
    building_id?: string
    period?: string
  }) => api.get<COPResult[]>('/statistics/cop', { params }),

  eui: (params: {
    building_id: string
    start_time: string
    end_time: string
  }) => api.get<EUIResult>('/statistics/eui', { params }),

  plantEfficiency: (params: {
    start_time: string
    end_time: string
    period?: string
  }) => api.get<PlantEfficiencyResult[]>('/statistics/plant-efficiency', { params }),

  anomalySummary: (params: {
    start_time: string
    end_time: string
    region_id?: string
    building_id?: string
  }) => api.get<AnomalyStatistics>('/statistics/anomaly-summary', { params }),
}
