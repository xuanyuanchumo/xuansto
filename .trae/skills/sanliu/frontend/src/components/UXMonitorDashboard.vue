<template>
  <div class="ux-monitor-dashboard">
    <el-card class="dashboard-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon :size="20"><Monitor /></el-icon>
            <span class="title">用户体验监控仪表盘</span>
            <el-tag :type="overallLevelType" size="small" effect="dark">{{ overallLevelLabel }}</el-tag>
          </div>
          <div class="header-actions">
            <el-select v-model="dashboardPeriod" size="small" style="width: 100px" @change="fetchDashboard">
              <el-option label="24h" value="24h" />
              <el-option label="7d" value="7d" />
              <el-option label="30d" value="30d" />
            </el-select>
            <el-button size="small" @click="fetchDashboard" :icon="Refresh">刷新</el-button>
          </div>
        </div>
      </template>

      <div class="dashboard-content">

        <div class="metrics-summary-row">
          <div v-for="metric in uxMetrics" :key="metric.metric_name" class="metric-card" :class="`level-${metric.level}`">
            <div class="metric-icon-wrap" :class="metric.level">
              <el-icon :size="24"><component :is="getMetricIcon(metric.metric_name)" /></el-icon>
            </div>
            <div class="metric-info">
              <div class="metric-name">{{ metric.display_name }}</div>
              <div class="metric-value-row">
                <span class="metric-value">{{ formatMetricValue(metric.value, metric.unit) }}</span>
                <span class="metric-unit">{{ metric.unit }}</span>
              </div>
              <div class="metric-trend" :class="metric.trend">
                {{ metric.trend === 'up' ? '↑' : metric.trend === 'down' ? '↓' : '→' }}
                {{ Math.abs(metric.change_percentage).toFixed(1) }}%
              </div>
            </div>
            <div class="metric-gauge">
              <svg viewBox="0 0 44 44" class="gauge-svg">
                <circle cx="22" cy="22" r="18" fill="none" stroke="#ebeef5" stroke-width="4"/>
                <circle cx="22" cy="22" r="18" fill="none" :stroke="getGaugeColor(metric.level)"
                  stroke-width="4" stroke-linecap="round"
                  :stroke-dasharray="`${getGaugePercent(metric)} 113`"
                  transform="rotate(-90 22 22)"/>
              </svg>
            </div>
          </div>
        </div>

        <el-divider />

        <div class="dashboard-grid">
          <div class="chart-section">
            <div class="section-title">性能趋势</div>
            <div class="trend-chart-area">
              <svg :viewBox="`0 0 ${chartWidth} ${chartHeight}`" class="trend-chart-svg">
                <defs>
                  <linearGradient :id="'uxGrad'" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#409eff" stop-opacity="0.2"/>
                    <stop offset="100%" stop-color="#409eff" stop-opacity="0.01"/>
                  </linearGradient>
                </defs>
                <g v-if="trendPoints.length > 1">
                  <path :d="trendAreaPath" :fill="'url(#uxGrad)'" />
                  <polyline :points="trendLinePoints" fill="none" stroke="#409eff" stroke-width="2" stroke-linejoin="round"/>
                  <circle v-for="(pt, i) in visibleTrendPoints" :key="i" :cx="pt.x" :cy="pt.y" r="3" fill="#409eff" opacity="0.8"/>
                </g>
                <text v-else x="50%" y="50%" text-anchor="middle" dominant-baseline="middle" fill="#c0c4cc" font-size="13">加载中...</text>
              </svg>
            </div>
            <div class="chart-legend">
              <span class="legend-item"><span class="dot" style="background:#409eff"></span>FCP/LCP</span>
              <span class="legend-item"><span class="dot" style="background:#67c23a"></span>FID</span>
              <span class="legend-item"><span class="dot" style="background:#e6a23c"></span>CLS</span>
            </div>
          </div>

          <div class="funnel-section">
            <div class="section-title">用户转化漏斗</div>
            <div class="funnel-container">
              <div v-for="(step, index) in funnelData" :key="step.step" class="funnel-step" :style="{ width: getFunnelWidth(step.rate) }">
                <div class="funnel-bar" :class="`funnel-${index}`">
                  <span class="funnel-label">{{ step.step }}</span>
                  <span class="funnel-count">{{ step.count }}</span>
                  <span class="funnel-rate">{{ step.rate }}%</span>
                </div>
                <div v-if="step.dropoff > 0" class="funnel-dropoff">
                  ↓ 流失 {{ step.dropoff }} ({{ step.dropoff_rate.toFixed(1) }}%)
                </div>
              </div>
            </div>
          </div>
        </div>

        <el-divider />

        <div class="bottom-grid">
          <div class="errors-section">
            <div class="section-header">
              <span class="section-title">错误分布</span>
              <el-badge :value="totalErrors" :hidden="totalErrors === 0" type="danger">
                <span class="error-count-label">错误</span>
              </el-badge>
            </div>
            <div class="error-bars">
              <div v-for="err in errorDistribution" :key="err.type" class="error-bar-item">
                <div class="error-bar-label">{{ err.type.replace('_', ' ') }}</div>
                <div class="error-bar-track">
                  <div class="error-bar-fill" :style="{ width: `${err.percentage}%` }"></div>
                </div>
                <div class="error-bar-count">{{ err.count }}</div>
              </div>
            </div>
          </div>

          <div class="pages-section">
            <div class="section-title">热门页面</div>
            <div class="pages-list">
              <div v-for="(page, index) in topPages" :key="page.path" class="page-item">
                <span class="page-rank" :class="`rank-${index + 1}`">{{ index + 1 }}</span>
                <div class="page-info">
                  <span class="page-name">{{ page.name }}</span>
                  <span class="page-path">{{ page.path }}</span>
                </div>
                <div class="page-stats">
                  <span class="page-views">{{ page.views.toLocaleString() }}</span>
                  <span class="page-duration">{{ page.avg_duration }}s</span>
                </div>
              </div>
            </div>
          </div>

          <div class="device-section">
            <div class="section-title">设备分布</div>
            <div class="device-charts">
              <div v-for="(data, device) in deviceBreakdown" :key="device" class="device-item">
                <div class="device-label">{{ device === 'desktop' ? '桌面端' : device === 'mobile' ? '移动端' : '平板' }}</div>
                <div class="device-bar-track">
                  <div class="device-bar-fill" :style="{ width: `${data.percentage}%`, background: deviceColors[device] }"></div>
                </div>
                <span class="device-percent">{{ data.percentage }}%</span>
                <span class="device-count">{{ data.count }}</span>
              </div>
            </div>
          </div>
        </div>

      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Monitor, Refresh, Timer, Clock, Warning, DataLine, Position } from '@element-plus/icons-vue'
import { uxMonitorApi, type UXMetricCard, type DashboardData } from '@/api'

const dashboardPeriod = ref('24h')
const uxMetrics = ref<UXMetricCard[]>([])
const dashboardData = ref<DashboardData | null>(null)
const chartWidth = 480
const chartHeight = 180

const deviceColors: Record<string, string> = {
  desktop: '#409eff', mobile: '#67c23a', tablet: '#e6a23c'
}

const overallScore = computed(() => {
  if (!uxMetrics.value.length) return 0
  const scores = uxMetrics.value.map(m =>
    m.level === 'excellent' ? 100 : m.level === 'good' ? 80 : m.level === 'fair' ? 60 : 30
  )
  return Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)
})

const overallLevel = computed(() => {
  if (overallScore.value >= 90) return 'excellent'
  if (overallScore.value >= 75) return 'good'
  if (overallScore.value >= 60) return 'fair'
  return 'poor'
})

const overallLevelType = computed(() => {
  const types: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
    excellent: 'success', good: 'success', fair: 'warning', poor: 'danger'
  }
  return types[overallLevel.value] || 'info'
})

const overallLevelLabel = computed(() => {
  const labels: Record<string, string> = { excellent: '优秀', good: '良好', fair: '一般', poor: '需改善' }
  return labels[overallLevel.value] || '未知'
})

const trendPoints = computed(() => {
  const data = dashboardData.value?.trend_data?.performance || []
  return data.map((p: any, i: number) => ({
    x: (i / Math.max(data.length - 1, 1)) * chartWidth,
    y: chartHeight - ((p.fcp || p.lcp || 1.5) / 4) * chartHeight * 0.8 - chartHeight * 0.1
  }))
})

const visibleTrendPoints = computed(() => {
  if (trendPoints.value.length > 20) return trendPoints.value.filter((_, i) => i % Math.ceil(trendPoints.value.length / 20) === 0)
  return trendPoints.value
})

const trendLinePoints = computed(() => trendPoints.value.map(p => `${p.x},${p.y}`).join(' '))
const trendAreaPath = computed(() => {
  const pts = trendPoints.value
  if (pts.length < 2) return ''
  return `M 0,${chartHeight} L ${pts.map(p => `${p.x},${p.y}`).join(' L ')} L ${pts[pts.length - 1].x},${chartHeight} Z`
})

const funnelData = computed(() => dashboardData.value?.user_flow_funnel || [])
const errorDistribution = computed(() => dashboardData.value?.error_distribution || [])
const totalErrors = computed(() => errorDistribution.value.reduce((sum: number, e: any) => sum + e.count, 0))
const topPages = computed(() => dashboardData.value?.top_pages || [])
const deviceBreakdown = computed(() => dashboardData.value?.device_breakdown || {})

function getMetricIcon(name: string): any {
  const icons: Record<string, any> = {
    fcp: Timer, lcp: Timer, fid: DataLine, cls: Warning, ttfb: Clock, interaction_time: Position
  }
  return icons[name] || Monitor
}

function formatMetricValue(value: number, unit: string): string {
  if (unit === 'ms') return value.toFixed(0)
  if (unit === 's') return value.toFixed(2)
  if (unit === '') return value.toFixed(3)
  return value.toFixed(1)
}

function getGaugeColor(level: string): string {
  return level === 'excellent' ? '#67c23a' : level === 'good' ? '#67c23a' : level === 'fair' ? '#e6a23c' : '#f56c6c'
}

function getGaugePercent(metric: UXMetricCard): number {
  const thresholds: Record<string, [number, number]> = {
    fcp: [3000, 1], lcp: [4000, 1], fid: [500, 1],
    cls: [0.3, 1], ttfb: [800, 1], interaction_time: [400, 1]
  }
  const [max] = thresholds[metric.metric_name] || [100, 1]
  return Math.max(0, Math.min(100, (1 - metric.value / max) * 100))
}

function getFunnelWidth(rate: number): string {
  return `${Math.max(20, rate)}%`
}

async function fetchDashboard() {
  try {
    const metrics = await uxMonitorApi.getMetrics()
    uxMetrics.value = metrics.metrics
    const dash = await uxMonitorApi.getDashboard(dashboardPeriod.value)
    dashboardData.value = dash
  } catch (error) {
    console.error('获取UX数据失败:', error)
  }
}

onMounted(fetchDashboard)
</script>

<style scoped>
.ux-monitor-dashboard { width: 100%; }
.dashboard-card { border-radius: 10px; }
.card-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
.header-left { display: flex; align-items: center; gap: 10px; }
.title { font-size: 17px; font-weight: 600; }
.header-actions { display: flex; gap: 8px; }

.dashboard-content { padding: 5px 0; }

.metrics-summary-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.metric-card {
  display: flex; align-items: center; gap: 12px; padding: 14px 16px;
  border-radius: 10px; background: #f5f7fa; border: 1px solid #ebeef5; transition: all 0.3s;
}
.metric-card.level-excellent { background: #f0f9eb; border-color: #e1f3d8; }
.metric-card.level-good { background: #ecf5ff; border-color: #d9ecff; }
.metric-card.level-fair { background: #fdf6ec; border-color: #faecd8; }
.metric-card.level-poor { background: #fef0f0; border-color: #fde2e2; }

.metric-icon-wrap {
  width: 44px; height: 44px; border-radius: 10px; display: flex;
  align-items: center; justify-content: center; color: #fff; flex-shrink: 0;
}
.metric-icon-wrap.excellent { background: linear-gradient(135deg, #67c23a, #85ce61); }
.metric-icon-wrap.good { background: linear-gradient(135deg, #409eff, #79bbff); }
.metric-icon-wrap.fair { background: linear-gradient(135deg, #e6a23c, #ebb563); }
.metric-icon-wrap.poor { background: linear-gradient(135deg, #f56c6c, #f78989); }

.metric-info { flex: 1; min-width: 0; }
.metric-name { font-size: 12px; color: #909399; margin-bottom: 3px; }
.metric-value-row { display: flex; align-items: baseline; gap: 3px; }
.metric-value { font-size: 22px; font-weight: 700; color: #303133; }
.metric-unit { font-size: 12px; color: #909399; }
.metric-trend { font-size: 11px; margin-top: 2px; }
.metric-trend.up { color: #f56c6c; }
.metric-trend.down { color: #67c23a; }
.metric-trend.stable { color: #909399; }

.metric-gauge { flex-shrink: 0; }
.gauge-svg { width: 44px; height: 44px; }

.dashboard-grid { display: grid; grid-template-columns: 1.5fr 1fr; gap: 20px; margin-top: 5px; }
.section-title { font-weight: 600; font-size: 14px; color: #303133; margin-bottom: 12px; }
.section-header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }

.trend-chart-area { background: #fafbfc; border: 1px solid #ebeef5; border-radius: 8px; padding: 10px; }
.trend-chart-svg { width: 100%; height: 180px; }
.chart-legend { display: flex; gap: 16px; margin-top: 8px; justify-content: center; }
.legend-item { display: flex; align-items: center; gap: 5px; font-size: 11px; color: #909399; }
.dot { width: 8px; height: 8px; border-radius: 50%; }

.funnel-container { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.funnel-step { transition: all 0.3s ease; }
.funnel-bar {
  display: flex; align-items: center; justify-content: center; gap: 8px;
  padding: 10px 16px; border-radius: 8px; color: #fff; font-size: 13px; font-weight: 500;
  min-width: 160px; text-align: center;
}
.funnel-0 { background: linear-gradient(135deg, #409eff, #79bbff); }
.funnel-1 { background: linear-gradient(135deg, #67c23a, #85ce61); }
.funnel-2 { background: linear-gradient(135deg, #e6a23c, #ebb563); }
.funnel-3 { background: linear-gradient(135deg, #f56c6c, #f78989); }
.funnel-4 { background: linear-gradient(135deg, #909399, #b0b3b8); }
.funel-rate { font-weight: 700; }
.funnel-dropoff { font-size: 11px; color: #f56c6c; margin-top: 2px; }

.bottom-grid { display: grid; grid-template-columns: 1fr 1fr 0.8fr; gap: 16px; margin-top: 5px; }
.error-bars { display: flex; flex-direction: column; gap: 8px; }
.error-bar-item { display: flex; align-items: center; gap: 8px; }
.error-bar-label { width: 90px; font-size: 12px; color: #606266; white-space: nowrap; }
.error-bar-track { flex: 1; height: 18px; background: #f0f2f5; border-radius: 4px; overflow: hidden; }
.error-bar-fill { height: 100%; border-radius: 4px; background: linear-gradient(90deg, #f56c6c, #f78989); transition: width 0.5s; }
.error-bar-count { width: 36px; text-align: right; font-size: 12px; font-weight: 600; color: #303133; }
.error-count-label { font-size: 13px; color: #606266; }

.pages-list { display: flex; flex-direction: column; gap: 8px; }
.page-item { display: flex; align-items: center; gap: 10px; padding: 8px 10px; background: #f5f7fa; border-radius: 6px; }
.page-rank { width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; flex-shrink: 0; }
.rank-1 { background: #fdf6ec; color: #e6a23c; }
.rank-2 { background: #f0f2f5; color: #909399; }
.rank-3 { background: #fef0f0; color: #f56c6c; }
.page-rank:not(.rank-1):not(.rank-2):not(.rank-3) { background: #ecf5ff; color: #409eff; }
.page-info { flex: 1; min-width: 0; }
.page-name { font-size: 13px; font-weight: 500; color: #303133; }
.page-path { font-size: 11px; color: #909399; }
.page-stats { display: flex; flex-direction: column; align-items: flex-end; gap: 2px; }
.page-views { font-size: 12px; font-weight: 600; color: #303133; }
.page-duration { font-size: 10px; color: #909399; }

.device-charts { display: flex; flex-direction: column; gap: 10px; }
.device-item { display: flex; align-items: center; gap: 8px; }
.device-label { width: 48px; font-size: 12px; color: #606266; }
.device-bar-track { flex: 1; height: 14px; background: #f0f2f5; border-radius: 3px; overflow: hidden; }
.device-bar-fill { height: 100%; border-radius: 3px; transition: width 0.5s; }
.device-percent { width: 36px; font-size: 12px; font-weight: 600; color: #303133; text-align: right; }
.device-count { width: 36px; font-size: 11px; color: #909399; text-align: right; }

@media (max-width: 1024px) {
  .metrics-summary-row { grid-template-columns: repeat(2, 1fr); }
  .dashboard-grid { grid-template-columns: 1fr; }
  .bottom-grid { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 640px) {
  .metrics-summary-row { grid-template-columns: 1fr; }
  .bottom-grid { grid-template-columns: 1fr; }
}
</style>
