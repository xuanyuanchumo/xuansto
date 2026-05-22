import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAgentsStore } from '@/stores/agents'

vi.mock('@/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

import api from '@/api'

describe('Agents Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('should have correct initial state', () => {
      const store = useAgentsStore()
      
      expect(store.agents).toEqual([])
      expect(store.currentAgent).toBeNull()
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })
  })

  describe('fetchAgents', () => {
    it('should fetch agents successfully', async () => {
      const mockAgents = [
        { id: 1, name: 'Agent 1', role: 'developer', skills: ['vue'], status: 'active', current_load: 0, max_load: 5, current_task: null, department_id: 1, last_heartbeat: '2024-01-01', created_at: '2024-01-01' },
        { id: 2, name: 'Agent 2', role: 'reviewer', skills: ['review'], status: 'idle', current_load: 0, max_load: 3, current_task: null, department_id: 2, last_heartbeat: '2024-01-01', created_at: '2024-01-01' }
      ]
      
      vi.mocked(api.get).mockResolvedValueOnce({ data: mockAgents })
      
      const store = useAgentsStore()
      await store.fetchAgents()
      
      expect(store.agents).toHaveLength(2)
      expect(store.agents[0].name).toBe('Agent 1')
      expect(store.loading).toBe(false)
    })

    it('should handle fetch error', async () => {
      const mockError = { message: 'Server error' }
      vi.mocked(api.get).mockRejectedValueOnce(mockError)
      
      const store = useAgentsStore()
      await store.fetchAgents()
      
      expect(store.error).toBe('Server error')
      expect(store.loading).toBe(false)
    })

    it('should pass status and department params', async () => {
      const mockAgents = []
      
      vi.mocked(api.get).mockResolvedValueOnce({ data: mockAgents })
      
      const store = useAgentsStore()
      await store.fetchAgents('active', 1)
      
      expect(api.get).toHaveBeenCalledWith('/agents', { params: { status: 'active', department_id: 1 } })
    })
  })

  describe('fetchAgent', () => {
    it('should fetch single agent successfully', async () => {
      const mockAgent = {
        id: 1,
        name: 'Agent 1',
        role: 'developer',
        skills: ['vue'],
        status: 'active',
        current_load: 0,
        max_load: 5,
        current_task: null,
        department_id: 1,
        last_heartbeat: '2024-01-01',
        created_at: '2024-01-01'
      }
      
      vi.mocked(api.get).mockResolvedValueOnce({ data: mockAgent })
      
      const store = useAgentsStore()
      await store.fetchAgent(1)
      
      expect(store.currentAgent).toEqual(mockAgent)
      expect(store.loading).toBe(false)
    })

    it('should handle fetch agent error', async () => {
      const mockError = { message: 'Not found' }
      vi.mocked(api.get).mockRejectedValueOnce(mockError)
      
      const store = useAgentsStore()
      await store.fetchAgent(999)
      
      expect(store.error).toBe('Not found')
      expect(store.loading).toBe(false)
    })
  })

  describe('updateAgent', () => {
    it('should update agent successfully', async () => {
      const existingAgent = {
        id: 1,
        name: 'Agent 1',
        role: 'developer',
        skills: ['vue'],
        status: 'active',
        current_load: 0,
        max_load: 5,
        current_task: null,
        department_id: 1,
        last_heartbeat: '2024-01-01',
        created_at: '2024-01-01'
      }
      
      const updatedAgent = {
        ...existingAgent,
        status: 'idle'
      }
      
      vi.mocked(api.get).mockResolvedValueOnce({ data: [existingAgent] })
      vi.mocked(api.put).mockResolvedValueOnce({ data: updatedAgent })
      
      const store = useAgentsStore()
      await store.fetchAgents()
      const result = await store.updateAgent(1, { status: 'idle' })
      
      expect(result).toEqual(updatedAgent)
      expect(api.put).toHaveBeenCalledWith('/agents/1', { status: 'idle' })
    })

    it('should return null on update failure', async () => {
      const mockError = { message: 'Update failed' }
      vi.mocked(api.put).mockRejectedValueOnce(mockError)
      
      const store = useAgentsStore()
      const result = await store.updateAgent(1, { status: 'idle' })
      
      expect(result).toBeNull()
      expect(store.error).toBe('Update failed')
    })
  })

  describe('clearError', () => {
    it('should clear error', () => {
      const store = useAgentsStore()
      store.error = 'Test error'
      
      store.clearError()
      
      expect(store.error).toBeNull()
    })
  })
})
