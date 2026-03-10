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
  endpoint: string | null
  transport: string
  mount_error: string | null
}

export const mcpApi = {
  getStatus: () => api.get<MCPStatus>('/mcp/status'),

  toggle: (enabled: boolean) =>
    api.post<{ enabled: boolean }>('/mcp/toggle', { enabled }),
}
