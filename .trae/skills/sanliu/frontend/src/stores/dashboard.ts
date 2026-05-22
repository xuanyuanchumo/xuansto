import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export interface RecentCall {
  id: number
  skill_name: string
  status: string
  created_at: string
}

export interface DashboardStats {
  total_skill_calls: number
  active_agents: number
  total_agents: number
  pending_tasks: number
  active_assignments: number
  recent_calls: RecentCall[]
  status_distribution: Record<string, number>
}

export const useDashboardStore = defineStore('dashboard', () => {
  const stats = ref<DashboardStats>({
    total_skill_calls: 0,
    active_agents: 0,
    total_agents: 0,
    pending_tasks: 0,
    active_assignments: 0,
    recent_calls: [],
    status_distribution: {}
  })

  const loading = ref(false)
  const error = ref<string | null>(null)

  const fetchStats = async () => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get('/dashboard/stats')
      stats.value = response.data
    } catch (e) {
      const err = e as Error
      error.value = err.message || '获取统计数据失败'
      console.error('Failed to fetch dashboard stats:', e)
    } finally {
      loading.value = false
    }
  }

  return {
    stats,
    loading,
    error,
    fetchStats
  }
})
