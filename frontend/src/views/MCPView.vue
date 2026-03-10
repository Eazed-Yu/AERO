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
      <div v-if="status?.mount_error" class="mount-error-box">
        <div class="mount-error-title">MCP 挂载异常</div>
        <div class="mount-error-text">{{ status.mount_error }}</div>
      </div>
    </div>

    <!-- 连接信息 -->
    <div class="surface" style="padding: 24px; margin-bottom: 16px">
      <div class="section-title" style="margin-bottom: 12px">连接信息</div>
      <div class="info-row">
        <span class="info-label">MCP 端点</span>
        <code class="info-value">{{ mcpEndpointUrl }}</code>
        <n-button text size="tiny" @click="copyText(mcpEndpointUrl)">复制</n-button>
      </div>
      <div style="margin-top: 10px; font-size: 12px; color: var(--text-secondary)">
        建议对外通过 HTTPS 暴露该端点，供 Cherry Studio、Claude Desktop、Cursor 等客户端导入。
      </div>
    </div>

    <!-- 客户接入流程 -->
    <div class="surface" style="padding: 24px; margin-bottom: 16px">
      <div class="section-title" style="margin-bottom: 12px">客户接入流程</div>
      <div style="font-size: 13px; color: var(--text-secondary); line-height: 1.8">
        1. 确认服务端可访问（建议公网 HTTPS 或企业内网网关）<br>
        2. 将下方对应客户端配置粘贴到客户端 MCP 设置中<br>
        3. 刷新客户端并执行 <code>health_check</code> 工具验证连通性<br>
        4. 再执行 <code>get_capabilities</code> 与业务工具进行验收
      </div>
    </div>

    <!-- 配置指南 -->
    <div class="surface" style="padding: 24px; margin-bottom: 16px">
      <div class="section-title" style="margin-bottom: 16px">客户端配置指南</div>

      <!-- Claude Desktop -->
      <div style="margin-bottom: 24px">
        <div class="guide-header-row">
          <div style="font-size: 14px; font-weight: 500">Claude Desktop</div>
          <n-button
            size="small"
            type="primary"
            :disabled="!canCopyClaudeConfig"
            @click="copyClaudeConfig"
          >
            {{ claudeCopied ? '已复制' : '一键复制 Claude 配置' }}
          </n-button>
        </div>
        <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 8px">
          配置文件位置：
        </div>
        <div style="font-size: 12px; color: var(--text-tertiary); margin-bottom: 4px; padding-left: 12px">
          • Windows: <code>%APPDATA%\Claude\claude_desktop_config.json</code>
        </div>
        <div style="font-size: 12px; color: var(--text-tertiary); margin-bottom: 8px; padding-left: 12px">
          • macOS: <code>~/Library/Application Support/Claude/claude_desktop_config.json</code>
        </div>
        <pre class="config-block" @click="copyText(claudeConfigJson)">{{ claudeConfigJson }}</pre>
      </div>

      <!-- Cherry Studio -->
      <div style="margin-bottom: 24px">
        <div style="font-size: 14px; font-weight: 500; margin-bottom: 12px">
          Cherry Studio
        </div>
        <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 8px">
          在设置 → MCP 服务器中添加：
        </div>
        <pre class="config-block" @click="copyText(cherryConfigJson)">{{ cherryConfigJson }}</pre>
      </div>

      <!-- 通用 HTTP 客户端 -->
      <div>
        <div style="font-size: 14px; font-weight: 500; margin-bottom: 12px">
          其他 MCP 客户端（HTTP）
        </div>
        <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 8px">
          直接使用 HTTP 端点：
        </div>
        <div class="info-row">
          <code class="info-value">{{ mcpEndpointUrl }}</code>
          <n-button text size="tiny" @click="copyText(mcpEndpointUrl)">复制</n-button>
        </div>
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
import { mcpApi, type MCPClientConfig, type MCPStatus } from '@/api/mcp'

const message = useMessage()
const status = ref<MCPStatus | null>(null)
const clientConfig = ref<MCPClientConfig | null>(null)
const toggling = ref(false)
const claudeCopied = ref(false)

const canCopyClaudeConfig = computed(() => {
  return Boolean(status.value?.available && !status.value?.mount_error && clientConfig.value)
})

const mcpEndpointUrl = computed(() => {
  return clientConfig.value?.endpoint || status.value?.endpoint || '-'
})

const claudeConfigJson = computed(() => {
  return JSON.stringify(clientConfig.value?.claudeDesktop ?? {}, null, 2)
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
    const [statusRes, configRes] = await Promise.all([
      mcpApi.getStatus(),
      mcpApi.getConfig(),
    ])
    status.value = statusRes.data
    clientConfig.value = configRes.data
  } catch {
    message.error('获取 MCP 配置失败')
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

function copyClaudeConfig() {
  if (!canCopyClaudeConfig.value) {
    message.warning('MCP 挂载异常或不可用，暂不可复制')
    return
  }
  copyText(claudeConfigJson.value)
  claudeCopied.value = true
  setTimeout(() => {
    claudeCopied.value = false
  }, 1600)
}

function copyText(text: string) {
  navigator.clipboard.writeText(text).then(
    () => message.success('已复制到剪贴板'),
    () => message.error('复制失败'),
  )
}

const cherryConfigJson = computed(() => {
  return JSON.stringify(clientConfig.value?.cherryStudio ?? {}, null, 2)
})

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

.mount-error-box {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 6px;
  border: 1px solid #f3b8ad;
  background: #fff3f0;
}

.mount-error-title {
  font-size: 12px;
  font-weight: 600;
  color: #c0392b;
  margin-bottom: 4px;
}

.mount-error-text {
  font-size: 12px;
  color: #a84232;
  word-break: break-word;
}

.guide-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
</style>
