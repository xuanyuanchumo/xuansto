import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import TaskList from '@/components/task/TaskList.vue'
import type { Task } from '@/stores/tasks'

vi.mock('element-plus', () => ({
  ElMessage: {
    info: vi.fn(),
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn()
  }
}))

const mockTasks: Task[] = [
  {
    id: 1,
    name: '任务1',
    title: '任务1',
    status: 'pending',
    priority: 'high',
    assigned_agent_name: 'Agent A',
    estimated_hours: 8,
    actual_hours: 6,
    created_at: '2024-01-01T10:00:00Z',
    project_id: 1,
    dependencies: [],
    status_history: []
  },
  {
    id: 2,
    name: '任务2',
    title: '任务2',
    status: 'in_progress',
    priority: 'medium',
    assigned_agent_name: null,
    estimated_hours: 4,
    actual_hours: null,
    created_at: '2024-01-02T10:00:00Z',
    project_id: 1,
    dependencies: [],
    status_history: []
  },
  {
    id: 3,
    name: '任务3',
    title: '任务3',
    status: 'completed',
    priority: 'low',
    assigned_agent_name: 'Agent B',
    estimated_hours: 2,
    actual_hours: 3,
    created_at: '2024-01-03T10:00:00Z',
    project_id: 1,
    dependencies: [],
    status_history: []
  }
]

describe('TaskList.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  const mountComponent = (props = {}) => {
    return mount(TaskList, {
      props: {
        tasks: mockTasks,
        total: 3,
        currentPage: 1,
        pageSize: 10,
        ...props
      },
      global: {
        stubs: {
          'el-table': { 
            template: '<div class="el-table"><slot /></div>',
            methods: {
              toggleRowSelection: vi.fn()
            }
          },
          'el-table-column': { template: '<div class="el-table-column"><slot /></div>' },
          'el-tag': { template: '<span class="el-tag"><slot /></span>' },
          'el-button': { template: '<button class="el-button"><slot /></button>' },
          'el-link': { template: '<a class="el-link"><slot /></a>' },
          'el-pagination': { template: '<div class="el-pagination" />' },
          'el-icon': { template: '<i class="el-icon"><slot /></i>' }
        }
      }
    })
  }

  describe('rendering', () => {
    it('should render with tasks', () => {
      const wrapper = mountComponent()
      expect(wrapper.find('.task-list').exists()).toBe(true)
    })

    it('should render with empty tasks', () => {
      const wrapper = mountComponent({ tasks: [], total: 0 })
      expect(wrapper.find('.task-list').exists()).toBe(true)
    })

    it('should show loading state', () => {
      const wrapper = mountComponent({ loading: true })
      expect(wrapper.find('.task-list').exists()).toBe(true)
    })
  })

  describe('status mapping', () => {
    it('should return correct status type for pending', () => {
      const wrapper = mountComponent()
      expect(wrapper.vm.getStatusType('pending')).toBe('info')
    })

    it('should return correct status type for in_progress', () => {
      const wrapper = mountComponent()
      expect(wrapper.vm.getStatusType('in_progress')).toBe('primary')
    })

    it('should return correct status type for review', () => {
      const wrapper = mountComponent()
      expect(wrapper.vm.getStatusType('review')).toBe('warning')
    })

    it('should return correct status type for completed', () => {
      const wrapper = mountComponent()
      expect(wrapper.vm.getStatusType('completed')).toBe('success')
    })

    it('should return info for unknown status', () => {
      const wrapper = mountComponent()
      expect(wrapper.vm.getStatusType('unknown')).toBe('info')
    })
  })

  describe('status text mapping', () => {
    it('should return correct status text for pending', () => {
      const wrapper = mountComponent()
      expect(wrapper.vm.getStatusText('pending')).toBe('待分配')
    })

    it('should return correct status text for in_progress', () => {
      const wrapper = mountComponent()
      expect(wrapper.vm.getStatusText('in_progress')).toBe('进行中')
    })

    it('should return correct status text for review', () => {
      const wrapper = mountComponent()
      expect(wrapper.vm.getStatusText('review')).toBe('待审核')
    })

    it('should return correct status text for completed', () => {
      const wrapper = mountComponent()
      expect(wrapper.vm.getStatusText('completed')).toBe('已完成')
    })

    it('should return original status for unknown', () => {
      const wrapper = mountComponent()
      expect(wrapper.vm.getStatusText('unknown')).toBe('unknown')
    })
  })

  describe('priority mapping', () => {
    it('should return correct priority type for low', () => {
      const wrapper = mountComponent()
      expect(wrapper.vm.getPriorityType('low')).toBe('info')
    })

    it('should return correct priority type for medium', () => {
      const wrapper = mountComponent()
      expect(wrapper.vm.getPriorityType('medium')).toBe('')
    })

    it('should return correct priority type for high', () => {
      const wrapper = mountComponent()
      expect(wrapper.vm.getPriorityType('high')).toBe('warning')
    })

    it('should return correct priority type for urgent', () => {
      const wrapper = mountComponent()
      expect(wrapper.vm.getPriorityType('urgent')).toBe('danger')
    })

    it('should return correct priority text', () => {
      const wrapper = mountComponent()
      expect(wrapper.vm.getPriorityText('low')).toBe('低')
      expect(wrapper.vm.getPriorityText('medium')).toBe('中')
      expect(wrapper.vm.getPriorityText('high')).toBe('高')
      expect(wrapper.vm.getPriorityText('urgent')).toBe('紧急')
    })
  })

  describe('time formatting', () => {
    it('should format time correctly', () => {
      const wrapper = mountComponent()
      const result = wrapper.vm.formatTime('2024-01-01T10:00:00Z')
      expect(result).toBeTruthy()
    })

    it('should return dash for empty time', () => {
      const wrapper = mountComponent()
      expect(wrapper.vm.formatTime('')).toBe('-')
      expect(wrapper.vm.formatTime(null as any)).toBe('-')
    })

    it('should cache formatted time', () => {
      const wrapper = mountComponent()
      const time = '2024-01-01T10:00:00Z'
      
      wrapper.vm.formatTime(time)
      wrapper.vm.formatTime(time)
      
      expect(wrapper.vm.timeFormatterCache.has(time)).toBe(true)
    })
  })

  describe('row key', () => {
    it('should return task id as row key', () => {
      const wrapper = mountComponent()
      const task = { id: 123 } as Task
      expect(wrapper.vm.rowKey(task)).toBe(123)
    })
  })

  describe('events', () => {
    it('should emit sort-change event', () => {
      const wrapper = mountComponent()
      wrapper.vm.handleSortChange({ prop: 'id', order: 'ascending' })
      expect(wrapper.emitted('sort-change')).toBeTruthy()
      expect(wrapper.emitted('sort-change')![0]).toEqual([{ prop: 'id', order: 'asc' }])
    })

    it('should emit sort-change with desc order', () => {
      const wrapper = mountComponent()
      wrapper.vm.handleSortChange({ prop: 'id', order: 'descending' })
      expect(wrapper.emitted('sort-change')![0]).toEqual([{ prop: 'id', order: 'desc' }])
    })

    it('should emit sort-change with empty order', () => {
      const wrapper = mountComponent()
      wrapper.vm.handleSortChange({ prop: 'id', order: null })
      expect(wrapper.emitted('sort-change')![0]).toEqual([{ prop: 'id', order: '' }])
    })

    it('should emit page size change', () => {
      const wrapper = mountComponent()
      wrapper.vm.handleSizeChange(20)
      expect(wrapper.emitted('update:pageSize')).toBeTruthy()
      expect(wrapper.emitted('update:pageSize')![0]).toEqual([20])
      expect(wrapper.emitted('update:currentPage')![0]).toEqual([1])
    })

    it('should emit page change', () => {
      const wrapper = mountComponent()
      wrapper.vm.handlePageChange(2)
      expect(wrapper.emitted('update:currentPage')).toBeTruthy()
      expect(wrapper.emitted('update:currentPage')![0]).toEqual([2])
    })
  })

  describe('props reactivity', () => {
    it('should update localCurrentPage when prop changes', async () => {
      const wrapper = mountComponent()
      expect(wrapper.vm.localCurrentPage).toBe(1)
      
      await wrapper.setProps({ currentPage: 2 })
      expect(wrapper.vm.localCurrentPage).toBe(2)
    })

    it('should update localPageSize when prop changes', async () => {
      const wrapper = mountComponent()
      expect(wrapper.vm.localPageSize).toBe(10)
      
      await wrapper.setProps({ pageSize: 20 })
      expect(wrapper.vm.localPageSize).toBe(20)
    })
  })
})
