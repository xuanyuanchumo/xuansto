<template>
  <el-card class="decision-log-viewer" shadow="hover">
    <template #header>
      <div class="card-header">
        <span class="title">决策日志</span>
        <el-tag v-if="decisions.length" type="info" size="small">
          共 {{ decisions.length }} 条决策
        </el-tag>
      </div>
    </template>

    <div v-if="!decisions || decisions.length === 0" class="empty-container">
      <el-empty description="暂无决策记录" :image-size="80" />
    </div>

    <div v-else class="decision-list">
      <el-collapse v-model="activeNames" accordion>
        <el-collapse-item
          v-for="(decision, index) in decisions"
          :key="decision.id || index"
          :name="decision.id || index"
        >
          <template #title>
            <div class="decision-title">
              <el-tag :type="getDecisionTypeTag(decision.type)" size="small">
                {{ getDecisionTypeLabel(decision.type) }}
              </el-tag>
              <span class="decision-name">{{ decision.name || `决策 #${index + 1}` }}</span>
              <span class="decision-time">{{ formatTime(decision.timestamp) }}</span>
            </div>
          </template>

          <div class="decision-content">
            <div class="content-section">
              <div class="section-label">决策依据</div>
              <div class="section-value">{{ decision.basis || '暂无依据说明' }}</div>
            </div>

            <div class="content-section">
              <div class="section-label">推理过程</div>
              <div class="reasoning-process">
                <el-steps direction="vertical" :active="decision.reasoning?.length || 0">
                  <el-step
                    v-for="(step, stepIndex) in decision.reasoning"
                    :key="stepIndex"
                    :title="step.title"
                    :description="step.description"
                    :status="getStepStatus(step.status)"
                  />
                </el-steps>
                <div v-if="!decision.reasoning || decision.reasoning.length === 0" class="no-data">
                  暂无推理过程
                </div>
              </div>
            </div>

            <div class="content-section">
              <div class="section-label">备选方案</div>
              <div v-if="decision.alternatives && decision.alternatives.length > 0" class="alternatives">
                <div
                  v-for="(alt, altIndex) in decision.alternatives"
                  :key="altIndex"
                  class="alternative-item"
                  :class="{ selected: alt.selected }"
                >
                  <div class="alternative-header">
                    <el-icon v-if="alt.selected" class="selected-icon"><Select /></el-icon>
                    <span class="alternative-name">{{ alt.name }}</span>
                    <el-tag v-if="alt.selected" type="success" size="small">已选择</el-tag>
                  </div>
                  <div class="alternative-desc">{{ alt.description }}</div>
                  <div v-if="alt.pros || alt.cons" class="alternative-analysis">
                    <div v-if="alt.pros" class="pros">
                      <span class="label">优点：</span>{{ alt.pros }}
                    </div>
                    <div v-if="alt.cons" class="cons">
                      <span class="label">缺点：</span>{{ alt.cons }}
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="no-data">暂无备选方案</div>
            </div>

            <div v-if="decision.confidence" class="content-section">
              <div class="section-label">置信度</div>
              <el-progress
                :percentage="decision.confidence"
                :status="getConfidenceStatus(decision.confidence)"
                :stroke-width="10"
              />
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, defineProps } from 'vue'
import { Select } from '@element-plus/icons-vue'

interface ReasoningStep {
  title: string
  description?: string
  status?: 'success' | 'process' | 'error' | 'wait'
}

interface Alternative {
  name: string
  description?: string
  selected?: boolean
  pros?: string
  cons?: string
}

interface Decision {
  id?: string | number
  name?: string
  type?: string
  timestamp?: string
  basis?: string
  reasoning?: ReasoningStep[]
  alternatives?: Alternative[]
  confidence?: number
}

defineProps<{
  decisions: Decision[]
}>()

const activeNames = ref<string | number | null>(null)

const decisionTypeMap: Record<string, { label: string; type: string }> = {
  architecture: { label: '架构决策', type: 'primary' },
  implementation: { label: '实现决策', type: 'success' },
  optimization: { label: '优化决策', type: 'warning' },
  risk: { label: '风险决策', type: 'danger' },
  resource: { label: '资源决策', type: 'info' }
}

const getDecisionTypeTag = (type?: string) => {
  if (!type) return 'info'
  return decisionTypeMap[type]?.type || 'info'
}

const getDecisionTypeLabel = (type?: string) => {
  if (!type) return '其他决策'
  return decisionTypeMap[type]?.label || type
}

const getStepStatus = (status?: string) => {
  const validStatuses = ['success', 'process', 'error', 'wait']
  if (!status || !validStatuses.includes(status)) return 'process'
  return status as 'success' | 'process' | 'error' | 'wait'
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
</script>

<style scoped>
.decision-log-viewer {
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

.decision-list {
  max-height: 600px;
  overflow-y: auto;
}

.decision-title {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.decision-name {
  font-weight: 500;
  flex: 1;
}

.decision-time {
  color: #909399;
  font-size: 12px;
}

.decision-content {
  padding: 10px 0;
}

.content-section {
  margin-bottom: 20px;
}

.content-section:last-child {
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

.reasoning-process {
  padding: 10px;
  background: #fafafa;
  border-radius: 4px;
}

.alternatives {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.alternative-item {
  padding: 12px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  background: #fff;
  transition: all 0.3s;
}

.alternative-item.selected {
  border-color: #67c23a;
  background: #f0f9eb;
}

.alternative-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.selected-icon {
  color: #67c23a;
}

.alternative-name {
  font-weight: 500;
  flex: 1;
}

.alternative-desc {
  color: #606266;
  font-size: 13px;
  margin-bottom: 8px;
}

.alternative-analysis {
  font-size: 12px;
  padding-top: 8px;
  border-top: 1px dashed #ebeef5;
}

.alternative-analysis .label {
  font-weight: 500;
}

.pros {
  color: #67c23a;
  margin-bottom: 4px;
}

.cons {
  color: #f56c6c;
}

.no-data {
  color: #909399;
  font-size: 13px;
  text-align: center;
  padding: 20px;
}
</style>
