<template>
  <div
    class="stage-node"
    :class="nodeClass"
    @click="handleClick"
  >
    <div class="stage-icon">
      <el-icon :size="24">
        <component :is="icon" />
      </el-icon>
    </div>
    <div class="stage-info">
      <div class="stage-name">{{ stage.name }}</div>
      <div class="stage-status">
        <el-tag :type="statusTag" size="small">
          {{ statusLabel }}
        </el-tag>
      </div>
    </div>
    <div v-if="stage.needsApproval && stage.status === 'waiting'" class="approval-badge">
      <el-icon><User /></el-icon>
      需审批
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineProps, defineEmits } from 'vue'
import { User, Document, DataAnalysis, Setting, DocumentChecked, Checked, Promotion } from '@element-plus/icons-vue'

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

const props = defineProps<{
  stage: Stage
  currentStageId?: string
}>()

const emit = defineEmits<{
  (e: 'click', stage: Stage): void
}>()

const stageIcons: Record<string, any> = {
  requirement: Document,
  design: DataAnalysis,
  implementation: Setting,
  testing: DocumentChecked,
  review: Checked,
  deployment: Promotion,
  monitoring: DataAnalysis
}

const stageStatusMap: Record<string, { label: string; type: string }> = {
  pending: { label: '待执行', type: 'info' },
  running: { label: '执行中', type: 'primary' },
  success: { label: '成功', type: 'success' },
  failed: { label: '失败', type: 'danger' },
  waiting: { label: '等待中', type: 'warning' },
  skipped: { label: '已跳过', type: 'info' }
}

const nodeClass = computed(() => {
  const classes = [`status-${props.stage.status}`]
  if (props.stage.id === props.currentStageId) classes.push('current')
  if (props.stage.needsApproval) classes.push('needs-approval')
  return classes.join(' ')
})

const icon = computed(() => stageIcons[props.stage.id] || Document)

const statusTag = computed(() => stageStatusMap[props.stage.status]?.type || 'info')

const statusLabel = computed(() => stageStatusMap[props.stage.status]?.label || props.stage.status)

const handleClick = () => {
  emit('click', props.stage)
}
</script>

<style scoped>
.stage-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  border-radius: 12px;
  background: #f5f7fa;
  min-width: 140px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
}

.stage-node:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stage-node.status-pending {
  background: #f5f7fa;
}

.stage-node.status-running {
  background: #ecf5ff;
  border: 2px solid #409eff;
}

.stage-node.status-success {
  background: #f0f9eb;
  border: 2px solid #67c23a;
}

.stage-node.status-failed {
  background: #fef0f0;
  border: 2px solid #f56c6c;
}

.stage-node.status-waiting {
  background: #fdf6ec;
  border: 2px solid #e6a23c;
}

.stage-node.current {
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.3);
}

.stage-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #fff;
  margin-bottom: 10px;
}

.stage-node.status-running .stage-icon {
  color: #409eff;
}

.stage-node.status-success .stage-icon {
  color: #67c23a;
}

.stage-node.status-failed .stage-icon {
  color: #f56c6c;
}

.stage-node.status-waiting .stage-icon {
  color: #e6a23c;
}

.stage-info {
  text-align: center;
}

.stage-name {
  font-weight: 500;
  font-size: 14px;
  color: #303133;
  margin-bottom: 6px;
}

.approval-badge {
  position: absolute;
  top: -8px;
  right: -8px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: #e6a23c;
  color: #fff;
  border-radius: 10px;
  font-size: 11px;
  white-space: nowrap;
}
</style>
