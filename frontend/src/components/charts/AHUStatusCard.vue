<template>
  <n-card :title="deviceName" size="small" :bordered="true">
    <n-space vertical :size="12">
      <!-- 运行状态与模式 -->
      <div style="display: flex; align-items: center; justify-content: space-between">
        <span style="font-size: 13px; color: #6b7280">运行状态</span>
        <div style="display: flex; gap: 6px; align-items: center">
          <n-tag :type="modeType" size="small" :bordered="false">
            {{ modeLabel }}
          </n-tag>
          <n-tag :type="statusType" size="small" :bordered="false">
            {{ statusLabel }}
          </n-tag>
        </div>
      </div>

      <!-- 温度信息 -->
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px">
        <div style="display: flex; justify-content: space-between">
          <span style="font-size: 13px; color: #6b7280">送风温度</span>
          <span style="font-size: 13px">{{ formatTemp(record.supply_air_temp) }} °C</span>
        </div>
        <div style="display: flex; justify-content: space-between">
          <span style="font-size: 13px; color: #6b7280">回风温度</span>
          <span style="font-size: 13px">{{ formatTemp(record.return_air_temp) }} °C</span>
        </div>
        <div style="display: flex; justify-content: space-between">
          <span style="font-size: 13px; color: #6b7280">混风温度</span>
          <span style="font-size: 13px">{{ formatTemp(record.mixed_air_temp) }} °C</span>
        </div>
        <div style="display: flex; justify-content: space-between">
          <span style="font-size: 13px; color: #6b7280">新风温度</span>
          <span style="font-size: 13px">{{ formatTemp(record.outdoor_air_temp) }} °C</span>
        </div>
      </div>

      <!-- 风机转速 -->
      <div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 4px">
          <span style="font-size: 13px; color: #6b7280">风机转速</span>
          <span style="font-size: 13px">{{ formatPercent(record.supply_fan_speed) }}</span>
        </div>
        <n-progress
          type="line"
          :percentage="safePercent(record.supply_fan_speed)"
          :show-indicator="false"
          :height="8"
          :border-radius="4"
          color="#2563eb"
          rail-color="#f3f4f6"
        />
      </div>

      <!-- 冷水阀 -->
      <div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 4px">
          <span style="font-size: 13px; color: #6b7280">冷水阀开度</span>
          <span style="font-size: 13px">{{ formatPercent(record.chw_valve_pos) }}</span>
        </div>
        <n-progress
          type="line"
          :percentage="safePercent(record.chw_valve_pos)"
          :show-indicator="false"
          :height="8"
          :border-radius="4"
          color="#16a34a"
          rail-color="#f3f4f6"
        />
      </div>

      <!-- 热水阀 -->
      <div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 4px">
          <span style="font-size: 13px; color: #6b7280">热水阀开度</span>
          <span style="font-size: 13px">{{ formatPercent(record.hw_valve_pos) }}</span>
        </div>
        <n-progress
          type="line"
          :percentage="safePercent(record.hw_valve_pos)"
          :show-indicator="false"
          :height="8"
          :border-radius="4"
          color="#dc2626"
          rail-color="#f3f4f6"
        />
      </div>

      <!-- 新风阀 -->
      <div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 4px">
          <span style="font-size: 13px; color: #6b7280">新风阀开度</span>
          <span style="font-size: 13px">{{ formatPercent(record.oa_damper_pos) }}</span>
        </div>
        <n-progress
          type="line"
          :percentage="safePercent(record.oa_damper_pos)"
          :show-indicator="false"
          :height="8"
          :border-radius="4"
          color="#d97706"
          rail-color="#f3f4f6"
        />
      </div>
    </n-space>
  </n-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NCard, NProgress, NTag, NSpace } from 'naive-ui'
import type { AHURecord } from '@/types/ahu'

const props = defineProps<{
  record: AHURecord
  deviceName?: string
}>()

const deviceName = computed(() => props.deviceName ?? props.record.device_id ?? '空调箱')

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

const modeLabel = computed(() => {
  const m = props.record.operating_mode
  if (!m) return '未知'
  const map: Record<string, string> = {
    cooling: '制冷',
    heating: '制热',
    ventilation: '通风',
    auto: '自动',
    economizer: '经济运行',
  }
  return map[m.toLowerCase()] ?? m
})

const modeType = computed(() => {
  const m = props.record.operating_mode?.toLowerCase()
  if (m === 'cooling') return 'info'
  if (m === 'heating') return 'error'
  if (m === 'ventilation') return 'default'
  if (m === 'economizer') return 'success'
  return 'warning'
})

function formatTemp(val?: number): string {
  return val != null ? val.toFixed(1) : '--'
}

function formatPercent(val?: number): string {
  return val != null ? val.toFixed(1) + '%' : '--'
}

function safePercent(val?: number): number {
  if (val == null) return 0
  return Math.min(100, Math.max(0, val))
}
</script>
