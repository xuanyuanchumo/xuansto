<template>
  <div class="performance-trend">
    <el-card class="trend-card">
      <template #header>
        <div class="card-header">
          <span class="title">性能趋势</span>
          <div class="header-actions">
            <el-radio-group v-model="selectedMetric" size="small" @change="fetchTrendData">
              <el-radio-button label="performance">响应时间</el-radio-button>
              <el-radio-button label="error_rate">错误率</el-radio-button>
              <el-radio-button label="code_quality">代码质量</el-radio-button>
              <el-radio-button label="test_coverage">测试覆盖率</el-radio-button>
            </el-radio-group>
            <el-select v-model="timeRange" size="small" @change="fetchTrendData" style="width: 120px; margin-left: 10px;">
              <el-option label="最近1小时" :value="1" />
              <el-option label="最近6小时" :value="6" />
              <el-option label="最近12小时" :value="12" />
              <el-option label="最近24小时" :value="24" />
              <el-option label="最近3天" :value="72" />
              <el-option label="最近7天" :value="168" />
            </el-select>
          </div>
        </div>
      </template>

      <div class="chart-container" ref="chartContainer">
        <div v-if="loading" class="chart-loading">
          <el-icon class="is-loading" :size="40"><Loading /></el-icon>
          <p>加载中...</p>
        </div>
        <div v-else-if="!trendData.length" class="chart-empty">
          <el-empty description="暂无数据" />
        </div>
      </div>

      <div class="trend-stats">
        <el-row :gutter="16">
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-label">当前值</div>
              <div class="stat-value" :class="currentValueClass">
                {{ currentValue.toFixed(2) }}
                <span class="stat-unit">{{ currentUnit }}</span>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-label">平均值</div>
              <div class="stat-value">
                {{ avgValue.toFixed(2) }}
                <span class="stat-unit">{{ currentUnit }}</span>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-label">最大值</div>
              <div class="stat-value">
                {{ maxValue.toFixed(2) }}
                <span class="stat-unit">{{ currentUnit }}</span>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-label">趋势</div>
              <div class="stat-value trend" :class="trendClass">
                <el-icon><component :is="trendIcon" /></el-icon>
                {{ trendLabel }}
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { Loading, Top, Bottom, Minus } from '@element-plus/icons-vue'
import api from '@/api'

interface TrendDataPoint {
  timestamp: string
  value: number
}

interface Props {
  autoRefresh?: boolean
  refreshInterval?: number
}

const props = withDefaults(defineProps<Props>(), {
  autoRefresh: true,
  refreshInterval: 60000
})

const selectedMetric = ref('performance')
const timeRange = ref(24)
const loading = ref(false)
const trendData = ref<TrendDataPoint[]>([])
const chartContainer = ref<HTMLElement | null>(null)

let echartsInstance: any = null
let echarts: any = null
let refreshTimer: ReturnType<typeof setInterval> | null = null

const metricConfig = computed(() => {
  const configs: Record<string, { unit: string; name: string; color: string; invertTrend?: boolean }> = {
    performance: { unit: 'ms', name: '响应时间', color: '#409eff', invertTrend: true },
    error_rate: { unit: '%', name: '错误率', color: '#f56c6c', invertTrend: true },
    code_quality: { unit: '分', name: '代码质量', color: '#67c23a' },
    test_coverage: { unit: '%', name: '测试覆盖率', color: '#e6a23c' }
  }
  return configs[selectedMetric.value] || configs.performance
})

const currentUnit = computed(() => metricConfig.value.unit)

const currentValue = computed(() => {
  if (!trendData.value.length) return 0
  return trendData.value[trendData.value.length - 1].value
})

const avgValue = computed(() => {
  if (!trendData.value.length) return 0
  const sum = trendData.value.reduce((acc, d) => acc + d.value, 0)
  return sum / trendData.value.length
})

const maxValue = computed(() => {
  if (!trendData.value.length) return 0
  return Math.max(...trendData.value.map(d => d.value))
})

const currentValueClass = computed(() => {
  const value = currentValue.value
  const metric = selectedMetric.value

  if (metric === 'performance') {
    if (value <= 200) return 'value-good'
    if (value <= 500) return 'value-warning'
    return 'value-critical'
  } else if (metric === 'error_rate') {
    if (value <= 1) return 'value-good'
    if (value <= 5) return 'value-warning'
    return 'value-critical'
  } else {
    if (value >= 80) return 'value-good'
    if (value >= 60) return 'value-warning'
    return 'value-critical'
  }
})

const trendClass = computed(() => {
  if (trendData.value.length < 2) return 'trend-stable'

  const recent = trendData.value.slice(-5)
  const older = trendData.value.slice(-10, -5)

  if (older.length === 0) return 'trend-stable'

  const recentAvg = recent.reduce((acc, d) => acc + d.value, 0) / recent.length
  const olderAvg = older.reduce((acc, d) => acc + d.value, 0) / older.length

  const change = ((recentAvg - olderAvg) / olderAvg) * 100

  if (metricConfig.value.invertTrend) {
    if (change > 5) return 'trend-down'
    if (change < -5) return 'trend-up'
  } else {
    if (change > 5) return 'trend-up'
    if (change < -5) return 'trend-down'
  }

  return 'trend-stable'
})

const trendIcon = computed(() => {
  const cls = trendClass.value
  if (cls === 'trend-up') return Top
  if (cls === 'trend-down') return Bottom
  return Minus
})

const trendLabel = computed(() => {
  const cls = trendClass.value
  if (cls === 'trend-up') return '上升'
  if (cls === 'trend-down') return '下降'
  return '稳定'
})

const fetchTrendData = async () => {
  loading.value = true
  try {
    const response = await api.get(`/quality/metrics/trend`, {
      params: {
        metric_type: selectedMetric.value,
        hours: timeRange.value
      }
    })

    trendData.value = response.trend || []

    await nextTick()
    if (!echartsInstance) {
      await initChart()
    }
    updateChart()
  } catch (error) {
    console.error('Failed to fetch trend data:', error)
  } finally {
    loading.value = false
  }
}

const initChart = async () => {
  if (!chartContainer.value) return

  try {
    if (!echarts) {
      echarts = await import('echarts')
    }

    if (echartsInstance) {
      echartsInstance.dispose()
    }

    echartsInstance = echarts.init(chartContainer.value)
  } catch (error) {
    console.error('Failed to initialize chart:', error)
  }
}

const updateChart = () => {
  if (!echartsInstance || !trendData.value.length) return

  const times = trendData.value.map(d => {
    const date = new Date(d.timestamp)
    if (timeRange.value <= 24) {
      return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    }
    return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
  })

  const values = trendData.value.map(d => d.value)

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const point = params[0]
        return `${point.name}<br/>${metricConfig.value.name}: ${point.value.toFixed(2)}${metricConfig.value.unit}`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: times,
      axisLine: { lineStyle: { color: '#ccc' } },
      axisLabel: {
        color: '#666',
        rotate: timeRange.value > 24 ? 45 : 0
      }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#ccc' } },
      axisLabel: {
        color: '#666',
        formatter: `{value}${metricConfig.value.unit}`
      },
      splitLine: { lineStyle: { color: '#eee' } }
    },
    series: [
      {
        name: metricConfig.value.name,
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        itemStyle: { color: metricConfig.value.color },
        lineStyle: {
          width: 2,
          color: metricConfig.value.color
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: `${metricConfig.value.color}40` },
              { offset: 1, color: `${metricConfig.value.color}05` }
            ]
          }
        },
        data: values
      }
    ]
  }

  echartsInstance.setOption(option, true)
}

const handleResize = () => {
  if (echartsInstance) {
    echartsInstance.resize()
  }
}

const startAutoRefresh = () => {
  if (props.autoRefresh && !refreshTimer) {
    refreshTimer = setInterval(fetchTrendData, props.refreshInterval)
  }
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

watch(() => props.autoRefresh, (newVal) => {
  if (newVal) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
})

onMounted(async () => {
  await fetchTrendData()
  if (props.autoRefresh) {
    startAutoRefresh()
  }
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  stopAutoRefresh()
  if (echartsInstance) {
    echartsInstance.dispose()
    echartsInstance = null
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.performance-trend {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 16px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  align-items: center;
}

.chart-container {
  height: 350px;
  position: relative;
}

.chart-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.chart-loading p {
  margin-top: 10px;
  color: #909399;
}

.chart-empty {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.trend-stats {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.stat-item {
  text-align: center;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.stat-unit {
  font-size: 14px;
  font-weight: normal;
  color: #909399;
  margin-left: 4px;
}

.value-good { color: #67c23a; }
.value-warning { color: #e6a23c; }
.value-critical { color: #f56c6c; }

.trend {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.trend-up { color: #67c23a; }
.trend-down { color: #f56c6c; }
.trend-stable { color: #909399; }
</style>
