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
      <n-button size="small" @click="openCreate">新增设备</n-button>
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

    <n-modal v-model:show="showModal" preset="card" :title="modalTitle" style="width: 800px">
      <n-form ref="formRef" :model="form" :rules="rules" label-placement="left" label-width="110">
        <n-space vertical :size="0">
          <n-space :size="12">
            <n-form-item label="设备ID" path="device_id" style="width: 340px">
              <n-input v-model:value="form.device_id" :disabled="mode === 'edit'" placeholder="唯一标识" />
            </n-form-item>
            <n-form-item label="设备名称" path="device_name" style="width: 340px">
              <n-input v-model:value="form.device_name" placeholder="设备名称" />
            </n-form-item>
          </n-space>
          <n-space :size="12">
            <n-form-item label="设备类型" path="device_type" style="width: 340px">
              <n-select v-model:value="form.device_type" :options="deviceTypeOptions" placeholder="选择设备类型" />
            </n-form-item>
            <n-form-item label="系统类型" path="system_type" style="width: 340px">
              <n-select v-model:value="form.system_type" :options="systemTypeOptions" placeholder="选择系统类型" />
            </n-form-item>
          </n-space>
          <n-space :size="12">
            <n-form-item label="建筑ID" path="building_id" style="width: 340px">
              <n-select
                v-model:value="form.building_id"
                :options="buildingOptions"
                placeholder="选择建筑"
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
  useMessage,
  useDialog,
  type DataTableColumn,
  type FormInst,
  type FormRules,
} from 'naive-ui'
import { useBuildingStore } from '@/stores/building'
import { equipmentApi } from '@/api/equipment'
import type { Equipment } from '@/types/equipment'

const buildingStore = useBuildingStore()
const message = useMessage()
const dialog = useDialog()
const loading = ref(false)
const equipment = ref<Equipment[]>([])
const saving = ref(false)

const showModal = ref(false)
const mode = ref<'create' | 'edit'>('create')
const formRef = ref<FormInst | null>(null)
const installDateTs = ref<number | null>(null)

const form = ref({
  building_id: '',
  device_id: '',
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
  building_id: [{ required: true, message: '请选择建筑', trigger: ['blur', 'change'] }],
  device_id: [{ required: true, message: '请输入设备ID', trigger: ['blur', 'input'] }],
  device_name: [{ required: true, message: '请输入设备名称', trigger: ['blur', 'input'] }],
  device_type: [{ required: true, message: '请选择设备类型', trigger: ['blur', 'change'] }],
  system_type: [{ required: true, message: '请选择系统类型', trigger: ['blur', 'change'] }],
}

const buildingFilter = ref<string | null>(buildingStore.current || null)
const typeFilter = ref<string | null>(null)
const systemFilter = ref<string | null>(null)

const buildingOptions = computed(() =>
  buildingStore.buildings.map((b) => ({
    label: b.name,
    value: b.building_id,
  }))
)

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
  { title: '建筑ID', key: 'building_id', width: 130, ellipsis: { tooltip: true } },
  { title: '型号', key: 'model', width: 120, ellipsis: { tooltip: true }, render(row) { return row.model || '--' } },
  { title: '制造商', key: 'manufacturer', width: 120, ellipsis: { tooltip: true }, render(row) { return row.manufacturer || '--' } },
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
    title: '额定容量',
    key: 'rated_capacity',
    width: 100,
    align: 'right',
    render(row) {
      return row.rated_capacity != null ? row.rated_capacity.toFixed(1) : '--'
    },
  },
  {
    title: '额定COP',
    key: 'rated_cop',
    width: 90,
    align: 'right',
    render(row) {
      return row.rated_cop != null ? row.rated_cop.toFixed(2) : '--'
    },
  },
  { title: '安装位置', key: 'location', width: 120, ellipsis: { tooltip: true }, render(row) { return row.location || '--' } },
  {
    title: '安装日期',
    key: 'install_date',
    width: 110,
    render(row) {
      return row.install_date?.slice(0, 10) ?? '--'
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
    width: 140,
    fixed: 'right',
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

function resetForm() {
  form.value = {
    building_id: buildingStore.current || '',
    device_id: '',
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
  resetForm()
  showModal.value = true
}

function openEdit(row: Equipment) {
  mode.value = 'edit'
  form.value = {
    building_id: row.building_id,
    device_id: row.device_id,
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
  loading.value = true
  try {
    const params: Record<string, any> = {}
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

  // Convert install date timestamp to string
  if (installDateTs.value) {
    form.value.install_date = new Date(installDateTs.value).toISOString().slice(0, 10)
  } else {
    form.value.install_date = ''
  }

  try {
    const payload: Partial<Equipment> = {
      building_id: form.value.building_id,
      device_id: form.value.device_id,
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
      const { device_id, ...updatePayload } = payload
      await equipmentApi.update(form.value.device_id, updatePayload)
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
