<template>
  <div class="realtime-quality-monitor">
    <el-card class="monitor-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span class="title">实时质量监控面板</span>
            <div class="connection-indicator" :class="connectionClass">
              <span class="dot"></span>
              <span class="label">{{ connectionLabel }}</span>
            </div>
          </div>
          <div class="header-actions">
            <el-select v-model="refreshRate" size="small" style="width: 110px" @change="handleRefreshRateChange">
              <el-option label="1秒" :value="1000" />
              <el-option label="3秒" :value="3000" />
              <el-option label="5秒" :value="5000" />
              <el-option label="10秒" :value="10000" />
            </el-select>
            <el-button
              :type="autoRefresh ? 'success' : 'default'"
              size="small"
              @click="toggleAutoRefresh"
            >
              {{ autoRefresh ? '自动刷新中' : '开启刷新' }}
            </el-button>
            <el-button
              v-if="!isConnected"
              type="warning"
              size="small"
              @click="reconnectWs"
            >
              重连
            </el-button>
          </div>
        </div>
      </template>

      <div class="monitor-content">
        <el-alert
          v-if="showReconnectNotice"
          type="warning"
          show-icon
          closable
          @close="showReconnectNotice = false"
          style="margin-bottom: 16px"
        >
          <template #title>连接已断开，正在尝试重连... (第 {{ reconnectAttempts }} 次)</template>
        </el-alert>

        <div class="metrics-cards">
          <el-row :gutter="16">
            <el-col :xs="12" :sm="6" v-for="metric in qualityMetrics" :key="metric.key">
              <div class="q-metric-card" :class="metric.statusClass">
                <div class="q-metric-icon-wrap">
                  <el-icon :size="28"><component :is="metric.icon" /></el-icon>
                </div>
                <div class="q-metric-body">
                  <div class="q-metric-label">{{ metric.label }}</div>
                  <div class="q-metric-value">{{ metric.displayValue }}</div>
                  <div class="q-metric-trend" :class="metric.trendClass">
                    {{ metric.trendIcon }} {{ metric.trendText }}
                  </div>
                </div>
                <div class="q-metric-sparkline" ref="sparklineRefs">
                  <svg :viewBox="`0 0 ${sparklineWidth} ${sparklineHeight}`" preserveAspectRatio="none" class="spark-svg">
                    <polyline
                      :points="getSparklinePoints(metric.history)"
                      fill="none"
                      :stroke="metric.sparkColor"
                      stroke-width="1.5"
                    />
                  </svg>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>

        <el-divider />

        <div class="radar-section">
          <div class="section-header">
            <span class="section-title">六维质量雷达</span>
            <el-radio-group v-model="radarViewMode" size="small">
              <el-radio-button label="radar">雷达图</el-radio-button>
              <el-radio-button label="bar">柱状图</el-radio-button>
            </el-radio-group>
          </div>
          <div class="radar-container" ref="radarRef">
            <svg :viewBox="`0 0 ${radarSize} ${radarSize}`" class="radar-svg" v-if="radarViewMode === 'radar'">
              <g :transform="`translate(${radarCenter}, ${radarCenter})`">
                <polygon
                  v-for="i in 5"
                  :key="'ring-' + i"
                  :points="getRadarRingPoints(i / 5)"
                  fill="none" stroke="#ebeef5" stroke-width="1"
                />
                <line
                  v-for="(axis, idx) in radarAxes"
                  :key="'axis-' + idx"
                  x1="0" y1="0"
                  :x2="getRadarAxisPoint(idx, 1).x"
                  :y2="getRadarAxisPoint(idx, 1).y"
                  stroke="#ebeef5" stroke-width="1"
                />
                <polygon
                  :points="getRadarDataPoints()"
                  fill="rgba(64,158,255,0.2)"
                  stroke="#409eff"
                  stroke-width="2"
                  stroke-linejoin="round"
                />
                <g v-for="(axis, idx) in radarAxes" :key="'dot-' + idx">
                  <circle
                    :cx="getRadarAxisPoint(idx, getRadarValue(axis.key)).x"
                    :cy="getRadarAxisPoint(idx, getRadarValue(axis.key)).y"
                    r="4"
                    fill="#409eff"
                    stroke="#fff"
                    stroke-width="2"
                  />
                  <text
                    :x="getRadarAxisPoint(idx, 1.18).x"
                    :y="getRadarAxisPoint(idx, 1.18).y"
                    text-anchor="middle"
                    font-size="11"
                    fill="#606266"
                    font-weight="500"
                  >{{ axis.label }}</text>
                </g>
              </g>
            </svg>

            <div v-else class="bar-chart-container">
              <div v-for="(axis, idx) in radarAxes" :key="'bar-' + idx" class="bar-item">
                <div class="bar-label">{{ axis.label }}</div>
                <div class="bar-track">
                  <div class="bar-fill" :style="{ width: `${getRadarValue(axis.key) * 100}%`, background: axis.color }"></div>
                </div>
                <div class="bar-value">{{ (getRadarValue(axis.key) * 100).toFixed(0) }}%</div>
              </div>
            </div>
          </div>
        </div>

        <el-divider />

        <div class="gate-section">
          <div class="section-header">
            <span class="section-title">质量门禁状态</span>
            <el-tag :type="gateStatusType" effect="dark" size="large">
              {{ gateStatusLabel }}
            </el-tag>
          </div>
          <div class="gate-lights">
            <div
              v-for="(criterion, key) in gateCriteria"
              :key="key"
              class="gate-light-item"
            >
              <div class="light-bulb" :class="criterion.passed ? 'bulb-green' : criterion.warning ? 'bulb-yellow' : 'bulb-red'"></div>
              <div class="light-info">
                <span class="light-name">{{ getGateLabel(key) }}</span>
                <span class="light-value" :class="criterion.passed ? 'text-green' : criterion.warning ? 'text-yellow' : 'text-red'">
                  {{ criterion.actual?.toFixed(1) || 0 }}
                  <small>/{{ criterion.threshold || '-' }}</small>
                </span>
              </div>
            </div>
          </div>
        </div>

        <el-divider />

        <div class="trend-section">
          <div class="section-header">
            <span class="section-title">实时趋势图</span>
            <el-radio-group v-model="trendMetric" size="small" @change="switchTrendMetric">
              <el-radio-button label="coverage">覆盖率</el-radio-button>
              <el-radio-button label="complexity">复杂度</el-radio-button>
              <el-radio-button label="pass_rate">通过率</el-radio-button>
              <el-radio-button label="technical_debt">技术债务</el-radio-button>
            </el-radio-group>
          </div>
          <div class="trend-chart-container" ref="trendChartRef">
            <svg :viewBox="`0 0 ${chartWidth} ${chartHeight}`" class="trend-svg" preserveAspectRatio="none">
              <defs>
                <linearGradient :id="'trendGradient-' + trendMetric" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" :stop-color="trendChartColor" stop-opacity="0.3" />
                  <stop offset="100%" :stop-color="trendChartColor" stop-opacity="0.02" />
                </linearGradient>
              </defs>
              <g v-if="trendDataPoints.length > 1">
                <path :d="trendAreaPath" :fill="`url(#trendGradient-${trendMetric})`" />
                <polyline
                  :points="trendLinePoints"
                  fill="none"
                  :stroke="trendChartColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
                <circle
                  v-for="(pt, idx) in visibleTrendPoints"
                  :key="idx"
                  :cx="pt.x"
                  :cy="pt.y"
                  r="3"
                  :fill="trendChartColor"
                  opacity="0.8"
                />
              </g>
              <text v-else x="50%" y="50%" text-anchor="middle" dominant-baseline="middle" fill="#909399" font-size="13">
                等待数据...
              </text>
            </svg>
          </div>
        </div>

        <el-divider />

        <div class="alerts-section">
          <div class="section-header">
            <span class="section-title">实时告警列表</span>
            <el-badge :value="alertsList.length" :hidden="alertsList.length === 0" type="danger">
              <el-button type="primary" link size="small" @click="clearAlerts">清空</el-button>
            </el-badge>
          </div>
          <div class="alerts-scroll" ref="alertsScrollRef">
            <transition-group name="alert-slide" tag="div">
              <div
                v-for="alert in alertsList"
                :key="alert.alert_id"
                class="alert-scroll-item"
                :class="`alert-severity-${alert.severity}`"
              >
                <div class="alert-scroll-icon">
                  <el-icon><component :is="getAlertIcon(alert.severity)" /></el-icon>
                </div>
                <div class="alert-scroll-body">
                  <div class="alert-scroll-title">{{ alert.title }}</div>
                  <div class="alert-scroll-msg">{{ alert.message }}</div>
                  <div class="alert-scroll-meta">
                    <el-tag :type="getAlertTagType(alert.severity)" size="small">{{ alert.metric_type }}</el-tag>
                    <span class="alert-time">{{ formatRelativeTime(alert.timestamp) }}</span>
                  </div>
                </div>
              </div>
            </transition-group>
            <div v-if="alertsList.length === 0" class="no-alerts">
              <el-icon :size="32"><CircleCheck /></el-icon>
              <span>暂无告警，系统运行正常</span>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  CircleCheck,
  DataLine,
  Warning,
  CircleClose,
  Document,
  TrendCharts,
  Timer,
  InfoFilled
} from '@element-plus/icons-vue'
import { useWebSocket, ConnectionState } from '@/composables/useWebSocket'
import { realtimeQualityApi, qualityGateApi, type RealtimeSummary, type QualityGateResult, type QualityAlertItem, type QualityTrendPoint } from '@/api'

const autoRefresh = ref(true)
const refreshRate = ref(5000)
const showReconnectNotice = ref(false)
const summaryData = ref<RealtimeSummary | null>(null)
const gateResult = ref<QualityGateResult | null>(null)
const alertsList = ref<QualityAlertItem[]>([])
const trendHistory = ref<QualityTrendPoint[]>([])

const sparklineWidth = 80
const sparklineHeight = 24
const chartWidth = 800
const chartHeight = 200
const maxTrendPoints = 60

const sparklineRefs = ref<HTMLElement[]>([])
const trendChartRef = ref<HTMLElement | null>(null)
const alertsScrollRef = ref<HTMLElement | null>(null)
const radarRef = ref<HTMLElement | null>(null)

const radarSize = 300
const radarCenter = radarSize / 2
const radarRadius = 100
const radarViewMode = ref<'radar' | 'bar'>('radar')

const radarAxes = [
  { key: 'coverage', label: '覆盖率', color: '#67c23a' },
  { key: 'complexity', label: '复杂度(逆)', color: '#409eff' },
  { key: 'pass_rate', label: '通过率', color: '#e6a23c' },
  { key: 'technical_debt', label: '技术债务(逆)', color: '#f56c6c' },
  { key: 'code_quality', label: '代码质量', color: '#722ed1' },
  { key: 'test_success', label: '测试成功', color: '#13c2c2' },
]

let pollTimer: ReturnType<typeof setInterval> | null = null

const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
const wsUrl = `${wsProtocol}//${window.location.host}/api/quality/realtime`

const {
  connectionState,
  reconnectAttempts,
  isConnected,
  connect: wsConnect,
  disconnect: wsDisconnect,
  reconnect: wsReconnect,
  send: wsSend,
  subscribeMultiple,
  getMetrics
} = useWebSocket({
  url: wsUrl,
  heartbeatInterval: 15000,
  onMessage: handleWsMessage,
  onStateChange: handleWsStateChange
})

const connectionClass = computed(() => {
  switch (connectionState.value) {
    case ConnectionState.CONNECTED: return 'conn-connected'
    case ConnectionState.CONNECTING:
    case ConnectionState.RECONNECTING: return 'conn-connecting'
    default: return 'conn-disconnected'
  }
})

const connectionLabel = computed(() => {
  switch (connectionState.value) {
    case ConnectionState.CONNECTED: return '已连接'
    case ConnectionState.CONNECTING: return '连接中...'
    case ConnectionState.RECONNECTING: return `重连中 (${reconnectAttempts.value})`
    default: return '未连接'
  }
})

const gateCriteria = computed(() => {
  if (!gateResult.value?.criteria) return {}
  return gateResult.value.criteria
})

const gateStatusType = computed(() => {
  const s = gateResult.value?.overall_status
  if (s === 'passed') return 'success'
  if (s === 'warning') return 'warning'
  return 'danger'
})

const gateStatusLabel = computed(() => {
  const labels: Record<string, string> = { passed: '通过', warning: '警告', failed: '未通过', skipped: '跳过' }
  return labels[gateResult.value?.overall_status || ''] || '未知'
})

const trendMetric = ref('coverage')

const qualityMetrics = computed(() => {
  const m = summaryData.value?.key_metrics
  if (!m) return []
  return [
    {
      key: 'coverage',
      label: '覆盖率',
      value: m.coverage,
      unit: '%',
      displayValue: `${m.coverage.toFixed(1)}%`,
      icon: DataLine,
      statusClass: m.coverge >= 80 ? 'metric-good' : m.coverage >= 60 ? 'metric-warning' : 'metric-critical',
      trendIcon: getTrendIcon(m.coverage),
      trendText: getTrendText(m.coverage),
      trendClass: getTrendClass(m.coverage),
      sparkColor: '#67c23a',
      history: trendHistory.value.map(p => p.coverage)
    },
    {
      key: 'complexity',
      label: '复杂度',
      value: m.complexity,
      unit: '',
      displayValue: m.complexity.toFixed(1),
      icon: TrendCharts,
      statusClass: m.complexity <= 10 ? 'metric-good' : m.complexity <= 20 ? 'metric-warning' : 'metric-critical',
      trendIcon: getTrendIconReverse(m.complexity),
      trendText: getTrendTextReverse(m.complexity),
      trendClass: getTrendClassReverse(m.complexity),
      sparkColor: '#409eff',
      history: trendHistory.value.map(p => p.complexity)
    },
    {
      key: 'pass_rate',
      label: '通过率',
      value: m.pass_rate,
      unit: '%',
      displayValue: `${m.pass_rate.toFixed(1)}%`,
      icon: CircleCheck,
      statusClass: m.pass_rate >= 90 ? 'metric-good' : m.pass_rate >= 70 ? 'metric-warning' : 'metric-critical',
      trendIcon: getTrendIcon(m.pass_rate),
      trendText: getTrendText(m.pass_rate),
      trendClass: getTrendClass(m.pass_rate),
      sparkColor: '#e6a23c',
      history: trendHistory.value.map(p => p.pass_rate)
    },
    {
      key: 'technical_debt',
      label: '技术债务',
      value: m.technical_debt,
      unit: 'h',
      displayValue: `${m.technical_debt.toFixed(1)}h`,
      icon: Warning,
      statusClass: m.technical_debt <= 10 ? 'metric-good' : m.technical_debt <= 50 ? 'metric-warning' : 'metric-critical',
      trendIcon: getTrendIconReverse(m.technical_debt),
      trendText: getTrendTextReverse(m.technical_debt),
      trendClass: getTrendClassReverse(m.technical_debt),
      sparkColor: '#f56c6c',
      history: trendHistory.value.map(p => p.technical_debt)
    }
  ]
})

const trendChartColor = computed(() => {
  const colors: Record<string, string> = {
    coverage: '#67c23a', complexity: '#409eff', pass_rate: '#e6a23c', technical_debt: '#f56c6c'
  }
  return colors[trendMetric.value] || '#409eff'
})

const trendDataPoints = computed(() => {
  return trendHistory.value.slice(-maxTrendPoints).map((p, i) => ({
    x: (i / Math.max(maxTrendPoints - 1, 1)) * chartWidth,
    y: normalizeY(p[trendMetric.value as keyof QualityTrendPoint] as number, trendMetric.value)
  }))
})

const visibleTrendPoints = computed(() => {
  if (trendDataPoints.value.length > 30) {
    return trendDataPoints.value.filter((_, i) => i % Math.ceil(trendDataPoints.value.length / 30) === 0)
  }
  return trendDataPoints.value
})

const trendLinePoints = computed(() => {
  return trendDataPoints.value.map(p => `${p.x},${p.y}`).join(' ')
})

const trendAreaPath = computed(() => {
  const pts = trendDataPoints.value
  if (pts.length < 2) return ''
  return `M 0,${chartHeight} L ${pts.map(p => `${p.x},${p.y}`).join(' L ')} L ${pts[pts.length - 1].x},${chartHeight} Z`
})

function normalizeY(value: number, metric: string): number {
  const ranges: Record<string, [number, number]> = {
    coverage: [0, 100], complexity: [0, 50], pass_rate: [0, 100], technical_debt: [0, 200]
  }
  const [min, max] = ranges[metric] || [0, 100]
  return chartHeight - ((value - min) / (max - min)) * chartHeight * 0.85 - chartHeight * 0.05
}

function getSparklinePoints(history: number[]): string {
  if (history.length < 2) return ''
  const minVal = Math.min(...history)
  const maxVal = Math.max(...history)
  const range = maxVal - minVal || 1
  return history.map((v, i) => {
    const x = (i / (history.length - 1)) * sparklineWidth
    const y = sparklineHeight - ((v - minVal) / range) * sparklineHeight * 0.8 - sparklineHeight * 0.1
    return `${x},${y}`
  }).join(' ')
}

function getTrendIcon(val: number): string {
  return val >= 80 ? '↑' : val >= 60 ? '→' : '↓'
}

function getTrendText(val: number): string {
  return val >= 80 ? '优秀' : val >= 60 ? '一般' : '需改进'
}

function getTrendClass(val: number): string {
  return val >= 80 ? 'trend-up' : val >= 60 ? 'trend-stable' : 'trend-down'
}

function getTrendIconReverse(val: number): string {
  return val <= 10 ? '↓' : val <= 20 ? '→' : '↑'
}

function getTrendTextReverse(val: number): string {
  return val <= 10 ? '低' : val <= 20 ? '中等' : '高'
}

function getTrendClassReverse(val: number): string {
  return val <= 10 ? 'trend-up' : val <= 20 ? 'trend-stable' : 'trend-down'
}

function getGateLabel(key: string): string {
  const labels: Record<string, string> = {
    coverage: '覆盖率', complexity: '复杂度', pass_rate: '通过率', technical_debt: '技术债务'
  }
  return labels[key] || key
}

function getRadarValue(key: string): number {
  const m = summaryData.value?.key_metrics
  if (!m) return 0.5
  const valMap: Record<string, () => number> = {
    coverage: () => m.coverage / 100,
    complexity: () => Math.max(0, 1 - m.complexity / 50),
    pass_rate: () => m.pass_rate / 100,
    technical_debt: () => Math.max(0, 1 - m.technical_debt / 100),
    code_quality: () => (m.coverage / 100 + m.pass_rate / 200),
    test_success: () => m.pass_rate / 100,
  }
  return valMap[key]?.() || 0.5
}

function getRadarAxisPoint(index: number, scale: number): { x: number; y: number } {
  const angle = (Math.PI * 2 * index) / radarAxes.length - Math.PI / 2
  return {
    x: Math.cos(angle) * radarRadius * scale,
    y: Math.sin(angle) * radarRadius * scale,
  }
}

function getRadarRingPoints(scale: number): string {
  return radarAxes.map((_, i) => {
    const p = getRadarAxisPoint(i, scale)
    return `${p.x},${p.y}`
  }).join(' ')
}

function getRadarDataPoints(): string {
  return radarAxes.map((axis, i) => {
    const p = getRadarAxisPoint(i, getRadarValue(axis.key))
    return `${p.x},${p.y}`
  }).join(' ')
}

function getAlertIcon(severity: string) {
  const icons: Record<string, any> = { info: InfoFilled, warning: Warning, error: CircleClose, critical: CircleClose }
  return icons[severity] || Warning
}

function getAlertTagType(severity: string): '' | 'success' | 'warning' | 'danger' | 'info' {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = { info: 'info', warning: 'warning', error: 'danger', critical: 'danger' }
  return types[severity] || 'info'
}

function formatTime(time: string | undefined): string {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

function formatRelativeTime(timestamp: string): string {
  const date = new Date(timestamp)
  const diff = Date.now() - date.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  return date.toLocaleTimeString('zh-CN')
}

async function fetchSummary() {
  try {
    const data = await realtimeQualityApi.getRealtimeSummary()
    summaryData.value = data
    addTrendPoint(data)
  } catch (error) {
    console.error('获取实时摘要失败:', error)
  }
}

async function fetchGate() {
  try {
    gateResult.value = await qualityGateApi.check()
  } catch (error) {
    console.error('质量门禁检查失败:', error)
  }
}

async function fetchAll() {
  await Promise.all([fetchSummary(), fetchGate()])
}

function addTrendPoint(summary: RealtimeSummary) {
  const m = summary.key_metrics
  trendHistory.value.push({
    timestamp: summary.timestamp,
    coverage: m.coverage,
    complexity: m.complexity,
    pass_rate: m.pass_rate,
    technical_debt: m.technical_debt
  })
  if (trendHistory.value.length > maxTrendPoints + 10) {
    trendHistory.value = trendHistory.value.slice(-maxTrendPoints)
  }
}

function handleWsMessage(data: any) {
  switch (data.type) {
    case 'quality_update':
      if (data.data) {
        summaryData.value = data.data
        addTrendPoint(data.data)
      }
      break
    case 'gate_update':
      if (data.data) gateResult.value = data.data
      break
    case 'alert':
      if (data.data) {
        alertsList.value.unshift(data.data)
        if (alertsList.value.length > 50) alertsList.value.pop()
        scrollToBottom()
      }
      break
    case 'trend_data':
      if (Array.isArray(data.data)) {
        data.data.forEach((p: QualityTrendPoint) => {
          trendHistory.value.push(p)
        })
        if (trendHistory.value.length > maxTrendPoints + 10) {
          trendHistory.value = trendHistory.value.slice(-maxTrendPoints)
        }
      }
      break
  }
}

function handleWsStateChange(state: ConnectionState) {
  if (state === ConnectionState.DISCONNECTED) {
    showReconnectNotice.value = true
  } else if (state === ConnectionState.CONNECTED) {
    showReconnectNotice.value = false
    subscribeMultiple(['coverage', 'complexity', 'pass_rate', 'technical_debt', 'alert'])
  }
}

function toggleAutoRefresh() {
  autoRefresh.value = !autoRefresh.value
  if (autoRefresh.value) {
    startPolling()
    ElMessage.success('自动刷新已开启')
  } else {
    stopPolling()
    ElMessage.info('自动刷新已关闭')
  }
}

function startPolling() {
  stopPolling()
  fetchAll()
  pollTimer = setInterval(fetchAll, refreshRate.value)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function handleRefreshRateChange() {
  if (autoRefresh.value) {
    startPolling()
  }
}

function reconnectWs() {
  wsReconnect()
}

function switchTrendMetric() {}

function clearAlerts() {
  alertsList.value = []
}

function scrollToBottom() {
  nextTick(() => {
    if (alertsScrollRef.value) {
      alertsScrollRef.value.scrollTop = 0
    }
  })
}

onMounted(async () => {
  await fetchAll()
  wsConnect()
  if (autoRefresh.value) startPolling()
})

onUnmounted(() => {
  wsDisconnect()
  stopPolling()
})
</script>

<style scoped>
.realtime-quality-monitor {
  width: 100%;
}

.monitor-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.title {
  font-size: 18px;
  font-weight: 600;
}

.connection-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  animation: pulse-dot 2s infinite;
}

.conn-connected .dot { background: #67c23a; }
.conn-connecting .dot { background: #e6a23c; animation: blink 0.8s infinite; }
.conn-disconnected .dot { background: #f56c6c; }

.conn-connected .label { color: #67c23a; }
.conn-connecting .label { color: #e6a23c; }
.conn-disconnected .label { color: #f56c6c; }

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.2); }
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.monitor-content {
  padding: 5px 0;
}

.metrics-cards {
  padding: 5px 0;
}

.q-metric-card {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 12px;
  transition: all 0.3s ease;
  overflow: hidden;
}

.q-metric-card.metric-good { background: #f0f9eb; border: 1px solid #e1f3d8; }
.q-metric-card.metric-warning { background: #fdf6ec; border: 1px solid #faecd8; }
.q-metric-card.metric-critical { background: #fef0f0; border: 1px solid #fde2e2; }

.q-metric-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.metric-good .q-metric-icon-wrap { background: linear-gradient(135deg, #67c23a, #85ce61); }
.metric-warning .q-metric-icon-wrap { background: linear-gradient(135deg, #e6a23c, #ebb563); }
.metric-critical .q-metric-icon-wrap { background: linear-gradient(135deg, #f56c6c, #f78989); }

.q-metric-body {
  flex: 1;
  min-width: 0;
}

.q-metric-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.q-metric-value {
  font-size: 22px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}

.q-metric-trend {
  font-size: 11px;
  margin-top: 4px;
}

.trend-up { color: #67c23a; }
.trend-stable { color: #e6a23c; }
.trend-down { color: #f56c6c; }

.q-metric-sparkline {
  position: absolute;
  right: 10px;
  bottom: 8px;
  width: 80px;
  height: 24px;
  opacity: 0.7;
}

.spark-svg {
  width: 100%;
  height: 100%;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
  flex-wrap: wrap;
  gap: 8px;
}

.section-title {
  font-weight: 600;
  font-size: 15px;
  color: #303133;
}

.gate-section {
  padding: 5px 0;
}

.gate-lights {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}

.gate-light-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.light-bulb {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 0 6px currentColor;
}

.bulb-green { background: #67c23a; color: #67c23a; }
.bulb-yellow { background: #e6a23c; color: #e6a23c; }
.bulb-red { background: #f56c6c; color: #f56c6c; }

.light-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.light-name {
  font-size: 12px;
  color: #909399;
}

.light-value {
  font-size: 15px;
  font-weight: 600;
}

.text-green { color: #67c23a; }
.text-yellow { color: #e6a23c; }
.text-red { color: #f56c6c; }

.trend-section {
  padding: 5px 0;
}

.radar-section {
  padding: 5px 0;
}

.radar-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 320px;
}

.radar-svg {
  width: 300px;
  height: 300px;
}

.bar-chart-container {
  width: 100%;
  max-width: 500px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 10px 20px;
}

.bar-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.bar-label {
  width: 90px;
  font-size: 13px;
  font-weight: 500;
  color: #606266;
  text-align: right;
  flex-shrink: 0;
}

.bar-track {
  flex: 1;
  height: 22px;
  background: #f0f2f5;
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.8s ease;
  min-width: 3px;
}

.bar-value {
  width: 42px;
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  text-align: right;
}

.trend-chart-container {
  width: 100%;
  height: 200px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #ebeef5;
}

.trend-svg {
  width: 100%;
  height: 100%;
}

.alerts-section {
  padding: 5px 0;
}

.alerts-scroll {
  max-height: 320px;
  overflow-y: auto;
}

.alert-scroll-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 6px;
  background: #f5f7fa;
  border-left: 3px solid #909399;
}

.alert-scroll-item.alert-severity-info { border-left-color: #909399; background: #f4f4f5; }
.alert-scroll-item.alert-severity-warning { border-left-color: #e6a23c; background: #fdf6ec; }
.alert-scroll-item.alert-severity-error { border-left-color: #f56c6c; background: #fef0f0; }
.alert-scroll-item.alert-severity-critical { border-left-color: #f56c6c; background: #fef0f0; }

.alert-scroll-icon {
  font-size: 18px;
  margin-top: 1px;
  flex-shrink: 0;
}

.alert-scroll-item.alert-severity-info .alert-scroll-icon { color: #909399; }
.alert-scroll-item.alert-severity-warning .alert-scroll-icon { color: #e6a23c; }
.alert-scroll-item.alert-severity-error .alert-scroll-icon { color: #f56c6c; }
.alert-scroll-item.alert-severity-critical .alert-scroll-icon { color: #f56c6c; }

.alert-scroll-body {
  flex: 1;
  min-width: 0;
}

.alert-scroll-title {
  font-weight: 600;
  font-size: 13px;
  color: #303133;
  margin-bottom: 3px;
}

.alert-scroll-msg {
  font-size: 12px;
  color: #606266;
  line-height: 1.4;
  margin-bottom: 5px;
}

.alert-scroll-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.alert-time {
  font-size: 11px;
  color: #909399;
}

.no-alerts {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 32px;
  color: #909399;
  font-size: 14px;
}

.alert-slide-enter-active { transition: all 0.3s ease-out; }
.alert-slide-leave-active { transition: all 0.2s ease-in; }
.alert-slide-enter-from { opacity: 0; transform: translateX(-20px); }
.alert-slide-leave-to { opacity: 0; transform: translateX(20px); }

@media (max-width: 768px) {
  .gate-lights { grid-template-columns: 1fr; }
  .q-metric-value { font-size: 18px; }
  .header-actions { width: 100%; justify-content: flex-end; }
}
</style>
