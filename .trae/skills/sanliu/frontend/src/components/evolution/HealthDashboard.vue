<template>
  <div class="health-dashboard">
    <el-card class="dashboard-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span class="title">技能健康度仪表板</span>
            <el-tag :type="overallHealthType" effect="dark" size="large">
              {{ overallHealthLabel }}
            </el-tag>
          </div>
          <div class="header-actions">
            <el-button
              type="primary"
              :loading="evaluating"
              @click="runFullEvaluation"
            >
              <el-icon><Refresh /></el-icon>
              全面评估
            </el-button>
            <el-button
              :type="autoRefresh ? 'success' : 'default'"
              @click="toggleAutoRefresh"
            >
              <el-icon><Timer /></el-icon>
              {{ autoRefresh ? '自动刷新中' : '开启自动刷新' }}
            </el-button>
          </div>
        </div>
      </template>

      <div class="dashboard-content">
        <div class="score-overview">
          <div class="main-score">
            <div class="score-circle" :class="healthLevelClass">
              <div class="score-value">{{ healthData?.overall_score?.toFixed(1) || 0 }}</div>
              <div class="score-label">健康度评分</div>
            </div>
            <div class="score-details">
              <div class="detail-item">
                <span class="detail-label">评估时间</span>
                <span class="detail-value">{{ formatTime(healthData?.evaluated_at) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">下次评估</span>
                <span class="detail-value">{{ formatTime(healthData?.next_evaluation) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">告警数量</span>
                <span class="detail-value alert-count" :class="{ 'has-alerts': alerts.length > 0 }">
                  {{ alerts.length }}
                </span>
              </div>
              <div class="detail-item">
                <span class="detail-label">趋势</span>
                <span class="detail-value trend" :class="trendClass">
                  <el-icon><component :is="trendIcon" /></el-icon>
                  {{ trendLabel }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <el-divider />

        <div class="metrics-section">
          <div class="section-title">健康指标</div>
          <el-row :gutter="16">
            <el-col :span="6" v-for="metric in metricsList" :key="metric.key">
              <div class="metric-card" :class="getMetricCardClass(metric)">
                <div class="metric-header">
                  <el-icon class="metric-icon" :size="24">
                    <component :is="metric.icon" />
                  </el-icon>
                  <span class="metric-name">{{ metric.label }}</span>
                </div>
                <div class="metric-value">{{ formatMetricValue(metric) }}</div>
                <el-progress
                  :percentage="metric.normalized_value || 0"
                  :stroke-width="8"
                  :color="getProgressColor(metric.normalized_value)"
                  :show-text="false"
                />
                <div class="metric-status">
                  <el-tag :type="getMetricStatusType(metric)" size="small">
                    {{ getMetricStatusLabel(metric) }}
                  </el-tag>
                  <span class="metric-change" v-if="metric.change !== undefined" :class="getChangeClass(metric.change)">
                    {{ formatChange(metric.change) }}
                  </span>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>

        <el-divider />

        <div class="alerts-section">
          <div class="section-header">
            <span class="section-title">告警列表</span>
            <el-button
              v-if="alerts.length > 0"
              type="primary"
              link
              @click="clearAllAlerts"
            >
              清除全部
            </el-button>
          </div>
          <div class="alerts-list" v-if="alerts.length > 0">
            <div
              v-for="alert in alerts"
              :key="alert.id"
              class="alert-item"
              :class="`alert-${alert.severity}`"
            >
              <div class="alert-icon">
                <el-icon>
                  <component :is="getAlertIcon(alert.severity)" />
                </el-icon>
              </div>
              <div class="alert-content">
                <div class="alert-title">{{ alert.title }}</div>
                <div class="alert-desc">{{ alert.description }}</div>
                <div class="alert-meta">
                  <span class="meta-item">{{ alert.source }}</span>
                  <span class="meta-item">{{ formatTime(alert.created_at) }}</span>
                </div>
              </div>
              <div class="alert-actions">
                <el-button
                  type="primary"
                  size="small"
                  @click="handleAlert(alert)"
                >
                  处理
                </el-button>
                <el-button
                  type="info"
                  size="small"
                  @click="dismissAlert(alert.id)"
                >
                  忽略
                </el-button>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无告警" :image-size="60" />
        </div>

        <el-divider />

        <div class="trend-section">
          <div class="section-header">
            <span class="section-title">健康度趋势</span>
            <el-radio-group v-model="trendPeriod" size="small" @change="fetchTrendData">
              <el-radio-button label="24h">24小时</el-radio-button>
              <el-radio-button label="7d">7天</el-radio-button>
              <el-radio-button label="30d">30天</el-radio-button>
            </el-radio-group>
          </div>
          <div class="trend-chart" ref="trendChartRef">
            <div v-if="trendLoading" class="chart-loading">
              <el-icon class="is-loading"><Loading /></el-icon>
            </div>
          </div>
        </div>

        <div v-if="healthData?.recommendations?.length" class="recommendations-section">
          <el-divider />
          <div class="section-title">优化建议</div>
          <el-timeline>
            <el-timeline-item
              v-for="(rec, index) in healthData.recommendations"
              :key="index"
              :type="getRecommendationType(rec.priority)"
            >
              <div class="recommendation-item">
                <div class="recommendation-header">
                  <span class="recommendation-title">{{ rec.title }}</span>
                  <el-tag size="small" :type="getRecommendationType(rec.priority)">
                    {{ getPriorityLabel(rec.priority) }}
                  </el-tag>
                </div>
                <div class="recommendation-desc">{{ rec.description }}</div>
                <div class="recommendation-impact" v-if="rec.estimated_impact">
                  预计提升: {{ rec.estimated_impact }}
                </div>
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Refresh,
  Timer,
  Loading,
  CircleCheck,
  CircleClose,
  Warning,
  TrendCharts,
  Timer as TimerIcon,
  Connection,
  Cpu,
  Document,
  Setting,
  DataLine,
  Top,
  Bottom,
  Minus
} from '@element-plus/icons-vue'
import { useWebSocket, ConnectionState } from '@/composables/useWebSocket'
import api from '@/api'

interface HealthMetric {
  key: string
  label: string
  value: number
  unit: string
  normalized_value: number
  threshold: {
    warning: number
    critical: number
  }
  change?: number
  icon: any
}

interface HealthAlert {
  id: number
  title: string
  description: string
  severity: 'info' | 'warning' | 'critical'
  source: string
  created_at: string
}

interface Recommendation {
  title: string
  description: string
  priority: 'high' | 'medium' | 'low'
  category: string
  estimated_impact?: string
}

interface HealthData {
  overall_score: number
  health_level: 'excellent' | 'good' | 'fair' | 'poor' | 'critical'
  evaluated_at: string
  next_evaluation: string
  recommendations: Recommendation[]
}

interface TrendDataPoint {
  timestamp: string
  score: number
}

interface Props {
  skillId?: string
  refreshInterval?: number
}

const props = withDefaults(defineProps<Props>(), {
  refreshInterval: 30000
})

const emit = defineEmits<{
  (e: 'evaluation-complete', data: HealthData): void
  (e: 'alert-handled', alert: HealthAlert): void
  (e: 'error', error: Error): void
}>()

const evaluating = ref(false)
const trendLoading = ref(false)
const autoRefresh = ref(true)
const trendPeriod = ref('7d')
const healthData = ref<HealthData | null>(null)
const metricsList = ref<HealthMetric[]>([])
const alerts = ref<HealthAlert[]>([])
const trendData = ref<TrendDataPoint[]>([])
const trendChartRef = ref<HTMLElement | null>(null)

let echartsInstance: any = null
let echarts: any = null
let refreshTimer: ReturnType<typeof setInterval> | null = null

const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
const wsHost = window.location.host
const wsUrl = `${wsProtocol}//${wsHost}/api/health-dashboard/ws${props.skillId ? `?skill_id=${props.skillId}` : ''}`

const {
  connectionState,
  isConnected,
  connect: wsConnect,
  disconnect: wsDisconnect
} = useWebSocket({
  url: wsUrl,
  heartbeatInterval: 30000,
  onMessage: handleWebSocketMessage
})

const overallHealthType = computed(() => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    excellent: 'success',
    good: 'primary',
    fair: 'warning',
    poor: 'danger',
    critical: 'danger'
  }
  return types[healthData.value?.health_level || 'fair'] || 'info'
})

const overallHealthLabel = computed(() => {
  const labels: Record<string, string> = {
    excellent: '优秀',
    good: '良好',
    fair: '一般',
    poor: '较差',
    critical: '危险'
  }
  return labels[healthData.value?.health_level || 'fair'] || '未知'
})

const healthLevelClass = computed(() => `level-${healthData.value?.health_level || 'fair'}`)

const trendClass = computed(() => {
  if (!healthData.value) return 'trend-stable'
  const score = healthData.value.overall_score
  if (score >= 80) return 'trend-up'
  if (score < 60) return 'trend-down'
  return 'trend-stable'
})

const trendIcon = computed(() => {
  if (!healthData.value) return Minus
  const score = healthData.value.overall_score
  if (score >= 80) return Top
  if (score < 60) return Bottom
  return Minus
})

const trendLabel = computed(() => {
  if (!healthData.value) return '稳定'
  const score = healthData.value.overall_score
  if (score >= 80) return '上升'
  if (score < 60) return '下降'
  return '稳定'
})

const formatTime = (time: string | undefined): string => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const formatMetricValue = (metric: HealthMetric): string => {
  return `${metric.value.toFixed(1)}${metric.unit}`
}

const formatChange = (change: number): string => {
  const prefix = change > 0 ? '+' : ''
  return `${prefix}${change.toFixed(1)}%`
}

const getProgressColor = (value: number | undefined): string => {
  if (value === undefined) return '#909399'
  if (value >= 80) return '#67c23a'
  if (value >= 60) return '#e6a23c'
  return '#f56c6c'
}

const getMetricCardClass = (metric: HealthMetric): string => {
  if (metric.normalized_value >= 80) return 'metric-good'
  if (metric.normalized_value >= 60) return 'metric-fair'
  return 'metric-poor'
}

const getMetricStatusType = (metric: HealthMetric): '' | 'success' | 'warning' | 'danger' | 'info' => {
  if (metric.normalized_value >= 80) return 'success'
  if (metric.normalized_value >= 60) return 'warning'
  return 'danger'
}

const getMetricStatusLabel = (metric: HealthMetric): string => {
  if (metric.normalized_value >= 80) return '良好'
  if (metric.normalized_value >= 60) return '一般'
  return '需改进'
}

const getChangeClass = (change: number): string => {
  if (change > 0) return 'change-up'
  if (change < 0) return 'change-down'
  return 'change-stable'
}

const getAlertIcon = (severity: string) => {
  const icons: Record<string, any> = {
    info: CircleCheck,
    warning: Warning,
    critical: CircleClose
  }
  return icons[severity] || Warning
}

const getRecommendationType = (priority: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    high: 'danger',
    medium: 'warning',
    low: 'info'
  }
  return types[priority] || 'info'
}

const getPriorityLabel = (priority: string): string => {
  const labels: Record<string, string> = {
    high: '高优先级',
    medium: '中优先级',
    low: '低优先级'
  }
  return labels[priority] || priority
}

const fetchHealthData = async () => {
  try {
    const url = props.skillId
      ? `/health-dashboard/${props.skillId}`
      : '/health-dashboard/current'
    const response = await api.get(url)
    healthData.value = response.health
    metricsList.value = response.metrics || []
    alerts.value = response.alerts || []
  } catch (error) {
    console.error('Failed to fetch health data:', error)
    emit('error', error as Error)
  }
}

const runFullEvaluation = async () => {
  evaluating.value = true
  try {
    const url = props.skillId
      ? `/health-dashboard/${props.skillId}/evaluate`
      : '/health-dashboard/evaluate'
    const response = await api.post(url)
    healthData.value = response.health
    metricsList.value = response.metrics || []
    ElMessage.success('健康度评估完成')
    emit('evaluation-complete', healthData.value)
    await fetchTrendData()
  } catch (error) {
    console.error('Failed to run evaluation:', error)
    ElMessage.error('健康度评估失败')
    emit('error', error as Error)
  } finally {
    evaluating.value = false
  }
}

const fetchTrendData = async () => {
  trendLoading.value = true
  try {
    const params: Record<string, any> = { period: trendPeriod.value }
    if (props.skillId) {
      params.skill_id = props.skillId
    }
    const response = await api.get('/health-dashboard/trends', { params })
    trendData.value = response || []
    await nextTick()
    if (!echartsInstance) {
      await initChart()
    }
    updateChart()
  } catch (error) {
    console.error('Failed to fetch trend data:', error)
  } finally {
    trendLoading.value = false
  }
}

const initChart = async () => {
  if (!trendChartRef.value) return
  try {
    if (!echarts) {
      echarts = await import('echarts')
    }
    if (echartsInstance) {
      echartsInstance.dispose()
    }
    echartsInstance = echarts.init(trendChartRef.value)
  } catch (error) {
    console.error('Failed to initialize chart:', error)
  }
}

const updateChart = () => {
  if (!echartsInstance || !trendData.value.length) return

  const times = trendData.value.map(d => {
    const date = new Date(d.timestamp)
    if (trendPeriod.value === '24h') {
      return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    }
    return date.toLocaleDateString('zh-CN')
  })
  const scores = trendData.value.map(d => d.score)

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const point = params[0]
        return `${point.name}<br/>健康度: ${point.value.toFixed(1)}`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: times,
      axisLine: { lineStyle: { color: '#ccc' } },
      axisLabel: { color: '#666' }
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLine: { lineStyle: { color: '#ccc' } },
      axisLabel: { color: '#666' },
      splitLine: { lineStyle: { color: '#eee' } }
    },
    series: [
      {
        name: '健康度',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        itemStyle: { color: '#409eff' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
              { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
            ]
          }
        },
        data: scores
      }
    ]
  }

  echartsInstance.setOption(option)
}

const handleAlert = async (alert: HealthAlert) => {
  try {
    await api.post(`/health-dashboard/alerts/${alert.id}/handle`)
    alerts.value = alerts.value.filter(a => a.id !== alert.id)
    ElMessage.success('告警已处理')
    emit('alert-handled', alert)
  } catch (error) {
    console.error('Failed to handle alert:', error)
    ElMessage.error('处理失败')
  }
}

const dismissAlert = async (id: number) => {
  try {
    await api.post(`/health-dashboard/alerts/${id}/dismiss`)
    alerts.value = alerts.value.filter(a => a.id !== id)
    ElMessage.success('告警已忽略')
  } catch (error) {
    console.error('Failed to dismiss alert:', error)
  }
}

const clearAllAlerts = async () => {
  try {
    await api.post('/health-dashboard/alerts/clear-all')
    alerts.value = []
    ElMessage.success('所有告警已清除')
  } catch (error) {
    console.error('Failed to clear alerts:', error)
    ElMessage.error('清除失败')
  }
}

const toggleAutoRefresh = () => {
  autoRefresh.value = !autoRefresh.value
  if (autoRefresh.value) {
    startAutoRefresh()
    ElMessage.success('已开启自动刷新')
  } else {
    stopAutoRefresh()
    ElMessage.info('已关闭自动刷新')
  }
}

const handleWebSocketMessage = (data: any) => {
  switch (data.type) {
    case 'health_update':
      healthData.value = data.data.health
      metricsList.value = data.data.metrics || []
      break
    case 'new_alert':
      alerts.value.unshift(data.data)
      ElMessage.warning(`新告警: ${data.data.title}`)
      break
    case 'metric_update':
      const metric = metricsList.value.find(m => m.key === data.data.key)
      if (metric) {
        metric.value = data.data.value
        metric.normalized_value = data.data.normalized_value
        metric.change = data.data.change
      }
      break
  }
}

const handleResize = () => {
  if (echartsInstance) {
    echartsInstance.resize()
  }
}

const startAutoRefresh = () => {
  if (autoRefresh.value && !refreshTimer && !isConnected.value) {
    refreshTimer = setInterval(fetchHealthData, props.refreshInterval)
  }
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

onMounted(async () => {
  await fetchHealthData()
  await fetchTrendData()
  wsConnect()
  if (autoRefresh.value) {
    startAutoRefresh()
  }
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  wsDisconnect()
  stopAutoRefresh()
  if (echartsInstance) {
    echartsInstance.dispose()
    echartsInstance = null
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.health-dashboard {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title {
  font-size: 18px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.dashboard-content {
  padding: 10px 0;
}

.score-overview {
  padding: 15px 0;
}

.main-score {
  display: flex;
  align-items: center;
  gap: 40px;
}

.score-circle {
  width: 160px;
  height: 160px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.score-circle.level-excellent { background: linear-gradient(135deg, #67c23a, #85ce61); }
.score-circle.level-good { background: linear-gradient(135deg, #409eff, #66b1ff); }
.score-circle.level-fair { background: linear-gradient(135deg, #e6a23c, #ebb563); }
.score-circle.level-poor { background: linear-gradient(135deg, #f56c6c, #f78989); }
.score-circle.level-critical { background: linear-gradient(135deg, #f56c6c, #c45656); }

.score-value {
  font-size: 42px;
  font-weight: 700;
}

.score-label {
  font-size: 14px;
  margin-top: 5px;
  opacity: 0.9;
}

.score-details {
  flex: 1;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #ebeef5;
}

.detail-label {
  color: #909399;
}

.detail-value {
  font-weight: 500;
}

.alert-count.has-alerts {
  color: #f56c6c;
}

.trend {
  display: flex;
  align-items: center;
  gap: 4px;
}

.trend-up { color: #67c23a; }
.trend-down { color: #f56c6c; }
.trend-stable { color: #909399; }

.section-title {
  font-weight: 500;
  margin-bottom: 15px;
  color: #303133;
  font-size: 15px;
}

.metrics-section {
  padding: 10px 0;
}

.metric-card {
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.metric-card.metric-good { background: #f0f9eb; border: 1px solid #c2e7b0; }
.metric-card.metric-fair { background: #fdf6ec; border: 1px solid #faecd8; }
.metric-card.metric-poor { background: #fef0f0; border: 1px solid #fbc4c4; }

.metric-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.metric-icon {
  color: #409eff;
}

.metric-name {
  font-size: 13px;
  color: #606266;
}

.metric-value {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 10px;
  color: #303133;
}

.metric-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.metric-change {
  font-size: 12px;
}

.change-up { color: #67c23a; }
.change-down { color: #f56c6c; }
.change-stable { color: #909399; }

.alerts-section {
  padding: 10px 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.alerts-list {
  max-height: 300px;
  overflow-y: auto;
}

.alert-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 10px;
  background: #f5f7fa;
}

.alert-item.alert-info { background: #f4f4f5; border-left: 3px solid #909399; }
.alert-item.alert-warning { background: #fdf6ec; border-left: 3px solid #e6a23c; }
.alert-item.alert-critical { background: #fef0f0; border-left: 3px solid #f56c6c; }

.alert-icon {
  font-size: 20px;
  padding-top: 2px;
}

.alert-item.alert-info .alert-icon { color: #909399; }
.alert-item.alert-warning .alert-icon { color: #e6a23c; }
.alert-item.alert-critical .alert-icon { color: #f56c6c; }

.alert-content {
  flex: 1;
}

.alert-title {
  font-weight: 500;
  margin-bottom: 5px;
}

.alert-desc {
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
}

.alert-meta {
  display: flex;
  gap: 15px;
  font-size: 12px;
  color: #909399;
}

.alert-actions {
  display: flex;
  gap: 8px;
}

.trend-section {
  padding: 10px 0;
}

.trend-chart {
  height: 250px;
  position: relative;
}

.chart-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.recommendations-section {
  margin-top: 15px;
}

.recommendation-item {
  padding: 5px 0;
}

.recommendation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

.recommendation-title {
  font-weight: 500;
}

.recommendation-desc {
  font-size: 13px;
  color: #606266;
  margin-bottom: 5px;
}

.recommendation-impact {
  font-size: 12px;
  color: #67c23a;
}

@media (max-width: 1200px) {
  .main-score {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
