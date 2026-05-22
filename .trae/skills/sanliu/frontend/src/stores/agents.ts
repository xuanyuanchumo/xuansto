import { defineStore } from 'pinia'
import { ref } from 'vue'
import api, { ApiError } from '@/api'

export interface Agent {
  id: number
  name: string
  role: string | null
  skills: string[] | null
  status: string
  current_load: number
  max_load: number
  current_task: string | null
  department_id: number | null
  last_heartbeat: string
  created_at: string
}

interface FetchAgentsParams {
  status?: string
  department_id?: number
}

export const useAgentsStore = defineStore('agents', () => {
  const agents = ref<Agent[]>([])
  const currentAgent = ref<Agent | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const handleError = (e: unknown, defaultMsg: string): string => {
    if (e && typeof e === 'object' && 'message' in e) {
      return (e as ApiError).message || defaultMsg
    }
    return defaultMsg
  }

  const fetchAgents = async (status?: string, departmentId?: number) => {
    loading.value = true
    error.value = null
    try {
      const params: FetchAgentsParams = {}
      if (status) params.status = status
      if (departmentId) params.department_id = departmentId
      
      const response = await api.get('/agents', { params })
      agents.value = response.data
    } catch (e) {
      error.value = handleError(e, '获取 Agent 列表失败')
      console.error('Failed to fetch agents:', e)
    } finally {
      loading.value = false
    }
  }

  const fetchAgent = async (id: number) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get(`/agents/${id}`)
      currentAgent.value = response.data
    } catch (e) {
      error.value = handleError(e, '获取 Agent 详情失败')
      console.error('Failed to fetch agent:', e)
    } finally {
      loading.value = false
    }
  }

  const updateAgent = async (id: number, data: Partial<Agent>) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.put(`/agents/${id}`, data)
      const index = agents.value.findIndex(a => a.id === id)
      if (index !== -1) {
        agents.value[index] = response.data
      }
      return response.data
    } catch (e) {
      error.value = handleError(e, '更新 Agent 失败')
      console.error('Failed to update agent:', e)
      return null
    } finally {
      loading.value = false
    }
  }

  const clearError = () => {
    error.value = null
  }

  return {
    agents,
    currentAgent,
    loading,
    error,
    fetchAgents,
    fetchAgent,
    updateAgent,
    clearError
  }
})
