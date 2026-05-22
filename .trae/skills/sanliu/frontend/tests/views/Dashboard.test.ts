import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import Dashboard from '@/views/Dashboard.vue'
import { useDashboardStore } from '@/stores/dashboard'

vi.mock('@/stores/dashboard', () => ({
  useDashboardStore: vi.fn()
}))

vi.mock('@element-plus/icons-vue', () => ({
  Document: { name: 'Document', template: '<svg />' },
  User: { name: 'User', template: '<svg />' },
  List: { name: 'List', template: '<svg />' },
  Connection: { name: 'Connection', template: '<svg />' }
}))

describe('Dashboard.vue', () => {
  let dashboardStore: ReturnType<typeof useDashboardStore>
  let clearIntervalSpy: vi.SpyInstance

  const mockStats = {
    total_skill_calls: 100,
    active_agents: 5,
    total_agents: 10,
    pending_tasks: 20,
    active_assignments: 15,
    recent_calls: [
      { id: 1, skill_name: 'Test Skill 1', status: 'completed', created_at: '2024-01-01T10:00:00' },
      { id: 2, skill_name: 'Test Skill 2', status: 'started', created_at: '2024-01-01T11:00:00' },
      { id: 3, skill_name: 'Test Skill 3', status: 'failed', created_at: '2024-01-01T12:00:00' }
    ],
    status_distribution: {
      completed: 50,
      pending: 30,
      failed: 20
    }
  }

  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    vi.useFakeTimers()

    clearIntervalSpy = vi.spyOn(global, 'clearInterval')

    dashboardStore = {
      stats: { ...mockStats },
      loading: false,
      error: null,
      fetchStats: vi.fn().mockResolvedValue(undefined)
    } as any

    vi.mocked(useDashboardStore).mockReturnValue(dashboardStore)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  const mountComponent = async () => {
    const wrapper = mount(Dashboard, {
      global: {
        stubs: {
          'el-row': { template: '<div class="el-row"><slot /></div>' },
          'el-col': { template: '<div class="el-col"><slot /></div>' },
          'el-card': { 
            template: '<div class="el-card"><slot name="header" /><slot /></div>' 
          },
          'el-table': { 
            template: '<div class="el-table"><slot /></div>',
            props: ['data']
          },
          'el-table-column': { template: '<div class="el-table-column" />' },
          'el-tag': { 
            template: '<span class="el-tag" :data-type="type"><slot /></span>',
            props: ['type']
          },
          'el-progress': { 
            template: '<div class="el-progress" :data-percentage="percentage" />',
            props: ['percentage', 'strokeWidth']
          },
          'el-icon': { template: '<i class="el-icon"><slot /></i>' }
        }
      }
    })
    await vi.runOnlyPendingTimersAsync()
    await wrapper.vm.$nextTick()
    return wrapper
  }

  describe('rendering', () => {
    it('should render title', async () => {
      const wrapper = await mountComponent()
      expect(wrapper.find('h2').text()).toBe('三省六部协同开发系统 - 仪表盘')
    })

    it('should render stat cards', async () => {
      const wrapper = await mountComponent()
      const statValues = wrapper.findAll('.stat-value')
      
      expect(statValues[0].text()).toBe('100')
      expect(statValues[1].text()).toBe('5 / 10')
      expect(statValues[2].text()).toBe('20')
      expect(statValues[3].text()).toBe('15')
    })

    it('should render recent calls table', async () => {
      const wrapper = await mountComponent()
      expect(wrapper.find('.recent-calls').exists()).toBe(true)
    })

    it('should render status distribution', async () => {
      const wrapper = await mountComponent()
      expect(wrapper.find('.status-distribution').exists()).toBe(true)
    })
  })

  describe('getStatusType', () => {
    it('should return correct type for started status', async () => {
      const wrapper = await mountComponent()
      expect(wrapper.vm.getStatusType('started')).toBe('primary')
    })

    it('should return correct type for completed status', async () => {
      const wrapper = await mountComponent()
      expect(wrapper.vm.getStatusType('completed')).toBe('success')
    })

    it('should return correct type for failed status', async () => {
      const wrapper = await mountComponent()
      expect(wrapper.vm.getStatusType('failed')).toBe('danger')
    })

    it('should return correct type for update status', async () => {
      const wrapper = await mountComponent()
      expect(wrapper.vm.getStatusType('update')).toBe('warning')
    })

    it('should return info for unknown status', async () => {
      const wrapper = await mountComponent()
      expect(wrapper.vm.getStatusType('unknown')).toBe('info')
    })
  })

  describe('formatTime', () => {
    it('should format time correctly', async () => {
      const wrapper = await mountComponent()
      const result = wrapper.vm.formatTime('2024-01-01T10:00:00')
      expect(result).toContain('2024')
    })

    it('should return dash for empty time', async () => {
      const wrapper = await mountComponent()
      expect(wrapper.vm.formatTime('')).toBe('-')
    })

    it('should return dash for null time', async () => {
      const wrapper = await mountComponent()
      expect(wrapper.vm.formatTime(null as any)).toBe('-')
    })
  })

  describe('getPercentage', () => {
    it('should calculate percentage correctly', async () => {
      const wrapper = await mountComponent()
      const result = wrapper.vm.getPercentage(50)
      expect(result).toBe(50)
    })

    it('should return 0 when total is 0', async () => {
      dashboardStore.stats = {
        ...mockStats,
        status_distribution: {}
      }
      const wrapper = await mountComponent()
      const result = wrapper.vm.getPercentage(0)
      expect(result).toBe(0)
    })
  })

  describe('lifecycle hooks', () => {
    it('should fetch stats on mount', async () => {
      await mountComponent()
      expect(dashboardStore.fetchStats).toHaveBeenCalled()
    })

    it('should set up refresh interval on mount', async () => {
      await mountComponent()
      
      vi.advanceTimersByTime(5000)
      await vi.runOnlyPendingTimersAsync()
      
      vi.advanceTimersByTime(5000)
      await vi.runOnlyPendingTimersAsync()
      
      expect(dashboardStore.fetchStats.mock.calls.length).toBeGreaterThanOrEqual(3)
    })

    it('should clear interval on unmount', async () => {
      const wrapper = await mountComponent()
      
      wrapper.unmount()
      
      expect(clearIntervalSpy).toHaveBeenCalled()
    })
  })

  describe('reactivity', () => {
    it('should update stats when store stats change', async () => {
      const wrapper = await mountComponent()
      
      expect(wrapper.vm.stats.total_skill_calls).toBe(100)
      
      dashboardStore.stats = {
        ...mockStats,
        total_skill_calls: 200
      }
      
      wrapper.vm.stats = dashboardStore.stats
      await wrapper.vm.$nextTick()
      
      const statValues = wrapper.findAll('.stat-value')
      expect(statValues[0].text()).toBe('200')
    })
  })

  describe('edge cases', () => {
    it('should handle empty recent calls', async () => {
      dashboardStore.stats = {
        ...mockStats,
        recent_calls: []
      }
      
      const wrapper = await mountComponent()
      
      expect(wrapper.vm.stats.recent_calls).toEqual([])
    })

    it('should handle empty status distribution', async () => {
      dashboardStore.stats = {
        ...mockStats,
        status_distribution: {}
      }
      
      const wrapper = await mountComponent()
      
      const distributionItems = wrapper.findAll('.distribution-item')
      expect(distributionItems.length).toBe(0)
    })

    it('should handle missing stats properties', async () => {
      dashboardStore.stats = {} as any
      
      const wrapper = await mountComponent()
      
      const statValues = wrapper.findAll('.stat-value')
      expect(statValues[0].text()).toBe('0')
      expect(statValues[1].text()).toBe('0 / 0')
    })
  })
})
