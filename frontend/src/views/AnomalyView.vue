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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted, watch } from 'vue'
import {
  NSelect,
  NButton,
  NDataTable,
  NTag,
  type DataTableColumn,
} from 'naive-ui'
import AnomalyScatterChart from '@/components/charts/AnomalyScatterChart.vue'
import { useBuildingStore } from '@/stores/building'
import { anomalyApi } from '@/api/anomaly'
import type { AnomalyEvent } from '@/types/anomaly'

const buildingStore = useBuildingStore()
const tableLoading = ref(false)
const detecting = ref(false)
const anomalies = ref<AnomalyEvent[]>([])

const severityFilter = ref<string | null>(null)
const resolvedFilter = ref<string | null>(null)

const severityOptions = [
  { label: 'Critical', value: 'critical' },
  { label: 'High', value: 'high' },
  { label: 'Medium', value: 'medium' },
  { label: 'Low', value: 'low' },
]

const resolvedOptions = [
  { label: '未解决', value: 'false' },
  { label: '已解决', value: 'true' },
]

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
  { title: '检测方法', key: 'detection_method', width: 100 },
]

const scatterData = computed(() =>
  anomalies.value.map((a) => ({
    timestamp: a.timestamp,
    metric_value: a.metric_value,
    severity: a.severity,
    anomaly_type: a.anomaly_type,
  }))
)

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

onMounted(() => {
  fetchAnomalies()
})

watch(() => buildingStore.current, () => {
  fetchAnomalies()
})
</script>
