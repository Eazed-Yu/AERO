import api from '.'

export interface ExportParams {
  building_id?: string
  start_time?: string
  end_time?: string
  metrics?: string
  electricity_min?: number
  electricity_max?: number
  hvac_min?: number
  hvac_max?: number
  outdoor_temp_min?: number
  outdoor_temp_max?: number
}

export const exportApi = {
  csv: (params: ExportParams) =>
    api.post('/export/csv', null, { params, responseType: 'blob' }),

  excel: (params: ExportParams) =>
    api.post('/export/excel', null, { params, responseType: 'blob' }),
}
