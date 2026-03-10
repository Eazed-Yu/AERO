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
      />
    </div>

    <n-modal v-model:show="showModal" preset="card" :title="modalTitle" style="width: 700px">
      <n-form ref="formRef" :model="form" :rules="rules" label-placement="left" label-width="110">
        <n-grid :cols="2" :x-gap="12">
          <n-form-item-gi label="建筑ID" path="building_id">
            <n-input v-model:value="form.building_id" />
          </n-form-item-gi>
          <n-form-item-gi label="设备ID" path="device_id">
            <n-input v-model:value="form.device_id" :disabled="mode === 'edit'" />
          </n-form-item-gi>
          <n-form-item-gi label="设备名称" path="device_name">
            <n-input v-model:value="form.device_name" />
          </n-form-item-gi>
          <n-form-item-gi label="设备类型" path="device_type">
            <n-input v-model:value="form.device_type" />
          </n-form-item-gi>
          <n-form-item-gi label="额定功率(kW)">
            <n-input-number v-model:value="form.rated_power_kw" :min="0" style="width: 100%" />
          </n-form-item-gi>
        </n-grid>
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
const form = ref({
  building_id: '',
  device_id: '',
  device_name: '',
  device_type: '',
  rated_power_kw: null as number | null,
})

const modalTitle = computed(() => (mode.value === 'create' ? '新增设备' : '编辑设备'))

const rules: FormRules = {
  building_id: [{ required: true, message: '请输入建筑ID', trigger: ['blur', 'input'] }],
  device_id: [{ required: true, message: '请输入设备ID', trigger: ['blur', 'input'] }],
  device_name: [{ required: true, message: '请输入设备名称', trigger: ['blur', 'input'] }],
  device_type: [{ required: true, message: '请输入设备类型', trigger: ['blur', 'input'] }],
}

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

function resetForm() {
  form.value = {
    building_id: buildingStore.current || '',
    device_id: '',
    device_name: '',
    device_type: '',
    rated_power_kw: null,
  }
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
    rated_power_kw: row.rated_power_kw ?? null,
  }
  showModal.value = true
}

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

async function submit() {
  await formRef.value?.validate()
  saving.value = true
  try {
    if (mode.value === 'create') {
      await equipmentApi.create({
        building_id: form.value.building_id,
        device_id: form.value.device_id,
        device_name: form.value.device_name,
        device_type: form.value.device_type,
        rated_power_kw: form.value.rated_power_kw ?? undefined,
      })
      message.success('新增成功')
    } else {
      await equipmentApi.update(form.value.device_id, {
        building_id: form.value.building_id,
        device_name: form.value.device_name,
        device_type: form.value.device_type,
        rated_power_kw: form.value.rated_power_kw ?? undefined,
      })
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
    content: `确定删除设备 ${row.device_id} 吗？`,
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
