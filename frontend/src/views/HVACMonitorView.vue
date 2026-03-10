<template>
  <div class="page-content">
    <div class="toolbar surface" style="margin-bottom: 16px; border-radius: 3px">
      <n-date-picker
        v-model:value="dateRange"
        type="datetimerange"
        clearable
        size="small"
        style="width: 380px"
        :shortcuts="dateShortcuts"
      />
      <n-button size="small" type="primary" @click="refreshCurrentTab">查询</n-button>
    </div>

    <n-tabs v-model:value="activeTab" type="line" @update:value="onTabChange">
      <!-- ==================== 冷站监测 ==================== -->
      <n-tab-pane name="chiller" tab="冷站监测">
        <n-spin :show="chillerLoading">
          <n-empty v-if="!chillerLoading && chillers.length === 0" description="暂无冷机设备" />
          <template v-else>
            <div style="margin-bottom: 12px; display: flex; gap: 8px; flex-wrap: wrap">
              <n-button
                v-for="eq in chillers"
                :key="eq.device_id"
                size="small"
                :type="selectedChiller === eq.device_id ? 'primary' : 'default'"
                @click="selectChiller(eq.device_id)"
              >
                {{ eq.device_name }}
              </n-button>
            </div>

            <div class="grid-2" style="margin-bottom: 16px">
              <div class="surface" style="padding: 16px">
                <div class="section-title">冷机运行参数</div>
                <n-empty v-if="chillerRecords.length === 0" description="暂无运行数据" style="padding: 40px 0" />
                <template v-else>
                  <div class="param-grid">
                    <div class="param-item">
                      <span class="param-label">运行状态</span>
                      <n-tag
                        :type="latestChiller?.running_status === 'running' ? 'success' : latestChiller?.running_status === 'stopped' ? 'default' : 'warning'"
                        size="small"
                        :bordered="false"
                      >
                        {{ statusText(latestChiller?.running_status) }}
                      </n-tag>
                    </div>
                    <div class="param-item">
                      <span class="param-label">COP</span>
                      <span class="param-value">{{ fmtNum(latestChiller?.cop, 2) }}</span>
                    </div>
                    <div class="param-item">
                      <span class="param-label">负荷率</span>
                      <span class="param-value">{{ fmtPct(latestChiller?.load_ratio) }}</span>
                    </div>
                    <div class="param-item">
                      <span class="param-label">功率</span>
                      <span class="param-value">{{ fmtNum(latestChiller?.power_kw, 1) }} <span class="param-unit">kW</span></span>
                    </div>
                    <div class="param-item">
                      <span class="param-label">冷冻水供水温度</span>
                      <span class="param-value">{{ fmtNum(latestChiller?.chw_supply_temp, 1) }} <span class="param-unit">&deg;C</span></span>
                    </div>
                    <div class="param-item">
                      <span class="param-label">冷冻水回水温度</span>
                      <span class="param-value">{{ fmtNum(latestChiller?.chw_return_temp, 1) }} <span class="param-unit">&deg;C</span></span>
                    </div>
                    <div class="param-item">
                      <span class="param-label">冷却水供水温度</span>
                      <span class="param-value">{{ fmtNum(latestChiller?.cw_supply_temp, 1) }} <span class="param-unit">&deg;C</span></span>
                    </div>
                    <div class="param-item">
                      <span class="param-label">冷却水回水温度</span>
                      <span class="param-value">{{ fmtNum(latestChiller?.cw_return_temp, 1) }} <span class="param-unit">&deg;C</span></span>
                    </div>
                  </div>
                </template>
              </div>

              <div class="surface" style="padding: 16px">
                <div class="section-title">COP 趋势</div>
                <n-empty v-if="chillerRecords.length === 0" description="暂无数据" style="padding: 40px 0" />
                <v-chart v-else :option="copChartOption" autoresize style="height: 280px; width: 100%" />
              </div>
            </div>

            <div class="surface" style="padding: 16px">
              <div class="section-title">冷冻水 / 冷却水温度对比</div>
              <n-empty v-if="chillerRecords.length === 0" description="暂无数据" style="padding: 40px 0" />
              <v-chart v-else :option="chillerTempChartOption" autoresize style="height: 300px; width: 100%" />
            </div>
          </template>
        </n-spin>
      </n-tab-pane>

      <!-- ==================== 空调机组 ==================== -->
      <n-tab-pane name="ahu" tab="空调机组">
        <n-spin :show="ahuLoading">
          <n-empty v-if="!ahuLoading && ahus.length === 0" description="暂无空调机组设备" />
          <template v-else>
            <div style="margin-bottom: 12px; display: flex; gap: 8px; flex-wrap: wrap">
              <n-button
                v-for="eq in ahus"
                :key="eq.device_id"
                size="small"
                :type="selectedAHU === eq.device_id ? 'primary' : 'default'"
                @click="selectAHU(eq.device_id)"
              >
                {{ eq.device_name }}
              </n-button>
            </div>

            <div class="grid-2" style="margin-bottom: 16px">
              <div class="surface" style="padding: 16px">
                <div class="section-title">机组运行参数</div>
                <n-empty v-if="ahuRecords.length === 0" description="暂无运行数据" style="padding: 40px 0" />
                <template v-else>
                  <div class="param-grid">
                    <div class="param-item">
                      <span class="param-label">运行状态</span>
                      <n-tag
                        :type="latestAHU?.running_status === 'running' ? 'success' : latestAHU?.running_status === 'stopped' ? 'default' : 'warning'"
                        size="small"
                        :bordered="false"
                      >
                        {{ statusText(latestAHU?.running_status) }}
                      </n-tag>
                    </div>
                    <div class="param-item">
                      <span class="param-label">运行模式</span>
                      <n-tag size="small" :bordered="false">
                        {{ modeText(latestAHU?.operating_mode) }}
                      </n-tag>
                    </div>
                    <div class="param-item">
                      <span class="param-label">送风温度 (SAT)</span>
                      <span class="param-value">{{ fmtNum(latestAHU?.supply_air_temp, 1) }} <span class="param-unit">&deg;C</span></span>
                    </div>
                    <div class="param-item">
                      <span class="param-label">回风温度 (RAT)</span>
                      <span class="param-value">{{ fmtNum(latestAHU?.return_air_temp, 1) }} <span class="param-unit">&deg;C</span></span>
                    </div>
                    <div class="param-item">
                      <span class="param-label">混风温度 (MAT)</span>
                      <span class="param-value">{{ fmtNum(latestAHU?.mixed_air_temp, 1) }} <span class="param-unit">&deg;C</span></span>
                    </div>
                    <div class="param-item">
                      <span class="param-label">室外温度 (OAT)</span>
                      <span class="param-value">{{ fmtNum(latestAHU?.outdoor_air_temp, 1) }} <span class="param-unit">&deg;C</span></span>
                    </div>
                    <div class="param-item">
                      <span class="param-label">送风机转速</span>
                      <span class="param-value">{{ fmtPct(latestAHU?.supply_fan_speed) }}</span>
                    </div>
                    <div class="param-item">
                      <span class="param-label">冷水阀开度</span>
                      <span class="param-value">{{ fmtPct(latestAHU?.chw_valve_pos) }}</span>
                    </div>
                    <div class="param-item">
                      <span class="param-label">热水阀开度</span>
                      <span class="param-value">{{ fmtPct(latestAHU?.hw_valve_pos) }}</span>
                    </div>
                  </div>
                </template>
              </div>

              <div class="surface" style="padding: 16px">
                <div class="section-title">温度趋势 (SAT / RAT / MAT / OAT)</div>
                <n-empty v-if="ahuRecords.length === 0" description="暂无数据" style="padding: 40px 0" />
                <v-chart v-else :option="ahuTempChartOption" autoresize style="height: 280px; width: 100%" />
              </div>
            </div>
          </template>
        </n-spin>
      </n-tab-pane>

      <!-- ==================== 末端系统 ==================== -->
      <n-tab-pane name="vav" tab="末端系统">
        <n-spin :show="vavLoading">
          <n-empty v-if="!vavLoading && vavs.length === 0" description="暂无末端设备" />
          <template v-else>
            <div style="margin-bottom: 12px; display: flex; gap: 8px; flex-wrap: wrap">
              <n-button
                v-for="eq in vavs"
                :key="eq.device_id"
                size="small"
                :type="selectedVAV === eq.device_id ? 'primary' : 'default'"
                @click="selectVAV(eq.device_id)"
              >
                {{ eq.device_name }}
              </n-button>
            </div>

            <div class="surface" style="padding: 0">
              <n-data-table
                :columns="vavColumns"
                :data="vavRecords"
                :bordered="false"
                size="small"
                :row-key="(row: VAVRecord) => row.id"
                :pagination="{ pageSize: 20 }"
                max-height="520"
              />
            </div>
          </template>
        </n-spin>
      </n-tab-pane>

      <!-- ==================== 热源系统 ==================== -->
      <n-tab-pane name="boiler" tab="热源系统">
        <n-spin :show="boilerLoading">
          <n-empty v-if="!boilerLoading && boilers.length === 0" description="暂无锅炉设备" />
          <template v-else>
            <div style="margin-bottom: 12px; display: flex; gap: 8px; flex-wrap: wrap">
              <n-button
                v-for="eq in boilers"
                :key="eq.device_id"
                size="small"
                :type="selectedBoiler === eq.device_id ? 'primary' : 'default'"
                @click="selectBoiler(eq.device_id)"
              >
                {{ eq.device_name }}
              </n-button>
            </div>

            <div class="surface" style="padding: 0">
              <n-data-table
                :columns="boilerColumns"
                :data="boilerRecords"
                :bordered="false"
                size="small"
                :row-key="(row: BoilerRecord) => row.id"
                :pagination="{ pageSize: 20 }"
                max-height="520"
              />
            </div>
          </template>
        </n-spin>
      </n-tab-pane>
    </n-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted } from 'vue'
import {
  NTabs,
  NTabPane,
  NDatePicker,
  NButton,
  NTag,
  NEmpty,
  NSpin,
  NDataTable,
  type DataTableColumn,
} from 'naive-ui'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

import { hvacApi, type HVACQueryParams } from '@/api/hvac'
import { equipmentApi } from '@/api/equipment'
import type { Equipment } from '@/types/equipment'
import type { ChillerRecord } from '@/types/chiller'
import type { AHURecord } from '@/types/ahu'
import type { VAVRecord } from '@/types/vav'
import type { BoilerRecord } from '@/types/boiler'

use([LineChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

// ----------------------------------------------------------------
// Date range
// ----------------------------------------------------------------
const defaultRange = (): [number, number] => {
  const end = Date.now()
  const start = end - 24 * 60 * 60 * 1000 // last 24h
  return [start, end]
}

const dateRange = ref<[number, number] | null>(defaultRange())

const dateShortcuts = {
  '近6小时': () => {
    const end = Date.now()
    return [end - 6 * 3600_000, end] as [number, number]
  },
  '近24小时': () => {
    const end = Date.now()
    return [end - 24 * 3600_000, end] as [number, number]
  },
  '近7天': () => {
    const end = Date.now()
    return [end - 7 * 24 * 3600_000, end] as [number, number]
  },
  '近30天': () => {
    const end = Date.now()
    return [end - 30 * 24 * 3600_000, end] as [number, number]
  },
}

function getTimeParams(): Pick<HVACQueryParams, 'start_time' | 'end_time'> {
  const range = dateRange.value || defaultRange()
  return {
    start_time: new Date(range[0]).toISOString().slice(0, 19),
    end_time: new Date(range[1]).toISOString().slice(0, 19),
  }
}

// ----------------------------------------------------------------
// Tab state
// ----------------------------------------------------------------
const activeTab = ref('chiller')

// ----------------------------------------------------------------
// Formatting helpers
// ----------------------------------------------------------------
function fmtNum(val: number | undefined | null, decimals = 1): string {
  if (val == null || isNaN(val)) return '--'
  return val.toFixed(decimals)
}

function fmtPct(val: number | undefined | null): string {
  if (val == null || isNaN(val)) return '--'
  return (val * 100).toFixed(1) + '%'
}

function fmtTimestamp(ts: string | undefined): string {
  if (!ts) return '--'
  return ts.replace('T', ' ').slice(0, 19)
}

function statusText(status: string | undefined): string {
  const map: Record<string, string> = {
    running: '运行中',
    stopped: '已停机',
    fault: '故障',
    standby: '待机',
    maintenance: '维护中',
  }
  return map[status ?? ''] ?? status ?? '--'
}

function modeText(mode: string | undefined): string {
  const map: Record<string, string> = {
    cooling: '制冷',
    heating: '制热',
    ventilation: '通风',
    auto: '自动',
    economizer: '经济运行',
  }
  return map[mode ?? ''] ?? mode ?? '--'
}

// ----------------------------------------------------------------
// Equipment lists
// ----------------------------------------------------------------
const chillers = ref<Equipment[]>([])
const ahus = ref<Equipment[]>([])
const vavs = ref<Equipment[]>([])
const boilers = ref<Equipment[]>([])

async function fetchEquipmentLists() {
  try {
    const { data } = await equipmentApi.list()
    chillers.value = data.filter((e) => e.device_type === 'chiller')
    ahus.value = data.filter((e) => e.device_type === 'ahu')
    vavs.value = data.filter((e) => e.device_type === 'vav')
    boilers.value = data.filter((e) => e.device_type === 'boiler')
  } catch {
    chillers.value = []
    ahus.value = []
    vavs.value = []
    boilers.value = []
  }
}

// ----------------------------------------------------------------
// Chiller tab
// ----------------------------------------------------------------
const chillerLoading = ref(false)
const selectedChiller = ref<string | null>(null)
const chillerRecords = ref<ChillerRecord[]>([])

const latestChiller = computed<ChillerRecord | null>(() => {
  if (chillerRecords.value.length === 0) return null
  return chillerRecords.value[chillerRecords.value.length - 1]
})

async function selectChiller(deviceId: string) {
  selectedChiller.value = deviceId
  await fetchChillerRecords()
}

async function fetchChillerRecords() {
  if (!selectedChiller.value) return
  chillerLoading.value = true
  try {
    const params: HVACQueryParams = {
      ...getTimeParams(),
      page: 1,
      page_size: 500,
      sort_by: 'timestamp',
      sort_order: 'asc',
    }
    const { data } = await hvacApi.queryChillerRecords(selectedChiller.value, params)
    chillerRecords.value = data.items
  } catch {
    chillerRecords.value = []
  } finally {
    chillerLoading.value = false
  }
}

const copChartOption = computed(() => {
  const records = chillerRecords.value
  const timestamps = records.map((r) => fmtTimestamp(r.timestamp))
  const copValues = records.map((r) => r.cop ?? null)

  return {
    tooltip: { trigger: 'axis' },
    grid: { top: 16, right: 16, bottom: 24, left: 48, containLabel: false },
    xAxis: {
      type: 'category',
      data: timestamps,
      axisLine: { lineStyle: { color: '#d1d5db' } },
      axisLabel: { fontSize: 10, color: '#6b7280', rotate: 30 },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      name: 'COP',
      nameTextStyle: { fontSize: 11, color: '#6b7280' },
      axisLine: { show: false },
      axisLabel: { fontSize: 11, color: '#6b7280' },
      splitLine: { lineStyle: { color: '#f3f4f6' } },
    },
    series: [
      {
        name: 'COP',
        type: 'line',
        data: copValues,
        symbol: 'none',
        lineStyle: { width: 2, color: '#18a058' },
        itemStyle: { color: '#18a058' },
        areaStyle: { color: 'rgba(24, 160, 88, 0.08)' },
      },
    ],
  }
})

const chillerTempChartOption = computed(() => {
  const records = chillerRecords.value
  const timestamps = records.map((r) => fmtTimestamp(r.timestamp))

  return {
    tooltip: { trigger: 'axis' },
    legend: {
      bottom: 0,
      textStyle: { fontSize: 11 },
    },
    grid: { top: 16, right: 16, bottom: 40, left: 48, containLabel: false },
    xAxis: {
      type: 'category',
      data: timestamps,
      axisLine: { lineStyle: { color: '#d1d5db' } },
      axisLabel: { fontSize: 10, color: '#6b7280', rotate: 30 },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      name: '\u00B0C',
      nameTextStyle: { fontSize: 11, color: '#6b7280' },
      axisLine: { show: false },
      axisLabel: { fontSize: 11, color: '#6b7280' },
      splitLine: { lineStyle: { color: '#f3f4f6' } },
    },
    series: [
      {
        name: '冷冻水供水',
        type: 'line',
        data: records.map((r) => r.chw_supply_temp ?? null),
        symbol: 'none',
        lineStyle: { width: 2, color: '#2080f0' },
        itemStyle: { color: '#2080f0' },
      },
      {
        name: '冷冻水回水',
        type: 'line',
        data: records.map((r) => r.chw_return_temp ?? null),
        symbol: 'none',
        lineStyle: { width: 2, color: '#36ad6a' },
        itemStyle: { color: '#36ad6a' },
      },
      {
        name: '冷却水供水',
        type: 'line',
        data: records.map((r) => r.cw_supply_temp ?? null),
        symbol: 'none',
        lineStyle: { width: 2, color: '#f0a020' },
        itemStyle: { color: '#f0a020' },
      },
      {
        name: '冷却水回水',
        type: 'line',
        data: records.map((r) => r.cw_return_temp ?? null),
        symbol: 'none',
        lineStyle: { width: 2, color: '#d03050' },
        itemStyle: { color: '#d03050' },
      },
    ],
  }
})

// ----------------------------------------------------------------
// AHU tab
// ----------------------------------------------------------------
const ahuLoading = ref(false)
const selectedAHU = ref<string | null>(null)
const ahuRecords = ref<AHURecord[]>([])

const latestAHU = computed<AHURecord | null>(() => {
  if (ahuRecords.value.length === 0) return null
  return ahuRecords.value[ahuRecords.value.length - 1]
})

async function selectAHU(deviceId: string) {
  selectedAHU.value = deviceId
  await fetchAHURecords()
}

async function fetchAHURecords() {
  if (!selectedAHU.value) return
  ahuLoading.value = true
  try {
    const params: HVACQueryParams = {
      ...getTimeParams(),
      page: 1,
      page_size: 500,
      sort_by: 'timestamp',
      sort_order: 'asc',
    }
    const { data } = await hvacApi.queryAHURecords(selectedAHU.value, params)
    ahuRecords.value = data.items
  } catch {
    ahuRecords.value = []
  } finally {
    ahuLoading.value = false
  }
}

const ahuTempChartOption = computed(() => {
  const records = ahuRecords.value
  const timestamps = records.map((r) => fmtTimestamp(r.timestamp))

  return {
    tooltip: { trigger: 'axis' },
    legend: {
      bottom: 0,
      textStyle: { fontSize: 11 },
    },
    grid: { top: 16, right: 16, bottom: 40, left: 48, containLabel: false },
    xAxis: {
      type: 'category',
      data: timestamps,
      axisLine: { lineStyle: { color: '#d1d5db' } },
      axisLabel: { fontSize: 10, color: '#6b7280', rotate: 30 },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      name: '\u00B0C',
      nameTextStyle: { fontSize: 11, color: '#6b7280' },
      axisLine: { show: false },
      axisLabel: { fontSize: 11, color: '#6b7280' },
      splitLine: { lineStyle: { color: '#f3f4f6' } },
    },
    series: [
      {
        name: '送风温度 (SAT)',
        type: 'line',
        data: records.map((r) => r.supply_air_temp ?? null),
        symbol: 'none',
        lineStyle: { width: 2, color: '#2080f0' },
        itemStyle: { color: '#2080f0' },
      },
      {
        name: '回风温度 (RAT)',
        type: 'line',
        data: records.map((r) => r.return_air_temp ?? null),
        symbol: 'none',
        lineStyle: { width: 2, color: '#18a058' },
        itemStyle: { color: '#18a058' },
      },
      {
        name: '混风温度 (MAT)',
        type: 'line',
        data: records.map((r) => r.mixed_air_temp ?? null),
        symbol: 'none',
        lineStyle: { width: 2, color: '#f0a020' },
        itemStyle: { color: '#f0a020' },
      },
      {
        name: '室外温度 (OAT)',
        type: 'line',
        data: records.map((r) => r.outdoor_air_temp ?? null),
        symbol: 'none',
        lineStyle: { width: 2, color: '#d03050' },
        itemStyle: { color: '#d03050' },
      },
    ],
  }
})

// ----------------------------------------------------------------
// VAV tab
// ----------------------------------------------------------------
const vavLoading = ref(false)
const selectedVAV = ref<string | null>(null)
const vavRecords = ref<VAVRecord[]>([])

async function selectVAV(deviceId: string) {
  selectedVAV.value = deviceId
  await fetchVAVRecords()
}

async function fetchVAVRecords() {
  if (!selectedVAV.value) return
  vavLoading.value = true
  try {
    const params: HVACQueryParams = {
      ...getTimeParams(),
      page: 1,
      page_size: 200,
      sort_by: 'timestamp',
      sort_order: 'desc',
    }
    const { data } = await hvacApi.queryVAVRecords(selectedVAV.value, params)
    vavRecords.value = data.items
  } catch {
    vavRecords.value = []
  } finally {
    vavLoading.value = false
  }
}

const vavColumns: DataTableColumn<VAVRecord>[] = [
  {
    title: '时间',
    key: 'timestamp',
    width: 170,
    render(row) {
      return fmtTimestamp(row.timestamp)
    },
  },
  {
    title: '区域温度',
    key: 'zone_temp',
    width: 100,
    align: 'right',
    render(row) {
      return row.zone_temp != null ? row.zone_temp.toFixed(1) + ' \u00B0C' : '--'
    },
  },
  {
    title: '制冷设定点',
    key: 'zone_temp_setpoint_clg',
    width: 110,
    align: 'right',
    render(row) {
      return row.zone_temp_setpoint_clg != null ? row.zone_temp_setpoint_clg.toFixed(1) + ' \u00B0C' : '--'
    },
  },
  {
    title: '制热设定点',
    key: 'zone_temp_setpoint_htg',
    width: 110,
    align: 'right',
    render(row) {
      return row.zone_temp_setpoint_htg != null ? row.zone_temp_setpoint_htg.toFixed(1) + ' \u00B0C' : '--'
    },
  },
  {
    title: '风阀开度',
    key: 'damper_pos',
    width: 100,
    align: 'right',
    render(row) {
      return row.damper_pos != null ? (row.damper_pos * 100).toFixed(1) + '%' : '--'
    },
  },
  {
    title: 'CO\u2082',
    key: 'zone_co2',
    width: 90,
    align: 'right',
    render(row) {
      return row.zone_co2 != null ? row.zone_co2.toFixed(0) + ' ppm' : '--'
    },
  },
  {
    title: '运行模式',
    key: 'operating_mode',
    width: 100,
    render(row) {
      return h(
        NTag,
        { size: 'small', bordered: false },
        { default: () => modeText(row.operating_mode) },
      )
    },
  },
  {
    title: '占用状态',
    key: 'occupancy_status',
    width: 90,
    render(row) {
      const occupied = row.occupancy_status === 'occupied'
      return h(
        NTag,
        { size: 'small', type: occupied ? 'success' : 'default', bordered: false },
        { default: () => (occupied ? '有人' : '无人') },
      )
    },
  },
]

// ----------------------------------------------------------------
// Boiler tab
// ----------------------------------------------------------------
const boilerLoading = ref(false)
const selectedBoiler = ref<string | null>(null)
const boilerRecords = ref<BoilerRecord[]>([])

async function selectBoiler(deviceId: string) {
  selectedBoiler.value = deviceId
  await fetchBoilerRecords()
}

async function fetchBoilerRecords() {
  if (!selectedBoiler.value) return
  boilerLoading.value = true
  try {
    const params: HVACQueryParams = {
      ...getTimeParams(),
      page: 1,
      page_size: 200,
      sort_by: 'timestamp',
      sort_order: 'desc',
    }
    const { data } = await hvacApi.queryBoilerRecords(selectedBoiler.value, params)
    boilerRecords.value = data.items
  } catch {
    boilerRecords.value = []
  } finally {
    boilerLoading.value = false
  }
}

const boilerColumns: DataTableColumn<BoilerRecord>[] = [
  {
    title: '时间',
    key: 'timestamp',
    width: 170,
    render(row) {
      return fmtTimestamp(row.timestamp)
    },
  },
  {
    title: '热水供水温度',
    key: 'hw_supply_temp',
    width: 120,
    align: 'right',
    render(row) {
      return row.hw_supply_temp != null ? row.hw_supply_temp.toFixed(1) + ' \u00B0C' : '--'
    },
  },
  {
    title: '热水回水温度',
    key: 'hw_return_temp',
    width: 120,
    align: 'right',
    render(row) {
      return row.hw_return_temp != null ? row.hw_return_temp.toFixed(1) + ' \u00B0C' : '--'
    },
  },
  {
    title: '效率',
    key: 'efficiency',
    width: 90,
    align: 'right',
    render(row) {
      return row.efficiency != null ? (row.efficiency * 100).toFixed(1) + '%' : '--'
    },
  },
  {
    title: '燃烧率',
    key: 'firing_rate',
    width: 90,
    align: 'right',
    render(row) {
      return row.firing_rate != null ? (row.firing_rate * 100).toFixed(1) + '%' : '--'
    },
  },
  {
    title: '功率',
    key: 'power_kw',
    width: 100,
    align: 'right',
    render(row) {
      return row.power_kw != null ? row.power_kw.toFixed(1) + ' kW' : '--'
    },
  },
  {
    title: '烟气温度',
    key: 'flue_gas_temp',
    width: 100,
    align: 'right',
    render(row) {
      return row.flue_gas_temp != null ? row.flue_gas_temp.toFixed(1) + ' \u00B0C' : '--'
    },
  },
  {
    title: '运行状态',
    key: 'running_status',
    width: 100,
    render(row) {
      const running = row.running_status === 'running'
      return h(
        NTag,
        { size: 'small', type: running ? 'success' : 'default', bordered: false },
        { default: () => statusText(row.running_status) },
      )
    },
  },
]

// ----------------------------------------------------------------
// Tab switch / refresh
// ----------------------------------------------------------------
function onTabChange(tab: string) {
  activeTab.value = tab
  refreshCurrentTab()
}

async function refreshCurrentTab() {
  switch (activeTab.value) {
    case 'chiller':
      if (!selectedChiller.value && chillers.value.length > 0) {
        selectedChiller.value = chillers.value[0].device_id
      }
      await fetchChillerRecords()
      break
    case 'ahu':
      if (!selectedAHU.value && ahus.value.length > 0) {
        selectedAHU.value = ahus.value[0].device_id
      }
      await fetchAHURecords()
      break
    case 'vav':
      if (!selectedVAV.value && vavs.value.length > 0) {
        selectedVAV.value = vavs.value[0].device_id
      }
      await fetchVAVRecords()
      break
    case 'boiler':
      if (!selectedBoiler.value && boilers.value.length > 0) {
        selectedBoiler.value = boilers.value[0].device_id
      }
      await fetchBoilerRecords()
      break
  }
}

// ----------------------------------------------------------------
// Init
// ----------------------------------------------------------------
onMounted(async () => {
  await fetchEquipmentLists()

  // Auto-select first device per category
  if (chillers.value.length > 0) selectedChiller.value = chillers.value[0].device_id
  if (ahus.value.length > 0) selectedAHU.value = ahus.value[0].device_id
  if (vavs.value.length > 0) selectedVAV.value = vavs.value[0].device_id
  if (boilers.value.length > 0) selectedBoiler.value = boilers.value[0].device_id

  // Load data for active tab
  await refreshCurrentTab()
})
</script>

<style scoped>
.param-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px 24px;
}

.param-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid var(--border-light);
}

.param-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.param-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
}

.param-unit {
  font-size: 12px;
  font-weight: 400;
  color: var(--text-tertiary);
}
</style>
