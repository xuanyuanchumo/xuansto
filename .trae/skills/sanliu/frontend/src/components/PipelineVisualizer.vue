<template>
  <el-card class="pipeline-visualizer" shadow="hover">
    <template #header>
      <div class="card-header">
        <span class="title">流水线可视化</span>
        <div class="header-actions">
          <el-tag :type="pipelineStatus.type" size="small">
            {{ pipelineStatus.label }}
          </el-tag>
          <el-button type="primary" size="small" @click="viewFullPipeline">
            <el-icon><FullScreen /></el-icon>
            全屏查看
          </el-button>
        </div>
      </div>
    </template>

    <div class="pipeline-container">
      <div class="pipeline-flow">
        <template v-for="(stage, index) in stages" :key="stage.id">
          <PipelineNode
            :stage="stage"
            :current-stage-id="currentStageId"
            @click="showStageDetail"
          />
          <PipelineEdge
            v-if="index < stages.length - 1"
            :is-active="isConnectorActive(index)"
          />
        </template>
      </div>

      <div class="pipeline-progress">
        <el-progress
          :percentage="pipelineProgress"
          :status="pipelineProgressStatus"
          :stroke-width="8"
        />
        <div class="progress-info">
          <span>当前阶段: {{ currentStageName }}</span>
          <span>进度: {{ completedStages }}/{{ stages.length }}</span>
        </div>
      </div>
    </div>

    <el-divider />

    <PipelineApprovalList
      :approvals="pendingApprovals"
      @approval="handleApproval"
    />

    <PipelineStageDetail
      v-model:visible="stageDetailVisible"
      :stage="currentStage"
      @download="downloadArtifact"
    />
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed, defineProps, defineEmits } from 'vue'
import { ElMessage } from 'element-plus'
import { FullScreen } from '@element-plus/icons-vue'
import PipelineNode from './pipeline/PipelineNode.vue'
import PipelineEdge from './pipeline/PipelineEdge.vue'
import PipelineStageDetail from './pipeline/PipelineStageDetail.vue'
import PipelineApprovalList from './pipeline/PipelineApprovalList.vue'

interface Task {
  id: string
  name: string
  status: 'pending' | 'running' | 'success' | 'failed'
  duration?: number
}

interface Artifact {
  id: string
  name: string
  url?: string
}

interface Log {
  time: string
  level: 'info' | 'warn' | 'error'
  message: string
}

interface Stage {
  id: string
  name: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'waiting' | 'skipped'
  needsApproval?: boolean
  description?: string
  duration?: number
  tasks?: Task[]
  artifacts?: Artifact[]
  logs?: Log[]
}

interface Approval {
  id: string
  stageId: string
  stageName: string
  reason: string
}

const props = defineProps<{
  stages: Stage[]
  currentStageId?: string
}>()

const emit = defineEmits<{
  (e: 'stageClick', stage: Stage): void
  (e: 'approval', approvalId: string, action: 'approve' | 'reject'): void
}>()

const stageDetailVisible = ref(false)
const currentStage = ref<Stage | null>(null)

const pipelineStatus = computed(() => {
  const hasFailed = props.stages.some(s => s.status === 'failed')
  const isRunning = props.stages.some(s => s.status === 'running')
  const isWaiting = props.stages.some(s => s.status === 'waiting')
  const allSuccess = props.stages.every(s => s.status === 'success' || s.status === 'skipped')

  if (hasFailed) return { type: 'danger', label: '执行失败' }
  if (isWaiting) return { type: 'warning', label: '等待审批' }
  if (isRunning) return { type: 'primary', label: '执行中' }
  if (allSuccess) return { type: 'success', label: '执行完成' }
  return { type: 'info', label: '待执行' }
})

const pipelineProgress = computed(() => {
  const completed = props.stages.filter(s =>
    s.status === 'success' || s.status === 'failed' || s.status === 'skipped'
  ).length
  return Math.round((completed / props.stages.length) * 100)
})

const pipelineProgressStatus = computed(() => {
  if (props.stages.some(s => s.status === 'failed')) return 'exception'
  if (pipelineProgress.value === 100) return 'success'
  return ''
})

const completedStages = computed(() =>
  props.stages.filter(s => s.status === 'success' || s.status === 'failed' || s.status === 'skipped').length
)

const currentStageName = computed(() => {
  const running = props.stages.find(s => s.status === 'running')
  if (running) return running.name
  const waiting = props.stages.find(s => s.status === 'waiting')
  if (waiting) return waiting.name
  return '-'
})

const pendingApprovals = computed(() => {
  return props.stages
    .filter(s => s.status === 'waiting' && s.needsApproval)
    .map(s => ({
      id: s.id,
      stageId: s.id,
      stageName: s.name,
      reason: '需要人工审批才能继续执行'
    }))
})

const isConnectorActive = (index: number) => {
  const currentStage = props.stages[index]
  return currentStage.status === 'success'
}

const showStageDetail = (stage: Stage) => {
  currentStage.value = stage
  stageDetailVisible.value = true
  emit('stageClick', stage)
}

const viewFullPipeline = () => {
  ElMessage.info('全屏查看功能')
}

const handleApproval = (approvalId: string, action: 'approve' | 'reject') => {
  emit('approval', approvalId, action)
  ElMessage.success(action === 'approve' ? '审批通过' : '审批拒绝')
}

const downloadArtifact = (artifact: Artifact) => {
  ElMessage.success(`下载: ${artifact.name}`)
}
</script>

<style scoped>
.pipeline-visualizer {
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

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.pipeline-container {
  padding: 10px 0;
}

.pipeline-flow {
  display: flex;
  align-items: center;
  overflow-x: auto;
  padding: 20px 10px;
  gap: 0;
}

.pipeline-progress {
  margin-top: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  font-size: 13px;
  color: #606266;
}

.el-divider {
  margin: 20px 0;
}
</style>
