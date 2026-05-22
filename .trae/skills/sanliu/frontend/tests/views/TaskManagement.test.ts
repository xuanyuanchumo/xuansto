import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import TaskManagement from '@/views/TaskManagement.vue'
import { useTasksStore } from '@/stores/tasks'
import { useAgentsStore } from '@/stores/agents'
import { ElMessage, ElMessageBox } from 'element-plus'

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn()
  }
}))

vi.mock('@/stores/tasks', () => ({
  useTasksStore: vi.fn()
}))

vi.mock('@/stores/agents', () => ({
  useAgentsStore: vi.fn()
}))

describe('TaskManagement.vue', () => {
  let tasksStore: ReturnType<typeof useTasksStore>
  let agentsStore: ReturnType<typeof useAgentsStore>

  const mockTasks = [
    { id: 1, name: 'Task 1', description: 'Test task 1', status: 'pending', priority: 'high', assigned_agent_id: null, assigned_agent_name: null, estimated_hours: null, actual_hours: null, project_id: 1, dependencies: [], created_at: '2024-01-01', updated_at: '2024-01-01' },
    { id: 2, name: 'Task 2', description: 'Test task 2', status: 'in_progress', priority: 'medium', assigned_agent_id: 1, assigned_agent_name: 'Agent 1', estimated_hours: 4, actual_hours: null, project_id: 1, dependencies: [], created_at: '2024-01-02', updated_at: '2024-01-02' }
  ]

  const mockAgents = [
    { id: 1, name: 'Agent 1', status: 'active', type: 'developer' },
    { id: 2, name: 'Agent 2', status: 'active', type: 'reviewer' }
  ]

  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()

    tasksStore = {
      tasks: [],
      total: 0,
      fetchTasks: vi.fn().mockImplementation(async () => {
        tasksStore.tasks = mockTasks
        tasksStore.total = mockTasks.length
      }),
      assignTask: vi.fn().mockResolvedValue({ id: 1, name: 'Task 1', assigned_agent_id: 1 }),
      fetchTaskDependencies: vi.fn().mockResolvedValue([
        { id: 1, task_id: 1, depends_on_task_id: 2, status: 'active', created_at: '2024-01-01' }
      ]),
      addTaskDependency: vi.fn().mockResolvedValue({ id: 2, task_id: 1, depends_on_task_id: 3 }),
      removeTaskDependency: vi.fn().mockResolvedValue(true)
    } as any

    agentsStore = {
      agents: [],
      fetchAgents: vi.fn().mockImplementation(async () => {
        agentsStore.agents = mockAgents
      })
    } as any

    vi.mocked(useTasksStore).mockReturnValue(tasksStore)
    vi.mocked(useAgentsStore).mockReturnValue(agentsStore)
  })

  const mountComponent = () => {
    return mount(TaskManagement, {
      global: {
        stubs: {
          TaskFilter: { 
            template: '<div class="task-filter" @search="$emit(\'search\')" />',
            emits: ['search']
          },
          TaskList: { 
            template: '<div class="task-list" />',
            props: ['tasks', 'loading', 'total']
          },
          AssignDialog: { 
            template: '<div class="assign-dialog" @confirm="$emit(\'confirm\', { agentId: 1, taskId: 1, estimatedHours: 2 })" />',
            props: ['modelValue', 'form', 'agents', 'loading'],
            emits: ['confirm', 'update:modelValue']
          },
          DependencyDialog: { 
            template: '<div class="dependency-dialog" @add-dependency="$emit(\'add-dependency\')" @remove-dependency="$emit(\'remove-dependency\', { id: 1 })" />',
            props: ['modelValue', 'currentTask', 'dependencies', 'loading'],
            emits: ['addDependency', 'removeDependency', 'update:modelValue']
          },
          AddDependencyDialog: { 
            template: '<div class="add-dependency-dialog" @confirm="$emit(\'confirm\', { currentTaskId: 1, dependsOnTaskId: 2 })" />',
            props: ['modelValue', 'form', 'availableTasks', 'loading'],
            emits: ['confirm', 'update:modelValue']
          },
          TaskDetailDialog: { 
            template: '<div class="task-detail-dialog" />',
            props: ['modelValue', 'task'],
            emits: ['update:modelValue']
          },
          'el-card': { template: '<div class="el-card"><slot name="header" /><slot /></div>' }
        }
      }
    })
  }

  describe('initialization', () => {
    it('should fetch tasks and agents on mount', async () => {
      const wrapper = mountComponent()
      await wrapper.vm.$nextTick()
      
      expect(tasksStore.fetchTasks).toHaveBeenCalled()
      expect(agentsStore.fetchAgents).toHaveBeenCalled()
    })
  })

  describe('data initialization', () => {
    it('should have correct initial data', () => {
      const wrapper = mountComponent()
      
      expect(wrapper.vm.searchText).toBe('')
      expect(wrapper.vm.filterStatus).toBe('')
      expect(wrapper.vm.filterPriority).toBe('')
      expect(wrapper.vm.currentPage).toBe(1)
      expect(wrapper.vm.pageSize).toBe(10)
      expect(wrapper.vm.assignDialogVisible).toBe(false)
      expect(wrapper.vm.dependenciesDialogVisible).toBe(false)
    })
  })

  describe('fetchTasks', () => {
    it('should call store fetchTasks with correct params', async () => {
      const wrapper = mountComponent()
      
      wrapper.vm.searchText = 'test'
      wrapper.vm.filterStatus = 'pending'
      wrapper.vm.filterPriority = 'high'
      wrapper.vm.currentPage = 2
      wrapper.vm.pageSize = 20
      
      await wrapper.vm.fetchTasks()
      
      expect(tasksStore.fetchTasks).toHaveBeenCalledWith({
        status: 'pending',
        priority: 'high',
        search: 'test',
        page: 2,
        page_size: 20,
        sort_by: undefined,
        sort_order: undefined
      })
    })
  })

  describe('handleSearch', () => {
    it('should reset page and fetch tasks', async () => {
      const wrapper = mountComponent()
      wrapper.vm.currentPage = 5
      
      await wrapper.vm.handleSearch()
      
      expect(wrapper.vm.currentPage).toBe(1)
      expect(tasksStore.fetchTasks).toHaveBeenCalled()
    })
  })

  describe('handleSortChange', () => {
    it('should update sort params and fetch tasks', async () => {
      const wrapper = mountComponent()
      
      await wrapper.vm.handleSortChange({ prop: 'created_at', order: 'desc' })
      
      expect(wrapper.vm.sortBy).toBe('created_at')
      expect(wrapper.vm.sortOrder).toBe('desc')
      expect(tasksStore.fetchTasks).toHaveBeenCalled()
    })
  })

  describe('openAssignDialog', () => {
    it('should open assign dialog with task data', () => {
      const wrapper = mountComponent()
      const task = mockTasks[1]
      
      wrapper.vm.openAssignDialog(task)
      
      expect(wrapper.vm.assignDialogVisible).toBe(true)
      expect(wrapper.vm.assignForm.taskId).toBe(2)
      expect(wrapper.vm.assignForm.taskName).toBe('Task 2')
      expect(wrapper.vm.assignForm.agentId).toBe(1)
    })
  })

  describe('handleAssign', () => {
    it('should show warning when agentId is null', async () => {
      const wrapper = mountComponent()
      
      await wrapper.vm.handleAssign({ taskId: 1, agentId: null, estimatedHours: 2 })
      
      expect(ElMessage.warning).toHaveBeenCalledWith('请选择 Agent')
    })

    it('should call assignTask and show success message', async () => {
      const wrapper = mountComponent()
      
      await wrapper.vm.handleAssign({ taskId: 1, agentId: 1, estimatedHours: 2 })
      
      expect(tasksStore.assignTask).toHaveBeenCalledWith(1, 1, 2)
      expect(ElMessage.success).toHaveBeenCalledWith('任务分配成功')
    })

    it('should show error message when assign fails', async () => {
      tasksStore.assignTask = vi.fn().mockResolvedValue(null)
      
      const wrapper = mountComponent()
      
      await wrapper.vm.handleAssign({ taskId: 1, agentId: 1, estimatedHours: 2 })
      
      expect(ElMessage.error).toHaveBeenCalledWith('任务分配失败')
    })
  })

  describe('viewTaskDetails', () => {
    it('should open detail dialog with task', () => {
      const wrapper = mountComponent()
      const task = mockTasks[0]
      
      wrapper.vm.viewTaskDetails(task)
      
      expect(wrapper.vm.taskDetailDialogVisible).toBe(true)
      expect(wrapper.vm.currentTaskDetail).toEqual(task)
    })
  })

  describe('viewDependencies', () => {
    it('should open dependencies dialog and fetch dependencies', async () => {
      const wrapper = mountComponent()
      const task = mockTasks[0]
      
      await wrapper.vm.viewDependencies(task)
      
      expect(wrapper.vm.dependenciesDialogVisible).toBe(true)
      expect(wrapper.vm.currentTask).toEqual(task)
      expect(tasksStore.fetchTaskDependencies).toHaveBeenCalledWith(1)
    })
  })

  describe('openAddDependencyDialog', () => {
    it('should open add dependency dialog', () => {
      const wrapper = mountComponent()
      wrapper.vm.currentTask = mockTasks[0]
      
      wrapper.vm.openAddDependencyDialog()
      
      expect(wrapper.vm.addDependencyDialogVisible).toBe(true)
      expect(wrapper.vm.addDependencyForm.currentTaskId).toBe(1)
    })
  })

  describe('handleAddDependency', () => {
    it('should show warning when dependsOnTaskId is null', async () => {
      const wrapper = mountComponent()
      
      await wrapper.vm.handleAddDependency({ currentTaskId: 1, dependsOnTaskId: null })
      
      expect(ElMessage.warning).toHaveBeenCalledWith('请选择依赖任务')
    })

    it('should add dependency and show success message', async () => {
      const wrapper = mountComponent()
      wrapper.vm.currentTask = mockTasks[0]
      
      await wrapper.vm.handleAddDependency({ currentTaskId: 1, dependsOnTaskId: 2 })
      
      expect(tasksStore.addTaskDependency).toHaveBeenCalledWith(1, 2)
      expect(ElMessage.success).toHaveBeenCalledWith('添加依赖成功')
    })

    it('should show error message when add fails', async () => {
      tasksStore.addTaskDependency = vi.fn().mockResolvedValue(null)
      
      const wrapper = mountComponent()
      
      await wrapper.vm.handleAddDependency({ currentTaskId: 1, dependsOnTaskId: 2 })
      
      expect(ElMessage.error).toHaveBeenCalledWith('添加依赖失败')
    })
  })

  describe('handleRemoveDependency', () => {
    it('should remove dependency when confirmed', async () => {
      vi.mocked(ElMessageBox.confirm).mockResolvedValueOnce({} as any)
      
      const wrapper = mountComponent()
      wrapper.vm.currentTask = mockTasks[0]
      
      await wrapper.vm.handleRemoveDependency({ id: 1 })
      
      expect(tasksStore.removeTaskDependency).toHaveBeenCalledWith(1, 1)
      expect(ElMessage.success).toHaveBeenCalledWith('移除依赖成功')
    })

    it('should show error when remove fails', async () => {
      vi.mocked(ElMessageBox.confirm).mockResolvedValueOnce({} as any)
      tasksStore.removeTaskDependency = vi.fn().mockResolvedValue(false)
      
      const wrapper = mountComponent()
      wrapper.vm.currentTask = mockTasks[0]
      
      await wrapper.vm.handleRemoveDependency({ id: 1 })
      
      expect(ElMessage.error).toHaveBeenCalledWith('移除依赖失败')
    })

    it('should not remove when user cancels', async () => {
      vi.mocked(ElMessageBox.confirm).mockRejectedValueOnce(new Error('cancel'))
      
      const wrapper = mountComponent()
      wrapper.vm.currentTask = mockTasks[0]
      
      await wrapper.vm.handleRemoveDependency({ id: 1 })
      
      expect(tasksStore.removeTaskDependency).not.toHaveBeenCalled()
    })
  })

  describe('availableTasksForDependency', () => {
    it('should exclude current task from available tasks', async () => {
      const wrapper = mountComponent()
      await wrapper.vm.fetchTasks()
      wrapper.vm.currentTask = mockTasks[0]
      
      expect(wrapper.vm.availableTasksForDependency).toHaveLength(1)
      expect(wrapper.vm.availableTasksForDependency[0].id).toBe(2)
    })
  })
})
