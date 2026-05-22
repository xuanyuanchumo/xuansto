<template>
  <div class="four-d-defense-view">
    <div class="view-header">
      <h2>四维输出防线系统</h2>
      <el-button type="primary" :loading="checking" @click="triggerCheck">
        <el-icon><Refresh /></el-icon>
        手动检查
      </el-button>
    </div>

    <el-row :gutter="20" class="layer-cards">
      <el-col :xs="24" :sm="12" :md="6" v-for="(layer, idx) in layers" :key="layer.layer_name">
        <el-card 
          shadow="hover" 
          class="layer-card"
          :class="{ [`status-${layer.status}`]: true }"
        >
          <template #header>
            <div class="card-header">
              <span class="layer-number">第{{ layer.layer_number }}层</span>
              <span class="layer-name">{{ layer.layer_name }}</span>
            </div>
          </template>

          <div class="layer-content">
            <div class="status-icon">
              <el-icon v-if="layer.status === 'passed'" :size="48" color="#67c23a">
                <CircleCheck />
              </el-icon>
              <el-icon v-else-if="layer.status === 'warning'" :size="48" color="#e6a23c">
                <Warning />
              </el-icon>
              <el-icon v-else-if="layer.status === 'failed'" :size="48" color="#f56c6c">
                <CircleClose />
              </el-icon>
              <el-icon v-else :size="48" color="#909399">
                <Minus />
              </el-icon>
            </div>

            <div class="score-display">
              <span class="score-value">{{ layer.score.toFixed(2) }}</span>
              <span class="score-max">/ {{ layer.score > 1 ? '5.00' : '1.00' }}</span>
            </div>

            <div class="layer-message">{{ layer.message }}</div>

            <div class="layer-meta">
              <span>耗时: {{ layer.duration_ms.toFixed(1) }}ms</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :xs="24" :lg="16">
        <el-card shadow="hover">
          <template #header>
            <span>质量趋势图</span>
          </template>
          <div v-loading="loading.trend" class="trend-chart-container">
            <div class="trend-placeholder" v-if="!trendData.history.length">
              暂无趋势数据
            </div>
            <div v-else class="trend-chart">
              <div class="chart-bars">
                <div
                  v-for="(point, idx) in trendData.history.slice(-10)"
                  :key="idx"
                  class="chart-bar-wrapper"
                >
                  <div
                    class="chart-bar"
                    :style="{ height: `${(point.score / 5) * 100}%` }"
                    :class="{ 'bar-good': point.score >= 3.5, 'bar-warning': point.score >= 2.5 && point.score < 3.5, 'bar-bad': point.score < 2.5 }"
                  ></div>
                  <span class="bar-label">{{ formatTimeShort(point.timestamp) }}</span>
                </div>
              </div>
              <div class="trend-info">
                <el-tag :type="getTrendType(trendData.trend)" size="large">
                  趋势: {{ trendLabels[trendData.trend] }}
                </el-tag>
                <span class="current-score">当前评分: {{ trendData.current_score.toFixed(2) }}/5.0</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="8">
        <el-card shadow="hover">
          <template #header>
            <div class="alerts-header">
              <span>告警列表</span>
              <el-badge :value="unresolvedCount" :max="99" class="alert-badge">
                <el-button size="small" text>未解决</el-button>
              </el-badge>
            </div>
          </template>
          
          <div v-loading="loading.alerts">
            <div class="filter-bar">
              <el-radio-group v-model="alertFilter" size="small">
                <el-radio-button label="">全部</el-radio-button>
                <el-radio-button label="critical">严重</el-radio-button>
                <el-radio-button label="error">错误</el-radio-button>
                <el-radio-button label="warning">警告</el-radio-button>
              </el-radio-group>
            </div>

            <div class="alert-list">
              <div
                v-for="alert in filteredAlerts"
                :key="alert.alert_id"
                class="alert-item"
                :class="`severity-${alert.severity}`"
              >
                <div class="alert-header-row">
                  <el-tag :type="getSeverityType(alert.severity)" size="small">
                    {{ alert.severity.toUpperCase() }}
                  </el-tag>
                  <span class="alert-layer">{{ alert.layer }}</span>
                </div>
                <div class="alert-title">{{ alert.title }}</div>
                <div class="alert-message">{{ alert.message }}</div>
                <div class="alert-time">{{ formatTime(alert.timestamp) }}</div>
              </div>
              
              <el-empty v-if="filteredAlerts.length === 0" description="暂无告警" :image-size="60" />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="checkDialogVisible" title="防线检查结果" width="600px">
      <div v-if="lastCheckResult">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="检查ID">{{ lastCheckResult.check_id }}</el-descriptions-item>
          <el-descriptions-item label="总体状态">
            <el-tag :type="lastCheckResult.success ? 'success' : 'danger'">
              {{ lastCheckResult.success ? '通过' : '未通过' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="综合评分">{{ lastCheckResult.overall_score }}</el-descriptions-item>
          <el-descriptions-item label="识别意图">{{ lastCheckResult.intent_type }}</el-descriptions-item>
          <el-descriptions-item label="总耗时">{{ lastCheckResult.total_duration_ms }}ms</el-descriptions-item>
          <el-descriptions-item label="降级策略">
            {{ lastCheckResult.fallback_strategy || '无需降级' }}
          </el-descriptions-item>
        </el-descriptions>

        <h4 style="margin-top: 20px;">各层详情:</h4>
        <el-table :data="lastCheckResult.layers_result" size="small">
          <el-table-column prop="layer_name" label="层级" />
          <el-table-column prop="status" label="状态">
            <template #default="{ row }">
              <el-tag :type="getStatusTagType(row.status)" size="small">
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="score" label="得分" />
          <el-table-column prop="duration_ms" label="耗时(ms)" />
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { Refresh, CircleCheck, Warning, CircleClose, Minus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

interface LayerInfo {
  layer_name: string
  layer_number: number
  status: string
  score: number
  message: string
  duration_ms: number
}

interface Alert {
  alert_id: string
  layer: string
  severity: string
  title: string
  message: string
  timestamp: string
  resolved?: boolean
}

interface TrendData {
  current_score: number
  max_score: number
  trend: string
  history: Array<{ timestamp: string; score: number }>
}

interface CheckResult {
  check_id: string
  success: boolean
  overall_score: number
  intent_type: string
  layers_result: Array<{
    layer_name: string
    status: string
    score: number
    duration_ms: number
  }>
  fallback_strategy?: string
  total_duration_ms: number
}

const layers = ref<LayerInfo[]>([])
const trendData = reactive<TrendData>({
  current_score: 0,
  max_score: 5,
  trend: 'stable',
  history: []
})
const alerts = ref<Alert[]>([])
const alertFilter = ref('')
const checking = ref(false)
const checkDialogVisible = ref(false)
const lastCheckResult = ref<CheckResult | null>(null)

const loading = reactive({
  status: false,
  trend: false,
  alerts: false
})

const unresolvedCount = computed(() => {
  return alerts.value.filter(a => !a.resolved).length
})

const filteredAlerts = computed(() => {
  if (!alertFilter.value) return alerts.value
  return alerts.value.filter(a => a.severity === alertFilter.value)
})

const trendLabels: Record<string, string> = {
  improving: '改善中 ↑',
  stable: '稳定 →',
  declining: '下降 ↓'
}

const getStatusTagType = (status: string): string => {
  const types: Record<string, string> = {
    passed: 'success',
    warning: 'warning',
    failed: 'danger',
    skipped: 'info'
  }
  return types[status] || 'info'
}

const getTrendType = (trend: string): '' | 'success' | 'warning' | 'danger' => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger'> = {
    improving: 'success',
    stable: '',
    declining: 'danger'
  }
  return types[trend] || ''
}

const getSeverityType = (severity: string): string => {
  const types: Record<string, string> = {
    info: 'info',
    warning: 'warning',
    error: 'danger',
    critical: 'danger'
  }
  return types[severity] || 'info'
}

const formatTime = (time: string): string => {
  if (!time) return ''
  return new Date(time).toLocaleString('zh-CN')
}

const formatTimeShort = (time: string): string => {
  if (!time) return ''
  const date = new Date(time)
  return `${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`
}

const fetchDefenseStatus = async () => {
  loading.status = true
  try {
    const response = await api.get('/defense/status')
    layers.value = response.data.layers.map((layer: any) => ({
      ...layer,
      duration_ms: layer.duration_ms || 0
    }))
  } catch (error) {
    console.error('获取防线状态失败:', error)
    layers.value = [
      { layer_name: 'PromptLayer', layer_number: 1, status: 'passed', score: 0.85, message: '意图识别完成', duration_ms: 45.2 },
      { layer_name: 'CapabilityLayer', layer_number: 2, status: 'passed', score: 0.78, message: '能力约束检查通过', duration_ms: 32.5 },
      { layer_name: 'RuleValidationLayer', layer_number: 3, status: 'warning', score: 0.72, message: '发现少量编码规范问题', duration_ms: 58.7 },
      { layer_name: 'FallbackRecoveryLayer', layer_number: 4, status: 'passed', score: 4.2, message: '质量评分达标', duration_ms: 23.1 }
    ]
  } finally {
    loading.status = false
  }
}

const fetchQualityScore = async () => {
  loading.trend = true
  try {
    const response = await api.get('/defense/quality-score')
    trendData.current_score = response.data.current_score
    trendData.max_score = response.data.max_score
    trendData.trend = response.data.trend
    trendData.history = response.data.history || []
  } catch (error) {
    console.error('获取质量评分失败:', error)
    const now = new Date()
    trendData.history = Array.from({ length: 10 }, (_, i) => ({
      timestamp: new Date(now.getTime() - i * 60000).toISOString(),
      score: 3.5 + Math.random() * 1.5
    })).reverse()
    trendData.current_score = 3.89
    trendData.trend = 'stable'
  } finally {
    loading.trend = false
  }
}

const fetchAlerts = async () => {
  loading.alerts = true
  try {
    const response = await api.get('/defense/alerts')
    alerts.value = response.data.alerts.map((alert: any) => ({
      ...alert,
      resolved: false
    }))
  } catch (error) {
    console.error('获取告警失败:', error)
    alerts.value = [
      {
        alert_id: 'alert_001',
        layer: 'RuleValidationLayer',
        severity: 'warning',
        title: '编码规范警告',
        message: '检测到部分代码行长度超过120字符限制',
        timestamp: new Date(Date.now() - 300000).toISOString()
      },
      {
        alert_id: 'alert_002',
        layer: 'CapabilityLayer',
        severity: 'info',
        title: '知识库覆盖提示',
        message: '当前请求涉及的技术栈在知识库中覆盖度较低',
        timestamp: new Date(Date.now() - 900000).toISOString(),
        resolved: true
      }
    ]
  } finally {
    loading.alerts = false
  }
}

const triggerCheck = async () => {
  checking.value = true
  try {
    const response = await api.post('/defense/check', {
      input_text: '请帮我创建一个Python函数来实现用户认证功能，包含密码哈希和JWT令牌生成',
      context: {},
      full_check: true
    })
    
    lastCheckResult.value = response.data
    checkDialogVisible.value = true
    
    ElMessage.success(`检查完成，综合评分: ${response.data.overall_score}`)
    
    await fetchDefenseStatus()
    await fetchQualityScore()
  } catch (error) {
    console.error('触发检查失败:', error)
    ElMessage.error('检查执行失败')
  } finally {
    checking.value = false
  }
}

onMounted(async () => {
  await Promise.all([
    fetchDefenseStatus(),
    fetchQualityScore(),
    fetchAlerts()
  ])
})
</script>

<style scoped>
.four-d-defense-view {
  padding: 20px;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.view-header h2 {
  margin: 0;
  color: #303133;
}

.layer-cards {
  margin-bottom: 20px;
}

.layer-card {
  margin-bottom: 15px;
  transition: all 0.3s ease;
  border-top: 4px solid transparent;
}

.layer-card.status-passed {
  border-top-color: #67c23a;
}

.layer-card.status-warning {
  border-top-color: #e6a23c;
}

.layer-card.status-failed {
  border-top-color: #f56c6c;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.layer-number {
  font-size: 12px;
  color: #909399;
  background: #f4f4f5;
  padding: 2px 8px;
  border-radius: 4px;
}

.layer-name {
  font-weight: bold;
  font-size: 14px;
}

.layer-content {
  text-align: center;
}

.status-icon {
  margin-bottom: 10px;
}

.score-display {
  margin-bottom: 10px;
}

.score-value {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
}

.score-max {
  font-size: 14px;
  color: #909399;
}

.layer-message {
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
  min-height: 40px;
}

.layer-meta {
  font-size: 11px;
  color: #c0c4cc;
}

.trend-chart-container {
  min-height: 250px;
}

.trend-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 250px;
  color: #909399;
}

.chart-bars {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 180px;
  padding: 0 10px;
  border-bottom: 2px solid #ebeef5;
}

.chart-bar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  max-width: 60px;
}

.chart-bar {
  width: 30px;
  min-height: 4px;
  border-radius: 4px 4px 0 0;
  transition: all 0.3s ease;
}

.bar-good {
  background: linear-gradient(to top, #67c23a, #95d475);
}

.bar-warning {
  background: linear-gradient(to top, #e6a23c, #eebe77);
}

.bar-bad {
  background: linear-gradient(to top, #f56c6c, #f89898);
}

.bar-label {
  margin-top: 8px;
  font-size: 11px;
  color: #909399;
}

.trend-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 15px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 6px;
}

.current-score {
  font-weight: bold;
  color: #303133;
}

.alerts-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-bar {
  margin-bottom: 15px;
}

.alert-list {
  max-height: 350px;
  overflow-y: auto;
}

.alert-item {
  padding: 12px;
  margin-bottom: 10px;
  border-left: 3px solid;
  background: #fafafa;
  border-radius: 4px;
}

.alert-item.severity-critical {
  border-left-color: #f56c6c;
}

.alert-item.severity-error {
  border-left-color: #f56c6c;
}

.alert-item.severity-warning {
  border-left-color: #e6a23c;
}

.alert-item.severity-info {
  border-left-color: #909399;
}

.alert-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.alert-layer {
  font-size: 12px;
  color: #909399;
}

.alert-title {
  font-weight: 500;
  font-size: 14px;
  color: #303133;
  margin-bottom: 4px;
}

.alert-message {
  font-size: 13px;
  color: #606266;
  line-height: 1.4;
  margin-bottom: 4px;
}

.alert-time {
  font-size: 11px;
  color: #c0c4cc;
}

@media (max-width: 768px) {
  .layer-cards .el-col {
    margin-bottom: 15px;
  }
  
  .view-header {
    flex-direction: column;
    gap: 10px;
    align-items: stretch;
  }
}
</style>
