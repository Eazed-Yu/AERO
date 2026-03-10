<template>
  <div class="page-content">
    <div class="surface" style="padding: 24px">
      <div class="section-title">上传能耗数据文件</div>
      <p style="font-size: 13px; color: var(--text-secondary); margin-bottom: 16px">
        支持 CSV/JSON 文件，包含 building_id、timestamp、electricity_kwh 等字段。
      </p>
      <n-upload
        action="/api/v1/import/upload"
        :max="5"
        accept=".csv,.json"
        :on-finish="handleFinish"
        :on-error="handleError"
        :on-before-upload="handleBeforeUpload"
        :headers="{ 'Accept': 'application/json' }"
      >
        <n-button size="small">选择文件</n-button>
      </n-upload>

      <div v-if="importResult" style="margin-top: 20px; border-top: 1px solid var(--border-light); padding-top: 16px">
        <div class="section-title">导入结果</div>
        <div class="import-result-row">
          <span class="import-label">总记录数</span>
          <span class="import-value">{{ importResult.total }}</span>
        </div>
        <div class="import-result-row">
          <span class="import-label">成功插入</span>
          <span class="import-value" style="color: var(--success)">{{ importResult.inserted }}</span>
        </div>
        <div class="import-result-row">
          <span class="import-label">跳过</span>
          <span class="import-value">{{ importResult.skipped }}</span>
        </div>
        <div class="import-result-row">
          <span class="import-label">错误</span>
          <span class="import-value" :style="importResult.errors > 0 ? 'color: var(--danger)' : ''">
            {{ importResult.errors }}
          </span>
        </div>
        <div v-if="importResult.error_details.length > 0" style="margin-top: 12px">
          <div class="section-title">错误详情</div>
          <div
            v-for="(err, idx) in importResult.error_details"
            :key="idx"
            style="font-size: 12px; color: var(--danger); padding: 2px 0; font-family: monospace"
          >
            {{ err }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NUpload, NButton } from 'naive-ui'
import type { ImportResult } from '@/types/energy'
import type { UploadFileInfo } from 'naive-ui'

const importResult = ref<ImportResult | null>(null)

function handleBeforeUpload() {
  importResult.value = null
  return true
}

function handleFinish({ file, event }: { file: UploadFileInfo; event?: ProgressEvent }) {
  try {
    const target = event?.target as XMLHttpRequest | undefined
    if (target?.response) {
      const result = JSON.parse(target.response)
      importResult.value = result
    }
  } catch {
    // ignore parse errors
  }
}

function handleError({ event }: { file: UploadFileInfo; event?: ProgressEvent }) {
  try {
    const target = event?.target as XMLHttpRequest | undefined
    if (target?.response) {
      const err = JSON.parse(target.response)
      importResult.value = {
        total: 0,
        inserted: 0,
        skipped: 0,
        errors: 1,
        error_details: [err.detail || '上传失败'],
      }
    }
  } catch {
    importResult.value = {
      total: 0,
      inserted: 0,
      skipped: 0,
      errors: 1,
      error_details: ['上传失败，请检查文件格式'],
    }
  }
}
</script>

<style scoped>
.import-result-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 0;
  border-bottom: 1px solid var(--border-light);
  max-width: 320px;
}

.import-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.import-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
}
</style>
