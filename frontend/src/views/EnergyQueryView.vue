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
      <n-select
        v-model:value="exportMetrics"
        :options="metricOptions"
        multiple
        clearable
        placeholder="导出指标"
        size="small"
        style="width: 240px"
      />
      <n-input-number
        v-model:value="electricityMin"
        size="small"
        placeholder="电力最小"
        style="width: 110px"
      />
      <n-input-number
        v-model:value="electricityMax"
        size="small"
        placeholder="电力最大"
        style="width: 110px"
      />
      <n-input-number
        v-model:value="hvacMin"
        size="small"
        placeholder="HVAC最小"
        style="width: 110px"
      />
      <n-input-number
        v-model:value="hvacMax"
        size="small"
        placeholder="HVAC最大"
        style="width: 110px"
      />
      <n-button size="small" type="primary" @click="doQuery">查询</n-button>
      <n-button size="small" @click="openCreate">新增记录</n-button>
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

    <n-modal v-model:show="showModal" preset="card" :title="mode === 'create' ? '新增能耗记录' : '编辑能耗记录'" style="width: 760px">
      <n-form ref="formRef" :model="form" :rules="rules" label-placement="left" label-width="120">
        <n-grid :cols="2" :x-gap="12">
          <n-form-item-gi label="建筑ID" path="building_id">
            <n-input v-model:value="form.building_id" />
          </n-form-item-gi>
          <n-form-item-gi label="时间(ISO)" path="timestamp">
            <n-input v-model:value="form.timestamp" placeholder="2026-03-10T08:00:00" />
          </n-form-item-gi>
          <n-form-item-gi label="用电(kWh)">
            <n-input-number v-model:value="form.electricity_kwh" :min="0" style="width:100%" />
          </n-form-item-gi>
          <n-form-item-gi label="用水(m³)">
            <n-input-number v-model:value="form.water_m3" :min="0" style="width:100%" />
          </n-form-item-gi>
          <n-form-item-gi label="燃气(m³)">
            <n-input-number v-model:value="form.gas_m3" :min="0" style="width:100%" />
          </n-form-item-gi>
          <n-form-item-gi label="HVAC(kWh)">
            <n-input-number v-model:value="form.hvac_kwh" :min="0" style="width:100%" />
          </n-form-item-gi>
        </n-grid>
      </n-form>
      <template #footer>
        <div style="display:flex;justify-content:flex-end;gap:8px;">
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" :loading="saving" @click="submit">保存</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch, h } from 'vue'
import {
  NSelect,
  NDatePicker,
  NButton,
  NDataTable,
  NModal,
  NForm,
  NFormItemGi,
  NGrid,
  NInput,
  NInputNumber,
  useMessage,
  useDialog,
  type DataTableColumn,
  type FormInst,
  type FormRules,
} from 'naive-ui'
import { useBuildingStore } from '@/stores/building'
import { useEnergyStore } from '@/stores/energy'
import { exportApi } from '@/api/export'
import { energyApi } from '@/api/energy'
import type { EnergyRecord } from '@/types/energy'

const buildingStore = useBuildingStore()
const energyStore = useEnergyStore()
const message = useMessage()
const dialog = useDialog()
const exporting = ref<string | null>(null)

const showModal = ref(false)
const saving = ref(false)
const mode = ref<'create' | 'edit'>('create')
const editingId = ref<number | null>(null)
const formRef = ref<FormInst | null>(null)

const form = ref({
  building_id: '',
  timestamp: '',
  electricity_kwh: null as number | null,
  water_m3: null as number | null,
  gas_m3: null as number | null,
  hvac_kwh: null as number | null,
})

const rules: FormRules = {
  building_id: [{ required: true, message: '请输入建筑ID', trigger: ['blur', 'input'] }],
  timestamp: [{ required: true, message: '请输入时间(ISO)', trigger: ['blur', 'input'] }],
}

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
const exportMetrics = ref<string[]>([])
const electricityMin = ref<number | null>(null)
const electricityMax = ref<number | null>(null)
const hvacMin = ref<number | null>(null)
const hvacMax = ref<number | null>(null)

const metricOptions = [
  { label: 'electricity_kwh', value: 'electricity_kwh' },
  { label: 'water_m3', value: 'water_m3' },
  { label: 'gas_m3', value: 'gas_m3' },
  { label: 'hvac_kwh', value: 'hvac_kwh' },
  { label: 'hvac_supply_temp', value: 'hvac_supply_temp' },
  { label: 'hvac_return_temp', value: 'hvac_return_temp' },
  { label: 'hvac_flow_rate', value: 'hvac_flow_rate' },
  { label: 'outdoor_temp', value: 'outdoor_temp' },
  { label: 'outdoor_humidity', value: 'outdoor_humidity' },
  { label: 'occupancy_density', value: 'occupancy_density' },
]

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
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render(row) {
      return h('div', { style: 'display:flex;gap:8px;' }, [
        h(NButton, { size: 'tiny', onClick: () => openEdit(row) }, { default: () => '编辑' }),
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

function resetForm() {
  form.value = {
    building_id: filters.building_id || buildingStore.current || '',
    timestamp: new Date().toISOString().slice(0, 19),
    electricity_kwh: null,
    water_m3: null,
    gas_m3: null,
    hvac_kwh: null,
  }
}

function openCreate() {
  mode.value = 'create'
  editingId.value = null
  resetForm()
  showModal.value = true
}

function openEdit(row: EnergyRecord) {
  mode.value = 'edit'
  editingId.value = row.id
  form.value = {
    building_id: row.building_id,
    timestamp: row.timestamp?.slice(0, 19) || '',
    electricity_kwh: row.electricity_kwh ?? null,
    water_m3: row.water_m3 ?? null,
    gas_m3: row.gas_m3 ?? null,
    hvac_kwh: row.hvac_kwh ?? null,
  }
  showModal.value = true
}

async function submit() {
  await formRef.value?.validate()
  saving.value = true
  try {
    const payload = {
      building_id: form.value.building_id,
      timestamp: form.value.timestamp,
      electricity_kwh: form.value.electricity_kwh ?? undefined,
      water_m3: form.value.water_m3 ?? undefined,
      gas_m3: form.value.gas_m3 ?? undefined,
      hvac_kwh: form.value.hvac_kwh ?? undefined,
    }

    if (mode.value === 'create') {
      await energyApi.create(payload)
      message.success('新增成功')
    } else if (editingId.value != null) {
      await energyApi.update(editingId.value, payload)
      message.success('更新成功')
    }
    showModal.value = false
    await doQuery()
  } catch {
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}

function remove(row: EnergyRecord) {
  dialog.warning({
    title: '确认删除',
    content: `确定删除记录 #${row.id} 吗？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await energyApi.remove(row.id)
        message.success('删除成功')
        await doQuery()
      } catch {
        message.error('删除失败')
      }
    },
  })
}

async function doQuery() {
  await energyStore.query(buildParams(1))
}

function handlePageChange(page: number) {
  energyStore.query(buildParams(page))
}

async function doExport(format: 'csv' | 'excel') {
  const range = dateRange.value
  const start = range ? new Date(range[0]).toISOString().slice(0, 19) : undefined
  const end = range ? new Date(range[1]).toISOString().slice(0, 19) : undefined

  exporting.value = format
  try {
    const exportFn = format === 'csv' ? exportApi.csv : exportApi.excel
    const { data } = await exportFn({
      building_id: filters.building_id || buildingStore.current || undefined,
      start_time: start,
      end_time: end,
      metrics: exportMetrics.value.length ? exportMetrics.value.join(',') : undefined,
      electricity_min: electricityMin.value ?? undefined,
      electricity_max: electricityMax.value ?? undefined,
      hvac_min: hvacMin.value ?? undefined,
      hvac_max: hvacMax.value ?? undefined,
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
