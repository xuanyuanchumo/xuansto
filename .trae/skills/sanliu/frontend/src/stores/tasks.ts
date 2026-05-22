import { defineStore } from 'pinia'
import { ref } from 'vue'
import api, { ApiError } from '@/api'

export interface TaskDependency {
  id: number
  task_id: number
  depends_on_task_id: number
  status: string
  created_at: string
  // 以下字段由后端在获取依赖列表时提供，用于显示
  task_name?: string
  dependency_completed?: boolean
}

export interface Task {
  id: number
  name: string
  description: string | null
  status: string
  priority: string
  assigned_agent_id: number | null
  assigned_agent_name: string | null
  estimated_hours: number | null
  actual_hours: number | null
  project_id: number | null
  dependencies: TaskDependency[]
  created_at: string
  updated_at: string
}

interface FetchTasksParams {
  status?: string
  priority?: string
  search?: string
  page?: number
  page_size?: number
  sort_by?: string
  sort_order?: string
}

interface TasksResponse {
  items: Task[]
  total: number
}

export const useTasksStore = defineStore('tasks', () => {
  const tasks = ref<Task[]>([])
  const currentTask = ref<Task | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const total = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(10)

  const handleError = (e: unknown, defaultMsg: string): string => {
    if (e && typeof e === 'object' && 'message' in e) {
      return (e as ApiError).message || defaultMsg
    }
    return defaultMsg
  }

  const withLoading = async <T>(fn: () => Promise<T>, errorMsg: string): Promise<T | null> => {
    loading.value = true
    error.value = null
    try {
      return await fn()
    } catch (e) {
      error.value = handleError(e, errorMsg)
      console.error(errorMsg, e)
      return null
    } finally {
      loading.value = false
    }
  }

  const buildQueryParams = (params?: FetchTasksParams): FetchTasksParams => {
    if (!params) return {}
    const queryParams: FetchTasksParams = {}
    if (params.status) queryParams.status = params.status
    if (params.priority) queryParams.priority = params.priority
    if (params.search) queryParams.search = params.search
    if (params.page) queryParams.page = params.page
    if (params.page_size) queryParams.page_size = params.page_size
    if (params.sort_by) queryParams.sort_by = params.sort_by
    if (params.sort_order) queryParams.sort_order = params.sort_order
    return queryParams
  }

  const fetchTasks = async (params?: FetchTasksParams) => {
    await withLoading(async () => {
      const queryParams = buildQueryParams(params)
      const response = await api.get<TasksResponse>('/tasks', { params: queryParams })
      tasks.value = response.data.items || response.data as unknown as Task[]
      total.value = response.data.total || tasks.value.length
      currentPage.value = params?.page || 1
      pageSize.value = params?.page_size || 10
    }, '获取任务列表失败')
  }

  const fetchTask = async (id: number) => {
    await withLoading(async () => {
      const response = await api.get(`/tasks/${id}`)
      currentTask.value = response.data
    }, '获取任务详情失败')
  }

  const createTask = async (data: Partial<Task>) => {
    const result = await withLoading(async () => {
      const response = await api.post('/tasks', data)
      tasks.value.unshift(response.data)
      total.value++
      return response.data
    }, '创建任务失败')
    return result
  }

  const updateTask = async (id: number, data: Partial<Task>) => {
    const result = await withLoading(async () => {
      const response = await api.put(`/tasks/${id}`, data)
      const index = tasks.value.findIndex(t => t.id === id)
      if (index !== -1) tasks.value[index] = response.data
      if (currentTask.value?.id === id) currentTask.value = response.data
      return response.data
    }, '更新任务失败')
    return result
  }

  const assignTask = async (taskId: number, agentId: number, estimatedHours?: number) => {
    const result = await withLoading(async () => {
      const response = await api.post(`/tasks/${taskId}/assign`, {
        agent_id: agentId,
        estimated_hours: estimatedHours
      })
      const index = tasks.value.findIndex(t => t.id === taskId)
      if (index !== -1) tasks.value[index] = response.data
      return response.data
    }, '分配任务失败')
    return result
  }

  const fetchTaskDependencies = async (taskId: number) => {
    const result = await withLoading(async () => {
      const response = await api.get<TaskDependency[]>(`/tasks/${taskId}/dependencies`)
      return response.data
    }, '获取任务依赖失败')
    return result || []
  }

  const addTaskDependency = async (taskId: number, dependsOnTaskId: number) => {
    const result = await withLoading(async () => {
      const response = await api.post(`/tasks/${taskId}/dependencies`, {
        depends_on_task_id: dependsOnTaskId
      })
      return response.data
    }, '添加任务依赖失败')
    return result
  }

  const removeTaskDependency = async (taskId: number, dependencyId: number) => {
    const result = await withLoading(async () => {
      await api.delete(`/tasks/${taskId}/dependencies/${dependencyId}`)
      return true
    }, '删除任务依赖失败')
    return result ?? false
  }

  const clearError = () => {
    error.value = null
  }

  return {
    tasks,
    currentTask,
    loading,
    error,
    total,
    currentPage,
    pageSize,
    fetchTasks,
    fetchTask,
    createTask,
    updateTask,
    assignTask,
    fetchTaskDependencies,
    addTaskDependency,
    removeTaskDependency,
    clearError
  }
})
