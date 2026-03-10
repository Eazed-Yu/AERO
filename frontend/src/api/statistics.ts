import api from '.'
import type { AggregationResult, COPResult, AnomalyStatistics } from '@/types/statistics'

export const statisticsApi = {
  aggregate: (params: {
    building_id: string
    start_time: string
    end_time: string
    period?: string
    metrics?: string
  }) => api.get<AggregationResult[]>('/statistics/aggregate', { params }),

  cop: (params: {
    building_id: string
    start_time: string
    end_time: string
    period?: string
  }) => api.get<COPResult[]>('/statistics/cop', { params }),

  anomalySummary: (params: {
    start_time: string
    end_time: string
    building_id?: string
  }) => api.get<AnomalyStatistics>('/statistics/anomaly-summary', { params }),
}
