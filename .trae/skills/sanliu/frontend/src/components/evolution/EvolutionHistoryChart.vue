<template>
  <div class="evolution-history-chart" :class="{ 'dark-theme': isDarkTheme }">
    <el-card class="chart-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span class="title">演化历史趋势</span>
            <el-tag v-if="historyData" size="small" :type="overallTrendType">
              {{ overallTrendLabel }}
            </el-tag>
          </div>
          <div class="header-actions">
            <el-select
              v-model="selectedEvolutionType"
              size="small"
              placeholder="演化类型"
              clearable
              @change="fetchHistoryData"
              style="width: 140px"
            >
              <el-option
                v-for="type in evolutionTypes"
                :key="type.value"
                :label="type.label"
                :value="type.value"
              />
            </el-select>
            <el-radio-group
              v-model="selectedTimeRange"
              size="small"
              @change="fetchHistoryData"
            >
              <el-radio-button label="day">日</el-radio-button>
              <el-radio-button label="week">周</el-radio-button>
              <el-radio-button label="month">月</el-radio-button>
            </el-radio-group>
            <el-button-group>
              <el-button
                size="small"
                :type="chartMode === 'success_rate' ? 'primary' : 'default'"
                @click="changeChartMode('success_rate')"
              >
                成功率
              </el-button>
              <el-button
                size="small"
                :type="chartMode === 'duration' ? 'primary' : 'default'"
                @click="changeChartMode('duration')"
              >
                耗时
              </el-button>
              <el-button
                size="small"
                :type="chartMode === 'count' ? 'primary' : 'default'"
                @click="changeChartMode('count')"
              >
                次数
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
        <div v-else-if="!historyData || historyData.data_points.length === 0" class="chart-empty">
          <el-empty description="暂无演化历史数据" :image-size="80" />
        </div>
      </div>

      <div v-if="historyData && showSummary" class="chart-summary">
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">总演化次数</div>
              <div class="summary-value">{{ historyData.total_count }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">成功次数</div>
              <div class="summary-value success">{{ historyData.success_count }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">平均成功率</div>
              <div class="summary-value" :class="successRateClass">
                {{ historyData.average_success_rate.toFixed(1) }}%
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">平均耗时</div>
              <div class="summary-value">{{ formatDuration(historyData.average_duration) }}</div>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <el-card v-if="showTypeBreakdown && historyData" class="breakdown-card">
      <template #header>
        <div class="card-header">
          <span class="title">演化类型分布</span>
        </div>
      </template>
      <div class="breakdown-container" ref="breakdownContainer">
        <div v-if="breakdownLoading" class="chart-loading">
          <el-icon class="is-loading"><Loading /></el-icon>
        </div>
      </div>
      <div class="breakdown-stats">
        <div
          v-for="(item, index) in typeBreakdown"
          :key="index"
          class="breakdown-item"
          @click="filterByType(item.type)"
        >
          <div class="breakdown-type">
            <el-tag size="small" :type="getTypeTagType(item.type)">
              {{ getTypeLabel(item.type) }}
            </el-tag>
          </div>
          <div class="breakdown-count">{{ item.count }} 次</div>
          <div class="breakdown-rate" :class="getRateClass(item.success_rate)">
            {{ item.success_rate.toFixed(1) }}%
          </div>
          <el-progress
            :percentage="item.percentage"
            :stroke-width="6"
            :show-text="false"
            :color="getTypeColor(item.type)"
          />
        </div>
      </div>
    </el-card>

    <el-dialog
      v-model="detailDialogVisible"
      :title="detailTitle"
      width="600px"
      destroy-on-close
    >
      <div v-if="selectedDetail" class="detail-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="演化ID">{{ selectedDetail.id }}</el-descriptions-item>
          <el-descriptions-item label="演化类型">
            <el-tag size="small">{{ getTypeLabel(selectedDetail.evolution_type) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ formatTime(selectedDetail.started_at) }}</el-descriptions-item>
          <el-descriptions-item label="结束时间">{{ formatTime(selectedDetail.completed_at) }}</el-descriptions-item>
          <el-descriptions-item label="耗时">{{ formatDuration(selectedDetail.duration) }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="selectedDetail.success ? 'success' : 'danger'" size="small">
              {{ selectedDetail.success ? '成功' : '失败' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
        <div v-if="selectedDetail.changes && selectedDetail.changes.length > 0" class="detail-changes">
          <div class="changes-title">变更详情</div>
          <el-table :data="selectedDetail.changes" size="small" max-height="200">
            <el-table-column prop="type" label="变更类型" width="120" />
            <el-table-column prop="description" label="描述" />
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
                  {{ row.status === 'success' ? '成功' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="viewFullReport">查看完整报告</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import api from '@/api'

interface HistoryDataPoint {
  timestamp: string
  value: number
  success_count: number
  fail_count: number
  total_count: number
  avg_duration: number
}

interface EvolutionHistoryData {
  time_range: string
  evolution_type: string | null
  data_points: HistoryDataPoint[]
  total_count: number
  success_count: number
  average_success_rate: number
  average_duration: number
  trend_direction: 'upward' | 'downward' | 'stable'
}

interface TypeBreakdownItem {
  type: string
  count: number
  success_rate: number
  percentage: number
}

interface EvolutionDetail {
  id: string
  evolution_type: string
  started_at: string
  completed_at: string
  duration: number
  success: boolean
  changes?: Array<{
    type: string
    description: string
    status: string
  }>
}

interface EvolutionTypeOption {
  label: string
  value: string
}

interface Props {
  projectId?: number
  showSummary?: boolean
  showTypeBreakdown?: boolean
  isDarkTheme?: boolean
  defaultTimeRange?: string
  defaultEvolutionType?: string
}

const props = withDefaults(defineProps<Props>(), {
  showSummary: true,
  showTypeBreakdown: true,
  isDarkTheme: false,
  defaultTimeRange: 'week',
  defaultEvolutionType: ''
})

const emit = defineEmits<{
  (e: 'time-range-change', range: string): void
  (e: 'type-change', type: string): void
  (e: 'data-loaded', data: EvolutionHistoryData): void
  (e: 'detail-view', detail: EvolutionDetail): void
  (e: 'error', error: Error): void
}>()

const loading = ref(false)
const breakdownLoading = ref(false)
const chartContainer = ref<HTMLElement | null>(null)
const breakdownContainer = ref<HTMLElement | null>(null)
const selectedTimeRange = ref(props.defaultTimeRange)
const selectedEvolutionType = ref(props.defaultEvolutionType)
const chartMode = ref<'success_rate' | 'duration' | 'count'>('success_rate')
const detailDialogVisible = ref(false)
const selectedDetail = ref<EvolutionDetail | null>(null)

const historyData = ref<EvolutionHistoryData | null>(null)
const typeBreakdown = ref<TypeBreakdownItem[]>([])

let echartsInstance: any = null
let breakdownEchartsInstance: any = null
let echarts: any = null

const evolutionTypes: EvolutionTypeOption[] = [
  { label: '技能优化', value: 'skill_optimization' },
  { label: '工作流适配', value: 'workflow_adaptation' },
  { label: '资源重平衡', value: 'resource_rebalance' },
  { label: '知识更新', value: 'knowledge_update' },
  { label: '性能调优', value: 'performance_tuning' },
  { label: '安全加固', value: 'security_enhancement' }
]

const overallTrendType = computed(() => {
  if (!historyData.value) return 'info'
  switch (historyData.value.trend_direction) {
    case 'upward':
      return 'success'
    case 'downward':
      return 'danger'
    default:
      return 'info'
  }
})

const overallTrendLabel = computed(() => {
  if (!historyData.value) return ''
  const labels = {
    upward: '趋势上升',
    downward: '趋势下降',
    stable: '趋势稳定'
  }
  return labels[historyData.value.trend_direction] || '稳定'
})

const successRateClass = computed(() => {
  if (!historyData.value) return ''
  const rate = historyData.value.average_success_rate
  if (rate >= 90) return 'rate-excellent'
  if (rate >= 70) return 'rate-good'
  if (rate >= 50) return 'rate-warning'
  return 'rate-danger'
})

const detailTitle = computed(() => {
  if (!selectedDetail.value) return '演化详情'
  return `演化详情 - ${selectedDetail.value.id}`
})

const getTypeLabel = (type: string): string => {
  const found = evolutionTypes.find(t => t.value === type)
  return found?.label || type
}

const getTypeTagType = (type: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    skill_optimization: '',
    workflow_adaptation: 'success',
    resource_rebalance: 'warning',
    knowledge_update: 'info',
    performance_tuning: 'danger',
    security_enhancement: ''
  }
  return types[type] || 'info'
}

const getTypeColor = (type: string): string => {
  const colors: Record<string, string> = {
    skill_optimization: '#409eff',
    workflow_adaptation: '#67c23a',
    resource_rebalance: '#e6a23c',
    knowledge_update: '#909399',
    performance_tuning: '#f56c6c',
    security_enhancement: '#b37feb'
  }
  return colors[type] || '#409eff'
}

const getRateClass = (rate: number): string => {
  if (rate >= 90) return 'rate-excellent'
  if (rate >= 70) return 'rate-good'
  if (rate >= 50) return 'rate-warning'
  return 'rate-danger'
}

const formatTime = (time: string): string => {
  return new Date(time).toLocaleString('zh-CN')
}

const formatDuration = (ms: number): string => {
  if (!ms) return '-'
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${(ms / 60000).toFixed(1)}min`
}

const formatValue = (value: number): string => {
  if (chartMode.value === 'success_rate') {
    return `${value.toFixed(1)}%`
  }
  if (chartMode.value === 'duration') {
    return formatDuration(value)
  }
  return value.toString()
}

const changeChartMode = (mode: 'success_rate' | 'duration' | 'count') => {
  chartMode.value = mode
  if (echartsInstance && historyData.value) {
    updateChart()
  }
}

const fetchHistoryData = async () => {
  loading.value = true
  try {
    const params: Record<string, any> = {
      time_range: selectedTimeRange.value
    }
    if (selectedEvolutionType.value) {
      params.evolution_type = selectedEvolutionType.value
    }
    if (props.projectId) {
      params.project_id = props.projectId
    }

    const response = await api.get('/evolution-monitor/history', { params })
    historyData.value = response.data as EvolutionHistoryData
    emit('time-range-change', selectedTimeRange.value)
    emit('type-change', selectedEvolutionType.value)
    emit('data-loaded', historyData.value)

    await nextTick()
    if (!echartsInstance) {
      await initChart()
    }
    updateChart()

    if (props.showTypeBreakdown) {
      await fetchTypeBreakdown()
    }
  } catch (error) {
    console.error('Failed to fetch evolution history:', error)
    emit('error', error as Error)
  } finally {
    loading.value = false
  }
}

const fetchTypeBreakdown = async () => {
  breakdownLoading.value = true
  try {
    const params: Record<string, any> = {}
    if (props.projectId) {
      params.project_id = props.projectId
    }
    if (selectedTimeRange.value) {
      params.time_range = selectedTimeRange.value
    }

    const response = await api.get('/evolution-monitor/history/type-breakdown', { params })
    typeBreakdown.value = response.data as TypeBreakdownItem[]

    await nextTick()
    if (!breakdownEchartsInstance) {
      await initBreakdownChart()
    }
    updateBreakdownChart()
  } catch (error) {
    console.error('Failed to fetch type breakdown:', error)
  } finally {
    breakdownLoading.value = false
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

    echartsInstance.on('click', handleChartClick)
  } catch (error) {
    console.error('Failed to initialize ECharts:', error)
  }
}

const initBreakdownChart = async () => {
  if (!breakdownContainer.value) return

  try {
    if (!echarts) {
      echarts = await import('echarts')
    }

    if (breakdownEchartsInstance) {
      breakdownEchartsInstance.dispose()
    }

    breakdownEchartsInstance = echarts.init(
      breakdownContainer.value,
      props.isDarkTheme ? 'dark' : undefined
    )
  } catch (error) {
    console.error('Failed to initialize breakdown chart:', error)
  }
}

const updateChart = () => {
  if (!echartsInstance || !historyData.value) return

  const data = historyData.value.data_points
  const times = data.map(d => formatTimeLabel(d.timestamp))
  let values: number[]
  let yAxisLabel: string
  let seriesName: string

  switch (chartMode.value) {
    case 'success_rate':
      values = data.map(d => d.total_count > 0 ? (d.success_count / d.total_count) * 100 : 0)
      yAxisLabel = '成功率 (%)'
      seriesName = '成功率'
      break
    case 'duration':
      values = data.map(d => d.avg_duration)
      yAxisLabel = '耗时 (ms)'
      seriesName = '平均耗时'
      break
    case 'count':
      values = data.map(d => d.total_count)
      yAxisLabel = '次数'
      seriesName = '演化次数'
      break
  }

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
        const point = data[params[0].dataIndex]
        return `
          ${params[0].name}<br/>
          成功率: ${point.total_count > 0 ? ((point.success_count / point.total_count) * 100).toFixed(1) : 0}%<br/>
          成功: ${point.success_count} / 失败: ${point.fail_count}<br/>
          平均耗时: ${formatDuration(point.avg_duration)}
        `
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
      axisLine: {
        lineStyle: {
          color: props.isDarkTheme ? '#555' : '#ccc'
        }
      },
      axisLabel: {
        color: props.isDarkTheme ? '#aaa' : '#666',
        rotate: times.length > 10 ? 45 : 0
      }
    },
    yAxis: {
      type: 'value',
      name: yAxisLabel,
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
        name: seriesName,
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        sampling: 'lttb',
        itemStyle: {
          color: '#409eff'
        },
        areaStyle: {
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
        },
        data: values
      }
    ]
  }

  echartsInstance.setOption(option)
}

const updateBreakdownChart = () => {
  if (!breakdownEchartsInstance || !typeBreakdown.value.length) return

  const data = typeBreakdown.value.map(item => ({
    name: getTypeLabel(item.type),
    value: item.count,
    itemStyle: {
      color: getTypeColor(item.type)
    }
  }))

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: props.isDarkTheme ? '#1f1f1f' : '#fff',
      borderColor: props.isDarkTheme ? '#333' : '#ddd',
      textStyle: {
        color: props.isDarkTheme ? '#fff' : '#333'
      },
      formatter: '{b}: {c} 次 ({d}%)'
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: props.isDarkTheme ? '#1f1f1f' : '#fff',
          borderWidth: 2
        },
        label: {
          show: false
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data
      }
    ]
  }

  breakdownEchartsInstance.setOption(option)
}

const formatTimeLabel = (timestamp: string): string => {
  const date = new Date(timestamp)
  if (selectedTimeRange.value === 'day') {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

const handleChartClick = async (params: any) => {
  if (!historyData.value) return

  const point = historyData.value.data_points[params.dataIndex]
  try {
    const response = await api.get('/evolution-monitor/history/detail', {
      params: {
        timestamp: point.timestamp,
        project_id: props.projectId
      }
    })
    selectedDetail.value = response.data as EvolutionDetail
    detailDialogVisible.value = true
  } catch (error) {
    console.error('Failed to fetch detail:', error)
    ElMessage.error('获取详情失败')
  }
}

const filterByType = (type: string) => {
  selectedEvolutionType.value = type
  fetchHistoryData()
}

const viewFullReport = () => {
  if (selectedDetail.value) {
    emit('detail-view', selectedDetail.value)
    detailDialogVisible.value = false
  }
}

const handleResize = () => {
  if (echartsInstance) {
    echartsInstance.resize()
  }
  if (breakdownEchartsInstance) {
    breakdownEchartsInstance.resize()
  }
}

watch(() => props.isDarkTheme, () => {
  if (echartsInstance) {
    echartsInstance.dispose()
    echartsInstance = null
    nextTick(() => {
      initChart()
      if (historyData.value) {
        updateChart()
      }
    })
  }
  if (breakdownEchartsInstance) {
    breakdownEchartsInstance.dispose()
    breakdownEchartsInstance = null
    nextTick(() => {
      initBreakdownChart()
      if (typeBreakdown.value.length) {
        updateBreakdownChart()
      }
    })
  }
})

onMounted(async () => {
  await fetchHistoryData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (echartsInstance) {
    echartsInstance.dispose()
    echartsInstance = null
  }
  if (breakdownEchartsInstance) {
    breakdownEchartsInstance.dispose()
    breakdownEchartsInstance = null
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.evolution-history-chart {
  width: 100%;
}

.chart-card,
.breakdown-card {
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

.breakdown-container {
  height: 200px;
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

.chart-summary {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.dark-theme .chart-summary {
  border-top-color: #3d3d3d;
}

.summary-item {
  text-align: center;
}

.summary-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.dark-theme .summary-label {
  color: #aaa;
}

.summary-value {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.dark-theme .summary-value {
  color: #e0e0e0;
}

.summary-value.success {
  color: #67c23a;
}

.rate-excellent {
  color: #67c23a;
}

.rate-good {
  color: #409eff;
}

.rate-warning {
  color: #e6a23c;
}

.rate-danger {
  color: #f56c6c;
}

.breakdown-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  margin-top: 15px;
}

.breakdown-item {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.breakdown-item:hover {
  background: #ecf5ff;
  transform: translateY(-2px);
}

.dark-theme .breakdown-item {
  background: #2d2d2d;
}

.dark-theme .breakdown-item:hover {
  background: #3d3d3d;
}

.breakdown-type {
  margin-bottom: 8px;
}

.breakdown-count {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.dark-theme .breakdown-count {
  color: #e0e0e0;
}

.breakdown-rate {
  font-size: 14px;
  margin-bottom: 8px;
}

.detail-content {
  padding: 10px 0;
}

.detail-changes {
  margin-top: 20px;
}

.changes-title {
  font-weight: 500;
  margin-bottom: 10px;
}

@media (max-width: 1200px) {
  .header-actions {
    flex-wrap: wrap;
  }

  .breakdown-stats {
    grid-template-columns: repeat(2, 1fr);
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

  .breakdown-stats {
    grid-template-columns: 1fr;
  }
}
</style>
