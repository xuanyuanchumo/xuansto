import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useDashboardStore } from '@/stores/dashboard'

vi.mock('@/api', () => ({
  default: {
    get: vi.fn()
  }
}))

import api from '@/api'

describe('Dashboard Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('should have correct initial stats', () => {
      const store = useDashboardStore()
      
      expect(store.stats).toEqual({
        total_skill_calls: 0,
        active_agents: 0,
        total_agents: 0,
        pending_tasks: 0,
        active_assignments: 0,
        recent_calls: [],
        status_distribution: {}
      })
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })
  })

  describe('fetchStats', () => {
    it('should fetch and set stats successfully', async () => {
      const mockStats = {
        total_skill_calls: 100,
        active_agents: 5,
        total_agents: 10,
        pending_tasks: 20,
        active_assignments: 15,
        recent_calls: [
          { id: 1, skill_name: 'Test Skill', status: 'completed', created_at: '2024-01-01T00:00:00' }
        ],
        status_distribution: { completed: 50, pending: 30, failed: 20 }
      }
      
      vi.mocked(api.get).mockResolvedValueOnce({ data: mockStats })
      
      const store = useDashboardStore()
      await store.fetchStats()
      
      expect(store.stats).toEqual(mockStats)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('should set error on fetch failure', async () => {
      const mockError = new Error('Network error')
      vi.mocked(api.get).mockRejectedValueOnce(mockError)
      
      const store = useDashboardStore()
      await store.fetchStats()
      
      expect(store.error).toBe('Network error')
      expect(store.loading).toBe(false)
    })

    it('should set loading state during fetch', async () => {
      const mockStats = {
        total_skill_calls: 0,
        active_agents: 0,
        total_agents: 0,
        pending_tasks: 0,
        active_assignments: 0,
        recent_calls: [],
        status_distribution: {}
      }
      
      vi.mocked(api.get).mockImplementationOnce(() => 
        new Promise(resolve => setTimeout(() => resolve({ data: mockStats }), 100))
      )
      
      const store = useDashboardStore()
      const promise = store.fetchStats()
      
      expect(store.loading).toBe(true)
      
      await promise
      
      expect(store.loading).toBe(false)
    })
  })
})
