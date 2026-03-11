<template>
  <div class="page-content">
    <!-- 筛选工具栏 -->
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
        v-model:value="filters.building_id"
        :options="buildingOptions"
        placeholder="全部建筑"
        clearable
        size="small"
        style="width: 180px"
      />
      <n-select
        v-model:value="filters.device_type"
        :options="deviceTypeOptions"
        placeholder="全部设备类型"
        clearable
        size="small"
        style="width: 150px"
      />
      <n-select
        v-model:value="filters.period"
        :options="periodOptions"
        size="small"
        style="width: 110px"
      />
      <n-date-picker
        v-model:value="dateRange"
        type="daterange"
        clearable
        size="small"
        style="width: 280px"
        :shortcuts="dateShortcuts"
      />
      <n-button size="small" type="primary" @click="fetchAll">查询</n-button>
    </div>

    <n-spin :show="loading">
      <!-- KPI 卡片 -->
      <div class="kpi-row surface">
        <div class="kpi-item" v-for="kpi in kpis" :key="kpi.label">
          <span class="kpi-label">{{ kpi.label }}</span>
          <span class="kpi-value">{{ kpi.value }}<span class="kpi-unit">{{ kpi.unit }}</span></span>
        </div>
      </div>

      <!-- 图表行 1: 能耗趋势 + COP 趋势 -->
      <div class="grid-2" style="margin-top: 16px">
        <div class="surface" style="padding: 16px">
          <div class="section-title">能耗趋势</div>
          <EnergyTrendChart :data="trendData" />
        </div>
        <div class="surface" style="padding: 16px">
          <div class="section-title">COP 趋势</div>
          <n-empty v-if="copTrendData.length === 0" description="暂无 COP 数据" style="padding: 40px 0" />
          <v-chart v-else :option="copChartOption" autoresize style="height: 320px; width: 100%" />
        </div>
      </div>

      <!-- 图表行 2: EUI 对比 + 能耗构成 -->
      <div class="grid-2" style="margin-top: 16px">
        <div class="surface" style="padding: 16px">
          <div class="section-title">建筑 EUI 对比</div>
          <n-empty v-if="euiData.length === 0" description="暂无 EUI 数据" style="padding: 40px 0" />
          <EUIBarChart v-else :data="euiData" />
        </div>
        <div class="surface" style="padding: 16px">
          <div class="section-title">能耗构成</div>
          <n-empty v-if="distData.length === 0" description="暂无构成数据" style="padding: 40px 0" />
          <EnergyDistributionChart v-else :data="distData" />
        </div>
      </div>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  NSelect,
  NDatePicker,
  NButton,
  NSpin,
  NEmpty,
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

import EnergyTrendChart from '@/components/charts/EnergyTrendChart.vue'
import EnergyDistributionChart from '@/components/charts/EnergyDistributionChart.vue'
import EUIBarChart from '@/components/charts/EUIBarChart.vue'
import { useRegionStore } from '@/stores/region'
import { useBuildingStore } from '@/stores/building'
import { statisticsApi } from '@/api/statistics'
import { equipmentApi } from '@/api/equipment'
import { anomalyApi } from '@/api/anomaly'
import type { COPResult } from '@/types/statistics'

use([LineChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const regionStore = useRegionStore()
const buildingStore = useBuildingStore()
const loading = ref(false)
const selectedRegion = ref<string>('')

// ----------------------------------------------------------------
// Filters
// ----------------------------------------------------------------
const filters = ref({
  building_id: null as string | null,
  device_type: null as string | null,
  period: 'day' as string,
})

const dateRange = ref<[number, number] | null>(null)

const dateShortcuts = {
  '近7天': () => {
    const end = Date.now()
    return [end - 7 * 24 * 3600_000, end] as [number, number]
  },
  '近30天': () => {
    const end = Date.now()
    return [end - 30 * 24 * 3600_000, end] as [number, number]
  },
  '近90天': () => {
    const end = Date.now()
    return [end - 90 * 24 * 3600_000, end] as [number, number]
  },
}

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
  filters.value.building_id = null
  if (val) {
    buildingStore.fetchBuildings(val)
    fetchAll()
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

const periodOptions = [
  { label: '按天', value: 'day' },
  { label: '按周', value: 'week' },
  { label: '按月', value: 'month' },
]

// ----------------------------------------------------------------
// KPI
// ----------------------------------------------------------------
interface KpiItem {
  label: string
  value: string
  unit: string
}

const kpis = ref<KpiItem[]>([
  { label: '总用电量', value: '--', unit: 'kWh' },
  { label: '设备总数', value: '--', unit: '台' },
  { label: '平均COP', value: '--', unit: '' },
  { label: '活跃异常数', value: '--', unit: '条' },
])

// ----------------------------------------------------------------
// Chart data
// ----------------------------------------------------------------
const trendData = ref<{ timestamp: string; electricity_kwh?: number; hvac_kwh?: number }[]>([])
const distData = ref<{ name: string; value: number }[]>([])
const copTrendData = ref<COPResult[]>([])
const euiData = ref<{ building_name: string; eui: number; hvac_eui?: number }[]>([])

// ----------------------------------------------------------------
// Helpers
// ----------------------------------------------------------------
function formatNum(val: number | undefined | null, decimals = 1): string {
  if (val == null || isNaN(val)) return '--'
  return val.toFixed(decimals)
}

function getDateRange() {
  if (dateRange.value) {
    return {
      start_time: new Date(dateRange.value[0]).toISOString().slice(0, 19),
      end_time: new Date(dateRange.value[1]).toISOString().slice(0, 19),
    }
  }
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - 7)
  return {
    start_time: start.toISOString().slice(0, 19),
    end_time: end.toISOString().slice(0, 19),
  }
}

// ----------------------------------------------------------------
// COP chart option
// ----------------------------------------------------------------
const copChartOption = computed(() => {
  const data = copTrendData.value
  const timestamps = data.map((r) => r.period_start.slice(0, 10))
  const copValues = data.map((r) => r.cop ?? null)

  return {
    tooltip: { trigger: 'axis' },
    grid: { top: 16, right: 16, bottom: 24, left: 48, containLabel: false },
    xAxis: {
      type: 'category',
      data: timestamps,
      axisLine: { lineStyle: { color: '#d1d5db' } },
      axisLabel: { fontSize: 11, color: '#6b7280' },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      name: 'COP',
      nameTextStyle: { fontSize: 11, color: '#6b7280' },
      axisLine: { show: false },
      axisLabel: { fontSize: 11, color: '#6b7280' },
      splitLine: { lineStyle: { color: '#f3f4f6' } },
    },
    series: [
      {
        name: 'COP',
        type: 'line',
        data: copValues,
        symbol: 'none',
        lineStyle: { width: 2, color: '#18a058' },
        itemStyle: { color: '#18a058' },
        areaStyle: { color: 'rgba(24, 160, 88, 0.08)' },
      },
    ],
  }
})

// ----------------------------------------------------------------
// Fetch all data
// ----------------------------------------------------------------
async function fetchAll() {
  const regionId = selectedRegion.value
  if (!regionId) return

  loading.value = true
  const range = getDateRange()

  try {
    const [aggRes, copRes, equipRes, anomalyRes] = await Promise.allSettled([
      statisticsApi.aggregate({
        region_id: regionId,
        building_id: filters.value.building_id || undefined,
        start_time: range.start_time,
        end_time: range.end_time,
        period: filters.value.period,
        metrics: 'total_electricity_kwh,hvac_electricity_kwh,lighting_kwh,plug_load_kwh',
      }),
      statisticsApi.cop({
        region_id: regionId,
        building_id: filters.value.building_id || undefined,
        start_time: range.start_time,
        end_time: range.end_time,
        period: filters.value.period,
      }),
      equipmentApi.list({
        region_id: regionId,
        ...(filters.value.device_type ? { device_type: filters.value.device_type } : {}),
      }),
      anomalyApi.list({
        region_id: regionId,
        resolved: false,
        limit: 1000,
      }),
    ])

    // --- Aggregation: trend + distribution + total electricity KPI ---
    let totalElec = 0
    let totalHvac = 0
    let totalLighting = 0
    let totalPlug = 0
    const elecByPeriod: Record<string, { electricity_kwh: number; hvac_kwh: number }> = {}

    if (aggRes.status === 'fulfilled') {
      for (const item of aggRes.value.data) {
        const period = item.period_start.slice(0, 10)
        if (!elecByPeriod[period]) elecByPeriod[period] = { electricity_kwh: 0, hvac_kwh: 0 }
        if (item.metric_name === 'total_electricity_kwh') {
          elecByPeriod[period].electricity_kwh = item.sum ?? 0
          totalElec += item.sum ?? 0
        }
        if (item.metric_name === 'hvac_electricity_kwh') {
          elecByPeriod[period].hvac_kwh = item.sum ?? 0
          totalHvac += item.sum ?? 0
        }
        if (item.metric_name === 'lighting_kwh') totalLighting += item.sum ?? 0
        if (item.metric_name === 'plug_load_kwh') totalPlug += item.sum ?? 0
      }
    }

    const sortedPeriods = Object.keys(elecByPeriod).sort()
    trendData.value = sortedPeriods.map((p) => ({
      timestamp: p,
      electricity_kwh: elecByPeriod[p].electricity_kwh,
      hvac_kwh: elecByPeriod[p].hvac_kwh,
    }))

    const otherElec = Math.max(0, totalElec - totalHvac - totalLighting - totalPlug)
    distData.value = [
      { name: 'HVAC', value: Math.round(totalHvac) },
      { name: '照明', value: Math.round(totalLighting) },
      { name: '插座', value: Math.round(totalPlug) },
      { name: '其他', value: Math.round(otherElec) },
    ].filter((d) => d.value > 0)

    // --- COP trend ---
    if (copRes.status === 'fulfilled') {
      copTrendData.value = copRes.value.data
    } else {
      copTrendData.value = []
    }

    // --- COP KPI (weighted average) ---
    let avgCop = '--'
    if (copRes.status === 'fulfilled' && copRes.value.data.length > 0) {
      let totalCooling = 0
      let totalPower = 0
      for (const c of copRes.value.data) {
        totalCooling += c.cooling_capacity_kwh ?? 0
        totalPower += c.power_kwh ?? 0
      }
      if (totalPower > 0) {
        avgCop = formatNum(totalCooling / totalPower)
      }
    }

    // --- Equipment count KPI ---
    let equipCount = '--'
    if (equipRes.status === 'fulfilled') {
      equipCount = String(equipRes.value.data.length)
    }

    // --- Anomaly count KPI ---
    let anomalyCount = '--'
    if (anomalyRes.status === 'fulfilled') {
      const anomalyData = anomalyRes.value.data
      anomalyCount = String(Array.isArray(anomalyData) ? anomalyData.length : 0)
    }

    kpis.value = [
      { label: '总用电量', value: totalElec > 0 ? formatNum(totalElec, 0) : '--', unit: 'kWh' },
      { label: '设备总数', value: equipCount, unit: '台' },
      { label: '平均COP', value: avgCop, unit: '' },
      { label: '活跃异常数', value: anomalyCount, unit: '条' },
    ]

    // --- EUI per building ---
    await fetchEUI(range)
  } finally {
    loading.value = false
  }
}

async function fetchEUI(range: { start_time: string; end_time: string }) {
  const buildings = buildingStore.buildings
  if (buildings.length === 0) {
    euiData.value = []
    return
  }

  const targetBuildings = filters.value.building_id
    ? buildings.filter((b) => b.building_id === filters.value.building_id)
    : buildings

  const results = await Promise.allSettled(
    targetBuildings.map((b) =>
      statisticsApi.eui({
        building_id: b.building_id,
        start_time: range.start_time,
        end_time: range.end_time,
      })
    )
  )

  euiData.value = results
    .filter((r): r is PromiseFulfilledResult<any> => r.status === 'fulfilled')
    .map((r) => ({
      building_name: r.value.data.building_name || r.value.data.building_id,
      eui: r.value.data.eui ?? 0,
      hvac_eui: r.value.data.hvac_eui,
    }))
    .filter((d) => d.eui > 0)
}

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
    fetchAll()
  }
})
</script>
