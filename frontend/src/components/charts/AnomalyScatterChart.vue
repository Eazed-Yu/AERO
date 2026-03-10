<template>
  <v-chart :option="chartOption" autoresize style="height: 320px; width: 100%" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { ScatterChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

use([ScatterChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

interface DataPoint {
  timestamp: string
  metric_value: number
  severity: string
  anomaly_type: string
}

const props = defineProps<{
  data: DataPoint[]
}>()

const severityColors: Record<string, string> = {
  critical: '#dc2626',
  high: '#d97706',
  medium: '#ca8a04',
  low: '#6b7280',
}

const severityOrder = ['critical', 'high', 'medium', 'low']

const chartOption = computed(() => {
  const grouped: Record<string, [string, number, string][]> = {}

  for (const d of props.data) {
    const key = d.severity.toLowerCase()
    if (!grouped[key]) grouped[key] = []
    grouped[key].push([d.timestamp, d.metric_value, d.anomaly_type])
  }

  const series = severityOrder
    .filter((sev) => grouped[sev]?.length)
    .map((sev) => ({
      name: sev.charAt(0).toUpperCase() + sev.slice(1),
      type: 'scatter' as const,
      data: grouped[sev],
      symbolSize: sev === 'critical' ? 10 : sev === 'high' ? 8 : 6,
      itemStyle: { color: severityColors[sev] },
    }))

  return {
    tooltip: {
      trigger: 'item',
      formatter(params: any) {
        const [ts, val, atype] = params.data
        return `${ts}<br/>Value: ${val}<br/>Type: ${atype}<br/>Severity: ${params.seriesName}`
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
      axisLine: { lineStyle: { color: '#d1d5db' } },
      axisLabel: { fontSize: 11, color: '#6b7280' },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      name: 'Metric Value',
      nameTextStyle: { fontSize: 11, color: '#6b7280' },
      axisLine: { show: false },
      axisLabel: { fontSize: 11, color: '#6b7280' },
      splitLine: { lineStyle: { color: '#f3f4f6' } },
    },
    series,
  }
})
</script>
