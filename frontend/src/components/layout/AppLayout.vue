<template>
  <n-layout has-sider style="height: 100vh">
    <AppSidebar />
    <n-layout>
      <AppHeader />
      <n-layout-content :native-scrollbar="false" content-style="background: var(--bg-base);">
        <router-view />
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<script setup lang="ts">
import { NLayout, NLayoutContent } from 'naive-ui'
import AppSidebar from './AppSidebar.vue'
import AppHeader from './AppHeader.vue'
</script>
