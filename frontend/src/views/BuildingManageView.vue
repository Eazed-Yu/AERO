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
        v-model:value="typeFilter"
        :options="buildingTypeOptions"
        placeholder="全部建筑类型"
        clearable
        size="small"
        style="width: 160px"
      />
      <n-button size="small" @click="fetchBuildings">查询</n-button>
      <div style="flex: 1" />
      <n-button size="small" type="primary" :disabled="!selectedRegion" @click="openCreate">新增建筑</n-button>
    </div>

    <div class="surface" style="padding: 0">
      <n-data-table
        :columns="columns"
        :data="buildings"
        :loading="loading"
        :row-key="(row: Building) => row.building_id"
        size="small"
        :bordered="false"
      />
    </div>

    <n-modal v-model:show="showModal" preset="card" :title="modalTitle" style="width: 680px">
      <n-form ref="formRef" :model="form" :rules="rules" label-placement="left" label-width="100">
        <n-grid :cols="2" :x-gap="12">
          <n-form-item-gi label="建筑名称" path="name">
            <n-input v-model:value="form.name" />
          </n-form-item-gi>
          <n-form-item-gi label="建筑类型" path="building_type">
            <n-select v-model:value="form.building_type" :options="buildingTypeOptions" placeholder="选择建筑类型" />
          </n-form-item-gi>
          <n-form-item-gi label="面积(m²)" path="area">
            <n-input-number v-model:value="form.area" :min="1" style="width: 100%" />
          </n-form-item-gi>
          <n-form-item-gi label="楼层">
            <n-input-number v-model:value="form.floors" :min="1" style="width: 100%" />
          </n-form-item-gi>
          <n-form-item-gi label="建成年份">
            <n-input-number v-model:value="form.year_built" :min="1900" :max="2100" style="width: 100%" />
          </n-form-item-gi>
        </n-grid>
        <n-form-item label="地址">
          <n-input v-model:value="form.address" />
        </n-form-item>
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
import { h, onMounted, reactive, ref, computed } from 'vue'
import {
  NButton,
  NDataTable,
  NForm,
  NFormItem,
  NFormItemGi,
  NGrid,
  NInput,
  NInputNumber,
  NModal,
  NSelect,
  useMessage,
  useDialog,
  type DataTableColumn,
  type FormInst,
  type FormRules,
} from 'naive-ui'
import { buildingsApi } from '@/api/buildings'
import { useRegionStore } from '@/stores/region'
import type { Building } from '@/types/building'

const message = useMessage()
const dialog = useDialog()
const regionStore = useRegionStore()

const loading = ref(false)
const saving = ref(false)
const buildings = ref<Building[]>([])
const typeFilter = ref<string | null>(null)
const selectedRegion = ref<string>('')

const showModal = ref(false)
const mode = ref<'create' | 'edit'>('create')
const editingBuildingId = ref('')
const formRef = ref<FormInst | null>(null)

const form = reactive({
  name: '',
  building_type: '' as string,
  area: null as number | null,
  address: '',
  floors: null as number | null,
  year_built: null as number | null,
})

const modalTitle = computed(() => (mode.value === 'create' ? '新增建筑' : '编辑建筑'))

const rules: FormRules = {
  name: [{ required: true, message: '请输入建筑名称', trigger: ['blur', 'input'] }],
  building_type: [{ required: true, message: '请选择建筑类型', trigger: ['blur', 'change'] }],
  area: [{ required: true, type: 'number', message: '请输入面积', trigger: ['blur', 'change'] }],
}

const regionOptions = computed(() =>
  regionStore.regions.map((r) => ({
    label: r.name,
    value: r.region_id,
  }))
)

const buildingTypeOptions = [
  { label: '办公', value: 'office' },
  { label: '商业', value: 'commercial' },
  { label: '住宅', value: 'residential' },
  { label: '教育', value: 'education' },
  { label: '医疗', value: 'medical' },
  { label: '工业', value: 'industrial' },
  { label: '酒店', value: 'hotel' },
  { label: '文体', value: 'cultural' },
  { label: '综合体', value: 'mixed_use' },
  { label: '数据中心', value: 'data_center' },
]

const columns: DataTableColumn<Building>[] = [
  { title: 'ID', key: 'building_id', width: 80 },
  { title: '名称', key: 'name', width: 180 },
  {
    title: '类型',
    key: 'building_type',
    width: 120,
    render(row) {
      const opt = buildingTypeOptions.find((o) => o.value === row.building_type)
      return opt ? opt.label : row.building_type
    },
  },
  { title: '面积(m²)', key: 'area', width: 120 },
  { title: '地址', key: 'address', ellipsis: { tooltip: true } },
  {
    title: '操作',
    key: 'actions',
    width: 180,
    render(row) {
      return h('div', { style: 'display:flex;gap:8px;' }, [
        h(
          NButton,
          { size: 'tiny', onClick: () => openEdit(row) },
          { default: () => '编辑' }
        ),
        h(
          NButton,
          {
            size: 'tiny',
            type: 'error',
            ghost: true,
            onClick: () => remove(row),
          },
          { default: () => '删除' }
        ),
      ])
    },
  },
]

function resetForm() {
  form.name = ''
  form.building_type = ''
  form.area = null
  form.address = ''
  form.floors = null
  form.year_built = null
}

function openCreate() {
  mode.value = 'create'
  editingBuildingId.value = ''
  resetForm()
  showModal.value = true
}

function openEdit(row: Building) {
  mode.value = 'edit'
  editingBuildingId.value = row.building_id
  form.name = row.name
  form.building_type = row.building_type
  form.area = row.area
  form.address = row.address || ''
  form.floors = row.floors ?? null
  form.year_built = row.year_built ?? null
  showModal.value = true
}

function onRegionChange(val: string) {
  selectedRegion.value = val
  if (val) fetchBuildings()
}

async function fetchBuildings() {
  if (!selectedRegion.value) return

  loading.value = true
  try {
    const params: { region_id: string; building_type?: string } = { region_id: selectedRegion.value }
    if (typeFilter.value) params.building_type = typeFilter.value
    const { data } = await buildingsApi.list(params)
    buildings.value = data
  } finally {
    loading.value = false
  }
}

async function submit() {
  await formRef.value?.validate()
  saving.value = true
  try {
    const payload = {
      region_id: selectedRegion.value,
      name: form.name,
      building_type: form.building_type,
      area: form.area!,
      address: form.address || undefined,
      floors: form.floors ?? undefined,
      year_built: form.year_built ?? undefined,
    }

    if (mode.value === 'create') {
      await buildingsApi.create(payload)
      message.success('新增成功')
    } else {
      await buildingsApi.update(editingBuildingId.value, payload)
      message.success('更新成功')
    }

    showModal.value = false
    await fetchBuildings()
  } catch {
    message.error('保存失败，请检查输入')
  } finally {
    saving.value = false
  }
}

function remove(row: Building) {
  dialog.warning({
    title: '确认删除',
    content: `确定删除建筑 ${row.name} 吗？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await buildingsApi.remove(row.building_id)
        message.success('删除成功')
        await fetchBuildings()
      } catch {
        message.error('删除失败')
      }
    },
  })
}

onMounted(() => {
  if (regionStore.regions.length === 0) {
    regionStore.fetchRegions()
  }
  if (regionStore.current) {
    selectedRegion.value = regionStore.current
    fetchBuildings()
  }
})
</script>
