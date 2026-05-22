import { ref, type Ref } from 'vue'
import api, { ApiError } from '@/api'

export interface PaginationState {
  total: number
  page: number
  pageSize: number
  totalPages: number
}

export interface AsyncState<T> {
  data: Ref<T>
  loading: Ref<boolean>
  error: Ref<string | null>
}

export function handleError(e: unknown, defaultMsg: string): string {
  if (e && typeof e === 'object' && 'message' in e) {
    return (e as ApiError).message || defaultMsg
  }
  return defaultMsg
}

export function useAsyncState<T>(initialValue: T): AsyncState<T> {
  const data = ref<T>(initialValue) as Ref<T>
  const loading = ref(false)
  const error = ref<string | null>(null)

  return { data, loading, error }
}

export function usePagination(initialPage = 1, initialPageSize = 10) {
  const pagination = ref<PaginationState>({
    total: 0,
    page: initialPage,
    pageSize: initialPageSize,
    totalPages: 0
  })

  const setPage = (page: number) => {
    pagination.value.page = page
  }

  const setPageSize = (size: number) => {
    pagination.value.pageSize = size
  }

  const updateFromResponse = (response: { total: number; page: number; page_size: number; total_pages: number }) => {
    pagination.value = {
      total: response.total,
      page: response.page,
      pageSize: response.page_size,
      totalPages: response.total_pages
    }
  }

  return {
    pagination,
    setPage,
    setPageSize,
    updateFromResponse
  }
}

export function createApiRequest<T, P = void>(
  endpoint: string,
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET'
) {
  return async (params?: P): Promise<T | null> => {
    try {
      let response
      switch (method) {
        case 'GET':
          response = await api.get<T>(endpoint, { params })
          break
        case 'POST':
          response = await api.post<T>(endpoint, params)
          break
        case 'PUT':
          response = await api.put<T>(endpoint, params)
          break
        case 'DELETE':
          response = await api.delete<T>(endpoint)
          break
      }
      return response.data
    } catch (e) {
      console.error(`API request failed: ${endpoint}`, e)
      return null
    }
  }
}

export function useCRUD<T extends { id: number }>(baseUrl: string) {
  const items = ref<T[]>([]) as Ref<T[]>
  const currentItem = ref<T | null>(null) as Ref<T | null>
  const loading = ref(false)
  const error = ref<string | null>(null)

  const fetchAll = async (params?: Record<string, any>) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<T[]>(baseUrl, { params })
      items.value = response.data
      return response.data
    } catch (e) {
      error.value = handleError(e, `获取列表失败`)
      console.error(`Failed to fetch ${baseUrl}:`, e)
      return null
    } finally {
      loading.value = false
    }
  }

  const fetchOne = async (id: number) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<T>(`${baseUrl}/${id}`)
      currentItem.value = response.data
      return response.data
    } catch (e) {
      error.value = handleError(e, `获取详情失败`)
      console.error(`Failed to fetch ${baseUrl}/${id}:`, e)
      return null
    } finally {
      loading.value = false
    }
  }

  const create = async (data: Partial<T>) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.post<T>(baseUrl, data)
      items.value.unshift(response.data)
      return response.data
    } catch (e) {
      error.value = handleError(e, `创建失败`)
      console.error(`Failed to create ${baseUrl}:`, e)
      return null
    } finally {
      loading.value = false
    }
  }

  const update = async (id: number, data: Partial<T>) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.put<T>(`${baseUrl}/${id}`, data)
      const index = items.value.findIndex(item => item.id === id)
      if (index !== -1) {
        items.value[index] = response.data
      }
      if (currentItem.value?.id === id) {
        currentItem.value = response.data
      }
      return response.data
    } catch (e) {
      error.value = handleError(e, `更新失败`)
      console.error(`Failed to update ${baseUrl}/${id}:`, e)
      return null
    } finally {
      loading.value = false
    }
  }

  const remove = async (id: number) => {
    loading.value = true
    error.value = null
    try {
      await api.delete(`${baseUrl}/${id}`)
      items.value = items.value.filter(item => item.id !== id)
      if (currentItem.value?.id === id) {
        currentItem.value = null
      }
      return true
    } catch (e) {
      error.value = handleError(e, `删除失败`)
      console.error(`Failed to delete ${baseUrl}/${id}:`, e)
      return false
    } finally {
      loading.value = false
    }
  }

  const clearError = () => {
    error.value = null
  }

  return {
    items,
    currentItem,
    loading,
    error,
    fetchAll,
    fetchOne,
    create,
    update,
    remove,
    clearError
  }
}
