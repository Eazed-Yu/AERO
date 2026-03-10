import api from '.'

export interface MCPToolParam {
  name: string
  type: string
  description: string
  required: boolean
}

export interface MCPTool {
  name: string
  description: string
  parameters: MCPToolParam[]
}

export interface MCPStatus {
  name: string
  enabled: boolean
  available: boolean
  tool_count: number
  tools: MCPTool[]
  mount_path: string
  endpoint: string | null
  transport: string
  mount_error: string | null
}

export interface MCPClientConfig {
  server_name: string
  endpoint: string
  transport: string
  claudeDesktop: Record<string, unknown>
  cherryStudio: Record<string, unknown>
}

export const mcpApi = {
  getStatus: () => api.get<MCPStatus>('/mcp/status'),

  getConfig: () => api.get<MCPClientConfig>('/mcp/config'),

  toggle: (enabled: boolean) =>
    api.post<{ enabled: boolean }>('/mcp/toggle', { enabled }),
}
