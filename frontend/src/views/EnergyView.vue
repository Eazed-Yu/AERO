<template>
  <div class="page-content">
    <!-- 查询工具栏 -->
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
        type="datetimerange"
        clearable
        size="small"
        style="width: 360px"
      />
      <n-select
        v-model:value="filters.page_size"
        :options="pageSizeOptions"
        size="small"
        style="width: 110px"
      />
      <n-button size="small" type="primary" @click="doQuery(1)">查询</n-button>
      <n-button size="small" @click="openCreate">新增记录</n-button>
      <div style="flex: 1" />
      <n-button size="small" @click="doExport('csv')" :loading="exporting === 'csv'">导出 CSV</n-button>
      <n-button size="small" @click="doExport('excel')" :loading="exporting === 'excel'">导出 Excel</n-button>
    </div>

    <!-- 数据表格 -->
    <div class="surface" style="padding: 0">
      <n-data-table
        :columns="columns"
        :data="records"
        :loading="loading"
        :row-key="(row: EnergyMeter) => row.id"
        size="small"
        :bordered="false"
      />
    </div>

    <!-- 分页 -->
    <div class="toolbar surface" style="margin-top: 16px; border-radius: 3px; justify-content: flex-end">
      <n-pagination
        v-model:page="filters.page"
        :page-size="filters.page_size"
        :item-count="total"
        show-quick-jumper
        :page-sizes="[20, 50, 100]"
        show-size-picker
        @update:page="doQuery"
        @update:page-size="handlePageSizeChange"
      />
    </div>

    <!-- 图表区域 -->
    <n-grid :cols="2" :x-gap="16" :y-gap="16" style="margin-top: 16px">
      <n-gi>
        <n-card title="能耗分布" size="small">
          <energy-distribution-chart :data="distributionData" />
        </n-card>
      </n-gi>
      <n-gi>
        <n-card title="能耗趋势" size="small">
          <energy-trend-chart :data="trendData" />
        </n-card>
      </n-gi>
    </n-grid>

    <!-- 新增/编辑弹窗 -->
    <n-modal v-model:show="showModal" preset="card" :title="modalTitle" style="width: 800px">
      <n-form ref="formRef" :model="form" :rules="rules" label-placement="left" label-width="130">
        <n-grid :cols="2" :x-gap="12">
          <n-form-item-gi label="建筑" path="building_id">
            <n-select
              v-model:value="form.building_id"
              :options="buildingOptions"
              placeholder="选择建筑"
              filterable
            />
          </n-form-item-gi>
          <n-form-item-gi label="时间" path="timestamp">
            <n-date-picker
              v-model:value="formTimestamp"
              type="datetime"
              clearable
              style="width: 100%"
            />
          </n-form-item-gi>
          <n-form-item-gi label="总用电(kWh)">
            <n-input-number v-model:value="form.total_electricity_kwh" :min="0" style="width: 100%" />
          </n-form-item-gi>
          <n-form-item-gi label="暖通用电(kWh)">
            <n-input-number v-model:value="form.hvac_electricity_kwh" :min="0" style="width: 100%" />
          </n-form-item-gi>
          <n-form-item-gi label="照明(kWh)">
            <n-input-number v-model:value="form.lighting_kwh" :min="0" style="width: 100%" />
          </n-form-item-gi>
          <n-form-item-gi label="插座(kWh)">
            <n-input-number v-model:value="form.plug_load_kwh" :min="0" style="width: 100%" />
          </n-form-item-gi>
          <n-form-item-gi label="燃气(m³)">
            <n-input-number v-model:value="form.gas_m3" :min="0" style="width: 100%" />
          </n-form-item-gi>
          <n-form-item-gi label="用水(m³)">
            <n-input-number v-model:value="form.water_m3" :min="0" style="width: 100%" />
          </n-form-item-gi>
          <n-form-item-gi label="峰值需量(kW)">
            <n-input-number v-model:value="form.peak_demand_kw" :min="0" style="width: 100%" />
          </n-form-item-gi>
          <n-form-item-gi label="制冷(kWh)">
            <n-input-number v-model:value="form.cooling_kwh" :min="0" style="width: 100%" />
          </n-form-item-gi>
          <n-form-item-gi label="制热(kWh)">
            <n-input-number v-model:value="form.heating_kwh" :min="0" style="width: 100%" />
          </n-form-item-gi>
        </n-grid>
      </n-form>
      <template #footer>
        <div style="display: flex; justify-content: flex-end; gap: 8px">
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" :loading="saving" @click="submit">保存</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted, watch } from 'vue'
import {
  NSelect,
  NDatePicker,
  NButton,
  NDataTable,
  NModal,
  NForm,
  NFormItemGi,
  NGrid,
  NGi,
  NCard,
  NInputNumber,
  NPagination,
  NSpace,
  useMessage,
  useDialog,
  type DataTableColumn,
  type FormInst,
  type FormRules,
} from 'naive-ui'
import { useBuildingStore } from '@/stores/building'
import { energyMeterApi } from '@/api/energy_meter'
import { exportApi } from '@/api/export'
import type { EnergyMeter } from '@/types/energy_meter'
import EnergyDistributionChart from '@/components/charts/EnergyDistributionChart.vue'
import EnergyTrendChart from '@/components/charts/EnergyTrendChart.vue'

const buildingStore = useBuildingStore()
const message = useMessage()
const dialog = useDialog()

const loading = ref(false)
const records = ref<EnergyMeter[]>([])
const total = ref(0)
const exporting = ref<string | null>(null)
const saving = ref(false)

const showModal = ref(false)
const mode = ref<'create' | 'edit'>('create')
const editingId = ref<number | null>(null)
const formRef = ref<FormInst | null>(null)
const formTimestamp = ref<number | null>(null)
const dateRange = ref<[number, number] | null>(null)

const filters = ref({
  building_id: buildingStore.current || (undefined as string | undefined),
  page: 1,
  page_size: 50,
})

const form = ref({
  building_id: '',
  timestamp: '',
  total_electricity_kwh: null as number | null,
  hvac_electricity_kwh: null as number | null,
  lighting_kwh: null as number | null,
  plug_load_kwh: null as number | null,
  gas_m3: null as number | null,
  water_m3: null as number | null,
  peak_demand_kw: null as number | null,
  cooling_kwh: null as number | null,
  heating_kwh: null as number | null,
})

const rules: FormRules = {
  building_id: [{ required: true, message: '请选择建筑', trigger: ['change', 'blur'] }],
  timestamp: [{ required: true, message: '请选择时间', trigger: ['change', 'blur'] }],
}

const modalTitle = computed(() => (mode.value === 'create' ? '新增能耗记录' : '编辑能耗记录'))

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

// 能耗分布数据（饼图）
const distributionData = computed(() => {
  let hvacTotal = 0
  let lightingTotal = 0
  let plugTotal = 0

  for (const r of records.value) {
    hvacTotal += r.hvac_electricity_kwh ?? 0
    lightingTotal += r.lighting_kwh ?? 0
    plugTotal += r.plug_load_kwh ?? 0
  }

  const items = []
  if (hvacTotal > 0) items.push({ name: '暖通空调', value: Math.round(hvacTotal * 100) / 100 })
  if (lightingTotal > 0) items.push({ name: '照明', value: Math.round(lightingTotal * 100) / 100 })
  if (plugTotal > 0) items.push({ name: '插座负荷', value: Math.round(plugTotal * 100) / 100 })

  return items
})

// 能耗趋势数据（折线图）
const trendData = computed(() =>
  records.value.map((r) => ({
    timestamp: r.timestamp?.replace('T', ' ').slice(0, 16) ?? '',
    electricity_kwh: r.total_electricity_kwh ?? undefined,
    hvac_kwh: r.hvac_electricity_kwh ?? undefined,
  }))
)

const columns: DataTableColumn<EnergyMeter>[] = [
  { title: '建筑ID', key: 'building_id', width: 130, ellipsis: { tooltip: true } },
  {
    title: '时间',
    key: 'timestamp',
    width: 170,
    render(row) {
      return row.timestamp?.replace('T', ' ').slice(0, 19) ?? ''
    },
  },
  {
    title: '总用电(kWh)',
    key: 'total_electricity_kwh',
    width: 120,
    align: 'right',
    render(row) {
      return row.total_electricity_kwh != null ? row.total_electricity_kwh.toFixed(1) : '--'
    },
  },
  {
    title: '暖通用电(kWh)',
    key: 'hvac_electricity_kwh',
    width: 130,
    align: 'right',
    render(row) {
      return row.hvac_electricity_kwh != null ? row.hvac_electricity_kwh.toFixed(1) : '--'
    },
  },
  {
    title: '照明(kWh)',
    key: 'lighting_kwh',
    width: 110,
    align: 'right',
    render(row) {
      return row.lighting_kwh != null ? row.lighting_kwh.toFixed(1) : '--'
    },
  },
  {
    title: '插座(kWh)',
    key: 'plug_load_kwh',
    width: 110,
    align: 'right',
    render(row) {
      return row.plug_load_kwh != null ? row.plug_load_kwh.toFixed(1) : '--'
    },
  },
  {
    title: '燃气(m³)',
    key: 'gas_m3',
    width: 100,
    align: 'right',
    render(row) {
      return row.gas_m3 != null ? row.gas_m3.toFixed(2) : '--'
    },
  },
  {
    title: '用水(m³)',
    key: 'water_m3',
    width: 100,
    align: 'right',
    render(row) {
      return row.water_m3 != null ? row.water_m3.toFixed(2) : '--'
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render(row) {
      return h('div', { style: 'display:flex;gap:8px;' }, [
        h(
          NButton,
          { size: 'tiny', onClick: () => openEdit(row) },
          { default: () => '编辑' }
        ),
        h(
          NButton,
          { size: 'tiny', type: 'error', ghost: true, onClick: () => remove(row) },
          { default: () => '删除' }
        ),
      ])
    },
  },
]

function buildParams(page = 1) {
  const params: Record<string, any> = {
    page,
    page_size: filters.value.page_size,
  }
  if (filters.value.building_id) {
    params.building_id = filters.value.building_id
  }
  if (dateRange.value) {
    params.start_time = new Date(dateRange.value[0]).toISOString().slice(0, 19)
    params.end_time = new Date(dateRange.value[1]).toISOString().slice(0, 19)
  }
  return params
}

async function doQuery(page = 1) {
  loading.value = true
  try {
    const { data } = await energyMeterApi.query(buildParams(page))
    records.value = data.items
    total.value = data.total
    filters.value.page = data.page
  } catch {
    records.value = []
    total.value = 0
    message.error('查询失败')
  } finally {
    loading.value = false
  }
}

function handlePageSizeChange(size: number) {
  filters.value.page_size = size
  doQuery(1)
}

function resetForm() {
  form.value = {
    building_id: filters.value.building_id || buildingStore.current || '',
    timestamp: '',
    total_electricity_kwh: null,
    hvac_electricity_kwh: null,
    lighting_kwh: null,
    plug_load_kwh: null,
    gas_m3: null,
    water_m3: null,
    peak_demand_kw: null,
    cooling_kwh: null,
    heating_kwh: null,
  }
  formTimestamp.value = Date.now()
}

function openCreate() {
  mode.value = 'create'
  editingId.value = null
  resetForm()
  showModal.value = true
}

function openEdit(row: EnergyMeter) {
  mode.value = 'edit'
  editingId.value = row.id
  form.value = {
    building_id: row.building_id,
    timestamp: row.timestamp?.slice(0, 19) || '',
    total_electricity_kwh: row.total_electricity_kwh ?? null,
    hvac_electricity_kwh: row.hvac_electricity_kwh ?? null,
    lighting_kwh: row.lighting_kwh ?? null,
    plug_load_kwh: row.plug_load_kwh ?? null,
    gas_m3: row.gas_m3 ?? null,
    water_m3: row.water_m3 ?? null,
    peak_demand_kw: row.peak_demand_kw ?? null,
    cooling_kwh: row.cooling_kwh ?? null,
    heating_kwh: row.heating_kwh ?? null,
  }
  formTimestamp.value = row.timestamp ? new Date(row.timestamp).getTime() : null
  showModal.value = true
}

async function submit() {
  form.value.timestamp = formTimestamp.value
    ? new Date(formTimestamp.value).toISOString().slice(0, 19)
    : ''
  await formRef.value?.validate()
  saving.value = true
  try {
    const payload: Partial<EnergyMeter> = {
      building_id: form.value.building_id,
      timestamp: form.value.timestamp,
      total_electricity_kwh: form.value.total_electricity_kwh ?? undefined,
      hvac_electricity_kwh: form.value.hvac_electricity_kwh ?? undefined,
      lighting_kwh: form.value.lighting_kwh ?? undefined,
      plug_load_kwh: form.value.plug_load_kwh ?? undefined,
      gas_m3: form.value.gas_m3 ?? undefined,
      water_m3: form.value.water_m3 ?? undefined,
      peak_demand_kw: form.value.peak_demand_kw ?? undefined,
      cooling_kwh: form.value.cooling_kwh ?? undefined,
      heating_kwh: form.value.heating_kwh ?? undefined,
    }

    if (mode.value === 'create') {
      await energyMeterApi.create(payload)
      message.success('新增成功')
    } else if (editingId.value != null) {
      await energyMeterApi.update(editingId.value, payload)
      message.success('更新成功')
    }
    showModal.value = false
    await doQuery(filters.value.page)
  } catch {
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}

function remove(row: EnergyMeter) {
  dialog.warning({
    title: '确认删除',
    content: `确定删除记录 #${row.id} 吗？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await energyMeterApi.remove(row.id)
        message.success('删除成功')
        await doQuery(filters.value.page)
      } catch {
        message.error('删除失败')
      }
    },
  })
}

async function doExport(format: 'csv' | 'excel') {
  const range = dateRange.value
  const start = range ? new Date(range[0]).toISOString().slice(0, 19) : undefined
  const end = range ? new Date(range[1]).toISOString().slice(0, 19) : undefined

  exporting.value = format
  try {
    const exportFn = format === 'csv' ? exportApi.csv : exportApi.excel
    const { data } = await exportFn({
      building_id: filters.value.building_id || buildingStore.current || undefined,
      start_time: start,
      end_time: end,
    })
    const ext = format === 'csv' ? 'csv' : 'xlsx'
    const blob = new Blob([data])
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `energy_meters_export.${ext}`
    a.click()
    URL.revokeObjectURL(url)
  } finally {
    exporting.value = null
  }
}

onMounted(() => {
  doQuery(1)
})

watch(() => buildingStore.current, (val) => {
  if (val) {
    filters.value.building_id = val
    doQuery(1)
  }
})

watch(formTimestamp, (val) => {
  if (val) {
    form.value.timestamp = new Date(val).toISOString().slice(0, 19)
  }
})
</script>
