<template>
  <n-layout-header bordered style="height: 48px; display: flex; align-items: center; padding: 0 20px; justify-content: space-between;">
    <div style="display: flex; align-items: center; gap: 12px;">
      <span class="header-title">{{ title }}</span>
    </div>
    <div style="display: flex; align-items: center; gap: 12px;">
      <n-select
        v-model:value="buildingStore.current"
        :options="buildingOptions"
        size="small"
        style="width: 180px"
        placeholder="选择建筑"
        @update:value="buildingStore.setCurrent"
      />
    </div>
  </n-layout-header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { NLayoutHeader, NSelect } from 'naive-ui'
import { useBuildingStore } from '@/stores/building'

const route = useRoute()
const buildingStore = useBuildingStore()

const title = computed(() => (route.meta.title as string) || 'AERO')

const buildingOptions = computed(() =>
  buildingStore.buildings.map((b) => ({
    label: b.name,
    value: b.building_id,
  }))
)
</script>

<style scoped>
.header-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
</style>
