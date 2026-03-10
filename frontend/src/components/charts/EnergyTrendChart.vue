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
  electricity_kwh?: number
  hvac_kwh?: number
}

const props = defineProps<{
  data: DataPoint[]
}>()

const chartOption = computed(() => {
  const timestamps = props.data.map((d) => d.timestamp)
  const electricity = props.data.map((d) => d.electricity_kwh ?? null)
  const hvac = props.data.map((d) => d.hvac_kwh ?? null)

  return {
    tooltip: {
      trigger: 'axis',
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
      name: 'kWh',
      nameTextStyle: { fontSize: 11, color: '#6b7280' },
      axisLine: { show: false },
      axisLabel: { fontSize: 11, color: '#6b7280' },
      splitLine: { lineStyle: { color: '#f3f4f6' } },
    },
    series: [
      {
        name: 'Electricity',
        type: 'line',
        data: electricity,
        symbol: 'none',
        lineStyle: { width: 2, color: '#2563eb' },
        itemStyle: { color: '#2563eb' },
      },
      {
        name: 'HVAC',
        type: 'line',
        data: hvac,
        symbol: 'none',
        lineStyle: { width: 2, color: '#d97706' },
        itemStyle: { color: '#d97706' },
      },
    ],
  }
})
</script>
