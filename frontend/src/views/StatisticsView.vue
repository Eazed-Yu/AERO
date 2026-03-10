<template>
  <div class="page-content">
    <div class="toolbar surface" style="margin-bottom: 16px; border-radius: 3px">
      <n-select
        v-model:value="period"
        :options="periodOptions"
        size="small"
        style="width: 120px"
      />
      <n-select
        v-model:value="metric"
        :options="metricOptions"
        size="small"
        style="width: 160px"
      />
      <n-date-picker
        v-model:value="dateRange"
        type="daterange"
        size="small"
        clearable
        style="width: 280px"
      />
      <n-button size="small" type="primary" @click="fetchAll">查询</n-button>
    </div>

    <n-spin :show="loading">
      <div class="grid-2">
        <div class="surface" style="padding: 16px">
          <div class="section-title">聚合统计</div>
          <EnergyTrendChart :data="aggChartData" />
        </div>
        <div class="surface" style="padding: 16px">
          <div class="section-title">COP趋势</div>
          <COPTrendChart :data="copData" />
        </div>
      </div>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { NSelect, NDatePicker, NButton, NSpin } from 'naive-ui'
import EnergyTrendChart from '@/components/charts/EnergyTrendChart.vue'
import COPTrendChart from '@/components/charts/COPTrendChart.vue'
import { useBuildingStore } from '@/stores/building'
import { statisticsApi } from '@/api/statistics'
import type { AggregationResult, COPResult } from '@/types/statistics'

const buildingStore = useBuildingStore()
const loading = ref(false)

const period = ref('day')
const metric = ref('electricity_kwh')

const periodOptions = [
  { label: '按小时', value: 'hour' },
  { label: '按天', value: 'day' },
  { label: '按周', value: 'week' },
  { label: '按月', value: 'month' },
]

const metricOptions = [
  { label: '用电量 (kWh)', value: 'electricity_kwh' },
  { label: '用水量 (m³)', value: 'water_m3' },
  { label: 'HVAC (kWh)', value: 'hvac_kwh' },
  { label: '燃气 (m³)', value: 'gas_m3' },
]

const defaultRange = (): [number, number] => {
  const end = Date.now()
  const start = end - 30 * 24 * 60 * 60 * 1000
  return [start, end]
}

const dateRange = ref<[number, number] | null>(defaultRange())

const aggChartData = ref<{ timestamp: string; electricity_kwh?: number; hvac_kwh?: number }[]>([])
const copData = ref<COPResult[]>([])

function getRange() {
  const range = dateRange.value || defaultRange()
  return {
    start_time: new Date(range[0]).toISOString().slice(0, 19),
    end_time: new Date(range[1]).toISOString().slice(0, 19),
  }
}

async function fetchAll() {
  const buildingId = buildingStore.current
  if (!buildingId) return

  loading.value = true
  const range = getRange()

  try {
    const [aggRes, copRes] = await Promise.allSettled([
      statisticsApi.aggregate({
        building_id: buildingId,
        start_time: range.start_time,
        end_time: range.end_time,
        period: period.value,
        metrics: metric.value + ',hvac_kwh',
      }),
      statisticsApi.cop({
        building_id: buildingId,
        start_time: range.start_time,
        end_time: range.end_time,
        period: period.value,
      }),
    ])

    // Build chart data from aggregation results
    if (aggRes.status === 'fulfilled') {
      const data = aggRes.value.data
      const byPeriod: Record<string, { electricity_kwh?: number; hvac_kwh?: number }> = {}
      for (const item of data) {
        const key = item.period_start
        if (!byPeriod[key]) byPeriod[key] = {}
        if (item.metric_name === metric.value) {
          byPeriod[key].electricity_kwh = item.sum ?? item.avg ?? 0
        }
        if (item.metric_name === 'hvac_kwh') {
          byPeriod[key].hvac_kwh = item.sum ?? item.avg ?? 0
        }
      }
      const sortedKeys = Object.keys(byPeriod).sort()
      aggChartData.value = sortedKeys.map((k) => ({
        timestamp: k.slice(0, period.value === 'hour' ? 16 : 10),
        electricity_kwh: byPeriod[k].electricity_kwh,
        hvac_kwh: byPeriod[k].hvac_kwh,
      }))
    } else {
      aggChartData.value = []
    }

    if (copRes.status === 'fulfilled') {
      copData.value = copRes.value.data
    } else {
      copData.value = []
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (buildingStore.current) {
    fetchAll()
  }
})

watch(() => buildingStore.current, (val) => {
  if (val) fetchAll()
})
</script>
