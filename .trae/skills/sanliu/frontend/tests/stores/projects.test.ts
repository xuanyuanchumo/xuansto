import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useProjectsStore } from '@/stores/projects'

vi.mock('@/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

import api from '@/api'

describe('Projects Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('should have correct initial state', () => {
      const store = useProjectsStore()
      
      expect(store.projects).toEqual([])
      expect(store.currentProject).toBeNull()
      expect(store.projectStatus).toBeNull()
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
      expect(store.pagination).toEqual({
        total: 0,
        page: 1,
        page_size: 12,
        total_pages: 0
      })
    })
  })

  describe('fetchProjects', () => {
    it('should fetch projects successfully', async () => {
      const mockResponse = {
        items: [
          { id: 1, name: 'Project 1', description: 'Test', tech_stack: [], status: 'active', status_history: [], milestones: [], created_at: '2024-01-01', updated_at: null },
          { id: 2, name: 'Project 2', description: 'Test 2', tech_stack: [], status: 'pending', status_history: [], milestones: [], created_at: '2024-01-02', updated_at: null }
        ],
        total: 2,
        page: 1,
        page_size: 12,
        total_pages: 1
      }
      
      vi.mocked(api.get).mockResolvedValueOnce({ data: mockResponse })
      
      const store = useProjectsStore()
      await store.fetchProjects()
      
      expect(store.projects).toHaveLength(2)
      expect(store.projects[0].name).toBe('Project 1')
      expect(store.pagination.total).toBe(2)
      expect(store.loading).toBe(false)
    })

    it('should handle fetch error', async () => {
      const mockError = { message: 'Server error' }
      vi.mocked(api.get).mockRejectedValueOnce(mockError)
      
      const store = useProjectsStore()
      await store.fetchProjects()
      
      expect(store.error).toBe('Server error')
      expect(store.loading).toBe(false)
    })

    it('should pass query params correctly', async () => {
      const mockResponse = {
        items: [],
        total: 0,
        page: 1,
        page_size: 12,
        total_pages: 0
      }
      
      vi.mocked(api.get).mockResolvedValueOnce({ data: mockResponse })
      
      const store = useProjectsStore()
      await store.fetchProjects({ status: 'active', search: 'test' })
      
      expect(api.get).toHaveBeenCalledWith('/projects', { 
        params: { status: 'active', search: 'test' } 
      })
    })
  })

  describe('fetchProject', () => {
    it('should fetch single project successfully', async () => {
      const mockProject = {
        id: 1,
        name: 'Project 1',
        description: 'Test',
        tech_stack: ['Vue', 'TypeScript'],
        status: 'active',
        status_history: [],
        milestones: [],
        created_at: '2024-01-01',
        updated_at: null
      }
      
      vi.mocked(api.get).mockResolvedValueOnce({ data: mockProject })
      
      const store = useProjectsStore()
      await store.fetchProject(1)
      
      expect(store.currentProject).toEqual(mockProject)
      expect(store.loading).toBe(false)
    })
  })

  describe('createProject', () => {
    it('should create project successfully', async () => {
      const newProject = {
        id: 3,
        name: 'New Project',
        description: 'New',
        tech_stack: [],
        status: 'pending',
        status_history: [],
        milestones: [],
        created_at: '2024-01-03',
        updated_at: null
      }
      
      vi.mocked(api.post).mockResolvedValueOnce({ data: newProject })
      
      const store = useProjectsStore()
      const result = await store.createProject({ name: 'New Project', description: 'New' })
      
      expect(result).toEqual(newProject)
      expect(store.projects).toHaveLength(1)
      expect(store.projects[0]).toEqual(newProject)
    })

    it('should return null on create failure', async () => {
      const mockError = { message: 'Create failed' }
      vi.mocked(api.post).mockRejectedValueOnce(mockError)
      
      const store = useProjectsStore()
      const result = await store.createProject({ name: 'Test' })
      
      expect(result).toBeNull()
      expect(store.error).toBe('Create failed')
    })
  })

  describe('updateProject', () => {
    it('should update project successfully', async () => {
      const existingProject = {
        id: 1,
        name: 'Project 1',
        description: 'Test',
        tech_stack: [],
        status: 'active',
        status_history: [],
        milestones: [],
        created_at: '2024-01-01',
        updated_at: null
      }
      
      const updatedProject = {
        ...existingProject,
        name: 'Updated Project',
        description: 'Updated'
      }
      
      vi.mocked(api.get).mockResolvedValueOnce({ 
        data: { items: [existingProject], total: 1, page: 1, page_size: 12, total_pages: 1 } 
      })
      vi.mocked(api.put).mockResolvedValueOnce({ data: updatedProject })
      
      const store = useProjectsStore()
      await store.fetchProjects()
      const result = await store.updateProject(1, { name: 'Updated Project' })
      
      expect(result).toEqual(updatedProject)
      expect(store.projects[0].name).toBe('Updated Project')
    })
  })

  describe('deleteProject', () => {
    it('should delete project successfully', async () => {
      const project = {
        id: 1,
        name: 'Project 1',
        description: 'Test',
        tech_stack: [],
        status: 'active',
        status_history: [],
        milestones: [],
        created_at: '2024-01-01',
        updated_at: null
      }
      
      vi.mocked(api.get).mockResolvedValueOnce({ 
        data: { items: [project], total: 1, page: 1, page_size: 12, total_pages: 1 } 
      })
      vi.mocked(api.delete).mockResolvedValueOnce({})
      
      const store = useProjectsStore()
      await store.fetchProjects()
      const result = await store.deleteProject(1)
      
      expect(result).toBe(true)
      expect(store.projects).toHaveLength(0)
    })

    it('should return false on delete failure', async () => {
      const mockError = { message: 'Delete failed' }
      vi.mocked(api.delete).mockRejectedValueOnce(mockError)
      
      const store = useProjectsStore()
      const result = await store.deleteProject(1)
      
      expect(result).toBe(false)
      expect(store.error).toBe('Delete failed')
    })
  })

  describe('searchProjects', () => {
    it('should search projects successfully', async () => {
      const mockProjects = [
        { id: 1, name: 'Test Project', description: 'Test', tech_stack: [], status: 'active', status_history: [], milestones: [], created_at: '2024-01-01', updated_at: null }
      ]
      
      vi.mocked(api.get).mockResolvedValueOnce({ data: mockProjects })
      
      const store = useProjectsStore()
      const result = await store.searchProjects('test')
      
      expect(result).toEqual(mockProjects)
      expect(api.get).toHaveBeenCalledWith('/projects/search', { 
        params: { q: 'test', limit: 10 } 
      })
    })
  })

  describe('clearError', () => {
    it('should clear error', () => {
      const store = useProjectsStore()
      store.error = 'Test error'
      
      store.clearError()
      
      expect(store.error).toBeNull()
    })
  })
})
