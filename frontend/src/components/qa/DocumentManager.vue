<template>
  <div class="doc-manager">
    <!-- Upload Area -->
    <div class="doc-upload-section">
      <n-tabs type="segment" size="small">
        <n-tab-pane name="text" tab="文本导入">
          <n-input
            v-model:value="textInput"
            type="textarea"
            placeholder="粘贴文本内容..."
            :rows="4"
            style="margin-bottom: 12px"
          />
          <n-button
            type="primary"
            size="small"
            :disabled="!textInput.trim()"
            :loading="ingesting"
            @click="handleIngestText"
          >
            导入文本
          </n-button>
        </n-tab-pane>
        <n-tab-pane name="file" tab="文件上传">
          <n-upload
            :custom-request="handleUpload"
            accept=".txt,.md"
            :show-file-list="false"
          >
            <n-upload-dragger>
              <div style="padding: 20px 0">
                <n-icon size="36" :depth="3">
                  <CloudUploadOutline />
                </n-icon>
                <p style="margin: 8px 0 0; font-size: 13px; color: var(--text-secondary)">
                  点击或拖拽上传 .txt / .md 文件
                </p>
              </div>
            </n-upload-dragger>
          </n-upload>
        </n-tab-pane>
      </n-tabs>
    </div>

    <!-- Document List -->
    <div class="doc-list-section">
      <div class="doc-list-header">
        <span class="section-title">文档列表</span>
        <n-button size="tiny" quaternary @click="qaStore.fetchDocuments()">
          刷新
        </n-button>
      </div>
      <n-data-table
        :columns="columns"
        :data="qaStore.documents"
        :loading="qaStore.documentsLoading"
        :pagination="pagination"
        :row-key="(row: DocumentResponse) => row.id"
        size="small"
        striped
        @update:page="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, h, computed, onMounted } from 'vue'
import {
  NTabs,
  NTabPane,
  NInput,
  NButton,
  NUpload,
  NUploadDragger,
  NIcon,
  NDataTable,
  NBadge,
  NTag,
  NPopconfirm,
  useMessage,
  type UploadCustomRequestOptions,
  type DataTableColumns,
} from 'naive-ui'
import { CloudUploadOutline } from '@vicons/ionicons5'
import { useQAStore } from '@/stores/qa'
import type { DocumentResponse } from '@/api/knowledge'

const qaStore = useQAStore()
const message = useMessage()
const textInput = ref('')
const ingesting = ref(false)

const pagination = computed(() => ({
  page: qaStore.documentsPage,
  pageSize: qaStore.documentsPageSize,
  itemCount: qaStore.documentsTotal,
  pageSlot: 5,
}))

const statusTagType = (status: string) => {
  const map: Record<string, 'success' | 'warning' | 'error' | 'info' | 'default'> = {
    processed: 'success',
    processing: 'warning',
    preprocessed: 'info',
    pending: 'default',
    failed: 'error',
  }
  return map[status] || 'default'
}

const statusLabel = (status: string) => {
  const map: Record<string, string> = {
    processed: '已完成',
    processing: '处理中',
    preprocessed: '预处理',
    pending: '等待中',
    failed: '失败',
  }
  return map[status] || status
}

const columns: DataTableColumns<DocumentResponse> = [
  {
    title: 'ID',
    key: 'id',
    width: 100,
    ellipsis: { tooltip: true },
    render: (row) => h('span', { style: 'font-family: monospace; font-size: 12px' }, row.id.slice(0, 12) + '...'),
  },
  {
    title: '摘要',
    key: 'content_summary',
    ellipsis: { tooltip: true },
  },
  {
    title: '长度',
    key: 'content_length',
    width: 80,
    render: (row) => row.content_length.toLocaleString(),
  },
  {
    title: '分块',
    key: 'chunks_count',
    width: 60,
    render: (row) => row.chunks_count ?? '-',
  },
  {
    title: '状态',
    key: 'status',
    width: 80,
    render: (row) => h(NTag, { type: statusTagType(row.status), size: 'small', bordered: false }, () => statusLabel(row.status)),
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 150,
    render: (row) => {
      if (!row.created_at) return '-'
      const d = new Date(row.created_at)
      return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 70,
    render: (row) =>
      h(
        NPopconfirm,
        { onPositiveClick: () => handleDelete(row.id) },
        {
          trigger: () => h(NButton, { size: 'tiny', type: 'error', quaternary: true }, () => '删除'),
          default: () => '确定删除此文档？',
        }
      ),
  },
]

async function handleIngestText() {
  if (!textInput.value.trim()) return
  ingesting.value = true
  try {
    await qaStore.ingestText(textInput.value.trim())
    textInput.value = ''
    message.success('文本已提交处理')
  } catch (e: any) {
    message.error(e.response?.data?.detail || '导入失败')
  } finally {
    ingesting.value = false
  }
}

async function handleUpload({ file, onFinish, onError }: UploadCustomRequestOptions) {
  try {
    await qaStore.uploadFile(file.file as File)
    message.success(`${file.name} 上传成功`)
    onFinish()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '上传失败')
    onError()
  }
}

async function handleDelete(docId: string) {
  try {
    await qaStore.deleteDocument(docId)
    message.success('文档已删除')
  } catch (e: any) {
    message.error(e.response?.data?.detail || '删除失败')
  }
}

function handlePageChange(page: number) {
  qaStore.fetchDocuments(page)
}

onMounted(() => {
  qaStore.fetchDocuments()
})
</script>

<style scoped>
.doc-manager {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
}

.doc-upload-section {
  background: var(--bg-surface);
  border: 1px solid var(--border-light);
  border-radius: 3px;
  padding: 16px;
}

.doc-list-section {
  flex: 1;
  min-height: 0;
}

.doc-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}
</style>
