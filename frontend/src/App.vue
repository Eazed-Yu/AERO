<template>
  <n-config-provider :theme-overrides="themeOverrides" :locale="zhCN" :date-locale="dateZhCN">
    <n-message-provider>
      <n-dialog-provider>
        <AppLayout />
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import {
  NConfigProvider,
  NDialogProvider,
  NMessageProvider,
  type GlobalThemeOverrides,
} from 'naive-ui'
import { zhCN, dateZhCN } from 'naive-ui'
import AppLayout from '@/components/layout/AppLayout.vue'
import { useBuildingStore } from '@/stores/building'

const buildingStore = useBuildingStore()
onMounted(() => buildingStore.fetchBuildings())

const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#18a058',
    primaryColorHover: '#36ad6a',
    primaryColorPressed: '#0c7a43',
    primaryColorSuppl: '#36ad6a',
    bodyColor: '#f5f7fa',
    cardColor: '#ffffff',
    borderRadius: '3px',
    borderColor: '#efeff5',
    fontSize: '14px',
    textColor1: '#262626',
    textColor2: '#525252',
    textColor3: '#a0a0a0',
  },
  Menu: {
    itemHeight: '36px',
  },
  DataTable: {
    thColor: '#fafafc',
    tdColor: '#ffffff',
    borderColor: '#efeff5',
  },
}
</script>
