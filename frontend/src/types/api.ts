export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface ApiError {
  detail: string
}

export interface BatchOperationResult {
  total: number
  success: number
  skipped: number
  failed: number
  failed_items: string[]
}
