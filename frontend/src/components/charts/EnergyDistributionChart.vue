<template>
  <v-chart :option="chartOption" autoresize style="height: 320px; width: 100%" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { PieChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

use([PieChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

interface DataPoint {
  name: string
  value: number
}

const props = defineProps<{
  data: DataPoint[]
}>()

const palette = ['#2563eb', '#d97706', '#16a34a', '#6b7280']

const chartOption = computed(() => {
  const seriesData = props.data.map((d, i) => ({
    name: d.name,
    value: d.value,
    itemStyle: { color: palette[i % palette.length] },
  }))

  return {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      bottom: 0,
      textStyle: { fontSize: 12 },
    },
    series: [
      {
        type: 'pie',
        radius: ['0%', '65%'],
        center: ['50%', '45%'],
        data: seriesData,
        label: {
          show: true,
          fontSize: 11,
          color: '#374151',
          formatter: '{b}: {d}%',
        },
        labelLine: {
          lineStyle: { color: '#d1d5db' },
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 0,
          },
        },
      },
    ],
  }
})
</script>
