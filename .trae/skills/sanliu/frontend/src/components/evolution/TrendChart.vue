<template>
  <div class="trend-chart" :class="{ 'dark-theme': isDarkTheme }">
    <el-card class="chart-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span class="title">{{ title }}</span>
            <el-tag v-if="trendData" size="small" :type="trendType">
              {{ trendLabel }}
            </el-tag>
          </div>
          <div class="header-actions">
            <el-select
              v-model="selectedMetric"
              size="small"
              placeholder="选择指标"
              @change="handleMetricChange"
              style="width: 140px"
            >
              <el-option
                v-for="metric in availableMetrics"
                :key="metric.value"
                :label="metric.label"
                :value="metric.value"
              />
            </el-select>
            <el-radio-group
              v-model="selectedPeriod"
              size="small"
              @change="fetchTrendData"
            >
              <el-radio-button label="1h">1小时</el-radio-button>
              <el-radio-button label="24h">24小时</el-radio-button>
              <el-radio-button label="7d">7天</el-radio-button>
              <el-radio-button label="30d">30天</el-radio-button>
            </el-radio-group>
            <el-button-group>
              <el-button
                size="small"
                :type="chartType === 'line' ? 'primary' : 'default'"
                @click="changeChartType('line')"
              >
                <el-icon><TrendCharts /></el-icon>
              </el-button>
              <el-button
                size="small"
                :type="chartType === 'bar' ? 'primary' : 'default'"
                @click="changeChartType('bar')"
              >
                <el-icon><Histogram /></el-icon>
              </el-button>
            </el-button-group>
          </div>
        </div>
      </template>

      <div class="chart-container" ref="chartContainer">
        <div v-if="loading" class="chart-loading">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>加载中...</span>
        </div>
        <div v-else-if="!trendData || trendData.data_points.length === 0" class="chart-empty">
          <el-empty description="暂无数据" :image-size="80" />
        </div>
      </div>

      <div v-if="trendData && showStatistics" class="chart-statistics">
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-label">当前值</div>
              <div class="stat-value">{{ formatValue(trendData.current_value) }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-label">平均值</div>
              <div class="stat-value">{{ formatValue(trendData.average_value) }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-label">最大值</div>
              <div class="stat-value">{{ formatValue(trendData.max_value) }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-label">最小值</div>
              <div class="stat-value">{{ formatValue(trendData.min_value) }}</div>
            </div>
          </el-col>
        </el-row>
        <el-row :gutter="20" style="margin-top: 15px">
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-label">变化率</div>
              <div class="stat-value" :class="changeClass">
                {{ formatChangeRate(trendData.change_percentage) }}
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-label">趋势方向</div>
              <div class="stat-value trend-direction">
                <el-icon v-if="trendData.trend_direction === 'upward'"><Top /></el-icon>
                <el-icon v-else-if="trendData.trend_direction === 'downward'"><Bottom /></el-icon>
                <el-icon v-else><Minus /></el-icon>
                {{ trendDirectionLabel }}
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-label">预测值</div>
              <div class="stat-value prediction">
                {{ trendData.prediction ? formatValue(trendData.prediction) : '-' }}
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-label">置信度</div>
              <div class="stat-value">
                {{ trendData.confidence ? `${(trendData.confidence * 100).toFixed(0)}%` : '-' }}
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <el-card v-if="showErrorChart" class="error-chart-card">
      <template #header>
        <div class="card-header">
          <span class="title">错误趋势</span>
          <el-radio-group
            v-model="errorPeriod"
            size="small"
            @change="fetchErrorTrendData"
          >
            <el-radio-button label="24h">24小时</el-radio-button>
            <el-radio-button label="7d">7天</el-radio-button>
            <el-radio-button label="30d">30天</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <div class="error-chart-container" ref="errorChartContainer">
        <div v-if="errorLoading" class="chart-loading">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>加载中...</span>
        </div>
      </div>
      <div v-if="errorTrendData" class="error-statistics">
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="stat-item error">
              <div class="stat-label">总错误数</div>
              <div class="stat-value">{{ errorTrendData.total_errors }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item error">
              <div class="stat-label">错误率</div>
              <div class="stat-value">{{ (errorTrendData.error_rate * 100).toFixed(2) }}%</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-label">最常见错误</div>
              <div class="stat-value text-ellipsis">
                {{ errorTrendData.most_common_error || '-' }}
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-label">错误趋势</div>
              <div class="stat-value" :class="errorTrendData.trend === 'increasing' ? 'error' : 'success'">
                {{ errorTrendData.trend === 'increasing' ? '上升' : '下降' }}
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <el-dialog
      v-model="customRangeDialogVisible"
      title="自定义时间范围"
      width="400px"
    >
      <el-form label-width="80px">
        <el-form-item label="开始时间">
          <el-date-picker
            v-model="customRange.start"
            type="datetime"
            placeholder="选择开始时间"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-date-picker
            v-model="customRange.end"
            type="datetime"
            placeholder="选择结束时间"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="customRangeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="applyCustomRange">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  TrendCharts,
  Histogram,
  Loading,
  Top,
  Bottom,
  Minus
} from '@element-plus/icons-vue'
import api from '@/api'

interface TrendDataPoint {
  timestamp: string
  value: number
  label?: string
}

interface TrendData {
  metric_name: string
  period: string
  data_points: TrendDataPoint[]
  trend_direction: 'upward' | 'downward' | 'stable'
  change_percentage: number
  current_value: number
  average_value: number
  max_value: number
  min_value: number
  prediction?: number
  confidence?: number
}

interface ErrorTrendData {
  period: string
  total_errors: number
  error_rate: number
  most_common_error: string | null
  trend: 'increasing' | 'decreasing' | 'stable'
  data_points: TrendDataPoint[]
  error_breakdown: Record<string, number>
}

interface MetricOption {
  label: string
  value: string
}

interface Props {
  title?: string
  projectId?: number
  showStatistics?: boolean
  showErrorChart?: boolean
  isDarkTheme?: boolean
  defaultMetric?: string
  defaultPeriod?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: '性能趋势',
  showStatistics: true,
  showErrorChart: true,
  isDarkTheme: false,
  defaultMetric: 'performance',
  defaultPeriod: '7d'
})

const emit = defineEmits<{
  (e: 'metric-change', metric: string): void
  (e: 'period-change', period: string): void
  (e: 'data-loaded', data: TrendData): void
  (e: 'error', error: Error): void
}>()

const loading = ref(false)
const errorLoading = ref(false)
const chartContainer = ref<HTMLElement | null>(null)
const errorChartContainer = ref<HTMLElement | null>(null)
const selectedMetric = ref(props.defaultMetric)
const selectedPeriod = ref(props.defaultPeriod)
const errorPeriod = ref('7d')
const chartType = ref<'line' | 'bar'>('line')
const customRangeDialogVisible = ref(false)
const customRange = ref({
  start: null as Date | null,
  end: null as Date | null
})

const trendData = ref<TrendData | null>(null)
const errorTrendData = ref<ErrorTrendData | null>(null)

let echartsInstance: any = null
let errorEchartsInstance: any = null
let echarts: any = null

const availableMetrics: MetricOption[] = [
  { label: '性能', value: 'performance' },
  { label: '效率', value: 'efficiency' },
  { label: '响应时间', value: 'response_time' },
  { label: '成功率', value: 'success_rate' },
  { label: '吞吐量', value: 'throughput' },
  { label: '资源使用率', value: 'resource_usage' }
]

const trendType = computed(() => {
  if (!trendData.value) return 'info'
  switch (trendData.value.trend_direction) {
    case 'upward':
      return 'success'
    case 'downward':
      return 'danger'
    default:
      return 'info'
  }
})

const trendLabel = computed(() => {
  if (!trendData.value) return ''
  const labels = {
    upward: '上升',
    downward: '下降',
    stable: '稳定'
  }
  return labels[trendData.value.trend_direction] || '稳定'
})

const trendDirectionLabel = computed(() => {
  if (!trendData.value) return '稳定'
  const labels = {
    upward: '上升',
    downward: '下降',
    stable: '稳定'
  }
  return labels[trendData.value.trend_direction] || '稳定'
})

const changeClass = computed(() => {
  if (!trendData.value) return ''
  if (trendData.value.change_percentage > 0) return 'success'
  if (trendData.value.change_percentage < 0) return 'danger'
  return ''
})

const formatValue = (value: number | undefined): string => {
  if (value === undefined) return '-'
  if (selectedMetric.value.includes('rate') || selectedMetric.value.includes('success')) {
    return `${value.toFixed(2)}%`
  }
  if (selectedMetric.value.includes('time')) {
    return `${value.toFixed(2)}s`
  }
  if (selectedMetric.value.includes('throughput')) {
    return `${value.toFixed(0)}/s`
  }
  return value.toFixed(2)
}

const formatChangeRate = (rate: number): string => {
  const prefix = rate > 0 ? '+' : ''
  return `${prefix}${rate.toFixed(2)}%`
}

const handleMetricChange = () => {
  emit('metric-change', selectedMetric.value)
  fetchTrendData()
}

const changeChartType = (type: 'line' | 'bar') => {
  chartType.value = type
  if (echartsInstance && trendData.value) {
    updateChart()
  }
}

const fetchTrendData = async () => {
  loading.value = true
  try {
    const params: Record<string, any> = {
      metric: selectedMetric.value,
      period: selectedPeriod.value
    }
    if (props.projectId) {
      params.project_id = props.projectId
    }

    const response = await api.get('/evolution-monitor/trends', { params })
    trendData.value = response as TrendData
    emit('period-change', selectedPeriod.value)
    emit('data-loaded', trendData.value)

    await nextTick()
    if (!echartsInstance) {
      await initChart()
    }
    updateChart()
  } catch (error) {
    console.error('Failed to fetch trend data:', error)
    emit('error', error as Error)
  } finally {
    loading.value = false
  }
}

const fetchErrorTrendData = async () => {
  errorLoading.value = true
  try {
    const params: Record<string, any> = {
      period: errorPeriod.value
    }
    if (props.projectId) {
      params.project_id = props.projectId
    }

    const response = await api.get('/evolution-monitor/errors/trends', { params })
    errorTrendData.value = response as ErrorTrendData

    await nextTick()
    if (!errorEchartsInstance) {
      await initErrorChart()
    }
    updateErrorChart()
  } catch (error) {
    console.error('Failed to fetch error trend data:', error)
  } finally {
    errorLoading.value = false
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

    echartsInstance = echarts.init(
      chartContainer.value,
      props.isDarkTheme ? 'dark' : undefined
    )
  } catch (error) {
    console.error('Failed to initialize ECharts:', error)
  }
}

const initErrorChart = async () => {
  if (!errorChartContainer.value) return

  try {
    if (!echarts) {
      echarts = await import('echarts')
    }

    if (errorEchartsInstance) {
      errorEchartsInstance.dispose()
    }

    errorEchartsInstance = echarts.init(
      errorChartContainer.value,
      props.isDarkTheme ? 'dark' : undefined
    )
  } catch (error) {
    console.error('Failed to initialize error chart:', error)
  }
}

const updateChart = () => {
  if (!echartsInstance || !trendData.value) return

  const data = trendData.value.data_points
  const times = data.map(d => formatTimeLabel(d.timestamp))
  const values = data.map(d => d.value)

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: props.isDarkTheme ? '#1f1f1f' : '#fff',
      borderColor: props.isDarkTheme ? '#333' : '#ddd',
      textStyle: {
        color: props.isDarkTheme ? '#fff' : '#333'
      },
      formatter: (params: any) => {
        const point = params[0]
        return `${point.name}<br/>${trendData.value!.metric_name}: ${formatValue(point.value)}`
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
      boundaryGap: chartType.value === 'bar',
      data: times,
      axisLine: {
        lineStyle: {
          color: props.isDarkTheme ? '#555' : '#ccc'
        }
      },
      axisLabel: {
        color: props.isDarkTheme ? '#aaa' : '#666',
        rotate: times.length > 20 ? 45 : 0
      }
    },
    yAxis: {
      type: 'value',
      axisLine: {
        lineStyle: {
          color: props.isDarkTheme ? '#555' : '#ccc'
        }
      },
      axisLabel: {
        color: props.isDarkTheme ? '#aaa' : '#666',
        formatter: (value: number) => formatValue(value)
      },
      splitLine: {
        lineStyle: {
          color: props.isDarkTheme ? '#333' : '#eee'
        }
      }
    },
    series: [
      {
        name: trendData.value.metric_name,
        type: chartType.value,
        smooth: chartType.value === 'line',
        symbol: 'circle',
        symbolSize: 6,
        sampling: 'lttb',
        itemStyle: {
          color: '#409eff'
        },
        areaStyle: chartType.value === 'line' ? {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
              { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
            ]
          }
        } : undefined,
        data: values
      }
    ]
  }

  echartsInstance.setOption(option)
}

const updateErrorChart = () => {
  if (!errorEchartsInstance || !errorTrendData.value) return

  const data = errorTrendData.value.data_points
  const times = data.map(d => formatTimeLabel(d.timestamp))
  const values = data.map(d => d.value)

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: props.isDarkTheme ? '#1f1f1f' : '#fff',
      borderColor: props.isDarkTheme ? '#333' : '#ddd',
      textStyle: {
        color: props.isDarkTheme ? '#fff' : '#333'
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
      data: times,
      axisLine: {
        lineStyle: {
          color: props.isDarkTheme ? '#555' : '#ccc'
        }
      },
      axisLabel: {
        color: props.isDarkTheme ? '#aaa' : '#666',
        rotate: times.length > 20 ? 45 : 0
      }
    },
    yAxis: {
      type: 'value',
      axisLine: {
        lineStyle: {
          color: props.isDarkTheme ? '#555' : '#ccc'
        }
      },
      axisLabel: {
        color: props.isDarkTheme ? '#aaa' : '#666'
      },
      splitLine: {
        lineStyle: {
          color: props.isDarkTheme ? '#333' : '#eee'
        }
      }
    },
    series: [
      {
        name: '错误数',
        type: 'bar',
        itemStyle: {
          color: '#f56c6c'
        },
        data: values
      }
    ]
  }

  errorEchartsInstance.setOption(option)
}

const formatTimeLabel = (timestamp: string): string => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  if (diff < 3600000) {
    return `${Math.floor(diff / 60000)}分钟前`
  }
  if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)}小时前`
  }
  return date.toLocaleDateString('zh-CN')
}

const applyCustomRange = () => {
  if (!customRange.value.start || !customRange.value.end) {
    ElMessage.warning('请选择完整的时间范围')
    return
  }

  if (customRange.value.start >= customRange.value.end) {
    ElMessage.warning('开始时间必须早于结束时间')
    return
  }

  customRangeDialogVisible.value = false
  fetchCustomRangeData()
}

const fetchCustomRangeData = async () => {
  loading.value = true
  try {
    const params: Record<string, any> = {
      metric: selectedMetric.value,
      start_time: customRange.value.start!.toISOString(),
      end_time: customRange.value.end!.toISOString()
    }
    if (props.projectId) {
      params.project_id = props.projectId
    }

    const response = await api.get('/evolution-monitor/trends/custom', { params })
    trendData.value = response as TrendData

    await nextTick()
    if (!echartsInstance) {
      await initChart()
    }
    updateChart()
  } catch (error) {
    console.error('Failed to fetch custom range data:', error)
    emit('error', error as Error)
  } finally {
    loading.value = false
  }
}

const handleResize = () => {
  if (echartsInstance) {
    echartsInstance.resize()
  }
  if (errorEchartsInstance) {
    errorEchartsInstance.resize()
  }
}

watch(() => props.isDarkTheme, () => {
  if (echartsInstance) {
    echartsInstance.dispose()
    echartsInstance = null
    nextTick(() => {
      initChart()
      if (trendData.value) {
        updateChart()
      }
    })
  }
  if (errorEchartsInstance) {
    errorEchartsInstance.dispose()
    errorEchartsInstance = null
    nextTick(() => {
      initErrorChart()
      if (errorTrendData.value) {
        updateErrorChart()
      }
    })
  }
})

onMounted(async () => {
  await fetchTrendData()
  if (props.showErrorChart) {
    await fetchErrorTrendData()
  }
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (echartsInstance) {
    echartsInstance.dispose()
    echartsInstance = null
  }
  if (errorEchartsInstance) {
    errorEchartsInstance.dispose()
    errorEchartsInstance = null
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.trend-chart {
  width: 100%;
}

.chart-card,
.error-chart-card {
  margin-bottom: 20px;
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
  font-size: 16px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chart-container {
  height: 350px;
  position: relative;
}

.error-chart-container {
  height: 250px;
  position: relative;
}

.chart-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  color: #909399;
}

.chart-empty {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-statistics,
.error-statistics {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.dark-theme .chart-statistics,
.dark-theme .error-statistics {
  border-top-color: #3d3d3d;
}

.stat-item {
  text-align: center;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.dark-theme .stat-label {
  color: #aaa;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.dark-theme .stat-value {
  color: #e0e0e0;
}

.stat-value.success {
  color: #67c23a;
}

.stat-value.error {
  color: #f56c6c;
}

.stat-value.danger {
  color: #f56c6c;
}

.trend-direction {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
}

.prediction {
  color: #e6a23c;
}

.text-ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 1200px) {
  .header-actions {
    flex-wrap: wrap;
  }
}

@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    gap: 15px;
  }

  .header-actions {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
