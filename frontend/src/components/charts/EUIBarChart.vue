<template>
  <v-chart :option="chartOption" autoresize style="height: 320px; width: 100%" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

use([BarChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

interface EUIDataPoint {
  building_name: string
  eui: number
  hvac_eui?: number
}

const props = defineProps<{
  data: EUIDataPoint[]
}>()

const chartOption = computed(() => {
  const names = props.data.map((d) => d.building_name)
  const euiValues = props.data.map((d) => d.eui ?? 0)
  const hvacEuiValues = props.data.map((d) => d.hvac_eui ?? 0)

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
    },
    legend: {
      bottom: 0,
      textStyle: { fontSize: 12 },
    },
    grid: {
      top: 16,
      right: 16,
      bottom: 40,
      left: 60,
      containLabel: false,
    },
    xAxis: {
      type: 'category',
      data: names,
      axisLine: { lineStyle: { color: '#d1d5db' } },
      axisLabel: { fontSize: 11, color: '#6b7280', rotate: names.length > 6 ? 30 : 0 },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      name: 'kWh/m²',
      nameTextStyle: { fontSize: 11, color: '#6b7280' },
      axisLine: { show: false },
      axisLabel: { fontSize: 11, color: '#6b7280' },
      splitLine: { lineStyle: { color: '#f3f4f6' } },
    },
    series: [
      {
        name: '总 EUI',
        type: 'bar',
        data: euiValues,
        barMaxWidth: 40,
        itemStyle: { color: '#2563eb', borderRadius: [3, 3, 0, 0] },
      },
      {
        name: 'HVAC EUI',
        type: 'bar',
        data: hvacEuiValues,
        barMaxWidth: 40,
        itemStyle: { color: '#d97706', borderRadius: [3, 3, 0, 0] },
      },
    ],
  }
})
</script>
