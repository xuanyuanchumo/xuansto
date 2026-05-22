<template>
  <div class="skill-health-panel">
    <el-card class="health-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span class="title">技能健康度</span>
            <el-tag :type="healthLevelType" effect="dark" size="large">
              {{ healthLevelLabel }}
            </el-tag>
          </div>
          <el-button type="primary" :loading="evaluating" @click="runEvaluation">
            <el-icon><Refresh /></el-icon>
            一键评估
          </el-button>
        </div>
      </template>

      <div class="health-content">
        <div class="score-section">
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
              <span class="detail-label">问题数量</span>
              <span class="detail-value issue-count" :class="{ 'has-issues': (healthData?.issues_count || 0) > 0 }">
                {{ healthData?.issues_count || 0 }}
              </span>
            </div>
          </div>
        </div>

        <el-divider />

        <div class="categories-section">
          <div class="section-title">分类得分</div>
          <div class="categories-grid">
            <div
              v-for="category in categoryScores"
              :key="category.key"
              class="category-item"
              :class="getCategoryClass(category.score)"
            >
              <div class="category-header">
                <el-icon :size="20">
                  <component :is="category.icon" />
                </el-icon>
                <span class="category-name">{{ category.label }}</span>
              </div>
              <el-progress
                :percentage="category.score"
                :stroke-width="12"
                :color="getProgressColor(category.score)"
              />
              <div class="category-details">
                <span class="category-score">{{ category.score?.toFixed(1) || 0 }}分</span>
                <span class="category-status">{{ getCategoryStatus(category.score) }}</span>
              </div>
            </div>
          </div>
        </div>

        <el-divider />

        <div class="trend-section">
          <div class="section-header">
            <span class="section-title">健康度趋势</span>
            <el-radio-group v-model="trendPeriod" size="small" @change="fetchTrendData">
              <el-radio-button label="7d">7天</el-radio-button>
              <el-radio-button label="30d">30天</el-radio-button>
              <el-radio-button label="90d">90天</el-radio-button>
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
  Document,
  Cpu,
  Setting,
  FolderOpened,
  DataLine,
  Loading
} from '@element-plus/icons-vue'
import api from '@/api'

interface HealthCategory {
  documentation: number
  scripts: number
  configuration: number
  paths: number
  metadata: number
}

interface Recommendation {
  title: string
  description: string
  priority: 'high' | 'medium' | 'low'
  category: string
}

interface HealthData {
  overall_score: number
  health_level: 'excellent' | 'good' | 'fair' | 'poor' | 'critical'
  category_scores: HealthCategory
  issues_count: number
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
  autoRefresh?: boolean
  refreshInterval?: number
}

const props = withDefaults(defineProps<Props>(), {
  autoRefresh: true,
  refreshInterval: 60000
})

const emit = defineEmits<{
  (e: 'evaluation-complete', data: HealthData): void
  (e: 'error', error: Error): void
}>()

const loading = ref(false)
const evaluating = ref(false)
const trendLoading = ref(false)
const trendPeriod = ref('7d')
const healthData = ref<HealthData | null>(null)
const trendData = ref<TrendDataPoint[]>([])
const trendChartRef = ref<HTMLElement | null>(null)

let echartsInstance: any = null
let echarts: any = null
let refreshTimer: ReturnType<typeof setInterval> | null = null

const healthLevelType = computed(() => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    excellent: 'success',
    good: 'primary',
    fair: 'warning',
    poor: 'danger',
    critical: 'danger'
  }
  return types[healthData.value?.health_level || 'fair'] || 'info'
})

const healthLevelLabel = computed(() => {
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

const categoryScores = computed(() => {
  if (!healthData.value?.category_scores) return []
  const scores = healthData.value.category_scores
  return [
    { key: 'documentation', label: '文档', score: scores.documentation, icon: Document },
    { key: 'scripts', label: '脚本', score: scores.scripts, icon: Cpu },
    { key: 'configuration', label: '配置', score: scores.configuration, icon: Setting },
    { key: 'paths', label: '路径', score: scores.paths, icon: FolderOpened },
    { key: 'metadata', label: '元数据', score: scores.metadata, icon: DataLine }
  ]
})

const formatTime = (time: string | undefined): string => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const getProgressColor = (score: number): string => {
  if (score >= 80) return '#67c23a'
  if (score >= 60) return '#e6a23c'
  return '#f56c6c'
}

const getCategoryClass = (score: number): string => {
  if (score >= 80) return 'category-good'
  if (score >= 60) return 'category-fair'
  return 'category-poor'
}

const getCategoryStatus = (score: number): string => {
  if (score >= 80) return '良好'
  if (score >= 60) return '一般'
  return '需改进'
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
  loading.value = true
  try {
    const url = props.skillId
      ? `/skill-health/${props.skillId}`
      : '/skill-health/current'
    const response = await api.get(url)
    healthData.value = response as HealthData
  } catch (error) {
    console.error('Failed to fetch health data:', error)
    emit('error', error as Error)
  } finally {
    loading.value = false
  }
}

const runEvaluation = async () => {
  evaluating.value = true
  try {
    const url = props.skillId
      ? `/skill-health/${props.skillId}/evaluate`
      : '/skill-health/evaluate'
    const response = await api.post(url)
    healthData.value = response as HealthData
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
    const response = await api.get('/skill-health/trends', { params })
    trendData.value = response as TrendDataPoint[]
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

  const times = trendData.value.map(d => new Date(d.timestamp).toLocaleDateString('zh-CN'))
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

const handleResize = () => {
  if (echartsInstance) {
    echartsInstance.resize()
  }
}

const startAutoRefresh = () => {
  if (props.autoRefresh && !refreshTimer) {
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
  startAutoRefresh()
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
.skill-health-panel {
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
  font-size: 16px;
  font-weight: 600;
}

.health-content {
  padding: 10px 0;
}

.score-section {
  display: flex;
  align-items: center;
  gap: 40px;
  padding: 20px 0;
}

.score-circle {
  width: 150px;
  height: 150px;
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
  font-size: 36px;
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
  padding: 10px 0;
  border-bottom: 1px solid #ebeef5;
}

.detail-label {
  color: #909399;
}

.detail-value {
  font-weight: 500;
}

.issue-count.has-issues {
  color: #f56c6c;
}

.section-title {
  font-weight: 500;
  margin-bottom: 15px;
  color: #303133;
}

.categories-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 15px;
}

.category-item {
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.category-item.category-good { background: #f0f9eb; }
.category-item.category-fair { background: #fdf6ec; }
.category-item.category-poor { background: #fef0f0; }

.category-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.category-name {
  font-size: 14px;
  font-weight: 500;
}

.category-details {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
}

.category-score {
  font-weight: 600;
  color: #303133;
}

.category-status {
  color: #909399;
}

.trend-section {
  margin-top: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
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
  margin-top: 20px;
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
}

@media (max-width: 1200px) {
  .categories-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .score-section {
    flex-direction: column;
    align-items: flex-start;
  }
  .categories-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
