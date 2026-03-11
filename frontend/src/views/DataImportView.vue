<template>
  <div class="page-content">
    <!-- 设备筛选工具栏 -->
    <div class="toolbar surface" style="margin-bottom: 16px; border-radius: 3px">
      <n-select
        v-model:value="selectedRegion"
        :options="regionOptions"
        placeholder="选择区域"
        size="small"
        style="width: 180px"
        @update:value="onRegionChange"
      />
      <n-select
        v-model:value="buildingFilter"
        :options="buildingOptions"
        placeholder="全部建筑"
        clearable
        size="small"
        style="width: 200px"
      />
      <n-select
        v-model:value="typeFilter"
        :options="deviceTypeOptions"
        placeholder="全部设备类型"
        clearable
        size="small"
        style="width: 160px"
      />
      <n-button size="small" type="primary" @click="fetchEquipment">查询</n-button>
    </div>

    <!-- 设备列表 -->
    <div class="surface" style="padding: 0; margin-bottom: 16px">
      <n-data-table
        :columns="tableColumns"
        :data="equipments"
        :loading="loading"
        :row-class-name="rowClassName"
        size="small"
        :max-height="280"
        :row-key="(row: Equipment) => row.device_id"
        :checked-row-keys="checkedKeys"
        @update:checked-row-keys="onCheck"
      />
    </div>

    <!-- 操作区 -->
    <div class="surface" style="padding: 16px" v-if="selectedDevice">
      <div style="margin-bottom: 12px; font-size: 13px; color: var(--text-secondary)">
        已选设备：<strong style="color: var(--text-primary)">{{ selectedDevice.device_name }}</strong>
        ({{ selectedDevice.device_id }} / {{ selectedDevice.device_type }})
      </div>

      <n-tabs type="line" size="small">
        <!-- 导入数据 tab -->
        <n-tab-pane name="import" tab="导入数据">
          <div style="display: flex; flex-direction: column; gap: 16px; padding-top: 8px">
            <div>
              <n-button size="small" @click="downloadTemplate" :loading="templateLoading">
                下载 CSV 模板
              </n-button>
            </div>
            <div>
              <n-upload
                :custom-request="handleUpload"
                :max="1"
                accept=".csv,.json"
                :show-file-list="true"
              >
                <n-button size="small" type="primary">选择文件上传</n-button>
              </n-upload>
            </div>
            <!-- import result -->
            <div v-if="importResult" style="border-top: 1px solid var(--border-light); padding-top: 12px">
              <div class="section-title">操作结果</div>
              <div class="import-result-row"><span class="import-label">总记录数</span><span class="import-value">{{ importResult.total }}</span></div>
              <div class="import-result-row"><span class="import-label">成功插入</span><span class="import-value" style="color: var(--success)">{{ importResult.inserted }}</span></div>
              <div class="import-result-row"><span class="import-label">跳过</span><span class="import-value">{{ importResult.skipped }}</span></div>
              <div class="import-result-row"><span class="import-label">错误</span><span class="import-value" :style="importResult.errors > 0 ? 'color: var(--danger)' : ''">{{ importResult.errors }}</span></div>
              <div v-if="importResult.error_details.length > 0" style="margin-top: 12px">
                <div class="section-title">错误详情</div>
                <div v-for="(err, idx) in importResult.error_details" :key="idx" style="font-size: 12px; color: var(--danger); padding: 2px 0; font-family: monospace">{{ err }}</div>
              </div>
            </div>
          </div>
        </n-tab-pane>

        <!-- 导出数据 tab -->
        <n-tab-pane name="export" tab="导出数据">
          <div style="display: flex; flex-direction: column; gap: 16px; padding-top: 8px">
            <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap">
              <n-date-picker
                v-model:value="exportRange"
                type="datetimerange"
                size="small"
                clearable
                style="width: 380px"
              />
              <n-select
                v-model:value="exportFormat"
                :options="formatOptions"
                size="small"
                style="width: 120px"
              />
              <n-button
                size="small"
                type="primary"
                @click="handleExport"
                :loading="exportLoading"
              >
                导出
              </n-button>
            </div>
          </div>
        </n-tab-pane>
      </n-tabs>
    </div>

    <div v-else class="surface" style="padding: 24px; text-align: center; color: var(--text-tertiary)">
      请先在上方设备列表中选择一台设备
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  NSelect, NButton, NDataTable, NTabs, NTabPane,
  NUpload, NDatePicker, useMessage,
  type DataTableColumns, type UploadCustomRequestOptions,
} from 'naive-ui'
import type { RowKey } from 'naive-ui/es/data-table/src/interface'
import type { Equipment } from '@/types/equipment'
import { equipmentApi } from '@/api/equipment'
import { deviceDataApi, type ImportResult } from '@/api/device_data'
import { useRegionStore } from '@/stores/region'
import { useBuildingStore } from '@/stores/building'

const message = useMessage()
const regionStore = useRegionStore()
const buildingStore = useBuildingStore()

// ── Region selector ──
const selectedRegion = ref<string>('')

const regionOptions = computed(() =>
  regionStore.regions.map((r) => ({
    label: r.name,
    value: r.region_id,
  }))
)

function onRegionChange(val: string) {
  selectedRegion.value = val
  buildingFilter.value = null
  if (val) {
    buildingStore.fetchBuildings(val)
    fetchEquipment()
  }
}

// ── Filter state ──
const buildingFilter = ref<string | null>(null)
const typeFilter = ref<string | null>(null)

const buildingOptions = computed(() =>
  buildingStore.buildings.map((b) => ({ label: b.name, value: b.building_id }))
)

const deviceTypeOptions = [
  { label: '冷水机组', value: 'chiller' },
  { label: '空调机组', value: 'ahu' },
  { label: '锅炉', value: 'boiler' },
  { label: 'VAV', value: 'vav' },
  { label: '冷冻水泵', value: 'chw_pump' },
  { label: '冷却水泵', value: 'cw_pump' },
  { label: '热水泵', value: 'hw_pump' },
  { label: '冷却塔', value: 'cooling_tower' },
]

// ── Equipment list ──
const equipments = ref<Equipment[]>([])
const loading = ref(false)
const selectedDevice = ref<Equipment | null>(null)
const checkedKeys = ref<string[]>([])

const tableColumns: DataTableColumns<Equipment> = [
  { type: 'selection', multiple: false },
  { title: '设备ID', key: 'device_id', width: 120, ellipsis: { tooltip: true } },
  { title: '设备名称', key: 'device_name', ellipsis: { tooltip: true } },
  { title: '类型', key: 'device_type', width: 100 },
  { title: '建筑', key: 'building_id', width: 100 },
  { title: '状态', key: 'status', width: 80 },
]

function rowClassName(row: Equipment) {
  return selectedDevice.value?.device_id === row.device_id ? 'row-selected' : ''
}

function onCheck(keys: RowKey[]) {
  checkedKeys.value = keys as string[]
  if (keys.length > 0) {
    selectedDevice.value = equipments.value.find(e => e.device_id === keys[0]) || null
  } else {
    selectedDevice.value = null
  }
  importResult.value = null
}

async function fetchEquipment() {
  const regionId = selectedRegion.value
  if (!regionId) return

  loading.value = true
  try {
    const params: Record<string, string> = { region_id: regionId }
    if (buildingFilter.value) params.building_id = buildingFilter.value
    if (typeFilter.value) params.device_type = typeFilter.value
    const res = await equipmentApi.list(params)
    equipments.value = res.data
    selectedDevice.value = null
    checkedKeys.value = []
  } catch {
    message.error('加载设备列表失败')
  } finally {
    loading.value = false
  }
}

// ── Import tab ──
const importResult = ref<ImportResult | null>(null)
const templateLoading = ref(false)

async function downloadTemplate() {
  if (!selectedDevice.value) return
  templateLoading.value = true
  try {
    const res = await deviceDataApi.downloadTemplate(selectedDevice.value.device_id)
    const blob = new Blob([res.data], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${selectedDevice.value.device_type}_template.csv`
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    message.error('下载模板失败')
  } finally {
    templateLoading.value = false
  }
}

async function handleUpload({ file, onFinish, onError }: UploadCustomRequestOptions) {
  if (!selectedDevice.value || !file.file) return
  try {
    const res = await deviceDataApi.upload(selectedDevice.value.device_id, file.file)
    importResult.value = res.data
    if (res.data.errors > 0) {
      message.warning(`导入完成，${res.data.errors} 条记录有错误`)
    } else {
      message.success(`成功导入 ${res.data.inserted} 条记录`)
    }
    onFinish()
  } catch {
    message.error('上传失败')
    onError()
  }
}

// ── Export tab ──
const exportRange = ref<[number, number] | null>(null)
const exportFormat = ref<'csv' | 'excel'>('csv')
const exportLoading = ref(false)

const formatOptions = [
  { label: 'CSV', value: 'csv' },
  { label: 'Excel', value: 'excel' },
]

async function handleExport() {
  if (!selectedDevice.value) return
  exportLoading.value = true
  try {
    const params: { format: 'csv' | 'excel'; start_time?: string; end_time?: string } = {
      format: exportFormat.value,
    }
    if (exportRange.value) {
      params.start_time = new Date(exportRange.value[0]).toISOString()
      params.end_time = new Date(exportRange.value[1]).toISOString()
    }
    const res = await deviceDataApi.exportData(selectedDevice.value.device_id, params)
    const ext = exportFormat.value === 'excel' ? 'xlsx' : 'csv'
    const blob = new Blob([res.data])
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${selectedDevice.value.device_id}_${selectedDevice.value.device_type}.${ext}`
    a.click()
    URL.revokeObjectURL(url)
    message.success('导出成功')
  } catch {
    message.error('导出失败')
  } finally {
    exportLoading.value = false
  }
}

// ── Init ──
onMounted(() => {
  if (regionStore.regions.length === 0) {
    regionStore.fetchRegions()
  }
  if (regionStore.current) {
    selectedRegion.value = regionStore.current
    buildingStore.fetchBuildings(regionStore.current)
    fetchEquipment()
  }
})
</script>

<style scoped>
:deep(.row-selected td) {
  background-color: rgba(var(--primary-rgb, 64, 128, 255), 0.08) !important;
}

.import-result-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 0;
  border-bottom: 1px solid var(--border-light);
  max-width: 320px;
}

.import-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.import-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
}
</style>
