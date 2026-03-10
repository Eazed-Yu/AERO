import api from '.'

// ── Types ────────────────────────────────────────────────

export interface DocumentResponse {
  id: string
  status: string
  content_summary: string
  content_length: number
  created_at: string
  updated_at: string
  file_path: string
  chunks_count: number | null
  error_msg: string | null
}

export interface DocumentListResponse {
  items: DocumentResponse[]
  total: number
  page: number
  page_size: number
}

export interface DocumentStatusCounts {
  pending: number
  processing: number
  preprocessed: number
  processed: number
  failed: number
}

export interface KnowledgeQueryResponse {
  answer: string
  mode_used: string
  processing_time_ms: number
}

export interface GraphNode {
  id: string
  label: string
  properties: Record<string, unknown>
}

export interface GraphEdge {
  source: string
  target: string
  relation: string
  properties: Record<string, unknown>
}

export interface SubgraphResponse {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface QueryMode {
  id: string
  name: string
  description: string
}

// ── API ──────────────────────────────────────────────────

export const knowledgeApi = {
  // Document Management
  ingestText: (data: { text: string; description?: string }) =>
    api.post('/knowledge/documents/text', data),

  uploadFile: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/knowledge/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
    })
  },

  listDocuments: (params?: { status?: string; page?: number; page_size?: number }) =>
    api.get<DocumentListResponse>('/knowledge/documents', { params }),

  getDocumentStatus: () =>
    api.get<DocumentStatusCounts>('/knowledge/documents/status'),

  getDocument: (docId: string) =>
    api.get<DocumentResponse>(`/knowledge/documents/${docId}`),

  deleteDocument: (docId: string) =>
    api.delete(`/knowledge/documents/${docId}`),

  // Graph Exploration
  getGraphLabels: () =>
    api.get<string[]>('/knowledge/graph/labels'),

  getSubgraph: (data: { label: string; max_depth?: number; max_nodes?: number }) =>
    api.post<SubgraphResponse>('/knowledge/graph/subgraph', data),

  getEntityInfo: (entityName: string) =>
    api.post('/knowledge/graph/entity/info', { entity_name: entityName }),

  deleteEntity: (entityName: string) =>
    api.delete(`/knowledge/graph/entity/${entityName}`),

  // Query
  query: (data: {
    question: string
    mode?: string
    top_k?: number
    only_need_context?: boolean
    response_type?: string
    conversation_history?: Array<{ role: string; content: string }>
  }) => api.post<KnowledgeQueryResponse>('/knowledge/query', data),

  queryStream: (data: {
    question: string
    mode?: string
    top_k?: number
    response_type?: string
    conversation_history?: Array<{ role: string; content: string }>
  }) => {
    return fetch('/api/v1/knowledge/query/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
  },

  getModes: () =>
    api.get<{ modes: QueryMode[] }>('/knowledge/modes'),
}
