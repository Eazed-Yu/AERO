<template>
  <div class="page-content">
    <!-- 状态卡片 -->
    <div class="surface" style="padding: 24px; margin-bottom: 16px">
      <div style="display: flex; align-items: center; justify-content: space-between">
        <div>
          <div class="section-title" style="margin-bottom: 4px">MCP 服务状态</div>
          <div style="font-size: 13px; color: var(--text-secondary)">
            Model Context Protocol — 允许 AI 客户端调用系统工具
          </div>
        </div>
        <div style="display: flex; align-items: center; gap: 12px">
          <span
            class="status-dot"
            :class="status?.enabled ? 'status-dot--on' : 'status-dot--off'"
          />
          <span style="font-size: 13px; color: var(--text-secondary)">
            {{ status?.enabled ? '运行中' : '已停用' }}
          </span>
          <n-switch
            :value="status?.enabled"
            :disabled="!status?.available || toggling"
            :loading="toggling"
            @update:value="handleToggle"
          />
        </div>
      </div>
      <div
        v-if="!status?.available"
        style="margin-top: 12px; font-size: 12px; color: var(--warning)"
      >
        FastMCP 未安装，MCP 功能不可用。请安装依赖：pip install fastmcp
      </div>
    </div>

    <!-- 连接信息 -->
    <div class="surface" style="padding: 24px; margin-bottom: 16px">
      <div class="section-title" style="margin-bottom: 12px">连接信息</div>
      <div class="info-row">
        <span class="info-label">SSE 端点</span>
        <code class="info-value">{{ mcpEndpointUrl }}</code>
        <n-button text size="tiny" @click="copyText(mcpEndpointUrl)">复制</n-button>
      </div>
      <div style="margin-top: 16px">
        <div style="font-size: 13px; color: var(--text-secondary); margin-bottom: 8px">
          Claude Desktop 配置（点击复制）
        </div>
        <pre class="config-block" @click="copyText(claudeConfigJson)">{{ claudeConfigJson }}</pre>
      </div>
    </div>

    <!-- 工具列表 -->
    <div class="surface" style="padding: 24px">
      <div class="section-title" style="margin-bottom: 12px">
        工具列表
        <span style="font-weight: 400; color: var(--text-tertiary); font-size: 12px; margin-left: 8px">
          共 {{ status?.tool_count ?? 0 }} 个
        </span>
      </div>
      <n-data-table
        :columns="toolColumns"
        :data="status?.tools ?? []"
        :bordered="false"
        size="small"
        :pagination="false"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import { NSwitch, NButton, NDataTable, NTag, useMessage } from 'naive-ui'
import { mcpApi, type MCPStatus } from '@/api/mcp'

const message = useMessage()
const status = ref<MCPStatus | null>(null)
const toggling = ref(false)

const mcpEndpointUrl = computed(() => {
  const origin = window.location.origin
  return `${origin}/mcp`
})

const claudeConfigJson = computed(() => {
  return JSON.stringify(
    {
      mcpServers: {
        aero: {
          url: mcpEndpointUrl.value,
        },
      },
    },
    null,
    2,
  )
})

const toolColumns = [
  {
    title: '工具名称',
    key: 'name',
    width: 200,
    render(row: any) {
      return h('code', { style: 'font-size: 13px' }, row.name)
    },
  },
  {
    title: '描述',
    key: 'description',
    ellipsis: { tooltip: true },
  },
  {
    title: '参数',
    key: 'parameters',
    width: 320,
    render(row: any) {
      if (!row.parameters?.length) return '—'
      return row.parameters.map((p: any) =>
        h(
          NTag,
          {
            size: 'small',
            type: p.required ? 'primary' : 'default',
            bordered: false,
            style: 'margin: 2px 4px 2px 0',
          },
          { default: () => `${p.name}: ${p.type}` },
        ),
      )
    },
  },
]

async function fetchStatus() {
  try {
    const res = await mcpApi.getStatus()
    status.value = res.data
  } catch {
    message.error('获取 MCP 状态失败')
  }
}

async function handleToggle(enabled: boolean) {
  toggling.value = true
  try {
    await mcpApi.toggle(enabled)
    await fetchStatus()
    message.success(enabled ? 'MCP 服务已启用' : 'MCP 服务已停用')
  } catch {
    message.error('切换失败')
  } finally {
    toggling.value = false
  }
}

function copyText(text: string) {
  navigator.clipboard.writeText(text).then(
    () => message.success('已复制到剪贴板'),
    () => message.error('复制失败'),
  )
}

onMounted(fetchStatus)
</script>

<style scoped>
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.status-dot--on {
  background: var(--success, #18a058);
  box-shadow: 0 0 6px var(--success, #18a058);
}

.status-dot--off {
  background: var(--text-tertiary, #999);
}

.info-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.info-label {
  font-size: 13px;
  color: var(--text-secondary);
  min-width: 72px;
}

.info-value {
  font-size: 13px;
  background: var(--bg-secondary, #f5f5f5);
  padding: 4px 10px;
  border-radius: 4px;
  user-select: all;
}

.config-block {
  background: var(--bg-secondary, #f5f5f5);
  border-radius: 6px;
  padding: 12px 16px;
  font-size: 12px;
  line-height: 1.6;
  cursor: pointer;
  user-select: all;
  overflow-x: auto;
  margin: 0;
  transition: background 0.15s;
}

.config-block:hover {
  background: var(--border-light, #e8e8e8);
}
</style>
