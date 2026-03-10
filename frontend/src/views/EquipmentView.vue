<template>
  <div class="page-content">
    <div class="toolbar surface" style="margin-bottom: 16px; border-radius: 3px">
      <n-select
        v-model:value="buildingFilter"
        :options="buildingOptions"
        placeholder="全部建筑"
        clearable
        size="small"
        style="width: 180px"
      />
      <n-select
        v-model:value="typeFilter"
        :options="deviceTypeOptions"
        placeholder="全部类型"
        clearable
        size="small"
        style="width: 160px"
      />
      <n-button size="small" type="primary" @click="fetchEquipment">查询</n-button>
    </div>

    <div class="surface" style="padding: 0">
      <n-data-table
        :columns="columns"
        :data="equipment"
        :loading="loading"
        :row-key="(row: Equipment) => row.device_id"
        size="small"
        :bordered="false"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted, watch } from 'vue'
import {
  NSelect,
  NButton,
  NDataTable,
  NTag,
  type DataTableColumn,
} from 'naive-ui'
import { useBuildingStore } from '@/stores/building'
import { equipmentApi } from '@/api/equipment'
import type { Equipment } from '@/types/equipment'

const buildingStore = useBuildingStore()
const loading = ref(false)
const equipment = ref<Equipment[]>([])

const buildingFilter = ref<string | null>(buildingStore.current || null)
const typeFilter = ref<string | null>(null)

const buildingOptions = computed(() =>
  buildingStore.buildings.map((b) => ({
    label: b.name,
    value: b.building_id,
  }))
)

const deviceTypeOptions = computed(() => {
  const types = new Set(equipment.value.map((e) => e.device_type))
  return Array.from(types).map((t) => ({ label: t, value: t }))
})

const columns: DataTableColumn<Equipment>[] = [
  { title: '设备ID', key: 'device_id', width: 140, ellipsis: { tooltip: true } },
  { title: '设备名称', key: 'device_name', width: 180 },
  {
    title: '类型',
    key: 'device_type',
    width: 120,
    render(row) {
      return h(
        NTag,
        { size: 'small', bordered: false },
        { default: () => row.device_type }
      )
    },
  },
  { title: '建筑ID', key: 'building_id', width: 130, ellipsis: { tooltip: true } },
  {
    title: '额定功率(kW)',
    key: 'rated_power_kw',
    width: 120,
    align: 'right',
    render(row) {
      return row.rated_power_kw != null ? row.rated_power_kw.toFixed(1) : '--'
    },
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 170,
    render(row) {
      return row.created_at?.replace('T', ' ').slice(0, 19) ?? ''
    },
  },
  {
    title: '更新时间',
    key: 'updated_at',
    width: 170,
    render(row) {
      return row.updated_at?.replace('T', ' ').slice(0, 19) ?? ''
    },
  },
]

async function fetchEquipment() {
  loading.value = true
  try {
    const params: Record<string, any> = {}
    if (buildingFilter.value) params.building_id = buildingFilter.value
    if (typeFilter.value) params.device_type = typeFilter.value

    const { data } = await equipmentApi.list(params)
    equipment.value = data
  } catch {
    equipment.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchEquipment()
})

watch(() => buildingStore.current, (val) => {
  if (val) {
    buildingFilter.value = val
    fetchEquipment()
  }
})
</script>
