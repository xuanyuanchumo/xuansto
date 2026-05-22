<template>
  <div class="evolution-insights-panel">
    <el-card class="panel-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon :size="20"><TrendCharts /></el-icon>
            <span class="title">演化洞察面板</span>
            <el-tag :type="phaseTagType" size="small" effect="dark">{{ phaseLabel }}</el-tag>
          </div>
          <div class="header-actions">
            <el-button type="primary" size="small" :loading="triggering" @click="handleTriggerEvolution" :icon="CaretRight">
              触发演化
            </el-button>
            <el-button size="small" @click="refreshAll" :icon="Refresh">刷新</el-button>
          </div>
        </div>
      </template>

      <div class="insights-content">

        <div class="status-section">
          <div class="section-title">系统状态</div>
          <div class="status-grid">
            <div class="status-item">
              <div class="status-label">健康评分</div>
              <div class="health-score-ring">
                <svg viewBox="0 0 100 100" class="score-svg">
                  <circle cx="50" cy="50" r="42" fill="none" stroke="#ebeef5" stroke-width="8"/>
                  <circle cx="50" cy="50" r="42" fill="none" :stroke="healthColor" stroke-width="8"
                    :stroke-dasharray="`${evolutionStatus.system_health_score * 2.64} 264`"
                    stroke-linecap="round" transform="rotate(-90 50 50)"/>
                  <text x="50" y="54" text-anchor="middle" :fill="healthColor" font-size="20" font-weight="700">{{ evolutionStatus.system_health_score }}</text>
                </svg>
              </div>
            </div>
            <div class="status-item">
              <div class="status-label">当前阶段</div>
              <div class="phase-indicator" :class="`phase-${evolutionStatus.current_phase}`">
                {{ phaseLabel }}
              </div>
            </div>
            <div class="status-item">
              <div class="status-label">完成演化</div>
              <div class="stat-value">{{ evolutionStatus.total_cycles_completed }} 次</div>
            </div>
            <div class="status-item">
              <div class="status-label">成功率</div>
              <div class="stat-value success">{{ (evolutionStatus.success_rate * 100).toFixed(1) }}%</div>
            </div>
          </div>

          <div class="capabilities-section">
            <div class="section-subtitle">能力模块状态</div>
            <div class="capabilities-grid">
              <div v-for="(info, key) in evolutionStatus.capabilities_status" :key="key" class="capability-card" :class="{ active: info.enabled }">
                <div class="cap-name">{{ formatCapabilityName(key) }}</div>
                <div class="cap-status-dot" :class="info.status"></div>
                <div class="cap-detail">
                  <span>运行: {{ info.success_count }}次</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <el-divider />

        <div class="trends-section">
          <div class="section-header">
            <span class="section-title">趋势预测</span>
            <el-radio-group v-model="trendPeriod" size="small" @change="fetchTrends">
              <el-radio-button label="24h">24小时</el-radio-button>
              <el-radio-button label="7d">7天</el-radio-button>
            </el-radio-group>
          </div>
          <div class="trends-grid">
            <div v-for="trend in trendData" :key="trend.metric_type" class="trend-card">
              <div class="trend-header">
                <span class="trend-metric-name">{{ formatMetricName(trend.metric_type) }}</span>
                <el-tag :type="trend.direction === 'upward' ? 'success' : trend.direction === 'downward' ? (trend.metric_type === 'error_rate' || trend.metric_type === 'technical_debt' || trend.metric_type === 'response_time' ? 'success' : 'danger') : 'info'" size="small">
                  {{ trend.direction === 'upward' ? '↑' : trend.direction === 'downward' ? '↓' : '→' }}
                  {{ Math.abs(trend.change_percentage).toFixed(1) }}%
                </el-tag>
              </div>
              <div class="trend-chart-mini">
                <svg :viewBox="`0 0 ${miniChartWidth} ${miniChartHeight}`" class="mini-svg">
                  <polyline
                    :points="getMiniChartPoints(trend.data_points)"
                    fill="none"
                    :stroke="getMetricColor(trend.metric_type)"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                  <circle
                    v-if="trend.data_points.length"
                    :cx="miniChartWidth - 5"
                    :cy="normalizeY(trend.data_points[trend.data_points.length - 1]?.value, trend.metric_type)"
                    r="3"
                    :fill="getMetricColor(trend.metric_type)"
                  />
                </svg>
              </div>
              <div class="trend-values">
                <div class="current-value">{{ formatValue(trend.current_value, trend.metric_type) }}</div>
                <div v-if="trend.predicted_value" class="predicted-value">
                  预测: {{ formatValue(trend.predicted_value, trend.metric_type) }}
                  <span class="confidence">({{ (trend.confidence_score * 100).toFixed(0) }}%置信)</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <el-divider />

        <div class="recommendations-section">
          <div class="section-header">
            <span class="section-title">改进建议</span>
            <el-badge :value="recommendations.length" type="danger">
              <el-button link type="primary" size="small">查看全部</el-button>
            </el-badge>
          </div>
          <div class="recommendations-list">
            <transition-group name="rec-list" tag="div">
              <div v-for="rec in recommendations.slice(0, 3)" :key="rec.recommendation_id" class="rec-item" :class="`priority-${rec.priority}`">
                <div class="rec-priority-bar"></div>
                <div class="rec-body">
                  <div class="rec-title">{{ rec.title }}</div>
                  <div class="rec-desc">{{ rec.description }}</div>
                  <div class="rec-meta">
                    <el-tag :type="getPriorityType(rec.priority)" size="small">{{ getPriorityLabel(rec.priority) }}</el-tag>
                    <el-tag size="small">{{ rec.category.replace('_', ' ') }}</el-tag>
                    <span class="rec-effort">工作量: {{ rec.effort_level }}</span>
                  </div>
                </div>
              </div>
            </transition-group>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { TrendCharts, Refresh, CaretRight } from '@element-plus/icons-vue'
import { evolutionInsightsApi, type TrendPrediction, type ImprovementRecommendation, type EvolutionStatusInsight } from '@/api'

const miniChartWidth = 120
const miniChartHeight = 40

const triggering = ref(false)
const trendPeriod = ref('7d')
const trendData = ref<TrendPrediction[]>([])
const recommendations = ref<ImprovementRecommendation[]>([])
const evolutionStatus = ref<EvolutionStatusInsight>({
  current_phase: 'idle' as any,
  progress_percentage: 0,
  total_cycles_completed: 0,
  success_rate: 0,
  system_health_score: 0,
  capabilities_status: {}
})

const phaseLabel = computed(() => {
  const labels: Record<string, string> = {
    idle: '空闲', analyzing: '分析中', planning: '规划中',
    executing: '执行中', validating: '验证中', deploying: '部署中'
  }
  return labels[evolutionStatus.value.current_phase] || '未知'
})

const phaseTagType = computed(() => {
  const types: Record<string, string> = {
    idle: 'info', analyzing: 'warning', planning: '',
    executing: 'danger', validating: '', deploying: 'success'
  }
  return types[evolutionStatus.value.current_phase] || 'info'
})

const healthColor = computed(() => {
  const score = evolutionStatus.value.system_health_score
  if (score >= 85) return '#67c23a'
  if (score >= 70) return '#e6a23c'
  return '#f56c6c'
})

function formatCapabilityName(key: string): string {
  const names: Record<string, string> = {
    self_iteration: '自迭代', self_optimization: '自优化',
    self_repair: '自修复', self_improvement: '自改进'
  }
  return names[key] || key
}

function formatMetricName(metric: string): string {
  const names: Record<string, string> = {
    performance: '性能', efficiency: '效率', success_rate: '成功率',
    response_time: '响应时间', resource_usage: '资源使用率',
    error_rate: '错误率', coverage: '覆盖率', technical_debt: '技术债务'
  }
  return names[metric] || metric
}

function formatValue(value: number, metric: string): string {
  const units: Record<string, string> = {
    response_time: 's', error_rate: '%', coverage: '%', technical_debt: 'h'
  }
  const unit = units[metric] || ''
  return `${value.toFixed(metric === 'response_time' ? 2 : 1)}${unit}`
}

function getMetricColor(metric: string): string {
  const colors: Record<string, string> = {
    performance: '#409eff', efficiency: '#67c23a', success_rate: '#e6a23c',
    response_time: '#f56c6c', resource_usage: '#909399',
    error_rate: '#f56c6c', coverage: '#67c23a', technical_debt: '#e6a23c'
  }
  return colors[metric] || '#409eff'
}

function normalizeY(value: number, metric: string): number {
  const ranges: Record<string, [number, number]> = {
    performance: [60, 100], efficiency: [55, 95], success_rate: [88, 99.8],
    response_time: [0.3, 4], resource_usage: [30, 90],
    error_rate: [0, 6], coverage: [65, 98], technical_debt: [5, 70]
  }
  const [min, max] = ranges[metric] || [0, 100]
  return miniChartHeight - ((value - min) / (max - min)) * miniChartHeight * 0.8 - miniChartHeight * 0.1
}

function getMiniChartPoints(points: any[]): string {
  if (!points.length) return ''
  return points.map((p, i) => `${(i / Math.max(points.length - 1, 1)) * miniChartWidth},${normalizeY(p.value, '')}`).join(' ')
}

function getPriorityType(priority: string): '' | 'success' | 'warning' | 'danger' | 'info' {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    critical: 'danger', high: 'warning', medium: '', low: 'info'
  }
  return types[priority] || 'info'
}

function getPriorityLabel(priority: string): string {
  const labels: Record<string, string> = {
    critical: '紧急', high: '高', medium: '中', low: '低'
  }
  return labels[priority] || priority
}

async function fetchTrends() {
  try {
    const data = await evolutionInsightsApi.getAllTrends(trendPeriod.value)
    trendData.value = data
  } catch (error) {
    console.error('获取趋势数据失败:', error)
  }
}

async function fetchRecommendations() {
  try {
    const data = await evolutionInsightsApi.getRecommendations()
    recommendations.value = data
  } catch (error) {
    console.error('获取推荐失败:', error)
  }
}

async function fetchStatus() {
  try {
    const data = await evolutionInsightsApi.getStatus()
    evolutionStatus.value = data
  } catch (error) {
    console.error('获取状态失败:', error)
  }
}

async function handleTriggerEvolution() {
  triggering.value = true
  try {
    await evolutionInsightsApi.trigger({})
    ElMessage.success('演化循环已触发')
    setTimeout(fetchStatus, 2000)
  } catch (error) {
    ElMessage.error('触发失败')
  } finally {
    triggering.value = false
  }
}

function refreshAll() {
  fetchTrends()
  fetchRecommendations()
  fetchStatus()
  ElMessage.success('数据已刷新')
}

onMounted(() => {
  refreshAll()
})
</script>

<style scoped>
.evolution-insights-panel { width: 100%; }
.panel-card { border-radius: 10px; }
.card-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
.header-left { display: flex; align-items: center; gap: 10px; }
.title { font-size: 17px; font-weight: 600; }
.header-actions { display: flex; gap: 8px; }

.insights-content { padding: 5px 0; }

.section-title { font-weight: 600; font-size: 15px; color: #303133; margin-bottom: 12px; }
.section-subtitle { font-weight: 500; font-size: 13px; color: #606266; margin-bottom: 10px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }

.status-section { padding: 5px 0; }
.status-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.status-item { text-align: center; padding: 14px; background: #f5f7fa; border-radius: 10px; }
.status-label { font-size: 12px; color: #909399; margin-bottom: 8px; }
.health-score-ring { display: inline-block; }
.score-svg { width: 72px; height: 72px; }
.phase-indicator { font-size: 15px; font-weight: 600; padding: 6px 12px; border-radius: 6px; display: inline-block; }
.phase-idle { background: #ecf5ff; color: #409eff; }
.phase-analyzing { background: #fdf6ec; color: #e6a23c; }
.phase-executing { background: #fef0f0; color: #f56c6c; animation: pulse-phase 2s infinite; }
.phase-deploying { background: #f0f9eb; color: #67c23a; }
.stat-value { font-size: 22px; font-weight: 700; color: #303133; }
.stat-value.success { color: #67c23a; }

@keyframes pulse-phase {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.65; }
}

.capabilities-section { margin-top: 16px; }
.capabilities-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
.capability-card { display: flex; align-items: center; gap: 8px; padding: 10px 12px; background: #fafafa; border-radius: 8px; border: 1px solid #ebeef5; transition: all 0.3s; }
.capability-card.active { border-color: #d9ecff; background: #ecf5ff; }
.cap-name { font-size: 13px; font-weight: 500; color: #303133; }
.cap-status-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.cap-status-dot.active { background: #67c23a; box-shadow: 0 0 4px #67c23a; }
.cap-statusDot.idle { background: #909399; }
.cap-status-dot.monitoring { background: #e6a23c; animation: blink 1.5s infinite; }
.cap-status-dot.learning { background: #409eff; }
.cap-detail { font-size: 11px; color: #909399; }

.trends-section { padding: 5px 0; }
.trends-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; }
.trend-card { background: #fafbfc; border: 1px solid #ebeef5; border-radius: 10px; padding: 14px; transition: all 0.3s; }
.trend-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); transform: translateY(-2px); }
.trend-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.trend-metric-name { font-size: 13px; font-weight: 600; color: #303133; }
.trend-chart-mini { margin: 8px 0; }
.mini-svg { width: 100%; height: 40px; }
.trend-values { display: flex; flex-direction: column; gap: 4px; }
.current-value { font-size: 18px; font-weight: 700; color: #303133; }
.predicted-value { font-size: 12px; color: #909399; }
.confidence { color: #67c23a; font-weight: 500; }

.recommendations-section { padding: 5px 0; }
.recommendations-list { display: flex; flex-direction: column; gap: 10px; }
.rec-item { display: flex; gap: 12px; padding: 14px; border-radius: 8px; background: #f5f7fa; transition: all 0.3s; }
.rec-item:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.rec-priority-bar { width: 4px; border-radius: 2px; flex-shrink: 0; }
.rec-item.priority-critical .rec-priority-bar { background: #f56c6c; }
.rec-item.priority-high .rec-priority-bar { background: #e6a23c; }
.rec-item.priority-medium .rec-priority-bar { background: #409eff; }
.rec-item.priority-low .rec-priority-bar { background: #909399; }
.rec-body { flex: 1; min-width: 0; }
.rec-title { font-size: 14px; font-weight: 600; color: #303133; margin-bottom: 4px; }
.rec-desc { font-size: 12px; color: #606266; line-height: 1.5; margin-bottom: 8px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.rec-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.rec-effort { font-size: 11px; color: #909399; }

@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }

.rec-list-enter-active { transition: all 0.4s ease-out; }
.rec-list-leave-active { transition: all 0.2s ease-in; }
.rec-list-enter-from { opacity: 0; transform: translateX(-15px); }
.rec-list-leave-to { opacity: 0; transform: translateX(15px); }

@media (max-width: 900px) {
  .status-grid, .capabilities-grid { grid-template-columns: repeat(2, 1fr); }
  .trends-grid { grid-template-columns: 1fr; }
}
</style>
