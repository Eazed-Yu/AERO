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

const chartOption = computed(() => {
  const periods = props.data.map((d) => d.period_start)
  const copValues = props.data.map((d) => d.cop ?? null)

  return {
    tooltip: {
      trigger: 'axis',
      formatter(params: any) {
        const p = Array.isArray(params) ? params[0] : params
        const idx = p.dataIndex
        const rating = props.data[idx]?.rating ?? ''
        return `${p.axisValue}<br/>COP: ${p.value ?? '—'}<br/>Rating: ${rating}`
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
      min: 0,
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
          data: [
            {
              yAxis: 2,
              label: { formatter: 'Poor', color: '#dc2626' },
              lineStyle: { color: '#dc2626' },
            },
            {
              yAxis: 3,
              label: { formatter: 'Fair', color: '#ca8a04' },
              lineStyle: { color: '#ca8a04' },
            },
            {
              yAxis: 4,
              label: { formatter: 'Good', color: '#16a34a' },
              lineStyle: { color: '#16a34a' },
            },
          ],
        },
      },
    ],
  }
})
</script>
