import { defineStore } from 'pinia'
import { ref } from 'vue'
import { regionsApi } from '@/api/region'
import type { Region } from '@/types/region'

export const useRegionStore = defineStore('region', () => {
  const regions = ref<Region[]>([])
  const current = ref<string>('')
  const loading = ref(false)

  async function fetchRegions() {
    loading.value = true
    try {
      const { data } = await regionsApi.list()
      regions.value = data
      if (!current.value && data.length > 0) {
        current.value = data[0].region_id
      }
    } finally {
      loading.value = false
    }
  }

  function setCurrent(id: string) {
    current.value = id
  }

  return { regions, current, loading, fetchRegions, setCurrent }
})
