<template>
  <div class="page-content">
    <div class="toolbar surface" style="margin-bottom: 16px; border-radius: 3px">
      <n-select
        v-model:value="severityFilter"
        :options="severityOptions"
        placeholder="全部级别"
        clearable
        size="small"
        style="width: 140px"
      />
      <n-select
        v-model:value="resolvedFilter"
        :options="resolvedOptions"
        placeholder="全部状态"
        clearable
        size="small"
        style="width: 140px"
      />
      <n-button size="small" @click="fetchAnomalies">刷新</n-button>
      <n-button size="small" @click="openCreate">手动新增</n-button>
      <div style="flex: 1" />
      <n-button
        size="small"
        type="primary"
        :loading="detecting"
        @click="runDetection"
      >
        执行检测
      </n-button>
    </div>

    <div class="surface" style="padding: 0; margin-bottom: 16px">
      <n-data-table
        :columns="columns"
        :data="anomalies"
        :loading="tableLoading"
        :row-key="(row: AnomalyEvent) => row.id"
        size="small"
        :bordered="false"
        :max-height="420"
      />
    </div>

    <div class="surface" style="padding: 16px">
      <div class="section-title">异常分布</div>
      <AnomalyScatterChart :data="scatterData" />
    </div>

    <n-modal v-model:show="showModal" preset="card" title="手动新增异常" style="width: 760px">
      <n-form ref="formRef" :model="form" :rules="rules" label-placement="left" label-width="120">
        <n-grid :cols="2" :x-gap="12">
          <n-form-item-gi label="建筑ID" path="building_id">
            <n-input v-model:value="form.building_id" />
          </n-form-item-gi>
          <n-form-item-gi label="时间(ISO)" path="timestamp">
            <n-input v-model:value="form.timestamp" placeholder="2026-03-10T08:00:00" />
          </n-form-item-gi>
          <n-form-item-gi label="异常类型" path="anomaly_type">
            <n-input v-model:value="form.anomaly_type" />
          </n-form-item-gi>
          <n-form-item-gi label="级别" path="severity">
            <n-select v-model:value="form.severity" :options="severityOptions" />
          </n-form-item-gi>
          <n-form-item-gi label="指标名" path="metric_name">
            <n-input v-model:value="form.metric_name" />
          </n-form-item-gi>
          <n-form-item-gi label="指标值" path="metric_value">
            <n-input-number v-model:value="form.metric_value" style="width:100%" />
          </n-form-item-gi>
        </n-grid>
        <n-form-item label="描述" path="description">
          <n-input v-model:value="form.description" type="textarea" :rows="3" />
        </n-form-item>
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
import AnomalyScatterChart from '@/components/charts/AnomalyScatterChart.vue'
import { useBuildingStore } from '@/stores/building'
import { anomalyApi } from '@/api/anomaly'
import type { AnomalyEvent } from '@/types/anomaly'

const buildingStore = useBuildingStore()
const message = useMessage()
const dialog = useDialog()
const tableLoading = ref(false)
const detecting = ref(false)
const saving = ref(false)
const anomalies = ref<AnomalyEvent[]>([])

const showModal = ref(false)
const formRef = ref<FormInst | null>(null)
const form = ref({
  building_id: '',
  timestamp: '',
  anomaly_type: '',
  severity: 'medium',
  metric_name: '',
  metric_value: null as number | null,
  description: '',
})

const severityFilter = ref<string | null>(null)
const resolvedFilter = ref<string | null>(null)

const severityOptions = [
  { label: 'critical', value: 'critical' },
  { label: 'high', value: 'high' },
  { label: 'medium', value: 'medium' },
  { label: 'low', value: 'low' },
]

const resolvedOptions = [
  { label: '未解决', value: 'false' },
  { label: '已解决', value: 'true' },
]

const rules: FormRules = {
  building_id: [{ required: true, message: '请输入建筑ID', trigger: ['blur', 'input'] }],
  timestamp: [{ required: true, message: '请输入时间(ISO)', trigger: ['blur', 'input'] }],
  anomaly_type: [{ required: true, message: '请输入异常类型', trigger: ['blur', 'input'] }],
  metric_name: [{ required: true, message: '请输入指标名', trigger: ['blur', 'input'] }],
  metric_value: [{ required: true, type: 'number', message: '请输入指标值', trigger: ['blur', 'change'] }],
  description: [{ required: true, message: '请输入描述', trigger: ['blur', 'input'] }],
}

const severityTagType: Record<string, 'error' | 'warning' | 'info' | 'default'> = {
  critical: 'error',
  high: 'warning',
  medium: 'info',
  low: 'default',
}

const columns: DataTableColumn<AnomalyEvent>[] = [
  {
    title: '时间',
    key: 'timestamp',
    width: 170,
    render(row) {
      return row.timestamp?.replace('T', ' ').slice(0, 19) ?? ''
    },
  },
  { title: '建筑ID', key: 'building_id', width: 120, ellipsis: { tooltip: true } },
  { title: '类型', key: 'anomaly_type', width: 120 },
  {
    title: '级别',
    key: 'severity',
    width: 90,
    render(row) {
      const sev = (row.severity || '').toLowerCase()
      return h(
        NTag,
        { type: severityTagType[sev] || 'default', size: 'small', bordered: false },
        { default: () => row.severity }
      )
    },
  },
  { title: '指标', key: 'metric_name', width: 130 },
  {
    title: '值',
    key: 'metric_value',
    width: 90,
    align: 'right',
    render(row) {
      return row.metric_value != null ? row.metric_value.toFixed(1) : '--'
    },
  },
  {
    title: '阈值',
    key: 'threshold_value',
    width: 90,
    align: 'right',
    render(row) {
      return row.threshold_value != null ? row.threshold_value.toFixed(1) : '--'
    },
  },
  { title: '描述', key: 'description', ellipsis: { tooltip: true } },
  {
    title: '状态',
    key: 'resolved',
    width: 80,
    render(row) {
      return h(
        NTag,
        {
          type: row.resolved ? 'success' : 'warning',
          size: 'small',
          bordered: false,
        },
        { default: () => (row.resolved ? '已解决' : '未解决') }
      )
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 170,
    render(row) {
      return h('div', { style: 'display:flex;gap:8px;' }, [
        h(
          NButton,
          { size: 'tiny', type: 'primary', ghost: true, disabled: row.resolved, onClick: () => resolve(row) },
          { default: () => '解决' }
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

const scatterData = computed(() =>
  anomalies.value.map((a) => ({
    timestamp: a.timestamp,
    metric_value: a.metric_value,
    severity: a.severity,
    anomaly_type: a.anomaly_type,
  }))
)

function resetForm() {
  form.value = {
    building_id: buildingStore.current || '',
    timestamp: new Date().toISOString().slice(0, 19),
    anomaly_type: '',
    severity: 'medium',
    metric_name: '',
    metric_value: null,
    description: '',
  }
}

function openCreate() {
  resetForm()
  showModal.value = true
}

async function submit() {
  await formRef.value?.validate()
  saving.value = true
  try {
    await anomalyApi.create({
      building_id: form.value.building_id,
      timestamp: form.value.timestamp,
      anomaly_type: form.value.anomaly_type,
      severity: form.value.severity,
      metric_name: form.value.metric_name,
      metric_value: form.value.metric_value!,
      description: form.value.description,
      detection_method: 'manual',
    })
    message.success('新增成功')
    showModal.value = false
    await fetchAnomalies()
  } catch {
    message.error('新增失败')
  } finally {
    saving.value = false
  }
}

async function fetchAnomalies() {
  tableLoading.value = true
  try {
    const params: Record<string, any> = {}
    if (buildingStore.current) params.building_id = buildingStore.current
    if (severityFilter.value) params.severity = severityFilter.value
    if (resolvedFilter.value != null) params.resolved = resolvedFilter.value === 'true'
    params.limit = 500

    const { data } = await anomalyApi.list(params)
    anomalies.value = data
  } catch {
    anomalies.value = []
  } finally {
    tableLoading.value = false
  }
}

async function runDetection() {
  const buildingId = buildingStore.current
  if (!buildingId) return

  detecting.value = true
  try {
    const end = new Date()
    const start = new Date()
    start.setDate(start.getDate() - 7)

    await anomalyApi.detect({
      building_id: buildingId,
      start_time: start.toISOString().slice(0, 19),
      end_time: end.toISOString().slice(0, 19),
    })
    await fetchAnomalies()
  } finally {
    detecting.value = false
  }
}

async function resolve(row: AnomalyEvent) {
  try {
    await anomalyApi.resolve(row.id)
    message.success('已标记为已解决')
    await fetchAnomalies()
  } catch {
    message.error('操作失败')
  }
}

function remove(row: AnomalyEvent) {
  dialog.warning({
    title: '确认删除',
    content: `确定删除异常 ${row.id} 吗？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await anomalyApi.remove(row.id)
        message.success('删除成功')
        await fetchAnomalies()
      } catch {
        message.error('删除失败')
      }
    },
  })
}

onMounted(() => {
  fetchAnomalies()
})

watch(() => buildingStore.current, () => {
  fetchAnomalies()
})
</script>
