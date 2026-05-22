import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export interface SkillCall {
  id: number
  skill_name: string
  caller: string | null
  status: string
  start_time: string
  end_time: string | null
  details: Record<string, unknown>
  parent_call_id: number | null
  created_at: string
}

export interface SkillCallTreeNode extends SkillCall {
  children: SkillCallTreeNode[]
}

interface FetchCallsParams {
  skill_name?: string
  status?: string
}

export const useSkillCallsStore = defineStore('skillCalls', () => {
  const calls = ref<SkillCall[]>([])
  const currentCall = ref<SkillCall | null>(null)
  const currentTree = ref<SkillCallTreeNode | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const fetchCalls = async (filters?: { skill_name?: string; status?: string }) => {
    loading.value = true
    error.value = null
    try {
      const params: FetchCallsParams = {}
      if (filters?.skill_name) params.skill_name = filters.skill_name
      if (filters?.status) params.status = filters.status
      
      const response = await api.get('/skill_calls', { params })
      calls.value = response.data
    } catch (e) {
      const err = e as Error
      error.value = err.message || '获取技能调用列表失败'
      console.error('Failed to fetch skill calls:', e)
    } finally {
      loading.value = false
    }
  }

  const fetchCall = async (id: number) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get(`/skill_calls/${id}`)
      currentCall.value = response.data
    } catch (e) {
      const err = e as Error
      error.value = err.message || '获取技能调用详情失败'
      console.error('Failed to fetch skill call:', e)
    } finally {
      loading.value = false
    }
  }

  const fetchCallTree = async (rootId: number) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get(`/skill_calls/tree/${rootId}`)
      currentTree.value = response.data
    } catch (e) {
      const err = e as Error
      error.value = err.message || '获取调用树失败'
      console.error('Failed to fetch call tree:', e)
    } finally {
      loading.value = false
    }
  }

  const createCall = async (data: Partial<SkillCall>) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.post('/skill_calls', data)
      calls.value.unshift(response.data)
      return response.data
    } catch (e) {
      const err = e as Error
      error.value = err.message || '创建技能调用失败'
      console.error('Failed to create skill call:', e)
      return null
    } finally {
      loading.value = false
    }
  }

  const updateCall = async (id: number, data: Partial<SkillCall>) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.put(`/skill_calls/${id}`, data)
      const index = calls.value.findIndex(c => c.id === id)
      if (index !== -1) {
        calls.value[index] = response.data
      }
      return response.data
    } catch (e) {
      const err = e as Error
      error.value = err.message || '更新技能调用失败'
      console.error('Failed to update skill call:', e)
      return null
    } finally {
      loading.value = false
    }
  }

  return {
    calls,
    currentCall,
    currentTree,
    loading,
    error,
    fetchCalls,
    fetchCall,
    fetchCallTree,
    createCall,
    updateCall
  }
})
