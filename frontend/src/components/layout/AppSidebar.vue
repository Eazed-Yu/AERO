<template>
  <n-layout-sider
    :width="200"
    :collapsed-width="48"
    collapse-mode="width"
    :collapsed="collapsed"
    show-trigger
    bordered
    :native-scrollbar="false"
    style="height: 100vh"
    @collapse="collapsed = true"
    @expand="collapsed = false"
  >
    <div class="sider-logo" v-if="!collapsed">
      <span class="logo-text">AERO</span>
      <span class="logo-sub">能源管理</span>
    </div>
    <div class="sider-logo sider-logo--collapsed" v-else>
      <span class="logo-text">A</span>
    </div>
    <n-menu
      :value="activeKey"
      :collapsed="collapsed"
      :collapsed-width="48"
      :collapsed-icon-size="18"
      :options="menuOptions"
      @update:value="handleSelect"
    />
  </n-layout-sider>
</template>

<script setup lang="ts">
import { h, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NLayoutSider, NMenu, type MenuOption } from 'naive-ui'
import {
  GridOutline,
  BusinessOutline,
  FlashOutline,
  StatsChartOutline,
  WarningOutline,
  HardwareChipOutline,
  ThermometerOutline,
  CloudUploadOutline,
  ChatbubbleEllipsesOutline,
  ExtensionPuzzleOutline,
} from '@vicons/ionicons5'
import { NIcon } from 'naive-ui'

const route = useRoute()
const router = useRouter()
const collapsed = ref(false)

const activeKey = computed(() => route.path)

function renderIcon(icon: any) {
  return () => h(NIcon, null, { default: () => h(icon) })
}

const menuOptions: MenuOption[] = [
  { label: '总览', key: '/dashboard', icon: renderIcon(GridOutline) },
  { label: '建筑管理', key: '/buildings', icon: renderIcon(BusinessOutline) },
  { label: '能耗监测', key: '/energy', icon: renderIcon(FlashOutline) },
  { label: '统计分析', key: '/statistics', icon: renderIcon(StatsChartOutline) },
  { label: '异常检测', key: '/anomaly', icon: renderIcon(WarningOutline) },
  { label: '设备管理', key: '/equipment', icon: renderIcon(HardwareChipOutline) },
  { label: '暖通监测', key: '/hvac', icon: renderIcon(ThermometerOutline) },
  { label: '数据导入', key: '/import', icon: renderIcon(CloudUploadOutline) },
  { label: '智能问答', key: '/qa', icon: renderIcon(ChatbubbleEllipsesOutline) },
  { label: 'MCP 服务', key: '/mcp', icon: renderIcon(ExtensionPuzzleOutline) },
]

function handleSelect(key: string) {
  router.push(key)
}
</script>

<style scoped>
.sider-logo {
  height: 48px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 16px;
  border-bottom: 1px solid var(--border-light);
}

.sider-logo--collapsed {
  justify-content: center;
  padding: 0;
}

.logo-text {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 1px;
}

.logo-sub {
  font-size: 11px;
  color: var(--text-tertiary);
}
</style>
