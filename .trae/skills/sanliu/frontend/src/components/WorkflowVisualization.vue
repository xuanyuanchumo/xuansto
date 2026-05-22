<template>
  <el-card class="workflow-visualization" shadow="hover">
    <template #header>
      <div class="card-header">
        <span class="title">工作流可视化</span>
        <el-tag :type="workflowStatusType" size="small">
          {{ workflowStatusText }}
        </el-tag>
      </div>
    </template>

    <div class="workflow-content">
      <div class="phase-progress">
        <div class="section-title">阶段进度</div>
        <el-steps :active="currentPhaseIndex" align-center>
          <el-step
            v-for="(phase, index) in phases"
            :key="phase.key"
            :title="phase.name"
            :status="getStepStatus(index)"
          >
            <template #icon>
              <el-icon v-if="index < currentPhaseIndex" class="step-icon completed">
                <Check />
              </el-icon>
              <span v-else class="step-number">{{ index + 1 }}</span>
            </template>
          </el-step>
        </el-steps>
      </div>

      <div class="task-statistics">
        <div class="section-title">任务完成情况</div>
        <div class="statistics-grid">
          <div
            v-for="phase in phases"
            :key="phase.key"
            class="phase-stat-card"
            :class="{ active: phase.key === currentPhase }"
          >
            <div class="phase-header">
              <span class="phase-name">{{ phase.name }}</span>
              <el-tag
                :type="getPhaseStatusType(phase.key)"
                size="small"
              >
                {{ getPhaseStatusText(phase.key) }}
              </el-tag>
            </div>
            <div class="task-count">
              <span class="completed">{{ getCompletedTasks(phase.key) }}</span>
              <span class="separator">/</span>
              <span class="total">{{ getTotalTasks(phase.key) }}</span>
              <span class="unit">任务</span>
            </div>
            <el-progress
              :percentage="getPhaseProgress(phase.key)"
              :status="getProgressStatus(phase.key)"
              :stroke-width="8"
            />
          </div>
        </div>
      </div>

      <div class="workflow-status">
        <div class="section-title">工作流状态</div>
        <div class="status-indicators">
          <div
            v-for="status in statusList"
            :key="status.key"
            class="status-item"
            :class="status.key"
          >
            <div class="status-dot"></div>
            <span class="status-label">{{ status.label }}</span>
            <span class="status-count">{{ status.count }}</span>
          </div>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed, defineProps } from 'vue'
import { Check } from '@element-plus/icons-vue'

interface PhaseTask {
  total: number
  completed: number
}

const props = defineProps<{
  currentPhase: string
  phaseTasks: Record<string, PhaseTask>
  statusCounts?: {
    inProgress?: number
    completed?: number
    pending?: number
  }
}>()

const phases = [
  { key: 'requirement', name: '需求分析' },
  { key: 'design', name: '设计' },
  { key: 'development', name: '开发' },
  { key: 'testing', name: '测试' },
  { key: 'deployment', name: '部署' },
  { key: 'completed', name: '完成' }
]

const currentPhaseIndex = computed(() => {
  const index = phases.findIndex(p => p.key === props.currentPhase)
  return index >= 0 ? index : 0
})

const getStepStatus = (index: number) => {
  if (index < currentPhaseIndex.value) {
    return 'success'
  } else if (index === currentPhaseIndex.value) {
    return 'process'
  }
  return 'wait'
}

const getTotalTasks = (phaseKey: string) => {
  return props.phaseTasks[phaseKey]?.total || 0
}

const getCompletedTasks = (phaseKey: string) => {
  return props.phaseTasks[phaseKey]?.completed || 0
}

const getPhaseProgress = (phaseKey: string) => {
  const tasks = props.phaseTasks[phaseKey]
  if (!tasks || tasks.total === 0) return 0
  return Math.round((tasks.completed / tasks.total) * 100)
}

const getProgressStatus = (phaseKey: string) => {
  const progress = getPhaseProgress(phaseKey)
  const currentIndex = phases.findIndex(p => p.key === phaseKey)
  
  if (progress === 100) return 'success'
  if (currentIndex === currentPhaseIndex.value) return undefined
  return undefined
}

const getPhaseStatusType = (phaseKey: string) => {
  const currentIndex = phases.findIndex(p => p.key === phaseKey)
  const progress = getPhaseProgress(phaseKey)
  
  if (progress === 100) return 'success'
  if (currentIndex === currentPhaseIndex.value) return 'primary'
  if (currentIndex < currentPhaseIndex.value) return 'success'
  return 'info'
}

const getPhaseStatusText = (phaseKey: string) => {
  const currentIndex = phases.findIndex(p => p.key === phaseKey)
  const progress = getPhaseProgress(phaseKey)
  
  if (progress === 100) return '已完成'
  if (currentIndex === currentPhaseIndex.value) return '进行中'
  if (currentIndex < currentPhaseIndex.value) return '已完成'
  return '待处理'
}

const workflowStatusType = computed(() => {
  const progress = getPhaseProgress(props.currentPhase)
  if (props.currentPhase === 'completed') return 'success'
  if (progress > 0) return 'primary'
  return 'info'
})

const workflowStatusText = computed(() => {
  if (props.currentPhase === 'completed') return '已完成'
  const currentPhaseName = phases.find(p => p.key === props.currentPhase)?.name || ''
  return `${currentPhaseName}阶段`
})

const statusList = computed(() => [
  {
    key: 'in-progress',
    label: '进行中',
    count: props.statusCounts?.inProgress || 0
  },
  {
    key: 'completed',
    label: '已完成',
    count: props.statusCounts?.completed || 0
  },
  {
    key: 'pending',
    label: '待处理',
    count: props.statusCounts?.pending || 0
  }
])
</script>

<style scoped>
.workflow-visualization {
  margin-bottom: 15px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-weight: bold;
  font-size: 16px;
}

.workflow-content {
  padding: 10px 0;
}

.section-title {
  font-weight: 500;
  font-size: 14px;
  color: #303133;
  margin-bottom: 15px;
  padding-left: 10px;
  border-left: 3px solid #409eff;
}

.phase-progress {
  margin-bottom: 25px;
}

.step-icon.completed {
  color: #67c23a;
  font-size: 18px;
}

.step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #c0c4cc;
  color: #fff;
  font-size: 12px;
}

.task-statistics {
  margin-bottom: 25px;
}

.statistics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
}

.phase-stat-card {
  padding: 15px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #fafafa;
  transition: all 0.3s;
}

.phase-stat-card.active {
  border-color: #409eff;
  background: #ecf5ff;
}

.phase-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.phase-name {
  font-weight: 500;
  font-size: 14px;
}

.task-count {
  margin-bottom: 10px;
  font-size: 13px;
}

.task-count .completed {
  font-weight: bold;
  color: #409eff;
  font-size: 18px;
}

.task-count .separator {
  color: #909399;
  margin: 0 4px;
}

.task-count .total {
  color: #606266;
}

.task-count .unit {
  color: #909399;
  margin-left: 4px;
  font-size: 12px;
}

.workflow-status {
  margin-bottom: 10px;
}

.status-indicators {
  display: flex;
  gap: 30px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.status-item.in-progress .status-dot {
  background: #409eff;
}

.status-item.completed .status-dot {
  background: #67c23a;
}

.status-item.pending .status-dot {
  background: #909399;
}

.status-label {
  font-size: 13px;
  color: #606266;
}

.status-count {
  font-weight: bold;
  font-size: 14px;
  color: #303133;
}
</style>
