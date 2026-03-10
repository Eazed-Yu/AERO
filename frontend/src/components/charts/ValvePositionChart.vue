<template>
  <v-chart :option="chartOption" autoresize style="height: 320px; width: 100%" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

use([LineChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

interface DataPoint {
  timestamp: string
  chw_valve_pos?: number
  hw_valve_pos?: number
  oa_damper_pos?: number
}

const props = defineProps<{
  data: DataPoint[]
}>()

const seriesConfig = [
  { key: 'chw_valve_pos' as const, name: '冷水阀', color: '#2563eb', areaColor: 'rgba(37, 99, 235, 0.15)' },
  { key: 'hw_valve_pos' as const, name: '热水阀', color: '#dc2626', areaColor: 'rgba(220, 38, 38, 0.15)' },
  { key: 'oa_damper_pos' as const, name: '新风阀', color: '#d97706', areaColor: 'rgba(217, 119, 6, 0.15)' },
]

function formatTimestamp(value: string): string {
  const normalized = value.replace('T', ' ')
  return /\d{2}:\d{2}/.test(normalized) ? normalized.slice(0, 16) : normalized.slice(0, 10)
}

const chartOption = computed(() => {
  const timestamps = props.data.map((d) => formatTimestamp(d.timestamp))

  const series = seriesConfig.map((cfg) => ({
    name: cfg.name,
    type: 'line' as const,
    data: props.data.map((d) => d[cfg.key] ?? null),
    symbol: 'none',
    lineStyle: { width: 2, color: cfg.color },
    itemStyle: { color: cfg.color },
    areaStyle: { color: cfg.areaColor },
    smooth: true,
    stack: undefined,
  }))

  return {
    tooltip: {
      trigger: 'axis',
      formatter(params: any) {
        const items = Array.isArray(params) ? params : [params]
        let result = items[0]?.axisValue ?? ''
        for (const item of items) {
          const val = typeof item.value === 'number' ? item.value.toFixed(1) + '%' : '--'
          result += `<br/>${item.marker} ${item.seriesName}: ${val}`
        }
        return result
      },
    },
    legend: {
      bottom: 0,
      textStyle: { fontSize: 12 },
    },
    grid: {
      top: 16,
      right: 16,
      bottom: 40,
      left: 48,
      containLabel: false,
    },
    xAxis: {
      type: 'category',
      data: timestamps,
      axisLine: { lineStyle: { color: '#d1d5db' } },
      axisLabel: { fontSize: 11, color: '#6b7280' },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      name: '开度 (%)',
      nameTextStyle: { fontSize: 11, color: '#6b7280' },
      axisLine: { show: false },
      axisLabel: { fontSize: 11, color: '#6b7280' },
      splitLine: { lineStyle: { color: '#f3f4f6' } },
      min: 0,
      max: 100,
    },
    series,
  }
})
</script>
