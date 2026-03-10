import { defineStore } from 'pinia'
import { ref } from 'vue'
import { energyApi, type EnergyQueryParams } from '@/api/energy'
import type { EnergyRecord } from '@/types/energy'

export const useEnergyStore = defineStore('energy', () => {
  const records = ref<EnergyRecord[]>([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(50)
  const loading = ref(false)

  async function query(params: EnergyQueryParams) {
    loading.value = true
    try {
      const { data } = await energyApi.query(params)
      records.value = data.items
      total.value = data.total
      page.value = data.page
      pageSize.value = data.page_size
    } finally {
      loading.value = false
    }
  }

  return { records, total, page, pageSize, loading, query }
})
