<template>
  <div class="kg-container">
    <!-- Controls -->
    <div class="kg-controls">
      <n-select
        v-model:value="qaStore.selectedLabel"
        :options="labelOptions"
        placeholder="选择实体标签..."
        size="small"
        filterable
        style="width: 200px"
        @update:value="handleLabelChange"
      />
      <n-input-number
        v-model:value="maxNodes"
        :min="10"
        :max="500"
        :step="10"
        size="small"
        style="width: 130px"
      >
        <template #prefix>节点</template>
      </n-input-number>
      <n-button size="small" type="primary" :loading="qaStore.graphLoading" @click="loadGraph">
        加载图谱
      </n-button>
      <n-button size="small" quaternary @click="qaStore.fetchGraphLabels()">
        刷新标签
      </n-button>
      <span v-if="qaStore.graphNodes.length" class="kg-stats">
        {{ qaStore.graphNodes.length }} 节点 / {{ qaStore.graphEdges.length }} 关系
      </span>
    </div>

    <!-- Graph Canvas -->
    <div class="kg-canvas-wrapper">
      <div ref="graphContainer" class="kg-canvas" />
      <div v-if="qaStore.graphLoading" class="kg-loading">
        <n-spin size="medium" />
      </div>
      <div v-if="!qaStore.graphLoading && qaStore.graphNodes.length === 0" class="kg-empty">
        <span>选择标签后加载知识图谱</span>
      </div>
    </div>

    <!-- Detail Panel -->
    <n-drawer v-model:show="showDetail" :width="360" placement="right">
      <n-drawer-content :title="selectedNode?.label || '节点详情'">
        <div v-if="selectedNode" class="kg-detail">
          <div class="kg-detail-row">
            <span class="kg-detail-label">ID</span>
            <span class="kg-detail-value" style="font-family: monospace">{{ selectedNode.id }}</span>
          </div>
          <div class="kg-detail-row">
            <span class="kg-detail-label">标签</span>
            <span class="kg-detail-value">{{ selectedNode.label }}</span>
          </div>
          <template v-for="(val, key) in selectedNode.properties" :key="key">
            <div class="kg-detail-row">
              <span class="kg-detail-label">{{ key }}</span>
              <span class="kg-detail-value">{{ val }}</span>
            </div>
          </template>
        </div>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import {
  NSelect,
  NInputNumber,
  NButton,
  NSpin,
  NDrawer,
  NDrawerContent,
} from 'naive-ui'
import { useQAStore } from '@/stores/qa'
import type { GraphNode } from '@/api/knowledge'

const qaStore = useQAStore()
const graphContainer = ref<HTMLElement | null>(null)
const maxNodes = ref(100)
const showDetail = ref(false)
const selectedNode = ref<GraphNode | null>(null)

let network: any = null

const labelOptions = ref<Array<{ label: string; value: string }>>([])

watch(
  () => qaStore.graphLabels,
  (labels) => {
    labelOptions.value = labels.map((l) => ({ label: l, value: l }))
  },
  { immediate: true }
)

function handleLabelChange(label: string) {
  if (label) loadGraph()
}

async function loadGraph() {
  if (!qaStore.selectedLabel) return
  await qaStore.fetchSubgraph(qaStore.selectedLabel, maxNodes.value)
  await nextTick()
  renderGraph()
}

function renderGraph() {
  if (!graphContainer.value) return

  const nodes = qaStore.graphNodes.map((n) => ({
    id: n.id,
    label: n.label,
    title: n.label,
    font: { size: 12 },
  }))

  const edges = qaStore.graphEdges.map((e, i) => ({
    id: `e-${i}`,
    from: e.source,
    to: e.target,
    label: e.relation,
    font: { size: 10, align: 'middle' },
    arrows: 'to',
  }))

  import('vis-network').then(({ Network }) => {
    import('vis-data').then(({ DataSet }) => {
      if (network) {
        network.destroy()
        network = null
      }

      const data = {
        nodes: new DataSet(nodes),
        edges: new DataSet(edges),
      }

      const options = {
        physics: {
          solver: 'forceAtlas2Based',
          forceAtlas2Based: {
            gravitationalConstant: -30,
            springLength: 120,
          },
          stabilization: { iterations: 100 },
        },
        nodes: {
          shape: 'dot',
          size: 16,
          color: {
            background: '#18a058',
            border: '#0c7a43',
            highlight: { background: '#36ad6a', border: '#0c7a43' },
          },
          font: { color: '#262626', face: 'system-ui' },
        },
        edges: {
          color: { color: '#d4d4d8', highlight: '#18a058' },
          smooth: { enabled: true, type: 'continuous', roundness: 0.5 },
          font: { color: '#999', strokeWidth: 0 },
        },
        interaction: {
          hover: true,
          tooltipDelay: 200,
        },
      }

      network = new Network(graphContainer.value!, data, options)

      network.on('click', (params: any) => {
        if (params.nodes.length > 0) {
          const nodeId = params.nodes[0]
          const node = qaStore.graphNodes.find((n) => n.id === nodeId)
          if (node) {
            selectedNode.value = node
            showDetail.value = true
          }
        }
      })
    })
  })
}

onMounted(() => {
  qaStore.fetchGraphLabels()
})

onBeforeUnmount(() => {
  if (network) {
    network.destroy()
    network = null
  }
})
</script>

<style scoped>
.kg-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 12px;
}

.kg-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.kg-stats {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-left: auto;
}

.kg-canvas-wrapper {
  flex: 1;
  min-height: 300px;
  position: relative;
  border: 1px solid var(--border-light);
  border-radius: 3px;
  background: #fafafc;
}

.kg-canvas {
  width: 100%;
  height: 100%;
}

.kg-loading,
.kg-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.kg-empty span {
  font-size: 13px;
  color: var(--text-tertiary);
}

.kg-detail {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.kg-detail-row {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.kg-detail-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
}

.kg-detail-value {
  font-size: 13px;
  color: var(--text-primary);
  word-break: break-all;
}
</style>
