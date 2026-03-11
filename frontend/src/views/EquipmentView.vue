<template>
  <div class="page-content">
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
        style="width: 180px"
      />
      <n-select
        v-model:value="typeFilter"
        :options="deviceTypeOptions"
        placeholder="全部设备类型"
        clearable
        size="small"
        style="width: 160px"
      />
      <n-select
        v-model:value="systemFilter"
        :options="systemTypeOptions"
        placeholder="全部系统类型"
        clearable
        size="small"
        style="width: 160px"
      />
      <n-button size="small" type="primary" @click="fetchEquipment">查询</n-button>
      <n-button size="small" :disabled="!selectedRegion" @click="openCreate">新增设备</n-button>
    </div>

    <div class="surface" style="padding: 0">
      <n-data-table
        :columns="columns"
        :data="equipment"
        :loading="loading"
        :row-key="(row: Equipment) => row.device_id"
        size="small"
        :bordered="false"
        :scroll-x="1600"
      />
    </div>

    <!-- 设备详情面板 -->
    <div v-if="detailDevice" class="surface" style="margin-top: 16px; padding: 16px">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px">
        <span style="font-weight: 600; font-size: 15px">
          设备详情: {{ detailDevice.device_name }} ({{ detailDevice.device_id }})
        </span>
        <n-button size="tiny" @click="detailDevice = null">关闭</n-button>
      </div>

      <n-tabs v-model:value="detailTab" type="line">
        <!-- 基本信息 Tab -->
        <n-tab-pane name="info" tab="基本信息">
          <div class="param-grid">
            <div class="param-item">
              <span class="param-label">设备ID</span>
              <span class="param-value">{{ detailDevice.device_id }}</span>
            </div>
            <div class="param-item">
              <span class="param-label">设备名称</span>
              <span class="param-value">{{ detailDevice.device_name }}</span>
            </div>
            <div class="param-item">
              <span class="param-label">设备类型</span>
              <span class="param-value">{{ detailDevice.device_type }}</span>
            </div>
            <div class="param-item">
              <span class="param-label">系统类型</span>
              <span class="param-value">{{ detailDevice.system_type || '--' }}</span>
            </div>
            <div class="param-item">
              <span class="param-label">所属建筑</span>
              <span class="param-value">{{ detailDevice.building_id || '--' }}</span>
            </div>
            <div class="param-item">
              <span class="param-label">型号</span>
              <span class="param-value">{{ detailDevice.model || '--' }}</span>
            </div>
            <div class="param-item">
              <span class="param-label">制造商</span>
              <span class="param-value">{{ detailDevice.manufacturer || '--' }}</span>
            </div>
            <div class="param-item">
              <span class="param-label">额定功率</span>
              <span class="param-value">{{ detailDevice.rated_power_kw != null ? detailDevice.rated_power_kw + ' kW' : '--' }}</span>
            </div>
            <div class="param-item">
              <span class="param-label">额定容量</span>
              <span class="param-value">{{ detailDevice.rated_capacity != null ? detailDevice.rated_capacity : '--' }}</span>
            </div>
            <div class="param-item">
              <span class="param-label">额定COP</span>
              <span class="param-value">{{ detailDevice.rated_cop != null ? detailDevice.rated_cop : '--' }}</span>
            </div>
            <div class="param-item">
              <span class="param-label">安装位置</span>
              <span class="param-value">{{ detailDevice.location || '--' }}</span>
            </div>
            <div class="param-item">
              <span class="param-label">安装日期</span>
              <span class="param-value">{{ detailDevice.install_date?.slice(0, 10) ?? '--' }}</span>
            </div>
            <div class="param-item">
              <span class="param-label">状态</span>
              <n-tag
                :type="detailDevice.status === 'active' ? 'success' : detailDevice.status === 'inactive' ? 'warning' : 'default'"
                size="small"
                :bordered="false"
              >
                {{ detailDevice.status || 'active' }}
              </n-tag>
            </div>
          </div>
        </n-tab-pane>

        <!-- 运行数据 Tab -->
        <n-tab-pane name="records" tab="运行数据">
          <div style="display: flex; gap: 8px; margin-bottom: 12px; align-items: center">
            <n-date-picker
              v-model:value="detailDateRange"
              type="datetimerange"
              clearable
              size="small"
              style="width: 380px"
              :shortcuts="detailDateShortcuts"
            />
            <n-button size="small" type="primary" @click="fetchDeviceRecords">查询</n-button>
          </div>
          <n-spin :show="recordsLoading">
            <n-empty v-if="!recordsLoading && deviceRecords.length === 0" description="暂无运行数据" />
            <n-data-table
              v-else
              :columns="recordColumns"
              :data="deviceRecords"
              :bordered="false"
              size="small"
              :row-key="(row: any) => row.id"
              :pagination="{ pageSize: 20 }"
              max-height="520"
            />
          </n-spin>
        </n-tab-pane>

        <!-- 数据图表 Tab -->
        <n-tab-pane name="charts" tab="数据图表">
          <div style="display: flex; gap: 8px; margin-bottom: 12px; align-items: center">
            <n-date-picker
              v-model:value="detailDateRange"
              type="datetimerange"
              clearable
              size="small"
              style="width: 380px"
              :shortcuts="detailDateShortcuts"
            />
            <n-button size="small" type="primary" @click="fetchDeviceRecords">查询</n-button>
          </div>
          <n-spin :show="recordsLoading">
            <n-empty v-if="!recordsLoading && deviceRecords.length === 0" description="暂无数据可绘图" />
            <template v-else>
              <!-- Chiller charts -->
              <template v-if="detailDevice.device_type === 'chiller'">
                <div class="grid-2">
                  <div class="surface" style="padding: 16px">
                    <div class="section-title">COP 趋势</div>
                    <v-chart :option="chillerCopChartOption" autoresize style="height: 280px; width: 100%" />
                  </div>
                  <div class="surface" style="padding: 16px">
                    <div class="section-title">冷冻水 / 冷却水温度对比</div>
                    <v-chart :option="chillerTempChartOption" autoresize style="height: 280px; width: 100%" />
                  </div>
                </div>
              </template>

              <!-- AHU charts -->
              <template v-else-if="detailDevice.device_type === 'ahu'">
                <div class="grid-2">
                  <div class="surface" style="padding: 16px">
                    <div class="section-title">温度趋势 (SAT / RAT / MAT / OAT)</div>
                    <v-chart :option="ahuTempChartOption" autoresize style="height: 280px; width: 100%" />
                  </div>
                  <div class="surface" style="padding: 16px">
                    <div class="section-title">阀位趋势</div>
                    <v-chart :option="ahuValveChartOption" autoresize style="height: 280px; width: 100%" />
                  </div>
                </div>
              </template>

              <!-- Boiler charts -->
              <template v-else-if="detailDevice.device_type === 'boiler'">
                <div class="grid-2">
                  <div class="surface" style="padding: 16px">
                    <div class="section-title">温度趋势</div>
                    <v-chart :option="boilerTempChartOption" autoresize style="height: 280px; width: 100%" />
                  </div>
                  <div class="surface" style="padding: 16px">
                    <div class="section-title">效率趋势</div>
                    <v-chart :option="boilerEffChartOption" autoresize style="height: 280px; width: 100%" />
                  </div>
                </div>
              </template>

              <!-- VAV charts -->
              <template v-else-if="detailDevice.device_type === 'vav'">
                <div class="surface" style="padding: 16px">
                  <div class="section-title">区域温度趋势</div>
                  <v-chart :option="vavTempChartOption" autoresize style="height: 300px; width: 100%" />
                </div>
              </template>

              <!-- Pump charts -->
              <template v-else-if="['chw_pump', 'cw_pump', 'hw_pump'].includes(detailDevice.device_type)">
                <div class="surface" style="padding: 16px">
                  <div class="section-title">速度 / 功率 / 流量趋势</div>
                  <v-chart :option="pumpChartOption" autoresize style="height: 300px; width: 100%" />
                </div>
              </template>

              <!-- Cooling Tower charts -->
              <template v-else-if="detailDevice.device_type === 'cooling_tower'">
                <div class="surface" style="padding: 16px">
                  <div class="section-title">温度 / 逼近度趋势</div>
                  <v-chart :option="ctChartOption" autoresize style="height: 300px; width: 100%" />
                </div>
              </template>
            </template>
          </n-spin>
        </n-tab-pane>
      </n-tabs>
    </div>

    <!-- CRUD Modal -->
    <n-modal v-model:show="showModal" preset="card" :title="modalTitle" style="width: 800px">
      <n-form ref="formRef" :model="form" :rules="rules" label-placement="left" label-width="110">
        <n-space vertical :size="0">
          <n-space :size="12">
            <n-form-item label="设备名称" path="device_name" style="width: 340px">
              <n-input v-model:value="form.device_name" placeholder="设备名称" />
            </n-form-item>
            <n-form-item label="设备类型" path="device_type" style="width: 340px">
              <n-select v-model:value="form.device_type" :options="deviceTypeOptions" placeholder="选择设备类型" />
            </n-form-item>
          </n-space>
          <n-space :size="12">
            <n-form-item label="系统类型" path="system_type" style="width: 340px">
              <n-select v-model:value="form.system_type" :options="systemTypeOptions" placeholder="选择系统类型" />
            </n-form-item>
          </n-space>
          <n-space :size="12">
            <n-form-item label="所属建筑" style="width: 340px">
              <n-select
                v-model:value="form.building_id"
                :options="buildingOptions"
                placeholder="可选，选择建筑"
                clearable
                filterable
              />
            </n-form-item>
            <n-form-item label="状态" style="width: 340px">
              <n-select v-model:value="form.status" :options="statusOptions" placeholder="选择状态" />
            </n-form-item>
          </n-space>
          <n-space :size="12">
            <n-form-item label="型号" style="width: 340px">
              <n-input v-model:value="form.model" placeholder="设备型号" />
            </n-form-item>
            <n-form-item label="制造商" style="width: 340px">
              <n-input v-model:value="form.manufacturer" placeholder="制造商" />
            </n-form-item>
          </n-space>
          <n-space :size="12">
            <n-form-item label="额定功率(kW)" style="width: 340px">
              <n-input-number v-model:value="form.rated_power_kw" :min="0" style="width: 100%" placeholder="kW" />
            </n-form-item>
            <n-form-item label="额定容量" style="width: 340px">
              <n-input-number v-model:value="form.rated_capacity" :min="0" style="width: 100%" placeholder="额定容量" />
            </n-form-item>
          </n-space>
          <n-space :size="12">
            <n-form-item label="额定COP" style="width: 340px">
              <n-input-number v-model:value="form.rated_cop" :min="0" :step="0.1" style="width: 100%" placeholder="额定COP" />
            </n-form-item>
            <n-form-item label="安装位置" style="width: 340px">
              <n-input v-model:value="form.location" placeholder="安装位置" />
            </n-form-item>
          </n-space>
          <n-space :size="12">
            <n-form-item label="安装日期" style="width: 340px">
              <n-date-picker
                v-model:value="installDateTs"
                type="date"
                clearable
                style="width: 100%"
              />
            </n-form-item>
          </n-space>
        </n-space>
      </n-form>
      <template #footer>
        <div style="display:flex; justify-content:flex-end; gap:8px;">
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
  NButton,
  NDataTable,
  NTag,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NDatePicker,
  NSpace,
  NTabs,
  NTabPane,
  NSpin,
  NEmpty,
  useMessage,
  useDialog,
  type DataTableColumn,
  type FormInst,
  type FormRules,
} from 'naive-ui'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

import { useRegionStore } from '@/stores/region'
import { useBuildingStore } from '@/stores/building'
import { equipmentApi } from '@/api/equipment'
import { hvacApi, type HVACQueryParams } from '@/api/hvac'
import type { Equipment } from '@/types/equipment'

use([LineChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const regionStore = useRegionStore()
const buildingStore = useBuildingStore()
const message = useMessage()
const dialog = useDialog()
const loading = ref(false)
const equipment = ref<Equipment[]>([])
const saving = ref(false)
const selectedRegion = ref<string>('')

const showModal = ref(false)
const mode = ref<'create' | 'edit'>('create')
const editingDeviceId = ref('')
const formRef = ref<FormInst | null>(null)
const installDateTs = ref<number | null>(null)

const form = ref({
  building_id: null as string | null,
  device_name: '',
  device_type: '',
  system_type: '',
  model: '',
  manufacturer: '',
  rated_power_kw: null as number | null,
  rated_capacity: null as number | null,
  rated_cop: null as number | null,
  location: '',
  install_date: '',
  status: 'active',
})

const modalTitle = computed(() => (mode.value === 'create' ? '新增设备' : '编辑设备'))

const rules: FormRules = {
  device_name: [{ required: true, message: '请输入设备名称', trigger: ['blur', 'input'] }],
  device_type: [{ required: true, message: '请选择设备类型', trigger: ['blur', 'change'] }],
  system_type: [{ required: true, message: '请选择系统类型', trigger: ['blur', 'change'] }],
}

const buildingFilter = ref<string | null>(null)
const typeFilter = ref<string | null>(null)
const systemFilter = ref<string | null>(null)

const buildingOptions = computed(() =>
  buildingStore.buildings.map((b) => ({
    label: b.name,
    value: b.building_id,
  }))
)

const regionOptions = computed(() =>
  regionStore.regions.map((r) => ({
    label: r.name,
    value: r.region_id,
  }))
)

function onRegionChange(val: string) {
  selectedRegion.value = val
  buildingFilter.value = null
  detailDevice.value = null
  if (val) {
    buildingStore.fetchBuildings(val)
    fetchEquipment()
  }
}

const deviceTypeOptions = [
  { label: 'chiller', value: 'chiller' },
  { label: 'ahu', value: 'ahu' },
  { label: 'boiler', value: 'boiler' },
  { label: 'vav', value: 'vav' },
  { label: 'chw_pump', value: 'chw_pump' },
  { label: 'cw_pump', value: 'cw_pump' },
  { label: 'hw_pump', value: 'hw_pump' },
  { label: 'cooling_tower', value: 'cooling_tower' },
]

const systemTypeOptions = [
  { label: 'cooling_plant', value: 'cooling_plant' },
  { label: 'air_system', value: 'air_system' },
  { label: 'heating_plant', value: 'heating_plant' },
  { label: 'terminal', value: 'terminal' },
]

const statusOptions = [
  { label: 'active', value: 'active' },
  { label: 'inactive', value: 'inactive' },
  { label: 'maintenance', value: 'maintenance' },
]

const statusTypeMap: Record<string, 'success' | 'warning' | 'default'> = {
  active: 'success',
  inactive: 'warning',
  maintenance: 'default',
}

// ----------------------------------------------------------------
// Table columns (with "详情" button)
// ----------------------------------------------------------------
const columns: DataTableColumn<Equipment>[] = [
  { title: '设备ID', key: 'device_id', width: 140, ellipsis: { tooltip: true }, fixed: 'left' },
  { title: '设备名称', key: 'device_name', width: 160 },
  {
    title: '设备类型',
    key: 'device_type',
    width: 110,
    render(row) {
      return h(NTag, { size: 'small', bordered: false }, { default: () => row.device_type })
    },
  },
  {
    title: '系统类型',
    key: 'system_type',
    width: 120,
    render(row) {
      return row.system_type
        ? h(NTag, { size: 'small', bordered: false, type: 'info' }, { default: () => row.system_type })
        : '--'
    },
  },
  { title: '建筑ID', key: 'building_id', width: 130, ellipsis: { tooltip: true }, render(row) { return row.building_id || '--' } },
  { title: '型号', key: 'model', width: 120, ellipsis: { tooltip: true }, render(row) { return row.model || '--' } },
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
    title: '状态',
    key: 'status',
    width: 90,
    render(row) {
      const s = row.status || 'active'
      return h(NTag, { size: 'small', bordered: false, type: statusTypeMap[s] || 'default' }, { default: () => s })
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    fixed: 'right',
    render(row) {
      return h('div', { style: 'display:flex;gap:8px;' }, [
        h(
          NButton,
          { size: 'tiny', type: 'info', onClick: () => openDetail(row) },
          { default: () => '详情' }
        ),
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

// ----------------------------------------------------------------
// CRUD functions (unchanged from original)
// ----------------------------------------------------------------
function resetForm() {
  form.value = {
    building_id: null,
    device_name: '',
    device_type: '',
    system_type: '',
    model: '',
    manufacturer: '',
    rated_power_kw: null,
    rated_capacity: null,
    rated_cop: null,
    location: '',
    install_date: '',
    status: 'active',
  }
  installDateTs.value = null
}

function openCreate() {
  mode.value = 'create'
  editingDeviceId.value = ''
  resetForm()
  showModal.value = true
}

function openEdit(row: Equipment) {
  mode.value = 'edit'
  editingDeviceId.value = row.device_id
  form.value = {
    building_id: row.building_id || null,
    device_name: row.device_name,
    device_type: row.device_type,
    system_type: row.system_type || '',
    model: row.model || '',
    manufacturer: row.manufacturer || '',
    rated_power_kw: row.rated_power_kw ?? null,
    rated_capacity: row.rated_capacity ?? null,
    rated_cop: row.rated_cop ?? null,
    location: row.location || '',
    install_date: row.install_date || '',
    status: row.status || 'active',
  }
  installDateTs.value = row.install_date ? new Date(row.install_date).getTime() : null
  showModal.value = true
}

async function fetchEquipment() {
  if (!selectedRegion.value) return

  loading.value = true
  try {
    const params: Record<string, any> = { region_id: selectedRegion.value }
    if (buildingFilter.value) params.building_id = buildingFilter.value
    if (typeFilter.value) params.device_type = typeFilter.value
    if (systemFilter.value) params.system_type = systemFilter.value

    const { data } = await equipmentApi.list(params)
    equipment.value = data
  } catch {
    equipment.value = []
  } finally {
    loading.value = false
  }
}

async function submit() {
  await formRef.value?.validate()
  saving.value = true

  if (installDateTs.value) {
    form.value.install_date = new Date(installDateTs.value).toISOString().slice(0, 10)
  } else {
    form.value.install_date = ''
  }

  try {
    const payload: Record<string, any> = {
      region_id: selectedRegion.value,
      building_id: form.value.building_id || undefined,
      device_name: form.value.device_name,
      device_type: form.value.device_type,
      system_type: form.value.system_type || undefined,
      model: form.value.model || undefined,
      manufacturer: form.value.manufacturer || undefined,
      rated_power_kw: form.value.rated_power_kw ?? undefined,
      rated_capacity: form.value.rated_capacity ?? undefined,
      rated_cop: form.value.rated_cop ?? undefined,
      location: form.value.location || undefined,
      install_date: form.value.install_date || undefined,
      status: form.value.status || undefined,
    }

    if (mode.value === 'create') {
      await equipmentApi.create(payload)
      message.success('新增成功')
    } else {
      await equipmentApi.update(editingDeviceId.value, payload)
      message.success('更新成功')
    }
    showModal.value = false
    await fetchEquipment()
  } catch {
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}

function remove(row: Equipment) {
  dialog.warning({
    title: '确认删除',
    content: `确定删除设备 ${row.device_name} (${row.device_id}) 吗？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await equipmentApi.remove(row.device_id)
        message.success('删除成功')
        await fetchEquipment()
      } catch {
        message.error('删除失败')
      }
    },
  })
}

// ----------------------------------------------------------------
// Detail panel
// ----------------------------------------------------------------
const detailDevice = ref<Equipment | null>(null)
const detailTab = ref('info')
const recordsLoading = ref(false)
const deviceRecords = ref<any[]>([])

const defaultDetailRange = (): [number, number] => {
  const end = Date.now()
  return [end - 24 * 3600_000, end]
}
const detailDateRange = ref<[number, number] | null>(defaultDetailRange())

const detailDateShortcuts = {
  '近6小时': () => {
    const end = Date.now()
    return [end - 6 * 3600_000, end] as [number, number]
  },
  '近24小时': () => {
    const end = Date.now()
    return [end - 24 * 3600_000, end] as [number, number]
  },
  '近7天': () => {
    const end = Date.now()
    return [end - 7 * 24 * 3600_000, end] as [number, number]
  },
  '近30天': () => {
    const end = Date.now()
    return [end - 30 * 24 * 3600_000, end] as [number, number]
  },
}

function getDetailTimeParams(): Pick<HVACQueryParams, 'start_time' | 'end_time'> {
  const range = detailDateRange.value || defaultDetailRange()
  return {
    start_time: new Date(range[0]).toISOString().slice(0, 19),
    end_time: new Date(range[1]).toISOString().slice(0, 19),
  }
}

function openDetail(row: Equipment) {
  detailDevice.value = row
  detailTab.value = 'info'
  detailDateRange.value = defaultDetailRange()
  deviceRecords.value = []
}

// HVAC query map
type QueryFn = (deviceId: string, params: HVACQueryParams) => Promise<any>
const hvacQueryMap: Record<string, QueryFn> = {
  chiller: hvacApi.queryChillerRecords,
  ahu: hvacApi.queryAHURecords,
  boiler: hvacApi.queryBoilerRecords,
  vav: hvacApi.queryVAVRecords,
  chw_pump: hvacApi.queryPumpRecords,
  cw_pump: hvacApi.queryPumpRecords,
  hw_pump: hvacApi.queryPumpRecords,
  cooling_tower: hvacApi.queryCTRecords,
}

async function fetchDeviceRecords() {
  if (!detailDevice.value) return
  const queryFn = hvacQueryMap[detailDevice.value.device_type]
  if (!queryFn) return

  recordsLoading.value = true
  try {
    const params: HVACQueryParams = {
      ...getDetailTimeParams(),
      page: 1,
      page_size: 500,
      sort_by: 'timestamp',
      sort_order: 'asc',
    }
    const { data } = await queryFn(detailDevice.value.device_id, params)
    deviceRecords.value = data.items
  } catch {
    deviceRecords.value = []
  } finally {
    recordsLoading.value = false
  }
}

// Auto-fetch records when switching to records/charts tab
watch(detailTab, (tab) => {
  if ((tab === 'records' || tab === 'charts') && deviceRecords.value.length === 0) {
    fetchDeviceRecords()
  }
})

// ----------------------------------------------------------------
// Formatting helpers
// ----------------------------------------------------------------
function fmtNum(val: number | undefined | null, decimals = 1): string {
  if (val == null || isNaN(val)) return '--'
  return val.toFixed(decimals)
}

function fmtPct(val: number | undefined | null): string {
  if (val == null || isNaN(val)) return '--'
  return (val * 100).toFixed(1) + '%'
}

function fmtTimestamp(ts: string | undefined): string {
  if (!ts) return '--'
  return ts.replace('T', ' ').slice(0, 19)
}

function statusText(status: string | undefined): string {
  const map: Record<string, string> = {
    running: '运行中', stopped: '已停机', fault: '故障', standby: '待机', maintenance: '维护中',
  }
  return map[status ?? ''] ?? status ?? '--'
}

function modeText(m: string | undefined): string {
  const map: Record<string, string> = {
    cooling: '制冷', heating: '制热', ventilation: '通风', auto: '自动', economizer: '经济运行',
  }
  return map[m ?? ''] ?? m ?? '--'
}

// ----------------------------------------------------------------
// Dynamic record table columns per device type
// ----------------------------------------------------------------
const recordColumns = computed<DataTableColumn<any>[]>(() => {
  const type = detailDevice.value?.device_type
  const tsCol: DataTableColumn<any> = {
    title: '时间', key: 'timestamp', width: 170,
    render(row: any) { return fmtTimestamp(row.timestamp) },
  }

  if (type === 'chiller') {
    return [
      tsCol,
      { title: 'COP', key: 'cop', width: 80, align: 'right', render: (r: any) => fmtNum(r.cop, 2) },
      { title: '功率(kW)', key: 'power_kw', width: 100, align: 'right', render: (r: any) => fmtNum(r.power_kw, 1) },
      { title: '负荷率', key: 'load_ratio', width: 90, align: 'right', render: (r: any) => fmtPct(r.load_ratio) },
      { title: '冷冻供水(°C)', key: 'chw_supply_temp', width: 110, align: 'right', render: (r: any) => fmtNum(r.chw_supply_temp) },
      { title: '冷冻回水(°C)', key: 'chw_return_temp', width: 110, align: 'right', render: (r: any) => fmtNum(r.chw_return_temp) },
      { title: '冷却供水(°C)', key: 'cw_supply_temp', width: 110, align: 'right', render: (r: any) => fmtNum(r.cw_supply_temp) },
      { title: '冷却回水(°C)', key: 'cw_return_temp', width: 110, align: 'right', render: (r: any) => fmtNum(r.cw_return_temp) },
      { title: '状态', key: 'running_status', width: 90, render: (r: any) => h(NTag, { size: 'small', bordered: false, type: r.running_status === 'running' ? 'success' : 'default' }, { default: () => statusText(r.running_status) }) },
    ]
  }

  if (type === 'ahu') {
    return [
      tsCol,
      { title: 'SAT(°C)', key: 'supply_air_temp', width: 90, align: 'right', render: (r: any) => fmtNum(r.supply_air_temp) },
      { title: 'RAT(°C)', key: 'return_air_temp', width: 90, align: 'right', render: (r: any) => fmtNum(r.return_air_temp) },
      { title: 'MAT(°C)', key: 'mixed_air_temp', width: 90, align: 'right', render: (r: any) => fmtNum(r.mixed_air_temp) },
      { title: 'OAT(°C)', key: 'outdoor_air_temp', width: 90, align: 'right', render: (r: any) => fmtNum(r.outdoor_air_temp) },
      { title: '风机转速', key: 'supply_fan_speed', width: 90, align: 'right', render: (r: any) => fmtPct(r.supply_fan_speed) },
      { title: '冷水阀', key: 'chw_valve_pos', width: 80, align: 'right', render: (r: any) => fmtPct(r.chw_valve_pos) },
      { title: '热水阀', key: 'hw_valve_pos', width: 80, align: 'right', render: (r: any) => fmtPct(r.hw_valve_pos) },
      { title: '模式', key: 'operating_mode', width: 80, render: (r: any) => h(NTag, { size: 'small', bordered: false }, { default: () => modeText(r.operating_mode) }) },
    ]
  }

  if (type === 'boiler') {
    return [
      tsCol,
      { title: '热水供水(°C)', key: 'hw_supply_temp', width: 110, align: 'right', render: (r: any) => fmtNum(r.hw_supply_temp) },
      { title: '热水回水(°C)', key: 'hw_return_temp', width: 110, align: 'right', render: (r: any) => fmtNum(r.hw_return_temp) },
      { title: '效率', key: 'efficiency', width: 80, align: 'right', render: (r: any) => fmtPct(r.efficiency) },
      { title: '燃烧率', key: 'firing_rate', width: 80, align: 'right', render: (r: any) => fmtPct(r.firing_rate) },
      { title: '功率(kW)', key: 'power_kw', width: 100, align: 'right', render: (r: any) => fmtNum(r.power_kw) },
      { title: '烟气温度(°C)', key: 'flue_gas_temp', width: 110, align: 'right', render: (r: any) => fmtNum(r.flue_gas_temp) },
      { title: '状态', key: 'running_status', width: 90, render: (r: any) => h(NTag, { size: 'small', bordered: false, type: r.running_status === 'running' ? 'success' : 'default' }, { default: () => statusText(r.running_status) }) },
    ]
  }

  if (type === 'vav') {
    return [
      tsCol,
      { title: '区域温度(°C)', key: 'zone_temp', width: 110, align: 'right', render: (r: any) => fmtNum(r.zone_temp) },
      { title: '制冷设定(°C)', key: 'zone_temp_setpoint_clg', width: 110, align: 'right', render: (r: any) => fmtNum(r.zone_temp_setpoint_clg) },
      { title: '制热设定(°C)', key: 'zone_temp_setpoint_htg', width: 110, align: 'right', render: (r: any) => fmtNum(r.zone_temp_setpoint_htg) },
      { title: '风阀开度', key: 'damper_pos', width: 90, align: 'right', render: (r: any) => fmtPct(r.damper_pos) },
      { title: 'CO₂(ppm)', key: 'zone_co2', width: 100, align: 'right', render: (r: any) => r.zone_co2 != null ? r.zone_co2.toFixed(0) : '--' },
      { title: '模式', key: 'operating_mode', width: 80, render: (r: any) => h(NTag, { size: 'small', bordered: false }, { default: () => modeText(r.operating_mode) }) },
      { title: '占用', key: 'occupancy_status', width: 80, render: (r: any) => h(NTag, { size: 'small', type: r.occupancy_status === 'occupied' ? 'success' : 'default', bordered: false }, { default: () => r.occupancy_status === 'occupied' ? '有人' : '无人' }) },
    ]
  }

  if (['chw_pump', 'cw_pump', 'hw_pump'].includes(type || '')) {
    return [
      tsCol,
      { title: '转速', key: 'speed', width: 80, align: 'right', render: (r: any) => fmtPct(r.speed) },
      { title: '功率(kW)', key: 'power_kw', width: 100, align: 'right', render: (r: any) => fmtNum(r.power_kw) },
      { title: '流量', key: 'flow_rate', width: 80, align: 'right', render: (r: any) => fmtNum(r.flow_rate) },
      { title: '入口压力', key: 'inlet_pressure', width: 100, align: 'right', render: (r: any) => fmtNum(r.inlet_pressure) },
      { title: '出口压力', key: 'outlet_pressure', width: 100, align: 'right', render: (r: any) => fmtNum(r.outlet_pressure) },
      { title: '压差', key: 'differential_pressure', width: 80, align: 'right', render: (r: any) => fmtNum(r.differential_pressure) },
      { title: '状态', key: 'running_status', width: 90, render: (r: any) => h(NTag, { size: 'small', bordered: false, type: r.running_status === 'running' ? 'success' : 'default' }, { default: () => statusText(r.running_status) }) },
    ]
  }

  if (type === 'cooling_tower') {
    return [
      tsCol,
      { title: '风机转速', key: 'fan_speed', width: 90, align: 'right', render: (r: any) => fmtPct(r.fan_speed) },
      { title: '风机功率(kW)', key: 'fan_power_kw', width: 110, align: 'right', render: (r: any) => fmtNum(r.fan_power_kw) },
      { title: '进水温度(°C)', key: 'cw_inlet_temp', width: 110, align: 'right', render: (r: any) => fmtNum(r.cw_inlet_temp) },
      { title: '出水温度(°C)', key: 'cw_outlet_temp', width: 110, align: 'right', render: (r: any) => fmtNum(r.cw_outlet_temp) },
      { title: '湿球温度(°C)', key: 'wet_bulb_temp', width: 110, align: 'right', render: (r: any) => fmtNum(r.wet_bulb_temp) },
      { title: '逼近度(°C)', key: 'approach', width: 100, align: 'right', render: (r: any) => fmtNum(r.approach) },
      { title: '状态', key: 'running_status', width: 90, render: (r: any) => h(NTag, { size: 'small', bordered: false, type: r.running_status === 'running' ? 'success' : 'default' }, { default: () => statusText(r.running_status) }) },
    ]
  }

  return [tsCol]
})

// ----------------------------------------------------------------
// Chart options per device type
// ----------------------------------------------------------------
function makeLineChartOption(config: {
  timestamps: string[]
  series: { name: string; data: (number | null)[]; color: string }[]
  yName?: string
}) {
  return {
    tooltip: { trigger: 'axis' },
    legend: { bottom: 0, textStyle: { fontSize: 11 } },
    grid: { top: 16, right: 16, bottom: 40, left: 48, containLabel: false },
    xAxis: {
      type: 'category',
      data: config.timestamps,
      axisLine: { lineStyle: { color: '#d1d5db' } },
      axisLabel: { fontSize: 10, color: '#6b7280', rotate: 30 },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      name: config.yName || '',
      nameTextStyle: { fontSize: 11, color: '#6b7280' },
      axisLine: { show: false },
      axisLabel: { fontSize: 11, color: '#6b7280' },
      splitLine: { lineStyle: { color: '#f3f4f6' } },
    },
    series: config.series.map((s) => ({
      name: s.name,
      type: 'line',
      data: s.data,
      symbol: 'none',
      lineStyle: { width: 2, color: s.color },
      itemStyle: { color: s.color },
    })),
  }
}

// Chiller COP chart
const chillerCopChartOption = computed(() => {
  const records = deviceRecords.value
  return makeLineChartOption({
    timestamps: records.map((r: any) => fmtTimestamp(r.timestamp)),
    yName: 'COP',
    series: [
      { name: 'COP', data: records.map((r: any) => r.cop ?? null), color: '#18a058' },
    ],
  })
})

// Chiller temperature chart
const chillerTempChartOption = computed(() => {
  const records = deviceRecords.value
  return makeLineChartOption({
    timestamps: records.map((r: any) => fmtTimestamp(r.timestamp)),
    yName: '°C',
    series: [
      { name: '冷冻水供水', data: records.map((r: any) => r.chw_supply_temp ?? null), color: '#2080f0' },
      { name: '冷冻水回水', data: records.map((r: any) => r.chw_return_temp ?? null), color: '#36ad6a' },
      { name: '冷却水供水', data: records.map((r: any) => r.cw_supply_temp ?? null), color: '#f0a020' },
      { name: '冷却水回水', data: records.map((r: any) => r.cw_return_temp ?? null), color: '#d03050' },
    ],
  })
})

// AHU temperature chart
const ahuTempChartOption = computed(() => {
  const records = deviceRecords.value
  return makeLineChartOption({
    timestamps: records.map((r: any) => fmtTimestamp(r.timestamp)),
    yName: '°C',
    series: [
      { name: 'SAT', data: records.map((r: any) => r.supply_air_temp ?? null), color: '#2080f0' },
      { name: 'RAT', data: records.map((r: any) => r.return_air_temp ?? null), color: '#18a058' },
      { name: 'MAT', data: records.map((r: any) => r.mixed_air_temp ?? null), color: '#f0a020' },
      { name: 'OAT', data: records.map((r: any) => r.outdoor_air_temp ?? null), color: '#d03050' },
    ],
  })
})

// AHU valve chart
const ahuValveChartOption = computed(() => {
  const records = deviceRecords.value
  return makeLineChartOption({
    timestamps: records.map((r: any) => fmtTimestamp(r.timestamp)),
    yName: '%',
    series: [
      { name: '冷水阀', data: records.map((r: any) => r.chw_valve_pos != null ? r.chw_valve_pos * 100 : null), color: '#2080f0' },
      { name: '热水阀', data: records.map((r: any) => r.hw_valve_pos != null ? r.hw_valve_pos * 100 : null), color: '#d03050' },
      { name: '风机转速', data: records.map((r: any) => r.supply_fan_speed != null ? r.supply_fan_speed * 100 : null), color: '#18a058' },
    ],
  })
})

// Boiler temperature chart
const boilerTempChartOption = computed(() => {
  const records = deviceRecords.value
  return makeLineChartOption({
    timestamps: records.map((r: any) => fmtTimestamp(r.timestamp)),
    yName: '°C',
    series: [
      { name: '热水供水', data: records.map((r: any) => r.hw_supply_temp ?? null), color: '#d03050' },
      { name: '热水回水', data: records.map((r: any) => r.hw_return_temp ?? null), color: '#2080f0' },
      { name: '烟气温度', data: records.map((r: any) => r.flue_gas_temp ?? null), color: '#f0a020' },
    ],
  })
})

// Boiler efficiency chart
const boilerEffChartOption = computed(() => {
  const records = deviceRecords.value
  return makeLineChartOption({
    timestamps: records.map((r: any) => fmtTimestamp(r.timestamp)),
    yName: '%',
    series: [
      { name: '效率', data: records.map((r: any) => r.efficiency != null ? r.efficiency * 100 : null), color: '#18a058' },
      { name: '燃烧率', data: records.map((r: any) => r.firing_rate != null ? r.firing_rate * 100 : null), color: '#f0a020' },
    ],
  })
})

// VAV temperature chart
const vavTempChartOption = computed(() => {
  const records = deviceRecords.value
  return makeLineChartOption({
    timestamps: records.map((r: any) => fmtTimestamp(r.timestamp)),
    yName: '°C',
    series: [
      { name: '区域温度', data: records.map((r: any) => r.zone_temp ?? null), color: '#2080f0' },
      { name: '制冷设定', data: records.map((r: any) => r.zone_temp_setpoint_clg ?? null), color: '#18a058' },
      { name: '制热设定', data: records.map((r: any) => r.zone_temp_setpoint_htg ?? null), color: '#d03050' },
    ],
  })
})

// Pump chart
const pumpChartOption = computed(() => {
  const records = deviceRecords.value
  return makeLineChartOption({
    timestamps: records.map((r: any) => fmtTimestamp(r.timestamp)),
    series: [
      { name: '转速', data: records.map((r: any) => r.speed != null ? r.speed * 100 : null), color: '#2080f0' },
      { name: '功率(kW)', data: records.map((r: any) => r.power_kw ?? null), color: '#d03050' },
      { name: '流量', data: records.map((r: any) => r.flow_rate ?? null), color: '#18a058' },
    ],
  })
})

// Cooling Tower chart
const ctChartOption = computed(() => {
  const records = deviceRecords.value
  return makeLineChartOption({
    timestamps: records.map((r: any) => fmtTimestamp(r.timestamp)),
    yName: '°C',
    series: [
      { name: '进水温度', data: records.map((r: any) => r.cw_inlet_temp ?? null), color: '#d03050' },
      { name: '出水温度', data: records.map((r: any) => r.cw_outlet_temp ?? null), color: '#2080f0' },
      { name: '湿球温度', data: records.map((r: any) => r.wet_bulb_temp ?? null), color: '#18a058' },
      { name: '逼近度', data: records.map((r: any) => r.approach ?? null), color: '#f0a020' },
    ],
  })
})

// ----------------------------------------------------------------
// Init
// ----------------------------------------------------------------
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
.param-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px 24px;
}

.param-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid var(--border-light);
}

.param-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.param-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
}
</style>
