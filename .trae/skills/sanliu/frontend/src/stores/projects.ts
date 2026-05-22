import { defineStore } from 'pinia'
import { ref } from 'vue'
import api, { ApiError } from '@/api'

export interface Milestone {
  id: number
  name: string
  status: string
  created_at: string
}

export interface Project {
  id: number
  name: string
  description: string | null
  tech_stack: string[] | null
  status: string
  status_history: StatusHistoryItem[] | null
  milestones: Milestone[] | null
  created_at: string
  updated_at: string | null
  task_stats?: {
    total: number
    completed: number
  }
}

export interface StatusHistoryItem {
  status: string
  previous_status: string
  timestamp: string
  comment: string | null
}

export interface TaskStats {
  id: number
  name: string
  status: string
}

export interface ProjectStats {
  project_id: number
  project_name: string
  status: string
  total_tasks: number
  completed_tasks: number
  pending_tasks: number
  in_progress_tasks: number
  review_tasks: number
  progress: number
  tasks_by_status: Record<string, number>
  tasks: TaskStats[]
}

export interface ProjectListParams {
  page?: number
  page_size?: number
  status?: string
  search?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface ProjectListResponse {
  items: Project[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export const useProjectsStore = defineStore('projects', () => {
  const projects = ref<Project[]>([])
  const currentProject = ref<Project | null>(null)
  const projectStatus = ref<ProjectStats | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const pagination = ref({
    total: 0,
    page: 1,
    page_size: 12,
    total_pages: 0
  })

  const handleError = (e: unknown, defaultMsg: string): string => {
    if (e && typeof e === 'object' && 'message' in e) {
      return (e as ApiError).message || defaultMsg
    }
    return defaultMsg
  }

  const fetchProjects = async (params?: ProjectListParams) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<ProjectListResponse>('/projects', { params })
      projects.value = response.data.items
      pagination.value = {
        total: response.data.total,
        page: response.data.page,
        page_size: response.data.page_size,
        total_pages: response.data.total_pages
      }
    } catch (e) {
      error.value = handleError(e, '获取项目列表失败')
      console.error('Failed to fetch projects:', e)
    } finally {
      loading.value = false
    }
  }

  const fetchProject = async (id: number) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<Project>(`/projects/${id}`)
      currentProject.value = response.data
    } catch (e) {
      error.value = handleError(e, '获取项目详情失败')
      console.error('Failed to fetch project:', e)
    } finally {
      loading.value = false
    }
  }

  const fetchProjectStatus = async (id: number) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<ProjectStats>(`/projects/${id}/stats`)
      projectStatus.value = response.data
    } catch (e) {
      error.value = handleError(e, '获取项目状态失败')
      console.error('Failed to fetch project status:', e)
    } finally {
      loading.value = false
    }
  }

  const createProject = async (data: Partial<Project>) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.post<Project>('/projects', data)
      projects.value.unshift(response.data)
      return response.data
    } catch (e) {
      error.value = handleError(e, '创建项目失败')
      console.error('Failed to create project:', e)
      return null
    } finally {
      loading.value = false
    }
  }

  const updateProject = async (id: number, data: Partial<Project>) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.put<Project>(`/projects/${id}`, data)
      const index = projects.value.findIndex(p => p.id === id)
      if (index !== -1) {
        projects.value[index] = response.data
      }
      if (currentProject.value?.id === id) {
        currentProject.value = response.data
      }
      return response.data
    } catch (e) {
      error.value = handleError(e, '更新项目失败')
      console.error('Failed to update project:', e)
      return null
    } finally {
      loading.value = false
    }
  }

  const deleteProject = async (id: number) => {
    loading.value = true
    error.value = null
    try {
      await api.delete(`/projects/${id}`)
      projects.value = projects.value.filter(p => p.id !== id)
      if (currentProject.value?.id === id) {
        currentProject.value = null
      }
      return true
    } catch (e) {
      error.value = handleError(e, '删除项目失败')
      console.error('Failed to delete project:', e)
      return false
    } finally {
      loading.value = false
    }
  }

  const searchProjects = async (query: string, limit: number = 10) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<Project[]>('/projects/search', {
        params: { q: query, limit }
      })
      return response.data
    } catch (e) {
      error.value = handleError(e, '搜索项目失败')
      console.error('Failed to search projects:', e)
      return []
    } finally {
      loading.value = false
    }
  }

  const clearError = () => {
    error.value = null
  }

  return {
    projects,
    currentProject,
    projectStatus,
    loading,
    error,
    pagination,
    fetchProjects,
    fetchProject,
    fetchProjectStatus,
    createProject,
    updateProject,
    deleteProject,
    searchProjects,
    clearError
  }
})
