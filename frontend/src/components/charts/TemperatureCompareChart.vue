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
  sat?: number
  rat?: number
  mat?: number
  oat?: number
}

const props = defineProps<{
  data: DataPoint[]
}>()

const seriesConfig = [
  { key: 'sat' as const, name: '送风温度', color: '#2563eb' },
  { key: 'rat' as const, name: '回风温度', color: '#d97706' },
  { key: 'mat' as const, name: '混风温度', color: '#16a34a' },
  { key: 'oat' as const, name: '新风温度', color: '#dc2626' },
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
    symbol: 'circle',
    symbolSize: 4,
    lineStyle: { width: 2, color: cfg.color },
    itemStyle: { color: cfg.color },
    smooth: true,
  }))

  return {
    tooltip: {
      trigger: 'axis',
      formatter(params: any) {
        const items = Array.isArray(params) ? params : [params]
        let result = items[0]?.axisValue ?? ''
        for (const item of items) {
          const val = typeof item.value === 'number' ? item.value.toFixed(1) + ' °C' : '--'
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
      name: '温度 (°C)',
      nameTextStyle: { fontSize: 11, color: '#6b7280' },
      axisLine: { show: false },
      axisLabel: { fontSize: 11, color: '#6b7280' },
      splitLine: { lineStyle: { color: '#f3f4f6' } },
    },
    series,
  }
})
</script>
