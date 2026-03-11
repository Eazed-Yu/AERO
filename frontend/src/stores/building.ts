import { defineStore } from 'pinia'
import { ref } from 'vue'
import { buildingsApi } from '@/api/buildings'
import type { Building } from '@/types/building'

export const useBuildingStore = defineStore('building', () => {
  const buildings = ref<Building[]>([])
  const current = ref<string>('')
  const loading = ref(false)

  async function fetchBuildings(regionId?: string) {
    loading.value = true
    try {
      const { data } = await buildingsApi.list(regionId ? { region_id: regionId } : undefined)
      buildings.value = data
      if (!current.value && data.length > 0) {
        current.value = data[0].building_id
      }
    } finally {
      loading.value = false
    }
  }

  function setCurrent(id: string) {
    current.value = id
  }

  return { buildings, current, loading, fetchBuildings, setCurrent }
})
