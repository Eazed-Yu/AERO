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
  MarkLineComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

use([
  LineChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  MarkLineComponent,
  CanvasRenderer,
])

interface DataPoint {
  period_start: string
  cop?: number
  rating: string
}

const props = defineProps<{
  data: DataPoint[]
}>()

function formatPeriodLabel(value: string): string {
  const normalized = value.replace('T', ' ')
  const hasHourDetail = /\d{2}:\d{2}/.test(normalized)
  return hasHourDetail ? normalized.slice(0, 16) : normalized.slice(0, 10)
}

const chartOption = computed(() => {
  const periods = props.data.map((d) => formatPeriodLabel(d.period_start))
  const copValues = props.data.map((d) => d.cop ?? null)
  const numericCopValues = copValues.filter((v): v is number => typeof v === 'number')

  const dataMin = numericCopValues.length > 0 ? Math.min(...numericCopValues) : 0
  const dataMax = numericCopValues.length > 0 ? Math.max(...numericCopValues) : 4
  const yMin = Math.max(0, Math.floor((dataMin - 0.4) * 10) / 10)
  const yMax = Math.ceil((dataMax + 0.4) * 10) / 10

  const thresholds = [
    { yAxis: 2, label: 'Poor', color: '#dc2626' },
    { yAxis: 3, label: 'Fair', color: '#ca8a04' },
    { yAxis: 4, label: 'Good', color: '#16a34a' },
  ]

  const visibleThresholds = thresholds
    .filter((t) => t.yAxis >= yMin && t.yAxis <= yMax)
    .map((t) => ({
      yAxis: t.yAxis,
      label: { formatter: t.label, color: t.color },
      lineStyle: { color: t.color },
    }))

  return {
    tooltip: {
      trigger: 'axis',
      formatter(params: any) {
        const p = Array.isArray(params) ? params[0] : params
        const idx = p.dataIndex
        const rating = props.data[idx]?.rating ?? ''
        const cop = typeof p.value === 'number' ? p.value.toFixed(2) : '—'
        return `${p.axisValue}<br/>COP: ${cop}<br/>Rating: ${rating}`
      },
    },
    grid: {
      top: 16,
      right: 16,
      bottom: 24,
      left: 48,
      containLabel: false,
    },
    xAxis: {
      type: 'category',
      data: periods,
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
      min: yMin,
      max: yMax,
    },
    series: [
      {
        name: 'COP',
        type: 'line',
        data: copValues,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { width: 2, color: '#2563eb' },
        itemStyle: { color: '#2563eb' },
        areaStyle: {
          color: 'rgba(37, 99, 235, 0.08)',
        },
        markLine: {
          silent: true,
          symbol: 'none',
          lineStyle: { type: 'dashed', width: 1 },
          label: {
            position: 'insideEndTop',
            fontSize: 10,
          },
          data: visibleThresholds,
        },
      },
    ],
  }
})
</script>
