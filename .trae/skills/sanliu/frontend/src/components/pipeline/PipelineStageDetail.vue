<template>
  <el-dialog :model-value="visible" :title="stage?.name" width="600px" @update:model-value="$emit('update:visible', $event)">
    <div v-if="stage" class="stage-detail">
      <div class="detail-section">
        <div class="section-label">阶段状态</div>
        <div class="status-info">
          <el-tag :type="getStageStatusTag(stage.status)" size="large">
            {{ getStageStatusLabel(stage.status) }}
          </el-tag>
          <span v-if="stage.duration" class="duration">
            耗时: {{ formatDuration(stage.duration) }}
          </span>
        </div>
      </div>

      <div class="detail-section" v-if="stage.description">
        <div class="section-label">阶段描述</div>
        <div class="section-value">{{ stage.description }}</div>
      </div>

      <div class="detail-section" v-if="stage.tasks && stage.tasks.length > 0">
        <div class="section-label">执行任务</div>
        <div class="task-list">
          <div
            v-for="task in stage.tasks"
            :key="task.id"
            class="task-item"
          >
            <el-icon :class="'task-status-' + task.status">
              <component :is="getTaskIcon(task.status)" />
            </el-icon>
            <span class="task-name">{{ task.name }}</span>
            <span v-if="task.duration" class="task-duration">{{ task.duration }}ms</span>
          </div>
        </div>
      </div>

      <div class="detail-section" v-if="stage.artifacts && stage.artifacts.length > 0">
        <div class="section-label">产出物</div>
        <div class="artifact-list">
          <div
            v-for="artifact in stage.artifacts"
            :key="artifact.id"
            class="artifact-item"
          >
            <el-icon><Document /></el-icon>
            <span>{{ artifact.name }}</span>
            <el-button type="primary" link size="small" @click="$emit('download', artifact)">
              下载
            </el-button>
          </div>
        </div>
      </div>

      <div class="detail-section" v-if="stage.logs && stage.logs.length > 0">
        <div class="section-label">执行日志</div>
        <div class="log-container">
          <div
            v-for="(log, index) in stage.logs"
            :key="index"
            class="log-line"
            :class="'log-' + log.level"
          >
            <span class="log-time">{{ log.time }}</span>
            <span class="log-level">[{{ log.level.toUpperCase() }}]</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'
import { Document, CircleCheck, CircleClose, Loading, Clock } from '@element-plus/icons-vue'

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

defineProps<{
  visible: boolean
  stage: Stage | null
}>()

defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'download', artifact: Artifact): void
}>()

const stageStatusMap: Record<string, { label: string; type: string }> = {
  pending: { label: '待执行', type: 'info' },
  running: { label: '执行中', type: 'primary' },
  success: { label: '成功', type: 'success' },
  failed: { label: '失败', type: 'danger' },
  waiting: { label: '等待中', type: 'warning' },
  skipped: { label: '已跳过', type: 'info' }
}

const getStageStatusTag = (status: string) => stageStatusMap[status]?.type || 'info'
const getStageStatusLabel = (status: string) => stageStatusMap[status]?.label || status

const getTaskIcon = (status: string) => {
  switch (status) {
    case 'success': return CircleCheck
    case 'failed': return CircleClose
    case 'running': return Loading
    default: return Clock
  }
}

const formatDuration = (ms?: number) => {
  if (!ms) return '-'
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${(ms / 60000).toFixed(1)}min`
}
</script>

<style scoped>
.stage-detail {
  padding: 10px 0;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.section-label {
  font-weight: 500;
  font-size: 14px;
  color: #303133;
  margin-bottom: 10px;
  padding-left: 10px;
  border-left: 3px solid #409eff;
}

.section-value {
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
  color: #606266;
  line-height: 1.6;
}

.status-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.duration {
  font-size: 13px;
  color: #909399;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #f5f7fa;
  border-radius: 6px;
  font-size: 13px;
}

.task-status-success {
  color: #67c23a;
}

.task-status-failed {
  color: #f56c6c;
}

.task-status-running {
  color: #409eff;
}

.task-status-pending {
  color: #909399;
}

.task-name {
  flex: 1;
}

.task-duration {
  color: #909399;
  font-size: 12px;
}

.artifact-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.artifact-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #f5f7fa;
  border-radius: 6px;
  font-size: 13px;
}

.artifact-item span {
  flex: 1;
}

.log-container {
  max-height: 200px;
  overflow-y: auto;
  padding: 12px;
  background: #1e1e1e;
  border-radius: 6px;
  font-family: 'Consolas', monospace;
  font-size: 12px;
}

.log-line {
  display: flex;
  gap: 8px;
  margin-bottom: 4px;
  color: #d4d4d4;
}

.log-line.log-warn {
  color: #e6a23c;
}

.log-line.log-error {
  color: #f56c6c;
}

.log-time {
  color: #6a9955;
}

.log-level {
  color: #569cd6;
}

.log-message {
  flex: 1;
}
</style>
