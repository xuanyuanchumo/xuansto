<template>
  <el-card class="acceptance-test-runner" shadow="hover">
    <template #header>
      <div class="card-header">
        <span class="title">验收测试</span>
        <div class="header-actions">
          <el-tag :type="overallStatus.type" size="small">
            {{ overallStatus.label }}
          </el-tag>
          <el-button type="primary" size="small" @click="runAllTests" :loading="isRunning">
            <el-icon><VideoPlay /></el-icon>
            执行全部测试
          </el-button>
        </div>
      </div>
    </template>

    <div class="test-summary">
      <div class="summary-stats">
        <div class="stat-item passed">
          <div class="stat-value">{{ passedCount }}</div>
          <div class="stat-label">通过</div>
        </div>
        <div class="stat-item failed">
          <div class="stat-value">{{ failedCount }}</div>
          <div class="stat-label">失败</div>
        </div>
        <div class="stat-item pending">
          <div class="stat-value">{{ pendingCount }}</div>
          <div class="stat-label">待执行</div>
        </div>
        <div class="stat-item total">
          <div class="stat-value">{{ totalCount }}</div>
          <div class="stat-label">总计</div>
        </div>
      </div>
      <el-progress
        :percentage="progressPercentage"
        :status="progressStatus"
        :stroke-width="12"
      />
    </div>

    <el-divider />

    <div v-if="!scenarios || scenarios.length === 0" class="empty-container">
      <el-empty description="暂无BDD场景" :image-size="80" />
    </div>

    <div v-else class="scenarios-list">
      <div
        v-for="(scenario, index) in scenarios"
        :key="scenario.id || index"
        class="scenario-item"
        :class="'status-' + scenario.status"
      >
        <div class="scenario-header">
          <div class="scenario-meta">
            <el-tag :type="getScenarioTypeTag(scenario.status)" size="small">
              {{ getScenarioStatusLabel(scenario.status) }}
            </el-tag>
            <span class="scenario-name">{{ scenario.name }}</span>
          </div>
          <div class="scenario-actions">
            <el-button
              type="primary"
              link
              size="small"
              @click="runSingleTest(scenario)"
              :loading="scenario.running"
            >
              执行
            </el-button>
            <el-button
              v-if="scenario.status === 'passed' || scenario.status === 'failed'"
              type="primary"
              link
              size="small"
              @click="viewResult(scenario)"
            >
              查看结果
            </el-button>
          </div>
        </div>

        <div class="bdd-content">
          <div class="bdd-line">
            <span class="keyword">Scenario:</span>
            <span>{{ scenario.name }}</span>
          </div>
          <div class="bdd-line">
            <span class="keyword">Given</span>
            <span>{{ scenario.given }}</span>
          </div>
          <div class="bdd-line">
            <span class="keyword">When</span>
            <span>{{ scenario.when }}</span>
          </div>
          <div class="bdd-line">
            <span class="keyword">Then</span>
            <span>{{ scenario.then }}</span>
          </div>
        </div>

        <div v-if="scenario.status === 'failed' && scenario.error" class="error-section">
          <div class="error-title">
            <el-icon><WarningFilled /></el-icon>
            错误信息
          </div>
          <div class="error-content">{{ scenario.error }}</div>
        </div>

        <div v-if="scenario.status === 'passed' && scenario.shadowResult" class="shadow-section">
          <div class="shadow-title">
            <el-icon><Hide /></el-icon>
            影子验证对比
          </div>
          <div class="shadow-comparison">
            <div class="comparison-item">
              <span class="label">预期结果：</span>
              <span>{{ scenario.shadowResult.expected }}</span>
            </div>
            <div class="comparison-item">
              <span class="label">实际结果：</span>
              <span>{{ scenario.shadowResult.actual }}</span>
            </div>
            <div class="comparison-item">
              <span class="label">匹配状态：</span>
              <el-tag :type="scenario.shadowResult.matched ? 'success' : 'danger'" size="small">
                {{ scenario.shadowResult.matched ? '匹配' : '不匹配' }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="resultDialogVisible" title="测试结果详情" width="600px">
      <div v-if="currentResult" class="result-detail">
        <div class="result-header">
          <el-tag :type="getScenarioTypeTag(currentResult.status)" size="large">
            {{ getScenarioStatusLabel(currentResult.status) }}
          </el-tag>
          <span class="result-name">{{ currentResult.name }}</span>
        </div>

        <div class="result-section">
          <div class="section-title">执行信息</div>
          <div class="info-grid">
            <div class="info-item">
              <span class="label">开始时间：</span>
              <span>{{ formatTime(currentResult.startTime) }}</span>
            </div>
            <div class="info-item">
              <span class="label">结束时间：</span>
              <span>{{ formatTime(currentResult.endTime) }}</span>
            </div>
            <div class="info-item">
              <span class="label">执行耗时：</span>
              <span>{{ currentResult.duration }}ms</span>
            </div>
          </div>
        </div>

        <div v-if="currentResult.steps && currentResult.steps.length > 0" class="result-section">
          <div class="section-title">执行步骤</div>
          <el-steps direction="vertical" :active="currentResult.steps.length">
            <el-step
              v-for="(step, index) in currentResult.steps"
              :key="index"
              :title="step.name"
              :status="step.status === 'passed' ? 'success' : step.status === 'failed' ? 'error' : 'process'"
            >
              <template #description>
                <div v-if="step.error" class="step-error">{{ step.error }}</div>
              </template>
            </el-step>
          </el-steps>
        </div>

        <div v-if="currentResult.shadowResult" class="result-section">
          <div class="section-title">影子验证结果</div>
          <div class="shadow-result">
            <div class="shadow-row">
              <span class="label">预期输出：</span>
              <pre>{{ currentResult.shadowResult.expected }}</pre>
            </div>
            <div class="shadow-row">
              <span class="label">实际输出：</span>
              <pre>{{ currentResult.shadowResult.actual }}</pre>
            </div>
            <div class="shadow-row">
              <span class="label">差异分析：</span>
              <pre>{{ currentResult.shadowResult.diff || '无差异' }}</pre>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed, defineProps, defineEmits } from 'vue'
import { ElMessage } from 'element-plus'
import { VideoPlay, WarningFilled, Hide } from '@element-plus/icons-vue'

interface ShadowResult {
  expected: string
  actual: string
  matched: boolean
  diff?: string
}

interface TestStep {
  name: string
  status: 'passed' | 'failed' | 'pending'
  error?: string
}

interface Scenario {
  id?: string
  name: string
  given: string
  when: string
  then: string
  status: 'pending' | 'passed' | 'failed' | 'running'
  running?: boolean
  error?: string
  shadowResult?: ShadowResult
  startTime?: string
  endTime?: string
  duration?: number
  steps?: TestStep[]
}

const props = defineProps<{
  scenarios: Scenario[]
}>()

const emit = defineEmits<{
  (e: 'runAll'): void
  (e: 'runSingle', scenarioId: string | number): void
  (e: 'viewResult', scenario: Scenario): void
}>()

const isRunning = ref(false)
const resultDialogVisible = ref(false)
const currentResult = ref<Scenario | null>(null)

const passedCount = computed(() =>
  props.scenarios.filter(s => s.status === 'passed').length
)

const failedCount = computed(() =>
  props.scenarios.filter(s => s.status === 'failed').length
)

const pendingCount = computed(() =>
  props.scenarios.filter(s => s.status === 'pending').length
)

const totalCount = computed(() => props.scenarios.length)

const progressPercentage = computed(() => {
  if (totalCount.value === 0) return 0
  const completed = passedCount.value + failedCount.value
  return Math.round((completed / totalCount.value) * 100)
})

const progressStatus = computed(() => {
  if (failedCount.value > 0) return 'exception'
  if (passedCount.value === totalCount.value) return 'success'
  return ''
})

const overallStatus = computed(() => {
  if (failedCount.value > 0) return { type: 'danger', label: '存在失败' }
  if (passedCount.value === totalCount.value && totalCount.value > 0) return { type: 'success', label: '全部通过' }
  if (passedCount.value > 0) return { type: 'warning', label: '部分通过' }
  return { type: 'info', label: '待执行' }
})

const statusMap: Record<string, { label: string; type: string }> = {
  pending: { label: '待执行', type: 'info' },
  running: { label: '执行中', type: 'warning' },
  passed: { label: '通过', type: 'success' },
  failed: { label: '失败', type: 'danger' }
}

const getScenarioTypeTag = (status: string) => statusMap[status]?.type || 'info'
const getScenarioStatusLabel = (status: string) => statusMap[status]?.label || status

const formatTime = (time?: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const runAllTests = () => {
  isRunning.value = true
  emit('runAll')
  setTimeout(() => {
    isRunning.value = false
    ElMessage.success('测试执行完成')
  }, 1000)
}

const runSingleTest = (scenario: Scenario) => {
  emit('runSingle', scenario.id || scenario.name)
}

const viewResult = (scenario: Scenario) => {
  currentResult.value = scenario
  resultDialogVisible.value = true
  emit('viewResult', scenario)
}
</script>

<style scoped>
.acceptance-test-runner {
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

.test-summary {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.summary-stats {
  display: flex;
  justify-content: space-around;
  margin-bottom: 16px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
}

.stat-item.passed .stat-value {
  color: #67c23a;
}

.stat-item.failed .stat-value {
  color: #f56c6c;
}

.stat-item.pending .stat-value {
  color: #e6a23c;
}

.stat-item.total .stat-value {
  color: #409eff;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.empty-container {
  padding: 20px 0;
}

.scenarios-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: 500px;
  overflow-y: auto;
}

.scenario-item {
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #fff;
  transition: all 0.3s;
}

.scenario-item.status-pending {
  border-left: 4px solid #909399;
}

.scenario-item.status-running {
  border-left: 4px solid #e6a23c;
  background: #fdf6ec;
}

.scenario-item.status-passed {
  border-left: 4px solid #67c23a;
}

.scenario-item.status-failed {
  border-left: 4px solid #f56c6c;
  background: #fef0f0;
}

.scenario-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.scenario-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.scenario-name {
  font-weight: 500;
  color: #303133;
}

.scenario-actions {
  display: flex;
  gap: 8px;
}

.bdd-content {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
  font-family: 'Consolas', monospace;
  font-size: 13px;
}

.bdd-line {
  margin-bottom: 4px;
  line-height: 1.6;
}

.bdd-line:last-child {
  margin-bottom: 0;
}

.bdd-line .keyword {
  color: #409eff;
  font-weight: bold;
  margin-right: 8px;
}

.error-section {
  margin-top: 12px;
  padding: 12px;
  background: #fef0f0;
  border-radius: 6px;
  border-left: 3px solid #f56c6c;
}

.error-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
  color: #f56c6c;
  margin-bottom: 8px;
}

.error-content {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  white-space: pre-wrap;
}

.shadow-section {
  margin-top: 12px;
  padding: 12px;
  background: #ecf5ff;
  border-radius: 6px;
  border-left: 3px solid #409eff;
}

.shadow-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
  color: #409eff;
  margin-bottom: 10px;
}

.shadow-comparison {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.comparison-item {
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.comparison-item .label {
  color: #909399;
}

.result-detail {
  padding: 10px 0;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.result-name {
  font-weight: 500;
  font-size: 16px;
}

.result-section {
  margin-bottom: 20px;
}

.section-title {
  font-weight: 500;
  font-size: 14px;
  color: #303133;
  margin-bottom: 12px;
  padding-left: 10px;
  border-left: 3px solid #409eff;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.info-item {
  font-size: 13px;
}

.info-item .label {
  color: #909399;
}

.step-error {
  color: #f56c6c;
  font-size: 12px;
  margin-top: 4px;
}

.shadow-result {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.shadow-row {
  margin-bottom: 12px;
}

.shadow-row:last-child {
  margin-bottom: 0;
}

.shadow-row .label {
  color: #909399;
  font-weight: 500;
}

.shadow-row pre {
  margin: 8px 0 0 0;
  padding: 8px;
  background: #fff;
  border-radius: 4px;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
}

.el-divider {
  margin: 20px 0;
}
</style>
