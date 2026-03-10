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
        style="width: 180px"
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

      <!-- EUI Section -->
      <div class="surface" style="padding: 16px; margin-top: 16px" v-if="euiData">
        <div class="section-title">EUI 能耗强度</div>
        <div class="kpi-row" style="margin-top: 12px">
          <div class="kpi-item">
            <span class="kpi-label">建筑名称</span>
            <span class="kpi-value" style="font-size: 14px">{{ euiData.building_name }}</span>
          </div>
          <div class="kpi-item">
            <span class="kpi-label">总用电量</span>
            <span class="kpi-value">{{ formatNum(euiData.total_electricity_kwh, 0) }}<span class="kpi-unit">kWh</span></span>
          </div>
          <div class="kpi-item">
            <span class="kpi-label">建筑面积</span>
            <span class="kpi-value">{{ formatNum(euiData.area, 0) }}<span class="kpi-unit">m²</span></span>
          </div>
          <div class="kpi-item">
            <span class="kpi-label">EUI</span>
            <span class="kpi-value">{{ formatNum(euiData.eui, 2) }}<span class="kpi-unit">kWh/m²</span></span>
          </div>
          <div class="kpi-item" v-if="euiData.hvac_eui != null">
            <span class="kpi-label">HVAC EUI</span>
            <span class="kpi-value">{{ formatNum(euiData.hvac_eui, 2) }}<span class="kpi-unit">kWh/m²</span></span>
          </div>
        </div>
      </div>

      <!-- Plant Efficiency Section -->
      <div class="surface" style="padding: 16px; margin-top: 16px" v-if="plantData.length > 0">
        <div class="section-title">冷站效率</div>
        <n-data-table
          :columns="plantColumns"
          :data="plantData"
          size="small"
          :bordered="false"
          style="margin-top: 12px"
        />
      </div>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted, watch } from 'vue'
import { NSelect, NDatePicker, NButton, NSpin, NDataTable, NTag, type DataTableColumn } from 'naive-ui'
import EnergyTrendChart from '@/components/charts/EnergyTrendChart.vue'
import COPTrendChart from '@/components/charts/COPTrendChart.vue'
import { useBuildingStore } from '@/stores/building'
import { statisticsApi } from '@/api/statistics'
import type { AggregationResult, COPResult, EUIResult, PlantEfficiencyResult } from '@/types/statistics'

const buildingStore = useBuildingStore()
const loading = ref(false)

const period = ref('day')
const metric = ref('total_electricity_kwh')

const periodOptions = [
  { label: '按小时', value: 'hour' },
  { label: '按天', value: 'day' },
  { label: '按周', value: 'week' },
  { label: '按月', value: 'month' },
]

const metricOptions = [
  { label: '总用电量 (kWh)', value: 'total_electricity_kwh' },
  { label: 'HVAC用电 (kWh)', value: 'hvac_electricity_kwh' },
  { label: '照明用电 (kWh)', value: 'lighting_kwh' },
  { label: '插座用电 (kWh)', value: 'plug_load_kwh' },
  { label: '用水量 (m\u00B3)', value: 'water_m3' },
  { label: '燃气 (m\u00B3)', value: 'gas_m3' },
  { label: '峰值需量 (kW)', value: 'peak_demand_kw' },
  { label: '供冷量 (kWh)', value: 'cooling_kwh' },
  { label: '供热量 (kWh)', value: 'heating_kwh' },
]

const defaultRange = (): [number, number] => {
  const end = Date.now()
  const start = end - 30 * 24 * 60 * 60 * 1000
  return [start, end]
}

const dateRange = ref<[number, number] | null>(defaultRange())

const aggChartData = ref<{ timestamp: string; electricity_kwh?: number; hvac_kwh?: number }[]>([])
const copData = ref<COPResult[]>([])
const euiData = ref<EUIResult | null>(null)
const plantData = ref<PlantEfficiencyResult[]>([])

function formatNum(val: number | undefined | null, decimals = 1): string {
  if (val == null || isNaN(val)) return '--'
  return val.toFixed(decimals)
}

function getRange() {
  const range = dateRange.value || defaultRange()
  return {
    start_time: new Date(range[0]).toISOString().slice(0, 19),
    end_time: new Date(range[1]).toISOString().slice(0, 19),
  }
}

const plantColumns: DataTableColumn<PlantEfficiencyResult>[] = [
  {
    title: '时段',
    key: 'period_start',
    width: 160,
    render(row) {
      return row.period_start?.slice(0, 16).replace('T', ' ') ?? ''
    },
  },
  {
    title: '总供冷量(kWh)',
    key: 'total_cooling_kwh',
    width: 130,
    align: 'right',
    render(row) { return formatNum(row.total_cooling_kwh, 1) },
  },
  {
    title: '主机耗电(kWh)',
    key: 'chiller_power_kwh',
    width: 130,
    align: 'right',
    render(row) { return formatNum(row.chiller_power_kwh, 1) },
  },
  {
    title: '水泵耗电(kWh)',
    key: 'pump_power_kwh',
    width: 130,
    align: 'right',
    render(row) { return formatNum(row.pump_power_kwh, 1) },
  },
  {
    title: '冷却塔耗电(kWh)',
    key: 'tower_power_kwh',
    width: 140,
    align: 'right',
    render(row) { return formatNum(row.tower_power_kwh, 1) },
  },
  {
    title: '总耗电(kWh)',
    key: 'total_power_kwh',
    width: 120,
    align: 'right',
    render(row) { return formatNum(row.total_power_kwh, 1) },
  },
  {
    title: '系统COP',
    key: 'system_cop',
    width: 100,
    align: 'right',
    render(row) {
      if (row.system_cop == null) return '--'
      const cop = row.system_cop
      const type = cop >= 4 ? 'success' : cop >= 3 ? 'warning' : 'error'
      return h(NTag, { size: 'small', bordered: false, type }, { default: () => cop.toFixed(2) })
    },
  },
]

async function fetchAll() {
  const buildingId = buildingStore.current
  if (!buildingId) return

  loading.value = true
  const range = getRange()

  try {
    const [aggRes, copRes, euiRes, plantRes] = await Promise.allSettled([
      statisticsApi.aggregate({
        building_id: buildingId,
        start_time: range.start_time,
        end_time: range.end_time,
        period: period.value,
        metrics: metric.value + ',hvac_electricity_kwh',
      }),
      statisticsApi.cop({
        building_id: buildingId,
        start_time: range.start_time,
        end_time: range.end_time,
        period: period.value,
      }),
      statisticsApi.eui({
        building_id: buildingId,
        start_time: range.start_time,
        end_time: range.end_time,
      }),
      statisticsApi.plantEfficiency({
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
        if (item.metric_name === 'hvac_electricity_kwh') {
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

    if (euiRes.status === 'fulfilled') {
      euiData.value = euiRes.value.data
    } else {
      euiData.value = null
    }

    if (plantRes.status === 'fulfilled') {
      plantData.value = plantRes.value.data
    } else {
      plantData.value = []
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
