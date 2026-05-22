<template>
  <el-card class="non-functional-checker" shadow="hover">
    <template #header>
      <div class="card-header">
        <span class="title">非功能性检查</span>
        <div class="header-actions">
          <el-tag :type="overallStatus.type" size="small">
            {{ overallStatus.label }}
          </el-tag>
          <el-button type="primary" size="small" @click="runCheck" :loading="isChecking">
            <el-icon><VideoPlay /></el-icon>
            执行检查
          </el-button>
        </div>
      </div>
    </template>

    <div class="check-summary">
      <div class="summary-cards">
        <div class="summary-card passed">
          <div class="card-value">{{ passedCount }}</div>
          <div class="card-label">通过</div>
        </div>
        <div class="summary-card warning">
          <div class="card-value">{{ warningCount }}</div>
          <div class="card-label">警告</div>
        </div>
        <div class="summary-card failed">
          <div class="card-value">{{ failedCount }}</div>
          <div class="card-label">失败</div>
        </div>
        <div class="summary-card pending">
          <div class="card-value">{{ pendingCount }}</div>
          <div class="card-label">待检查</div>
        </div>
      </div>
    </div>

    <el-divider />

    <el-tabs v-model="activeTab">
      <el-tab-pane label="性能检查" name="performance">
        <div v-if="!performanceItems || performanceItems.length === 0" class="empty-container">
          <el-empty description="暂无性能检查项" :image-size="80" />
        </div>
        <div v-else class="check-list">
          <div
            v-for="item in performanceItems"
            :key="item.id"
            class="check-item"
            :class="'status-' + item.status"
          >
            <div class="check-header">
              <div class="check-meta">
                <el-tag :type="getStatusTag(item.status)" size="small">
                  {{ getStatusLabel(item.status) }}
                </el-tag>
                <span class="check-name">{{ item.name }}</span>
              </div>
              <el-tag type="info" size="small">{{ item.category }}</el-tag>
            </div>

            <div class="check-description">{{ item.description }}</div>

            <div class="check-metrics">
              <div class="metric-item">
                <span class="metric-label">基线值</span>
                <span class="metric-value baseline">{{ item.baseline }}{{ item.unit }}</span>
              </div>
              <div class="metric-arrow">
                <el-icon><Right /></el-icon>
              </div>
              <div class="metric-item">
                <span class="metric-label">实际值</span>
                <span class="metric-value" :class="getMetricClass(item)">
                  {{ item.actual !== undefined ? item.actual + item.unit : '-' }}
                </span>
              </div>
              <div class="metric-item">
                <span class="metric-label">偏差</span>
                <span class="metric-value" :class="getDeviationClass(item)">
                  {{ getDeviation(item) }}
                </span>
              </div>
            </div>

            <div v-if="item.status === 'failed' && item.suggestion" class="check-suggestion">
              <el-icon><InfoFilled /></el-icon>
              {{ item.suggestion }}
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="安全检查" name="security">
        <div v-if="!securityItems || securityItems.length === 0" class="empty-container">
          <el-empty description="暂无安全检查项" :image-size="80" />
        </div>
        <div v-else class="check-list">
          <div
            v-for="item in securityItems"
            :key="item.id"
            class="check-item"
            :class="'status-' + item.status"
          >
            <div class="check-header">
              <div class="check-meta">
                <el-tag :type="getStatusTag(item.status)" size="small">
                  {{ getStatusLabel(item.status) }}
                </el-tag>
                <span class="check-name">{{ item.name }}</span>
              </div>
              <el-tag :type="getSeverityTag(item.severity)" size="small" effect="dark">
                {{ getSeverityLabel(item.severity) }}风险
              </el-tag>
            </div>

            <div class="check-description">{{ item.description }}</div>

            <div class="check-details">
              <div class="detail-item">
                <span class="detail-label">检查项：</span>
                <span>{{ item.checkItem }}</span>
              </div>
              <div v-if="item.actual !== undefined" class="detail-item">
                <span class="detail-label">检测结果：</span>
                <span :class="item.status === 'passed' ? 'text-success' : 'text-danger'">
                  {{ item.actual }}
                </span>
              </div>
            </div>

            <div v-if="item.status === 'failed' && item.vulnerability" class="vulnerability-info">
              <div class="vuln-title">漏洞详情</div>
              <div class="vuln-content">{{ item.vulnerability }}</div>
            </div>

            <div v-if="item.status === 'failed' && item.remediation" class="check-suggestion">
              <el-icon><InfoFilled /></el-icon>
              {{ item.remediation }}
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="合规检查" name="compliance">
        <div v-if="!complianceItems || complianceItems.length === 0" class="empty-container">
          <el-empty description="暂无合规检查项" :image-size="80" />
        </div>
        <div v-else class="check-list">
          <div
            v-for="item in complianceItems"
            :key="item.id"
            class="check-item"
            :class="'status-' + item.status"
          >
            <div class="check-header">
              <div class="check-meta">
                <el-tag :type="getStatusTag(item.status)" size="small">
                  {{ getStatusLabel(item.status) }}
                </el-tag>
                <span class="check-name">{{ item.name }}</span>
              </div>
              <el-tag type="info" size="small">{{ item.standard }}</el-tag>
            </div>

            <div class="check-description">{{ item.description }}</div>

            <div class="compliance-details">
              <div class="compliance-item">
                <span class="label">条款编号：</span>
                <span>{{ item.clause }}</span>
              </div>
              <div class="compliance-item">
                <span class="label">要求描述：</span>
                <span>{{ item.requirement }}</span>
              </div>
              <div class="compliance-item">
                <span class="label">合规状态：</span>
                <el-tag :type="item.status === 'passed' ? 'success' : 'danger'" size="small">
                  {{ item.status === 'passed' ? '符合' : '不符合' }}
                </el-tag>
              </div>
            </div>

            <div v-if="item.status === 'failed' && item.gap" class="gap-analysis">
              <div class="gap-title">差距分析</div>
              <div class="gap-content">{{ item.gap }}</div>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed, defineProps, defineEmits } from 'vue'
import { ElMessage } from 'element-plus'
import { VideoPlay, Right, InfoFilled } from '@element-plus/icons-vue'

interface PerformanceItem {
  id: string
  name: string
  category: string
  description: string
  baseline: number
  actual?: number
  unit: string
  status: 'pending' | 'passed' | 'warning' | 'failed'
  suggestion?: string
}

interface SecurityItem {
  id: string
  name: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  description: string
  checkItem: string
  actual?: string
  status: 'pending' | 'passed' | 'failed'
  vulnerability?: string
  remediation?: string
}

interface ComplianceItem {
  id: string
  name: string
  standard: string
  clause: string
  requirement: string
  description: string
  status: 'pending' | 'passed' | 'failed'
  gap?: string
}

const props = defineProps<{
  performanceItems: PerformanceItem[]
  securityItems: SecurityItem[]
  complianceItems: ComplianceItem[]
}>()

const emit = defineEmits<{
  (e: 'check'): void
}>()

const activeTab = ref('performance')
const isChecking = ref(false)

const allItems = computed(() => [
  ...props.performanceItems,
  ...props.securityItems,
  ...props.complianceItems
])

const passedCount = computed(() =>
  allItems.value.filter(i => i.status === 'passed').length
)

const warningCount = computed(() =>
  allItems.value.filter(i => i.status === 'warning').length
)

const failedCount = computed(() =>
  allItems.value.filter(i => i.status === 'failed').length
)

const pendingCount = computed(() =>
  allItems.value.filter(i => i.status === 'pending').length
)

const overallStatus = computed(() => {
  if (failedCount.value > 0) return { type: 'danger', label: '存在失败项' }
  if (warningCount.value > 0) return { type: 'warning', label: '存在警告' }
  if (passedCount.value === allItems.value.length && allItems.value.length > 0) {
    return { type: 'success', label: '全部通过' }
  }
  return { type: 'info', label: '待检查' }
})

const statusMap: Record<string, { label: string; type: string }> = {
  pending: { label: '待检查', type: 'info' },
  passed: { label: '通过', type: 'success' },
  warning: { label: '警告', type: 'warning' },
  failed: { label: '失败', type: 'danger' }
}

const severityMap: Record<string, { label: string; type: string }> = {
  low: { label: '低', type: 'info' },
  medium: { label: '中', type: 'warning' },
  high: { label: '高', type: 'danger' },
  critical: { label: '严重', type: 'danger' }
}

const getStatusTag = (status: string) => statusMap[status]?.type || 'info'
const getStatusLabel = (status: string) => statusMap[status]?.label || status
const getSeverityTag = (severity: string) => severityMap[severity]?.type || 'info'
const getSeverityLabel = (severity: string) => severityMap[severity]?.label || severity

const getMetricClass = (item: PerformanceItem) => {
  if (item.actual === undefined) return ''
  const deviation = ((item.actual - item.baseline) / item.baseline) * 100
  if (deviation <= 0) return 'good'
  if (deviation <= 20) return 'acceptable'
  return 'poor'
}

const getDeviationClass = (item: PerformanceItem) => {
  if (item.actual === undefined) return ''
  const deviation = ((item.actual - item.baseline) / item.baseline) * 100
  if (deviation <= 0) return 'good'
  if (deviation <= 20) return 'acceptable'
  return 'poor'
}

const getDeviation = (item: PerformanceItem) => {
  if (item.actual === undefined) return '-'
  const deviation = ((item.actual - item.baseline) / item.baseline) * 100
  const sign = deviation >= 0 ? '+' : ''
  return `${sign}${deviation.toFixed(1)}%`
}

const runCheck = () => {
  isChecking.value = true
  emit('check')
  setTimeout(() => {
    isChecking.value = false
    ElMessage.success('检查完成')
  }, 1000)
}
</script>

<style scoped>
.non-functional-checker {
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

.check-summary {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.summary-card {
  text-align: center;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
}

.card-value {
  font-size: 28px;
  font-weight: bold;
}

.summary-card.passed .card-value {
  color: #67c23a;
}

.summary-card.warning .card-value {
  color: #e6a23c;
}

.summary-card.failed .card-value {
  color: #f56c6c;
}

.summary-card.pending .card-value {
  color: #909399;
}

.card-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.empty-container {
  padding: 20px 0;
}

.check-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.check-item {
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #fff;
  transition: all 0.3s;
}

.check-item.status-pending {
  border-left: 4px solid #909399;
}

.check-item.status-passed {
  border-left: 4px solid #67c23a;
}

.check-item.status-warning {
  border-left: 4px solid #e6a23c;
  background: #fdf6ec;
}

.check-item.status-failed {
  border-left: 4px solid #f56c6c;
  background: #fef0f0;
}

.check-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.check-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.check-name {
  font-weight: 500;
  color: #303133;
}

.check-description {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  margin-bottom: 12px;
}

.check-metrics {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-label {
  font-size: 12px;
  color: #909399;
}

.metric-value {
  font-size: 16px;
  font-weight: 500;
}

.metric-value.baseline {
  color: #409eff;
}

.metric-value.good {
  color: #67c23a;
}

.metric-value.acceptable {
  color: #e6a23c;
}

.metric-value.poor {
  color: #f56c6c;
}

.metric-arrow {
  color: #c0c4cc;
}

.check-suggestion {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-top: 12px;
  padding: 10px;
  background: #ecf5ff;
  border-radius: 6px;
  font-size: 13px;
  color: #409eff;
}

.check-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.detail-item {
  font-size: 13px;
}

.detail-label {
  color: #909399;
}

.text-success {
  color: #67c23a;
}

.text-danger {
  color: #f56c6c;
}

.vulnerability-info {
  margin-top: 12px;
  padding: 12px;
  background: #fef0f0;
  border-radius: 6px;
  border-left: 3px solid #f56c6c;
}

.vuln-title {
  font-weight: 500;
  color: #f56c6c;
  margin-bottom: 8px;
}

.vuln-content {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}

.compliance-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.compliance-item {
  font-size: 13px;
}

.compliance-item .label {
  color: #909399;
}

.gap-analysis {
  margin-top: 12px;
  padding: 12px;
  background: #fdf6ec;
  border-radius: 6px;
  border-left: 3px solid #e6a23c;
}

.gap-title {
  font-weight: 500;
  color: #e6a23c;
  margin-bottom: 8px;
}

.gap-content {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}

.el-divider {
  margin: 20px 0;
}
</style>
