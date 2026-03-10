<template>
  <div class="page-content">
    <div class="toolbar surface" style="margin-bottom: 16px; border-radius: 3px">
      <n-select
        v-model:value="filters.building_id"
        :options="buildingOptions"
        placeholder="全部建筑"
        clearable
        size="small"
        style="width: 180px"
      />
      <n-date-picker
        v-model:value="dateRange"
        type="daterange"
        size="small"
        clearable
        style="width: 280px"
      />
      <n-select
        v-model:value="filters.page_size"
        :options="pageSizeOptions"
        size="small"
        style="width: 110px"
      />
      <n-button size="small" type="primary" @click="doQuery">查询</n-button>
      <div style="flex: 1" />
      <n-button size="small" @click="doExport('csv')" :loading="exporting === 'csv'">导出 CSV</n-button>
      <n-button size="small" @click="doExport('excel')" :loading="exporting === 'excel'">导出 Excel</n-button>
    </div>
    <div class="surface" style="padding: 0">
      <n-data-table
        :columns="columns"
        :data="energyStore.records"
        :loading="energyStore.loading"
        :row-key="(row: EnergyRecord) => row.id"
        :pagination="pagination"
        remote
        size="small"
        :bordered="false"
        @update:page="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import {
  NSelect,
  NDatePicker,
  NButton,
  NDataTable,
  type DataTableColumn,
} from 'naive-ui'
import { useBuildingStore } from '@/stores/building'
import { useEnergyStore, } from '@/stores/energy'
import { exportApi } from '@/api/export'
import type { EnergyRecord } from '@/types/energy'

const buildingStore = useBuildingStore()
const energyStore = useEnergyStore()
const exporting = ref<string | null>(null)

const buildingOptions = computed(() =>
  buildingStore.buildings.map((b) => ({
    label: b.name,
    value: b.building_id,
  }))
)

const pageSizeOptions = [
  { label: '20 条/页', value: 20 },
  { label: '50 条/页', value: 50 },
  { label: '100 条/页', value: 100 },
]

const dateRange = ref<[number, number] | null>(null)

const filters = reactive({
  building_id: buildingStore.current || undefined as string | undefined,
  page_size: 50,
})

const pagination = computed(() => ({
  page: energyStore.page,
  pageSize: energyStore.pageSize,
  pageCount: Math.ceil(energyStore.total / energyStore.pageSize),
  itemCount: energyStore.total,
}))

const columns: DataTableColumn<EnergyRecord>[] = [
  { title: '建筑ID', key: 'building_id', width: 120, ellipsis: { tooltip: true } },
  {
    title: '时间',
    key: 'timestamp',
    width: 170,
    render(row) {
      return row.timestamp?.replace('T', ' ').slice(0, 19) ?? ''
    },
  },
  { title: '用电(kWh)', key: 'electricity_kwh', width: 110, align: 'right' },
  { title: '用水(m³)', key: 'water_m3', width: 100, align: 'right' },
  { title: '燃气(m³)', key: 'gas_m3', width: 100, align: 'right' },
  { title: 'HVAC(kWh)', key: 'hvac_kwh', width: 110, align: 'right' },
  { title: '供水温度', key: 'hvac_supply_temp', width: 100, align: 'right' },
  { title: '回水温度', key: 'hvac_return_temp', width: 100, align: 'right' },
  { title: '室外温度', key: 'outdoor_temp', width: 100, align: 'right' },
  { title: '湿度(%)', key: 'outdoor_humidity', width: 90, align: 'right' },
]

function buildParams(page = 1) {
  const params: Record<string, any> = {
    page,
    page_size: filters.page_size,
  }
  if (filters.building_id) {
    params.building_id = filters.building_id
  }
  if (dateRange.value) {
    params.start_time = new Date(dateRange.value[0]).toISOString().slice(0, 19)
    params.end_time = new Date(dateRange.value[1]).toISOString().slice(0, 19)
  }
  return params
}

async function doQuery() {
  await energyStore.query(buildParams(1))
}

function handlePageChange(page: number) {
  energyStore.query(buildParams(page))
}

async function doExport(format: 'csv' | 'excel') {
  const buildingId = filters.building_id || buildingStore.current
  if (!buildingId) return

  const range = dateRange.value
  const start = range ? new Date(range[0]).toISOString().slice(0, 19) : new Date(Date.now() - 7 * 86400000).toISOString().slice(0, 19)
  const end = range ? new Date(range[1]).toISOString().slice(0, 19) : new Date().toISOString().slice(0, 19)

  exporting.value = format
  try {
    const exportFn = format === 'csv' ? exportApi.csv : exportApi.excel
    const { data } = await exportFn({
      building_id: buildingId,
      start_time: start,
      end_time: end,
    })
    const ext = format === 'csv' ? 'csv' : 'xlsx'
    const blob = new Blob([data])
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `energy_export.${ext}`
    a.click()
    URL.revokeObjectURL(url)
  } finally {
    exporting.value = null
  }
}

onMounted(() => {
  doQuery()
})

watch(() => buildingStore.current, (val) => {
  if (val) {
    filters.building_id = val
    doQuery()
  }
})
</script>
