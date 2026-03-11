<template>
  <div class="page-content">
    <div class="toolbar surface" style="margin-bottom: 16px; border-radius: 3px">
      <n-input
        v-model:value="nameFilter"
        placeholder="按名称过滤"
        clearable
        size="small"
        style="width: 220px"
      />
      <n-button size="small" @click="fetchRegions">查询</n-button>
      <div style="flex: 1" />
      <n-button size="small" type="primary" @click="openCreate">新增区域</n-button>
    </div>

    <div class="surface" style="padding: 0">
      <n-data-table
        :columns="columns"
        :data="filteredRegions"
        :loading="loading"
        :row-key="(row: Region) => row.region_id"
        size="small"
        :bordered="false"
      />
    </div>

    <n-modal v-model:show="showModal" preset="card" :title="modalTitle" style="width: 600px">
      <n-form ref="formRef" :model="form" :rules="rules" label-placement="left" label-width="80">
        <n-form-item label="名称" path="name">
          <n-input v-model:value="form.name" placeholder="区域名称" />
        </n-form-item>
        <n-form-item label="描述">
          <n-input v-model:value="form.description" type="textarea" placeholder="区域描述" :rows="2" />
        </n-form-item>
        <n-form-item label="地址">
          <n-input v-model:value="form.address" placeholder="区域地址" />
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
  NInput,
  NModal,
  useMessage,
  useDialog,
  type DataTableColumn,
  type FormInst,
  type FormRules,
} from 'naive-ui'
import { regionsApi } from '@/api/region'
import { useRegionStore } from '@/stores/region'
import type { Region } from '@/types/region'

const message = useMessage()
const dialog = useDialog()
const regionStore = useRegionStore()

const loading = ref(false)
const saving = ref(false)
const regions = ref<Region[]>([])
const nameFilter = ref('')

const showModal = ref(false)
const mode = ref<'create' | 'edit'>('create')
const editingRegionId = ref('')
const formRef = ref<FormInst | null>(null)

const form = reactive({
  name: '',
  description: '',
  address: '',
})

const modalTitle = computed(() => (mode.value === 'create' ? '新增区域' : '编辑区域'))

const rules: FormRules = {
  name: [{ required: true, message: '请输入区域名称', trigger: ['blur', 'input'] }],
}

const filteredRegions = computed(() => {
  if (!nameFilter.value) return regions.value
  const kw = nameFilter.value.toLowerCase()
  return regions.value.filter(
    (r) => r.name.toLowerCase().includes(kw) || r.region_id.toLowerCase().includes(kw)
  )
})

const columns: DataTableColumn<Region>[] = [
  { title: 'ID', key: 'region_id', width: 80 },
  { title: '名称', key: 'name', width: 180 },
  { title: '描述', key: 'description', ellipsis: { tooltip: true }, render(row) { return row.description || '--' } },
  { title: '地址', key: 'address', ellipsis: { tooltip: true }, render(row) { return row.address || '--' } },
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
  form.description = ''
  form.address = ''
}

function openCreate() {
  mode.value = 'create'
  editingRegionId.value = ''
  resetForm()
  showModal.value = true
}

function openEdit(row: Region) {
  mode.value = 'edit'
  editingRegionId.value = row.region_id
  form.name = row.name
  form.description = row.description || ''
  form.address = row.address || ''
  showModal.value = true
}

async function fetchRegions() {
  loading.value = true
  try {
    const { data } = await regionsApi.list()
    regions.value = data
  } finally {
    loading.value = false
  }
}

async function submit() {
  await formRef.value?.validate()
  saving.value = true
  try {
    const payload = {
      name: form.name,
      description: form.description || undefined,
      address: form.address || undefined,
    }

    if (mode.value === 'create') {
      await regionsApi.create(payload)
      message.success('新增成功')
    } else {
      await regionsApi.update(editingRegionId.value, payload)
      message.success('更新成功')
    }

    showModal.value = false
    await fetchRegions()
    await regionStore.fetchRegions()
  } catch {
    message.error('保存失败，请检查输入')
  } finally {
    saving.value = false
  }
}

function remove(row: Region) {
  dialog.warning({
    title: '确认删除',
    content: `确定删除区域 ${row.name} 吗？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await regionsApi.remove(row.region_id)
        message.success('删除成功')
        await fetchRegions()
        await regionStore.fetchRegions()
      } catch {
        message.error('删除失败')
      }
    },
  })
}

onMounted(() => {
  fetchRegions()
})
</script>
