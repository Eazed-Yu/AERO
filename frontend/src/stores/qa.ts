import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  knowledgeApi,
  type DocumentResponse,
  type DocumentListResponse,
  type GraphNode,
  type GraphEdge,
  type QueryMode,
} from '@/api/knowledge'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  processing_time_ms?: number
}

export const useQAStore = defineStore('qa', () => {
  // ── Chat State ─────────────────────────────────────────
  const messages = ref<ChatMessage[]>([])
  const loading = ref(false)
  const mode = ref('hybrid')
  const topK = ref(10)
  const responseType = ref('Multiple Paragraphs')
  const modes = ref<QueryMode[]>([])

  // ── Document State ─────────────────────────────────────
  const documents = ref<DocumentResponse[]>([])
  const documentsTotal = ref(0)
  const documentsPage = ref(1)
  const documentsPageSize = ref(20)
  const documentsLoading = ref(false)

  // ── Graph State ────────────────────────────────────────
  const graphLabels = ref<string[]>([])
  const graphNodes = ref<GraphNode[]>([])
  const graphEdges = ref<GraphEdge[]>([])
  const graphLoading = ref(false)
  const selectedLabel = ref('')

  // ── Chat Actions ───────────────────────────────────────

  async function ask(question: string) {
    const history = messages.value
      .filter((m) => m.role === 'user' || m.role === 'assistant')
      .slice(-10)
      .map((m) => ({ role: m.role, content: m.content }))

    messages.value.push({
      role: 'user',
      content: question,
      timestamp: new Date().toISOString(),
    })

    loading.value = true
    try {
      const { data } = await knowledgeApi.query({
        question,
        mode: mode.value,
        top_k: topK.value,
        response_type: responseType.value,
        conversation_history: history,
      })
      messages.value.push({
        role: 'assistant',
        content: data.answer,
        timestamp: new Date().toISOString(),
        processing_time_ms: data.processing_time_ms,
      })
    } catch (e: any) {
      messages.value.push({
        role: 'assistant',
        content: `错误: ${e.response?.data?.detail || e.message}`,
        timestamp: new Date().toISOString(),
      })
    } finally {
      loading.value = false
    }
  }

  function clearMessages() {
    messages.value = []
  }

  async function fetchModes() {
    try {
      const { data } = await knowledgeApi.getModes()
      modes.value = data.modes
    } catch {
      // keep defaults
    }
  }

  // ── Document Actions ───────────────────────────────────

  async function fetchDocuments(page?: number) {
    documentsLoading.value = true
    try {
      const { data } = await knowledgeApi.listDocuments({
        page: page ?? documentsPage.value,
        page_size: documentsPageSize.value,
      })
      documents.value = data.items
      documentsTotal.value = data.total
      documentsPage.value = data.page
    } finally {
      documentsLoading.value = false
    }
  }

  async function ingestText(text: string) {
    await knowledgeApi.ingestText({ text })
    await fetchDocuments(1)
  }

  async function uploadFile(file: File) {
    await knowledgeApi.uploadFile(file)
    await fetchDocuments(1)
  }

  async function deleteDocument(docId: string) {
    await knowledgeApi.deleteDocument(docId)
    await fetchDocuments()
  }

  // ── Graph Actions ──────────────────────────────────────

  async function fetchGraphLabels() {
    graphLoading.value = true
    try {
      const { data } = await knowledgeApi.getGraphLabels()
      graphLabels.value = Array.isArray(data) ? data : []
    } finally {
      graphLoading.value = false
    }
  }

  async function fetchSubgraph(label: string, maxNodes = 100) {
    graphLoading.value = true
    selectedLabel.value = label
    try {
      const { data } = await knowledgeApi.getSubgraph({
        label,
        max_depth: 3,
        max_nodes: maxNodes,
      })
      graphNodes.value = data.nodes
      graphEdges.value = data.edges
    } finally {
      graphLoading.value = false
    }
  }

  return {
    // chat
    messages,
    loading,
    mode,
    topK,
    responseType,
    modes,
    ask,
    clearMessages,
    fetchModes,
    // documents
    documents,
    documentsTotal,
    documentsPage,
    documentsPageSize,
    documentsLoading,
    fetchDocuments,
    ingestText,
    uploadFile,
    deleteDocument,
    // graph
    graphLabels,
    graphNodes,
    graphEdges,
    graphLoading,
    selectedLabel,
    fetchGraphLabels,
    fetchSubgraph,
  }
})
