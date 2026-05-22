import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useTasksStore } from '@/stores/tasks'

vi.mock('@/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

import api from '@/api'

describe('Tasks Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('should have correct initial state', () => {
      const store = useTasksStore()
      
      expect(store.tasks).toEqual([])
      expect(store.currentTask).toBeNull()
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
      expect(store.total).toBe(0)
      expect(store.currentPage).toBe(1)
      expect(store.pageSize).toBe(10)
    })
  })

  describe('fetchTasks', () => {
    it('should fetch tasks successfully', async () => {
      const mockResponse = {
        items: [
          { id: 1, name: 'Task 1', description: 'Test', status: 'pending', priority: 'high', assigned_agent_id: null, assigned_agent_name: null, estimated_hours: null, actual_hours: null, project_id: null, dependencies: [], created_at: '2024-01-01', updated_at: '2024-01-01' },
          { id: 2, name: 'Task 2', description: 'Test 2', status: 'in_progress', priority: 'medium', assigned_agent_id: 1, assigned_agent_name: 'Agent 1', estimated_hours: 4, actual_hours: null, project_id: 1, dependencies: [], created_at: '2024-01-02', updated_at: '2024-01-02' }
        ],
        total: 2
      }
      
      vi.mocked(api.get).mockResolvedValueOnce({ data: mockResponse })
      
      const store = useTasksStore()
      await store.fetchTasks()
      
      expect(store.tasks).toHaveLength(2)
      expect(store.tasks[0].name).toBe('Task 1')
      expect(store.total).toBe(2)
      expect(store.loading).toBe(false)
    })

    it('should handle fetch error', async () => {
      const mockError = { message: 'Server error' }
      vi.mocked(api.get).mockRejectedValueOnce(mockError)
      
      const store = useTasksStore()
      await store.fetchTasks()
      
      expect(store.error).toBe('Server error')
      expect(store.loading).toBe(false)
    })

    it('should pass query params correctly', async () => {
      const mockResponse = { items: [], total: 0 }
      
      vi.mocked(api.get).mockResolvedValueOnce({ data: mockResponse })
      
      const store = useTasksStore()
      await store.fetchTasks({ 
        status: 'pending', 
        priority: 'high', 
        search: 'test',
        page: 2,
        page_size: 20,
        sort_by: 'created_at',
        sort_order: 'desc'
      })
      
      expect(api.get).toHaveBeenCalledWith('/tasks', { 
        params: { 
          status: 'pending', 
          priority: 'high', 
          search: 'test',
          page: 2,
          page_size: 20,
          sort_by: 'created_at',
          sort_order: 'desc'
        } 
      })
    })
  })

  describe('fetchTask', () => {
    it('should fetch single task successfully', async () => {
      const mockTask = {
        id: 1,
        name: 'Task 1',
        description: 'Test',
        status: 'pending',
        priority: 'high',
        assigned_agent_id: null,
        assigned_agent_name: null,
        estimated_hours: null,
        actual_hours: null,
        project_id: null,
        dependencies: [],
        created_at: '2024-01-01',
        updated_at: '2024-01-01'
      }
      
      vi.mocked(api.get).mockResolvedValueOnce({ data: mockTask })
      
      const store = useTasksStore()
      await store.fetchTask(1)
      
      expect(store.currentTask).toEqual(mockTask)
      expect(store.loading).toBe(false)
    })
  })

  describe('createTask', () => {
    it('should create task successfully', async () => {
      const newTask = {
        id: 3,
        name: 'New Task',
        description: 'New',
        status: 'pending',
        priority: 'medium',
        assigned_agent_id: null,
        assigned_agent_name: null,
        estimated_hours: null,
        actual_hours: null,
        project_id: null,
        dependencies: [],
        created_at: '2024-01-03',
        updated_at: '2024-01-03'
      }
      
      vi.mocked(api.post).mockResolvedValueOnce({ data: newTask })
      
      const store = useTasksStore()
      const result = await store.createTask({ name: 'New Task', description: 'New' })
      
      expect(result).toEqual(newTask)
      expect(store.tasks).toHaveLength(1)
      expect(store.total).toBe(1)
    })

    it('should return null on create failure', async () => {
      const mockError = { message: 'Create failed' }
      vi.mocked(api.post).mockRejectedValueOnce(mockError)
      
      const store = useTasksStore()
      const result = await store.createTask({ name: 'Test' })
      
      expect(result).toBeNull()
      expect(store.error).toBe('Create failed')
    })
  })

  describe('updateTask', () => {
    it('should update task successfully', async () => {
      const existingTask = {
        id: 1,
        name: 'Task 1',
        description: 'Test',
        status: 'pending',
        priority: 'high',
        assigned_agent_id: null,
        assigned_agent_name: null,
        estimated_hours: null,
        actual_hours: null,
        project_id: null,
        dependencies: [],
        created_at: '2024-01-01',
        updated_at: '2024-01-01'
      }
      
      const updatedTask = {
        ...existingTask,
        name: 'Updated Task',
        status: 'in_progress'
      }
      
      vi.mocked(api.get).mockResolvedValueOnce({ 
        data: { items: [existingTask], total: 1 } 
      })
      vi.mocked(api.put).mockResolvedValueOnce({ data: updatedTask })
      
      const store = useTasksStore()
      await store.fetchTasks()
      const result = await store.updateTask(1, { name: 'Updated Task', status: 'in_progress' })
      
      expect(result).toEqual(updatedTask)
      expect(store.tasks[0].name).toBe('Updated Task')
    })
  })

  describe('assignTask', () => {
    it('should assign task successfully', async () => {
      const existingTask = {
        id: 1,
        name: 'Task 1',
        description: 'Test',
        status: 'pending',
        priority: 'high',
        assigned_agent_id: null,
        assigned_agent_name: null,
        estimated_hours: null,
        actual_hours: null,
        project_id: null,
        dependencies: [],
        created_at: '2024-01-01',
        updated_at: '2024-01-01'
      }
      
      const assignedTask = {
        ...existingTask,
        assigned_agent_id: 1,
        assigned_agent_name: 'Agent 1',
        estimated_hours: 4
      }
      
      vi.mocked(api.get).mockResolvedValueOnce({ 
        data: { items: [existingTask], total: 1 } 
      })
      vi.mocked(api.post).mockResolvedValueOnce({ data: assignedTask })
      
      const store = useTasksStore()
      await store.fetchTasks()
      const result = await store.assignTask(1, 1, 4)
      
      expect(result).toEqual(assignedTask)
      expect(api.post).toHaveBeenCalledWith('/tasks/1/assign', {
        agent_id: 1,
        estimated_hours: 4
      })
    })
  })

  describe('fetchTaskDependencies', () => {
    it('should fetch dependencies successfully', async () => {
      const mockDependencies = [
        { id: 1, task_id: 1, depends_on_task_id: 2, status: 'active', created_at: '2024-01-01' }
      ]
      
      vi.mocked(api.get).mockResolvedValueOnce({ data: mockDependencies })
      
      const store = useTasksStore()
      const result = await store.fetchTaskDependencies(1)
      
      expect(result).toEqual(mockDependencies)
      expect(api.get).toHaveBeenCalledWith('/tasks/1/dependencies')
    })

    it('should return empty array on failure', async () => {
      vi.mocked(api.get).mockRejectedValueOnce({ message: 'Error' })
      
      const store = useTasksStore()
      const result = await store.fetchTaskDependencies(1)
      
      expect(result).toEqual([])
    })
  })

  describe('addTaskDependency', () => {
    it('should add dependency successfully', async () => {
      const mockDependency = {
        id: 1,
        task_id: 1,
        depends_on_task_id: 2,
        status: 'active',
        created_at: '2024-01-01'
      }
      
      vi.mocked(api.post).mockResolvedValueOnce({ data: mockDependency })
      
      const store = useTasksStore()
      const result = await store.addTaskDependency(1, 2)
      
      expect(result).toEqual(mockDependency)
      expect(api.post).toHaveBeenCalledWith('/tasks/1/dependencies', {
        depends_on_task_id: 2
      })
    })
  })

  describe('removeTaskDependency', () => {
    it('should remove dependency successfully', async () => {
      vi.mocked(api.delete).mockResolvedValueOnce({})
      
      const store = useTasksStore()
      const result = await store.removeTaskDependency(1, 1)
      
      expect(result).toBe(true)
      expect(api.delete).toHaveBeenCalledWith('/tasks/1/dependencies/1')
    })

    it('should return false on failure', async () => {
      vi.mocked(api.delete).mockRejectedValueOnce({ message: 'Error' })
      
      const store = useTasksStore()
      const result = await store.removeTaskDependency(1, 1)
      
      expect(result).toBe(false)
    })
  })

  describe('clearError', () => {
    it('should clear error', () => {
      const store = useTasksStore()
      store.error = 'Test error'
      
      store.clearError()
      
      expect(store.error).toBeNull()
    })
  })
})
