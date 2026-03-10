<template>
  <n-card :title="deviceName" size="small" :bordered="true">
    <n-space vertical :size="12">
      <!-- 运行状态 -->
      <div style="display: flex; align-items: center; justify-content: space-between">
        <span style="font-size: 13px; color: #6b7280">运行状态</span>
        <n-tag :type="statusType" size="small" :bordered="false">
          {{ statusLabel }}
        </n-tag>
      </div>

      <!-- COP -->
      <div style="display: flex; align-items: center; justify-content: space-between">
        <span style="font-size: 13px; color: #6b7280">COP</span>
        <n-statistic :value="record.cop ?? 0" style="text-align: right">
          <template #prefix>
            <span :style="{ color: copColor, fontWeight: 600, fontSize: '20px' }">
              {{ record.cop != null ? record.cop.toFixed(2) : '--' }}
            </span>
          </template>
          <template #suffix>
            <n-tag :color="{ color: copBgColor, textColor: copColor }" size="tiny" :bordered="false" style="margin-left: 6px">
              {{ copRating }}
            </n-tag>
          </template>
        </n-statistic>
      </div>

      <!-- 负荷率 -->
      <div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 4px">
          <span style="font-size: 13px; color: #6b7280">负荷率</span>
          <span style="font-size: 13px">{{ record.load_ratio != null ? (record.load_ratio * 100).toFixed(1) + '%' : '--' }}</span>
        </div>
        <n-progress
          type="line"
          :percentage="loadPercent"
          :show-indicator="false"
          :height="8"
          :border-radius="4"
          :color="loadColor"
          :rail-color="'#f3f4f6'"
        />
      </div>

      <!-- 冷冻水温度 -->
      <div style="display: flex; justify-content: space-between">
        <span style="font-size: 13px; color: #6b7280">冷冻水供/回水温度</span>
        <span style="font-size: 13px">
          {{ formatTemp(record.chw_supply_temp) }} / {{ formatTemp(record.chw_return_temp) }} °C
        </span>
      </div>

      <!-- 冷却水温度 -->
      <div style="display: flex; justify-content: space-between">
        <span style="font-size: 13px; color: #6b7280">冷却水供/回水温度</span>
        <span style="font-size: 13px">
          {{ formatTemp(record.cw_supply_temp) }} / {{ formatTemp(record.cw_return_temp) }} °C
        </span>
      </div>

      <!-- 功率 -->
      <div style="display: flex; justify-content: space-between">
        <span style="font-size: 13px; color: #6b7280">功率</span>
        <span style="font-size: 13px">
          {{ record.power_kw != null ? record.power_kw.toFixed(1) + ' kW' : '--' }}
        </span>
      </div>
    </n-space>
  </n-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NCard, NProgress, NTag, NStatistic, NSpace } from 'naive-ui'
import type { ChillerRecord } from '@/types/chiller'

const props = defineProps<{
  record: ChillerRecord
}>()

const deviceName = computed(() => props.record.device_id ?? '冷水机组')

const statusLabel = computed(() => {
  const s = props.record.running_status
  if (!s) return '未知'
  const map: Record<string, string> = {
    running: '运行中',
    stopped: '已停止',
    fault: '故障',
    standby: '待机',
  }
  return map[s.toLowerCase()] ?? s
})

const statusType = computed(() => {
  const s = props.record.running_status?.toLowerCase()
  if (s === 'running') return 'success'
  if (s === 'fault') return 'error'
  if (s === 'standby') return 'warning'
  return 'default'
})

const copColor = computed(() => {
  const cop = props.record.cop
  if (cop == null) return '#6b7280'
  if (cop > 4) return '#16a34a'
  if (cop > 3) return '#2563eb'
  if (cop > 2) return '#ca8a04'
  return '#dc2626'
})

const copBgColor = computed(() => {
  const cop = props.record.cop
  if (cop == null) return '#f3f4f6'
  if (cop > 4) return '#dcfce7'
  if (cop > 3) return '#dbeafe'
  if (cop > 2) return '#fef9c3'
  return '#fee2e2'
})

const copRating = computed(() => {
  const cop = props.record.cop
  if (cop == null) return '无数据'
  if (cop > 4) return '优秀'
  if (cop > 3) return '良好'
  if (cop > 2) return '一般'
  return '较差'
})

const loadPercent = computed(() => {
  const lr = props.record.load_ratio
  if (lr == null) return 0
  return Math.min(100, Math.max(0, lr * 100))
})

const loadColor = computed(() => {
  const pct = loadPercent.value
  if (pct > 90) return '#dc2626'
  if (pct > 70) return '#d97706'
  return '#2563eb'
})

function formatTemp(val?: number): string {
  return val != null ? val.toFixed(1) : '--'
}
</script>
