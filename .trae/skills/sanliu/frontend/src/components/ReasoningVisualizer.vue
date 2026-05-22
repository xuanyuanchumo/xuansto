<template>
  <el-card class="reasoning-visualizer" shadow="hover">
    <template #header>
      <div class="card-header">
        <span class="title">推理过程</span>
        <div class="header-actions">
          <el-button-group size="small">
            <el-button :type="viewMode === 'timeline' ? 'primary' : 'default'" @click="viewMode = 'timeline'">
              时间线
            </el-button>
            <el-button :type="viewMode === 'flow' ? 'primary' : 'default'" @click="viewMode = 'flow'">
              流程图
            </el-button>
          </el-button-group>
        </div>
      </div>
    </template>

    <div v-if="!steps || steps.length === 0" class="empty-container">
      <el-empty description="暂无推理过程" :image-size="80" />
    </div>

    <div v-else class="reasoning-container">
      <div v-if="viewMode === 'timeline'" class="timeline-view">
        <el-timeline>
          <el-timeline-item
            v-for="(step, index) in steps"
            :key="step.id || index"
            :timestamp="formatTime(step.timestamp)"
            placement="top"
            :type="getTimelineType(step.status)"
            :hollow="!isKeyDecision(step)"
            :size="isKeyDecision(step) ? 'large' : 'normal'"
          >
            <el-card
              shadow="hover"
              :class="{ 'key-decision': isKeyDecision(step), 'step-card': true }"
            >
              <div class="step-header">
                <div class="step-title-row">
                  <span class="step-number">步骤 {{ index + 1 }}</span>
                  <el-tag :type="getStatusType(step.status)" size="small">
                    {{ getStatusLabel(step.status) }}
                  </el-tag>
                  <el-tag v-if="isKeyDecision(step)" type="warning" size="small">
                    <el-icon><Star /></el-icon>
                    关键决策
                  </el-tag>
                </div>
                <div class="step-name">{{ step.name }}</div>
              </div>

              <div class="step-content">
                <div v-if="step.description" class="step-description">
                  {{ step.description }}
                </div>

                <div v-if="step.input" class="step-section">
                  <div class="section-label">输入</div>
                  <div class="section-value">{{ step.input }}</div>
                </div>

                <div v-if="step.output" class="step-section">
                  <div class="section-label">输出</div>
                  <div class="section-value">{{ step.output }}</div>
                </div>

                <div v-if="step.reasoning" class="step-section">
                  <div class="section-label">推理依据</div>
                  <div class="reasoning-detail">
                    <div v-for="(reason, rIndex) in step.reasoning" :key="rIndex" class="reason-item">
                      <el-icon class="reason-icon"><Right /></el-icon>
                      <span>{{ reason }}</span>
                    </div>
                  </div>
                </div>

                <div v-if="step.confidence !== undefined" class="step-section">
                  <div class="section-label">置信度</div>
                  <el-progress
                    :percentage="step.confidence"
                    :status="getConfidenceStatus(step.confidence)"
                    :stroke-width="8"
                  />
                </div>

                <div v-if="step.duration" class="step-duration">
                  <el-icon><Timer /></el-icon>
                  耗时: {{ formatDuration(step.duration) }}
                </div>
              </div>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </div>

      <div v-else class="flow-view">
        <div class="flow-container">
          <div
            v-for="(step, index) in steps"
            :key="step.id || index"
            class="flow-step"
            :class="{ 'key-decision': isKeyDecision(step) }"
          >
            <div class="flow-step-content">
              <div class="flow-step-header">
                <el-tag :type="getStatusType(step.status)" size="small">
                  {{ getStatusLabel(step.status) }}
                </el-tag>
                <span class="flow-step-name">{{ step.name }}</span>
              </div>
              <div v-if="step.description" class="flow-step-desc">
                {{ step.description }}
              </div>
            </div>
            <div v-if="index < steps.length - 1" class="flow-arrow">
              <el-icon><Bottom /></el-icon>
            </div>
          </div>
        </div>
      </div>

      <div class="reasoning-summary">
        <div class="summary-item">
          <span class="label">总步骤</span>
          <span class="value">{{ steps.length }}</span>
        </div>
        <div class="summary-item">
          <span class="label">关键决策</span>
          <span class="value highlight">{{ keyDecisionsCount }}</span>
        </div>
        <div class="summary-item">
          <span class="label">总耗时</span>
          <span class="value">{{ formatDuration(totalDuration) }}</span>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed, defineProps } from 'vue'
import { Star, Right, Timer, Bottom } from '@element-plus/icons-vue'

interface ReasoningStep {
  id?: string | number
  name: string
  description?: string
  status?: 'success' | 'processing' | 'failed' | 'pending'
  timestamp?: string
  input?: string
  output?: string
  reasoning?: string[]
  confidence?: number
  duration?: number
  isKeyDecision?: boolean
}

const props = defineProps<{
  steps: ReasoningStep[]
}>()

const viewMode = ref<'timeline' | 'flow'>('timeline')

const statusMap: Record<string, { label: string; type: string }> = {
  success: { label: '成功', type: 'success' },
  processing: { label: '处理中', type: 'primary' },
  failed: { label: '失败', type: 'danger' },
  pending: { label: '待处理', type: 'info' }
}

const keyDecisionsCount = computed(() => {
  return props.steps.filter(s => s.isKeyDecision).length
})

const totalDuration = computed(() => {
  return props.steps.reduce((sum, s) => sum + (s.duration || 0), 0)
})

const isKeyDecision = (step: ReasoningStep) => step.isKeyDecision

const getStatusType = (status?: string) => {
  if (!status) return 'info'
  return statusMap[status]?.type || 'info'
}

const getStatusLabel = (status?: string) => {
  if (!status) return '未知'
  return statusMap[status]?.label || status
}

const getTimelineType = (status?: string) => {
  const types: Record<string, string> = {
    success: 'success',
    processing: 'primary',
    failed: 'danger',
    pending: 'info'
  }
  return types[status || ''] || 'info'
}

const getConfidenceStatus = (confidence: number) => {
  if (confidence >= 80) return 'success'
  if (confidence >= 50) return 'warning'
  return 'exception'
}

const formatTime = (time?: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const formatDuration = (ms: number) => {
  if (!ms) return '-'
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${(ms / 60000).toFixed(1)}min`
}
</script>

<style scoped>
.reasoning-visualizer {
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

.empty-container {
  padding: 20px 0;
}

.reasoning-container {
  padding: 10px 0;
}

.timeline-view {
  max-height: 600px;
  overflow-y: auto;
}

.step-card {
  transition: all 0.3s;
}

.step-card.key-decision {
  border-left: 3px solid #e6a23c;
}

.step-header {
  margin-bottom: 10px;
}

.step-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.step-number {
  font-size: 12px;
  color: #909399;
}

.step-name {
  font-weight: 600;
  font-size: 15px;
  color: #303133;
}

.step-content {
  padding-top: 5px;
}

.step-description {
  color: #606266;
  line-height: 1.6;
  margin-bottom: 12px;
}

.step-section {
  margin-bottom: 12px;
}

.section-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
}

.section-value {
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 13px;
  color: #606266;
}

.reasoning-detail {
  padding: 8px 12px;
  background: #fafafa;
  border-radius: 4px;
}

.reason-item {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-bottom: 6px;
  font-size: 13px;
  color: #606266;
}

.reason-item:last-child {
  margin-bottom: 0;
}

.reason-icon {
  color: #409eff;
  margin-top: 3px;
}

.step-duration {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
  margin-top: 10px;
}

.flow-view {
  padding: 10px;
}

.flow-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  max-height: 500px;
  overflow-y: auto;
}

.flow-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 400px;
}

.flow-step-content {
  width: 100%;
  padding: 15px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  transition: all 0.3s;
}

.flow-step.key-decision .flow-step-content {
  border-color: #e6a23c;
  background: #fdf6ec;
}

.flow-step-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.flow-step-name {
  font-weight: 500;
  font-size: 14px;
}

.flow-step-desc {
  font-size: 13px;
  color: #606266;
}

.flow-arrow {
  padding: 8px 0;
  color: #dcdfe6;
}

.reasoning-summary {
  display: flex;
  justify-content: center;
  gap: 40px;
  margin-top: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.summary-item .label {
  font-size: 12px;
  color: #909399;
}

.summary-item .value {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.summary-item .value.highlight {
  color: #e6a23c;
}
</style>
