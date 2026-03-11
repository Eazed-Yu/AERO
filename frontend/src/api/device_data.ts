import api from './index'

export interface ImportResult {
  total: number
  inserted: number
  skipped: number
  errors: number
  error_details: string[]
}

export interface ExportParams {
  format: 'csv' | 'excel'
  start_time?: string
  end_time?: string
}

export const deviceDataApi = {
  upload: (deviceId: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<ImportResult>(`/import/device/${deviceId}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  downloadTemplate: (deviceId: string) =>
    api.get(`/import/device/${deviceId}/template`, { responseType: 'blob' }),

  exportData: (deviceId: string, params: ExportParams) =>
    api.post(`/export/device/${deviceId}`, params, { responseType: 'blob' }),
}
