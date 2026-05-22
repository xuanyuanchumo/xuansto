import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import TaskDetail from '@/components/TaskDetail.vue'
import axios from 'axios'

vi.mock('axios')

vi.mock('element-plus', () => ({
  ElMessage: {
    info: vi.fn(),
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn()
  }
}))

vi.mock('@element-plus/icons-vue', () => ({
  Loading: { name: 'Loading', template: '<svg />' },
  User: { name: 'User', template: '<svg />' }
}))

describe('TaskDetail.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  const mockTaskDetail = {
    title: '测试任务',
    status: 'IN_PROGRESS',
    priority: 'high',
    required_skill: 'Vue.js',
    project_id: 1,
    estimated_hours: 8,
    actual_hours: 4,
    created_at: '2024-01-01T10:00:00Z',
    completed_at: null,
    description: '这是一个测试任务',
    agent: {
      id: 1,
      name: 'Agent A',
      role: 'Developer',
      status: 'busy'
    },
    dependencies_detail: [
      { id: 2, title: '前置任务', status: 'COMPLETED' }
    ],
    status_history_detail: [
      { timestamp: '2024-01-01T10:00:00Z', status: 'PENDING', from_status: null, comment: '创建任务' },
      { timestamp: '2024-01-02T10:00:00Z', status: 'IN_PROGRESS', from_status: 'PENDING', comment: '开始工作' }
    ]
  }

  const mountComponent = (props = {}) => {
    return mount(TaskDetail, {
      props: {
        modelValue: false,
        taskId: null,
        ...props
      },
      global: {
        stubs: {
          'el-dialog': { 
            template: '<div class="el-dialog" v-if="modelValue"><slot /><slot name="footer" /></div>',
            props: ['modelValue']
          },
          'el-descriptions': { template: '<div class="el-descriptions"><slot /></div>' },
          'el-descriptions-item': { template: '<div class="el-descriptions-item"><slot /></div>' },
          'el-tag': { template: '<span class="el-tag"><slot /></span>' },
          'el-card': { template: '<div class="el-card"><slot /></div>' },
          'el-divider': { template: '<hr class="el-divider" />' },
          'el-empty': { template: '<div class="el-empty"><slot /></div>' },
          'el-tree': { template: '<div class="el-tree"><slot /></div>' },
          'el-timeline': { template: '<div class="el-timeline"><slot /></div>' },
          'el-timeline-item': { template: '<div class="el-timeline-item"><slot /></div>' },
          'el-button': { template: '<button class="el-button"><slot /></button>' },
          'el-icon': { template: '<i class="el-icon"><slot /></i>' }
        }
      }
    })
  }

  describe('visibility', () => {
    it('should not render dialog when modelValue is false', () => {
      const wrapper = mountComponent({ modelValue: false })
      expect(wrapper.find('.el-dialog').exists()).toBe(false)
    })

    it('should render dialog when modelValue is true', async () => {
      const wrapper = mountComponent({ modelValue: true, taskId: 1 })
      
      vi.mocked(axios.get).mockResolvedValueOnce({ data: mockTaskDetail })
      
      expect(wrapper.find('.el-dialog').exists()).toBe(true)
    })
  })

  describe('status mapping', () => {
    it('should return correct status type', () => {
      const wrapper = mountComponent()
      
      expect(wrapper.vm.getStatusType('PENDING')).toBe('info')
      expect(wrapper.vm.getStatusType('IN_PROGRESS')).toBe('primary')
      expect(wrapper.vm.getStatusType('REVIEW')).toBe('warning')
      expect(wrapper.vm.getStatusType('COMPLETED')).toBe('success')
      expect(wrapper.vm.getStatusType('UNKNOWN')).toBe('info')
    })

    it('should return correct status label', () => {
      const wrapper = mountComponent()
      
      expect(wrapper.vm.getStatusLabel('PENDING')).toBe('待处理')
      expect(wrapper.vm.getStatusLabel('IN_PROGRESS')).toBe('进行中')
      expect(wrapper.vm.getStatusLabel('REVIEW')).toBe('审核中')
      expect(wrapper.vm.getStatusLabel('COMPLETED')).toBe('已完成')
      expect(wrapper.vm.getStatusLabel('UNKNOWN')).toBe('UNKNOWN')
    })
  })

  describe('priority mapping', () => {
    it('should return correct priority type', () => {
      const wrapper = mountComponent()
      
      expect(wrapper.vm.getPriorityType('high')).toBe('danger')
      expect(wrapper.vm.getPriorityType('medium')).toBe('warning')
      expect(wrapper.vm.getPriorityType('low')).toBe('info')
      expect(wrapper.vm.getPriorityType('unknown')).toBe('info')
    })

    it('should return correct priority label', () => {
      const wrapper = mountComponent()
      
      expect(wrapper.vm.getPriorityLabel('high')).toBe('高')
      expect(wrapper.vm.getPriorityLabel('medium')).toBe('中')
      expect(wrapper.vm.getPriorityLabel('low')).toBe('低')
      expect(wrapper.vm.getPriorityLabel('unknown')).toBe('unknown')
    })
  })

  describe('agent status mapping', () => {
    it('should return correct agent status type', () => {
      const wrapper = mountComponent()
      
      expect(wrapper.vm.getAgentStatusType('idle')).toBe('success')
      expect(wrapper.vm.getAgentStatusType('busy')).toBe('warning')
      expect(wrapper.vm.getAgentStatusType('offline')).toBe('danger')
      expect(wrapper.vm.getAgentStatusType('unknown')).toBe('info')
    })
  })

  describe('timeline type mapping', () => {
    it('should return correct timeline type', () => {
      const wrapper = mountComponent()
      
      expect(wrapper.vm.getTimelineType('PENDING')).toBe('primary')
      expect(wrapper.vm.getTimelineType('IN_PROGRESS')).toBe('primary')
      expect(wrapper.vm.getTimelineType('REVIEW')).toBe('warning')
      expect(wrapper.vm.getTimelineType('COMPLETED')).toBe('success')
      expect(wrapper.vm.getTimelineType('UNKNOWN')).toBe('info')
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
      
      expect(wrapper.vm.timeFormatCache.has(time)).toBe(true)
    })
  })

  describe('data fetching', () => {
    it('should fetch task detail when dialog opens', async () => {
      vi.mocked(axios.get).mockResolvedValueOnce({ data: mockTaskDetail })
      
      const wrapper = mountComponent({ modelValue: false, taskId: 1 })
      
      await wrapper.setProps({ modelValue: true })
      
      expect(axios.get).toHaveBeenCalledWith('/api/tasks/1', expect.any(Object))
    })

    it('should not fetch when taskId is null', async () => {
      const wrapper = mountComponent({ modelValue: false, taskId: null })
      
      await wrapper.setProps({ modelValue: true })
      
      expect(axios.get).not.toHaveBeenCalled()
    })

    it('should handle fetch error', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      vi.mocked(axios.get).mockRejectedValueOnce(new Error('Network error'))
      
      const wrapper = mountComponent({ modelValue: false, taskId: 1 })
      
      await wrapper.setProps({ modelValue: true })
      
      await new Promise(resolve => setTimeout(resolve, 0))
      
      expect(consoleSpy).toHaveBeenCalled()
      consoleSpy.mockRestore()
    })
  })

  describe('close handler', () => {
    it('should emit update:modelValue with false', async () => {
      const wrapper = mountComponent({ modelValue: true, taskId: 1 })
      
      wrapper.vm.handleClose()
      
      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      expect(wrapper.emitted('update:modelValue')![0]).toEqual([false])
    })

    it('should clear task detail on close', async () => {
      vi.mocked(axios.get).mockResolvedValueOnce({ data: mockTaskDetail })
      
      const wrapper = mountComponent({ modelValue: true, taskId: 1 })
      
      await new Promise(resolve => setTimeout(resolve, 0))
      
      wrapper.vm.handleClose()
      
      expect(wrapper.vm.taskDetail).toBeNull()
    })
  })

  describe('dependency tree data', () => {
    it('should return empty array when no dependencies', () => {
      const wrapper = mountComponent()
      expect(wrapper.vm.dependencyTreeData).toEqual([])
    })

    it('should build dependency tree from task detail', async () => {
      vi.mocked(axios.get).mockResolvedValueOnce({ data: mockTaskDetail })
      
      const wrapper = mountComponent({ modelValue: true, taskId: 1 })
      
      await new Promise(resolve => setTimeout(resolve, 0))
      
      expect(wrapper.vm.dependencyTreeData).toEqual([
        { id: 2, title: '前置任务', status: 'COMPLETED', children: [] }
      ])
    })
  })

  describe('abort controller', () => {
    it('should abort previous request on new fetch', async () => {
      vi.mocked(axios.get).mockResolvedValueOnce({ data: mockTaskDetail })
      
      const wrapper = mountComponent({ modelValue: true, taskId: 1 })
      
      await wrapper.setProps({ taskId: 2 })
      
      expect(wrapper.vm.abortController).toBeTruthy()
    })
  })
})
