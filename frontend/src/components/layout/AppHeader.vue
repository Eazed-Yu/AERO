<template>
  <n-layout-header bordered style="height: 48px; display: flex; align-items: center; padding: 0 20px; justify-content: space-between;">
    <div style="display: flex; align-items: center; gap: 12px;">
      <span class="header-title">{{ title }}</span>
    </div>
  </n-layout-header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { NLayoutHeader } from 'naive-ui'

const route = useRoute()

const title = computed(() => (route.meta.title as string) || 'AERO')
</script>

<style scoped>
.header-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
</style>
