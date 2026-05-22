<template>
  <div class="realtime-quality-dashboard">
    <el-card class="dashboard-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span class="title">实时质量监控</span>
            <el-tag :type="connectionStatus" effect="dark" size="small">
              {{ connectionLabel }}
            </el-tag>
          </div>
          <div class="header-actions">
            <el-button
              :type="autoRefresh ? 'success' : 'default'"
              size="small"
              @click="toggleAutoRefresh"
            >
              <el-icon><VideoPlay v-if="!autoRefresh" /><VideoPause v-else /></el-icon>
              {{ autoRefresh ? '暂停' : '启动' }}
            </el-button>
            <el-select v-model="refreshInterval" size="small" style="width: 120px; margin-left: 10px;">
              <el-option label="1秒" :value="1000" />
              <el-option label="5秒" :value="5000" />
              <el-option label="10秒" :value="10000" />
              <el-option label="30秒" :value="30000" />
            </el-select>
          </div>
        </div>
      </template>

      <div class="dashboard-content">
        <div class="realtime-metrics">
          <el-row :gutter="16">
            <el-col :span="6">
              <div class="metric-card" :class="cpuStatus">
                <div class="metric-icon cpu">
                  <el-icon :size="32"><Cpu /></el-icon>
                </div>
                <div class="metric-info">
                  <div class="metric-label">CPU使用率</div>
                  <div class="metric-value">{{ realtimeData?.cpu_usage_percent?.toFixed(1) || 0 }}%</div>
                  <el-progress
                    :percentage="realtimeData?.cpu_usage_percent || 0"
                    :stroke-width="6"
                    :color="getProgressColor(realtimeData?.cpu_usage_percent)"
                    :show-text="false"
                  />
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="metric-card" :class="memoryStatus">
                <div class="metric-icon memory">
                  <el-icon :size="32"><Coin /></el-icon>
                </div>
                <div class="metric-info">
                  <div class="metric-label">内存使用率</div>
                  <div class="metric-value">{{ realtimeData?.memory_usage_percent?.toFixed(1) || 0 }}%</div>
                  <el-progress
                    :percentage="realtimeData?.memory_usage_percent || 0"
                    :stroke-width="6"
                    :color="getProgressColor(realtimeData?.memory_usage_percent)"
                    :show-text="false"
                  />
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="metric-card" :class="diskStatus">
                <div class="metric-icon disk">
                  <el-icon :size="32"><Folder /></el-icon>
                </div>
                <div class="metric-info">
                  <div class="metric-label">磁盘使用率</div>
                  <div class="metric-value">{{ realtimeData?.disk_usage_percent?.toFixed(1) || 0 }}%</div>
                  <el-progress
                    :percentage="realtimeData?.disk_usage_percent || 0"
                    :stroke-width="6"
                    :color="getProgressColor(realtimeData?.disk_usage_percent)"
                    :show-text="false"
                  />
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="metric-card" :class="responseStatus">
                <div class="metric-icon response">
                  <el-icon :size="32"><Timer /></el-icon>
                </div>
                <div class="metric-info">
                  <div class="metric-label">响应时间</div>
                  <div class="metric-value">{{ realtimeData?.avg_response_time_ms?.toFixed(0) || 0 }}ms</div>
                  <el-progress
                    :percentage="Math.min(100, (realtimeData?.avg_response_time_ms || 0) / 10)"
                    :stroke-width="6"
                    :color="getResponseTimeColor(realtimeData?.avg_response_time_ms)"
                    :show-text="false"
                  />
                </div>
              </div>
            </el-col>
          </el-row>
        </div>

        <el-divider />

        <div class="performance-section">
          <div class="section-header">
            <span class="section-title">性能指标</span>
            <el-tag size="small" type="info">
              更新于: {{ formatTime(realtimeData?.timestamp) }}
            </el-tag>
          </div>
          <el-row :gutter="16">
            <el-col :span="8">
              <div class="perf-item">
                <div class="perf-label">每秒请求数</div>
                <div class="perf-value">{{ realtimeData?.requests_per_second?.toFixed(2) || 0 }}</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="perf-item">
                <div class="perf-label">活跃线程</div>
                <div class="perf-value">{{ realtimeData?.active_threads || 0 }}</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="perf-item">
                <div class="perf-label">错误率</div>
                <div class="perf-value" :class="errorRateClass">
                  {{ realtimeData?.error_rate_percent?.toFixed(2) || 0 }}%
                </div>
              </div>
            </el-col>
          </el-row>
        </div>

        <el-divider />

        <div class="charts-section">
          <el-row :gutter="16">
            <el-col :span="12">
              <div class="chart-wrapper">
                <div class="chart-title">CPU使用率趋势</div>
                <div class="chart-container" ref="cpuChartRef"></div>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="chart-wrapper">
                <div class="chart-title">内存使用率趋势</div>
                <div class="chart-container" ref="memoryChartRef"></div>
              </div>
            </el-col>
          </el-row>
        </div>

        <el-divider />

        <div class="alerts-preview">
          <div class="section-header">
            <span class="section-title">最新告警</span>
            <el-badge :value="criticalAlertsCount" :hidden="criticalAlertsCount === 0" type="danger">
              <el-button type="primary" link @click="viewAllAlerts">
                查看全部
              </el-button>
            </el-badge>
          </div>
          <div class="alerts-list">
            <div
              v-for="alert in recentAlerts"
              :key="alert.alert_id"
              class="alert-item"
              :class="`alert-${alert.severity}`"
            >
              <el-icon class="alert-icon">
                <component :is="getAlertIcon(alert.severity)" />
              </el-icon>
              <div class="alert-content">
                <div class="alert-title">{{ alert.title }}</div>
                <div class="alert-time">{{ formatTime(alert.timestamp) }}</div>
              </div>
              <el-tag :type="getSeverityType(alert.severity)" size="small">
                {{ getSeverityLabel(alert.severity) }}
              </el-tag>
            </div>
            <el-empty v-if="recentAlerts.length === 0" description="暂无告警" :image-size="60" />
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  VideoPlay,
  VideoPause,
  Cpu,
  Coin,
  Folder,
  Timer,
  Warning,
  CircleClose,
  InfoFilled
} from '@element-plus/icons-vue'
import api from '@/api'

interface RealtimePerformanceData {
  timestamp: string
  cpu_usage_percent: number
  memory_usage_percent: number
  disk_usage_percent: number
  network_io_bytes_sec: number
  active_threads: number
  open_file_descriptors: number
  request_queue_size: number
  avg_response_time_ms: number
  requests_per_second: number
  error_rate_percent: number
}

interface QualityAlert {
  alert_id: string
  severity: 'info' | 'warning' | 'error' | 'critical'
  title: string
  timestamp: string
}

const autoRefresh = ref(true)
const refreshInterval = ref(5000)
const realtimeData = ref<RealtimePerformanceData | null>(null)
const recentAlerts = ref<QualityAlert[]>([])
const cpuChartRef = ref<HTMLElement | null>(null)
const memoryChartRef = ref<HTMLElement | null>(null)

let refreshTimer: ReturnType<typeof setInterval> | null = null
let cpuChartInstance: any = null
let memoryChartInstance: any = null
let echarts: any = null
let cpuHistory: Array<{ time: string; value: number }> = []
let memoryHistory: Array<{ time: string; value: number }> = []

const connectionStatus = computed(() => {
  return autoRefresh.value ? 'success' : 'info'
})

const connectionLabel = computed(() => {
  return autoRefresh.value ? '实时连接' : '已暂停'
})

const cpuStatus = computed(() => {
  const value = realtimeData.value?.cpu_usage_percent || 0
  if (value >= 80) return 'status-critical'
  if (value >= 60) return 'status-warning'
  return 'status-good'
})

const memoryStatus = computed(() => {
  const value = realtimeData.value?.memory_usage_percent || 0
  if (value >= 80) return 'status-critical'
  if (value >= 60) return 'status-warning'
  return 'status-good'
})

const diskStatus = computed(() => {
  const value = realtimeData.value?.disk_usage_percent || 0
  if (value >= 80) return 'status-critical'
  if (value >= 60) return 'status-warning'
  return 'status-good'
})

const responseStatus = computed(() => {
  const value = realtimeData.value?.avg_response_time_ms || 0
  if (value >= 500) return 'status-critical'
  if (value >= 200) return 'status-warning'
  return 'status-good'
})

const errorRateClass = computed(() => {
  const rate = realtimeData.value?.error_rate_percent || 0
  if (rate <= 1) return 'rate-good'
  if (rate <= 5) return 'rate-warning'
  return 'rate-critical'
})

const criticalAlertsCount = computed(() => {
  return recentAlerts.value.filter(a => a.severity === 'critical' || a.severity === 'error').length
})

const getProgressColor = (value: number | undefined): string => {
  if (value === undefined) return '#67c23a'
  if (value >= 80) return '#f56c6c'
  if (value >= 60) return '#e6a23c'
  return '#67c23a'
}

const getResponseTimeColor = (value: number | undefined): string => {
  if (value === undefined) return '#67c23a'
  if (value >= 500) return '#f56c6c'
  if (value >= 200) return '#e6a23c'
  return '#67c23a'
}

const formatTime = (time: string | undefined): string => {
  if (!time) return '-'
  return new Date(time).toLocaleTimeString('zh-CN')
}

const getAlertIcon = (severity: string) => {
  const icons: Record<string, any> = {
    info: InfoFilled,
    warning: Warning,
    error: CircleClose,
    critical: CircleClose
  }
  return icons[severity] || Warning
}

const getSeverityType = (severity: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    info: 'info',
    warning: 'warning',
    error: 'danger',
    critical: 'danger'
  }
  return types[severity] || 'info'
}

const getSeverityLabel = (severity: string): string => {
  const labels: Record<string, string> = {
    info: '信息',
    warning: '警告',
    error: '错误',
    critical: '严重'
  }
  return labels[severity] || severity
}

const fetchRealtimeData = async () => {
  try {
    const response = await api.get('/quality/realtime/performance')
    realtimeData.value = response

    const now = new Date().toLocaleTimeString('zh-CN')
    cpuHistory.push({ time: now, value: response.cpu_usage_percent || 0 })
    memoryHistory.push({ time: now, value: response.memory_usage_percent || 0 })

    if (cpuHistory.length > 60) {
      cpuHistory.shift()
      memoryHistory.shift()
    }

    await nextTick()
    updateCharts()
  } catch (error) {
    console.error('Failed to fetch realtime data:', error)
  }
}

const fetchRecentAlerts = async () => {
  try {
    const response = await api.get('/quality/alerts', {
      params: { severity: 'critical,error,warning' }
    })
    recentAlerts.value = (response || []).slice(0, 5)
  } catch (error) {
    console.error('Failed to fetch alerts:', error)
  }
}

const initCharts = async () => {
  if (!echarts) {
    echarts = await import('echarts')
  }

  if (cpuChartRef.value) {
    if (cpuChartInstance) {
      cpuChartInstance.dispose()
    }
    cpuChartInstance = echarts.init(cpuChartRef.value)
  }

  if (memoryChartRef.value) {
    if (memoryChartInstance) {
      memoryChartInstance.dispose()
    }
    memoryChartInstance = echarts.init(memoryChartRef.value)
  }
}

const updateCharts = () => {
  if (cpuChartInstance && cpuHistory.length > 0) {
    const option = {
      backgroundColor: 'transparent',
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '10%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: cpuHistory.map(d => d.time),
        axisLine: { lineStyle: { color: '#ccc' } },
        axisLabel: { color: '#666', fontSize: 10, rotate: 45 }
      },
      yAxis: {
        type: 'value',
        max: 100,
        axisLine: { lineStyle: { color: '#ccc' } },
        axisLabel: { color: '#666', formatter: '{value}%' },
        splitLine: { lineStyle: { color: '#eee' } }
      },
      series: [
        {
          type: 'line',
          smooth: true,
          symbol: 'none',
          lineStyle: { width: 2, color: '#409eff' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: '#409eff40' },
                { offset: 1, color: '#409eff05' }
              ]
            }
          },
          data: cpuHistory.map(d => d.value)
        }
      ]
    }
    cpuChartInstance.setOption(option)
  }

  if (memoryChartInstance && memoryHistory.length > 0) {
    const option = {
      backgroundColor: 'transparent',
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '10%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: memoryHistory.map(d => d.time),
        axisLine: { lineStyle: { color: '#ccc' } },
        axisLabel: { color: '#666', fontSize: 10, rotate: 45 }
      },
      yAxis: {
        type: 'value',
        max: 100,
        axisLine: { lineStyle: { color: '#ccc' } },
        axisLabel: { color: '#666', formatter: '{value}%' },
        splitLine: { lineStyle: { color: '#eee' } }
      },
      series: [
        {
          type: 'line',
          smooth: true,
          symbol: 'none',
          lineStyle: { width: 2, color: '#67c23a' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: '#67c23a40' },
                { offset: 1, color: '#67c23a05' }
              ]
            }
          },
          data: memoryHistory.map(d => d.value)
        }
      ]
    }
    memoryChartInstance.setOption(option)
  }
}

const toggleAutoRefresh = () => {
  autoRefresh.value = !autoRefresh.value
  if (autoRefresh.value) {
    startAutoRefresh()
    ElMessage.success('实时监控已启动')
  } else {
    stopAutoRefresh()
    ElMessage.info('实时监控已暂停')
  }
}

const startAutoRefresh = () => {
  if (autoRefresh.value && !refreshTimer) {
    fetchRealtimeData()
    refreshTimer = setInterval(fetchRealtimeData, refreshInterval.value)
  }
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

const viewAllAlerts = () => {
  ElMessage.info('跳转到告警管理页面')
}

const handleResize = () => {
  if (cpuChartInstance) {
    cpuChartInstance.resize()
  }
  if (memoryChartInstance) {
    memoryChartInstance.resize()
  }
}

onMounted(async () => {
  await initCharts()
  await fetchRealtimeData()
  await fetchRecentAlerts()
  if (autoRefresh.value) {
    startAutoRefresh()
  }
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  stopAutoRefresh()
  if (cpuChartInstance) {
    cpuChartInstance.dispose()
    cpuChartInstance = null
  }
  if (memoryChartInstance) {
    memoryChartInstance.dispose()
    memoryChartInstance = null
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.realtime-quality-dashboard {
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
  align-items: center;
}

.dashboard-content {
  padding: 10px 0;
}

.realtime-metrics {
  padding: 10px 0;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.metric-card.status-good {
  background: #f0f9eb;
  border: 1px solid #c2e7b0;
}

.metric-card.status-warning {
  background: #fdf6ec;
  border: 1px solid #faecd8;
}

.metric-card.status-critical {
  background: #fef0f0;
  border: 1px solid #fbc4c4;
}

.metric-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.metric-icon.cpu { background: linear-gradient(135deg, #409eff, #66b1ff); }
.metric-icon.memory { background: linear-gradient(135deg, #67c23a, #85ce61); }
.metric-icon.disk { background: linear-gradient(135deg, #e6a23c, #ebb563); }
.metric-icon.response { background: linear-gradient(135deg, #f56c6c, #f78989); }

.metric-info {
  flex: 1;
}

.metric-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.section-title {
  font-weight: 500;
  color: #303133;
  font-size: 15px;
}

.performance-section {
  padding: 10px 0;
}

.perf-item {
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
  text-align: center;
}

.perf-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}

.perf-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.rate-good { color: #67c23a; }
.rate-warning { color: #e6a23c; }
.rate-critical { color: #f56c6c; }

.charts-section {
  padding: 10px 0;
}

.chart-wrapper {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 15px;
}

.chart-title {
  font-weight: 500;
  color: #303133;
  margin-bottom: 10px;
  font-size: 14px;
}

.chart-container {
  height: 200px;
}

.alerts-preview {
  padding: 10px 0;
}

.alerts-list {
  max-height: 300px;
  overflow-y: auto;
}

.alert-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 6px;
  background: #f5f7fa;
}

.alert-item.alert-info { border-left: 3px solid #909399; }
.alert-item.alert-warning { border-left: 3px solid #e6a23c; }
.alert-item.alert-error { border-left: 3px solid #f56c6c; }
.alert-item.alert-critical { border-left: 3px solid #f56c6c; }

.alert-icon {
  font-size: 20px;
}

.alert-item.alert-info .alert-icon { color: #909399; }
.alert-item.alert-warning .alert-icon { color: #e6a23c; }
.alert-item.alert-error .alert-icon { color: #f56c6c; }
.alert-item.alert-critical .alert-icon { color: #f56c6c; }

.alert-content {
  flex: 1;
}

.alert-title {
  font-weight: 500;
  font-size: 14px;
  color: #303133;
  margin-bottom: 4px;
}

.alert-time {
  font-size: 12px;
  color: #909399;
}
</style>
