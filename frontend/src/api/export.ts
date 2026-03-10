import api from '.'

export const exportApi = {
  csv: (params: { building_id: string; start_time: string; end_time: string }) =>
    api.post('/export/csv', null, { params, responseType: 'blob' }),

  excel: (params: { building_id: string; start_time: string; end_time: string }) =>
    api.post('/export/excel', null, { params, responseType: 'blob' }),
}
