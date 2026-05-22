import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import PipelineVisualizer from '@/components/PipelineVisualizer.vue'
import PipelineNode from '@/components/pipeline/PipelineNode.vue'
import PipelineEdge from '@/components/pipeline/PipelineEdge.vue'
import { ElMessage } from 'element-plus'

vi.mock('element-plus', () => ({
  ElMessage: {
    info: vi.fn(),
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn()
  }
}))

vi.mock('@element-plus/icons-vue', () => ({
  FullScreen: { name: 'FullScreen', template: '<svg />' },
  Right: { name: 'Right', template: '<svg />' },
  User: { name: 'User', template: '<svg />' },
  Document: { name: 'Document', template: '<svg />' },
  DataAnalysis: { name: 'DataAnalysis', template: '<svg />' },
  Setting: { name: 'Setting', template: '<svg />' },
  DocumentChecked: { name: 'DocumentChecked', template: '<svg />' },
  Checked: { name: 'Checked', template: '<svg />' },
  Promotion: { name: 'Promotion', template: '<svg />' }
}))

describe('PipelineVisualizer.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  const defaultStages = [
    { id: 'requirement', name: '需求分析', status: 'success' as const, needsApproval: false },
    { id: 'design', name: '设计', status: 'running' as const, needsApproval: false },
    { id: 'implementation', name: '实现', status: 'pending' as const, needsApproval: false },
    { id: 'testing', name: '测试', status: 'pending' as const, needsApproval: false },
    { id: 'deployment', name: '部署', status: 'pending' as const, needsApproval: true }
  ]

  const mountComponent = (props = {}) => {
    return mount(PipelineVisualizer, {
      props: {
        stages: defaultStages,
        ...props
      },
      global: {
        stubs: {
          PipelineNode: true,
          PipelineEdge: true,
          PipelineStageDetail: true,
          PipelineApprovalList: true,
          'el-card': { template: '<div class="el-card"><slot name="header" /><slot /></div>' },
          'el-tag': { template: '<span class="el-tag"><slot /></span>' },
          'el-button': { template: '<button class="el-button"><slot /></button>' },
          'el-progress': { template: '<div class="el-progress" />' },
          'el-divider': { template: '<hr class="el-divider" />' },
          'el-icon': { template: '<i class="el-icon"><slot /></i>' }
        }
      }
    })
  }

  describe('rendering', () => {
    it('should render all stages', () => {
      const wrapper = mountComponent()
      const nodes = wrapper.findAllComponents(PipelineNode)
      expect(nodes.length).toBe(5)
    })

    it('should render correct number of edges', () => {
      const wrapper = mountComponent()
      const edges = wrapper.findAllComponents(PipelineEdge)
      expect(edges.length).toBe(4)
    })

    it('should display title', () => {
      const wrapper = mountComponent()
      expect(wrapper.find('.title').text()).toBe('流水线可视化')
    })
  })

  describe('pipelineStatus computed', () => {
    it('should return danger when any stage failed', () => {
      const failedStages = [
        { id: 'requirement', name: '需求分析', status: 'success' as const },
        { id: 'design', name: '设计', status: 'failed' as const }
      ]
      const wrapper = mountComponent({ stages: failedStages })
      expect(wrapper.vm.pipelineStatus).toEqual({ type: 'danger', label: '执行失败' })
    })

    it('should return warning when any stage is waiting', () => {
      const waitingStages = [
        { id: 'requirement', name: '需求分析', status: 'success' as const },
        { id: 'design', name: '设计', status: 'waiting' as const, needsApproval: true }
      ]
      const wrapper = mountComponent({ stages: waitingStages })
      expect(wrapper.vm.pipelineStatus).toEqual({ type: 'warning', label: '等待审批' })
    })

    it('should return primary when any stage is running', () => {
      const runningStages = [
        { id: 'requirement', name: '需求分析', status: 'success' as const },
        { id: 'design', name: '设计', status: 'running' as const }
      ]
      const wrapper = mountComponent({ stages: runningStages })
      expect(wrapper.vm.pipelineStatus).toEqual({ type: 'primary', label: '执行中' })
    })

    it('should return success when all stages completed', () => {
      const completedStages = [
        { id: 'requirement', name: '需求分析', status: 'success' as const },
        { id: 'design', name: '设计', status: 'success' as const }
      ]
      const wrapper = mountComponent({ stages: completedStages })
      expect(wrapper.vm.pipelineStatus).toEqual({ type: 'success', label: '执行完成' })
    })

    it('should return info when all stages pending', () => {
      const pendingStages = [
        { id: 'requirement', name: '需求分析', status: 'pending' as const },
        { id: 'design', name: '设计', status: 'pending' as const }
      ]
      const wrapper = mountComponent({ stages: pendingStages })
      expect(wrapper.vm.pipelineStatus).toEqual({ type: 'info', label: '待执行' })
    })
  })

  describe('pipelineProgress computed', () => {
    it('should calculate correct progress', () => {
      const wrapper = mountComponent()
      expect(wrapper.vm.pipelineProgress).toBe(20)
    })

    it('should return 100 when all stages completed', () => {
      const completedStages = [
        { id: 'requirement', name: '需求分析', status: 'success' as const },
        { id: 'design', name: '设计', status: 'success' as const }
      ]
      const wrapper = mountComponent({ stages: completedStages })
      expect(wrapper.vm.pipelineProgress).toBe(100)
    })

    it('should return 0 when no stages completed', () => {
      const pendingStages = [
        { id: 'requirement', name: '需求分析', status: 'pending' as const },
        { id: 'design', name: '设计', status: 'pending' as const }
      ]
      const wrapper = mountComponent({ stages: pendingStages })
      expect(wrapper.vm.pipelineProgress).toBe(0)
    })
  })

  describe('pipelineProgressStatus computed', () => {
    it('should return exception when any stage failed', () => {
      const failedStages = [
        { id: 'requirement', name: '需求分析', status: 'failed' as const }
      ]
      const wrapper = mountComponent({ stages: failedStages })
      expect(wrapper.vm.pipelineProgressStatus).toBe('exception')
    })

    it('should return success when progress is 100', () => {
      const completedStages = [
        { id: 'requirement', name: '需求分析', status: 'success' as const }
      ]
      const wrapper = mountComponent({ stages: completedStages })
      expect(wrapper.vm.pipelineProgressStatus).toBe('success')
    })

    it('should return empty string otherwise', () => {
      const wrapper = mountComponent()
      expect(wrapper.vm.pipelineProgressStatus).toBe('')
    })
  })

  describe('completedStages computed', () => {
    it('should count completed stages correctly', () => {
      const wrapper = mountComponent()
      expect(wrapper.vm.completedStages).toBe(1)
    })
  })

  describe('currentStageName computed', () => {
    it('should return running stage name', () => {
      const wrapper = mountComponent()
      expect(wrapper.vm.currentStageName).toBe('设计')
    })

    it('should return waiting stage name when no running', () => {
      const waitingStages = [
        { id: 'requirement', name: '需求分析', status: 'success' as const },
        { id: 'design', name: '设计', status: 'waiting' as const }
      ]
      const wrapper = mountComponent({ stages: waitingStages })
      expect(wrapper.vm.currentStageName).toBe('设计')
    })

    it('should return dash when no running or waiting stage', () => {
      const pendingStages = [
        { id: 'requirement', name: '需求分析', status: 'pending' as const }
      ]
      const wrapper = mountComponent({ stages: pendingStages })
      expect(wrapper.vm.currentStageName).toBe('-')
    })
  })

  describe('pendingApprovals computed', () => {
    it('should return stages needing approval', () => {
      const wrapper = mountComponent()
      expect(wrapper.vm.pendingApprovals).toHaveLength(0)
    })

    it('should return waiting stages with needsApproval', () => {
      const waitingStages = [
        { id: 'design', name: '设计', status: 'waiting' as const, needsApproval: true }
      ]
      const wrapper = mountComponent({ stages: waitingStages })
      expect(wrapper.vm.pendingApprovals).toHaveLength(1)
      expect(wrapper.vm.pendingApprovals[0].stageName).toBe('设计')
    })
  })

  describe('isConnectorActive', () => {
    it('should return true when previous stage is success', () => {
      const wrapper = mountComponent()
      expect(wrapper.vm.isConnectorActive(0)).toBe(true)
    })

    it('should return false when previous stage is not success', () => {
      const wrapper = mountComponent()
      expect(wrapper.vm.isConnectorActive(1)).toBe(false)
    })
  })

  describe('methods', () => {
    it('should emit stageClick when showStageDetail called', () => {
      const wrapper = mountComponent()
      const stage = defaultStages[0]
      wrapper.vm.showStageDetail(stage)
      expect(wrapper.emitted('stageClick')).toBeTruthy()
      expect(wrapper.emitted('stageClick')![0]).toEqual([stage])
    })

    it('should show message when viewFullPipeline called', () => {
      const wrapper = mountComponent()
      wrapper.vm.viewFullPipeline()
      expect(ElMessage.info).toHaveBeenCalledWith('全屏查看功能')
    })

    it('should emit approval when handleApproval called', () => {
      const wrapper = mountComponent()
      wrapper.vm.handleApproval('approval-1', 'approve')
      expect(wrapper.emitted('approval')).toBeTruthy()
      expect(wrapper.emitted('approval')![0]).toEqual(['approval-1', 'approve'])
      expect(ElMessage.success).toHaveBeenCalledWith('审批通过')
    })

    it('should show reject message when handleApproval called with reject', () => {
      const wrapper = mountComponent()
      wrapper.vm.handleApproval('approval-1', 'reject')
      expect(ElMessage.success).toHaveBeenCalledWith('审批拒绝')
    })

    it('should show message when downloadArtifact called', () => {
      const wrapper = mountComponent()
      wrapper.vm.downloadArtifact({ id: '1', name: 'artifact.zip' })
      expect(ElMessage.success).toHaveBeenCalledWith('下载: artifact.zip')
    })
  })
})
