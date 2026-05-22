<template>
  <div class="quality-dashboard">
    <el-card class="dashboard-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span class="title">质量监控仪表板</span>
            <el-tag :type="overallScoreType" effect="dark" size="large">
              {{ overallScoreLabel }}
            </el-tag>
          </div>
          <div class="header-actions">
            <el-button
              type="primary"
              :loading="checking"
              @click="triggerQualityCheck"
            >
              <el-icon><Refresh /></el-icon>
              质量检查
            </el-button>
            <el-button
              type="warning"
              :loading="gateChecking"
              @click="quickGateCheck"
            >
              <el-icon><CircleCheck /></el-icon>
              门禁检查
            </el-button>
            <el-button
              type="success"
              :loading="generatingReport"
              @click="quickGenerateReport"
            >
              <el-icon><Download /></el-icon>
              生成报告
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
            <div class="score-circle" :class="scoreClass">
              <div class="score-value">{{ dashboard?.overall_score?.toFixed(1) || 0 }}</div>
              <div class="score-label">总体质量分数</div>
            </div>
            <div class="score-details">
              <div class="detail-item">
                <span class="detail-label">最后更新</span>
                <span class="detail-value">{{ formatTime(dashboard?.last_updated) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">活跃告警</span>
                <span class="detail-value alert-count" :class="{ 'has-alerts': activeAlertsCount > 0 }">
                  {{ activeAlertsCount }}
                </span>
              </div>
              <div class="detail-item">
                <span class="detail-label">性能状态</span>
                <el-tag :type="performanceStatusType" size="small">
                  {{ performanceStatusLabel }}
                </el-tag>
              </div>
              <div class="detail-item">
                <span class="detail-label">错误率</span>
                <span class="detail-value" :class="errorRateClass">
                  {{ dashboard?.errors?.error_rate?.toFixed(2) || 0 }}%
                </span>
              </div>
            </div>
          </div>

          <div v-if="realtimeSummary" class="realtime-badge-row">
            <el-tag type="success" effect="plain" size="small">
              实时: {{ realtimeSummary.overall_health === 'excellent' ? '优秀' : realtimeSummary.overall_health === 'good' ? '良好' : realtimeSummary.overall_health === 'fair' ? '一般' : '需改进' }}
            </el-tag>
            <el-tag :type="gateResult?.overall_status === 'passed' ? 'success' : gateResult?.overall_status === 'warning' ? 'warning' : 'danger'" effect="plain" size="small">
              门禁: {{ gateResult?.overall_status === 'passed' ? '通过' : gateResult?.overall_status === 'warning' ? '警告' : '未通过' }}
            </el-tag>
            <el-tag type="info" effect="plain" size="small">
              告警: {{ realtimeSummary.active_alerts_count }}
            </el-tag>
          </div>
        </div>

        <el-divider />

        <div class="metrics-section">
          <div class="section-title">核心指标</div>
          <el-row :gutter="16">
            <el-col :span="6" v-for="metric in coreMetrics" :key="metric.key">
              <div class="metric-card" :class="metric.status">
                <div class="metric-header">
                  <el-icon class="metric-icon" :size="24">
                    <component :is="metric.icon" />
                  </el-icon>
                  <span class="metric-name">{{ metric.label }}</span>
                </div>
                <div class="metric-value">{{ formatMetricValue(metric) }}</div>
                <el-progress
                  :percentage="metric.percentage || 0"
                  :stroke-width="8"
                  :color="getProgressColor(metric.percentage)"
                  :show-text="false"
                />
                <div class="metric-status">
                  <el-tag :type="getMetricTagType(metric.status)" size="small">
                    {{ getMetricStatusLabel(metric.status) }}
                  </el-tag>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>

        <el-divider />

        <div class="performance-section">
          <div class="section-title">性能指标</div>
          <el-row :gutter="16">
            <el-col :span="8">
              <div class="perf-card">
                <div class="perf-title">响应时间</div>
                <div class="perf-metrics">
                  <div class="perf-item">
                    <span class="perf-label">平均</span>
                    <span class="perf-value">{{ dashboard?.performance?.avg_response_time_ms?.toFixed(2) || 0 }} ms</span>
                  </div>
                  <div class="perf-item">
                    <span class="perf-label">P95</span>
                    <span class="perf-value">{{ dashboard?.performance?.p95_response_time_ms?.toFixed(2) || 0 }} ms</span>
                  </div>
                  <div class="perf-item">
                    <span class="perf-label">P99</span>
                    <span class="perf-value">{{ dashboard?.performance?.p99_response_time_ms?.toFixed(2) || 0 }} ms</span>
                  </div>
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="perf-card">
                <div class="perf-title">吞吐量</div>
                <div class="perf-metrics">
                  <div class="perf-item">
                    <span class="perf-label">请求/秒</span>
                    <span class="perf-value">{{ dashboard?.performance?.throughput_per_sec?.toFixed(2) || 0 }}</span>
                  </div>
                  <div class="perf-item">
                    <span class="perf-label">总请求</span>
                    <span class="perf-value">{{ dashboard?.performance?.total_request_count || 0 }}</span>
                  </div>
                  <div class="perf-item">
                    <span class="perf-label">慢请求</span>
                    <span class="perf-value perf-warning">{{ dashboard?.performance?.slow_request_count || 0 }}</span>
                  </div>
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="perf-card">
                <div class="perf-title">错误统计</div>
                <div class="perf-metrics">
                  <div class="perf-item">
                    <span class="perf-label">错误率</span>
                    <span class="perf-value" :class="errorRateClass">{{ dashboard?.performance?.error_rate_percent?.toFixed(2) || 0 }}%</span>
                  </div>
                  <div class="perf-item">
                    <span class="perf-label">总错误</span>
                    <span class="perf-value">{{ dashboard?.errors?.total_errors || 0 }}</span>
                  </div>
                  <div class="perf-item">
                    <span class="perf-label">最近错误</span>
                    <span class="perf-value">{{ dashboard?.errors?.recent_errors?.length || 0 }}</span>
                  </div>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>

        <el-divider />

        <div class="charts-section">
          <div class="section-title">趋势图表</div>
          <el-row :gutter="16">
            <el-col :span="12">
              <div class="chart-card">
                <div id="error-trend-chart" style="width: 100%; height: 300px;"></div>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="chart-card">
                <div id="coverage-trend-chart" style="width: 100%; height: 300px;"></div>
              </div>
            </el-col>
          </el-row>
        </div>

        <el-divider />

        <div class="actions-section">
          <div class="section-title">高级功能</div>
          <el-row :gutter="16">
            <el-col :span="6">
              <el-button type="primary" @click="showTrendDialog" style="width: 100%">
                <el-icon><TrendChartsIcon /></el-icon>
                查看趋势
              </el-button>
            </el-col>
            <el-col :span="6">
              <el-button type="success" @click="showReportDialog" style="width: 100%">
                <el-icon><Download /></el-icon>
                生成报告
              </el-button>
            </el-col>
            <el-col :span="6">
              <el-button type="warning" @click="showBenchmarkDialog" style="width: 100%">
                <el-icon><DataAnalysis /></el-icon>
                基准对比
              </el-button>
            </el-col>
            <el-col :span="6">
              <el-button type="info" @click="showPredictionDialog" style="width: 100%">
                <el-icon><Aim /></el-icon>
                质量预测
              </el-button>
            </el-col>
          </el-row>
        </div>

        <el-divider />

        <div class="quality-section">
          <div class="section-title">代码质量</div>
          <el-row :gutter="16">
            <el-col :span="12">
              <div class="quality-card">
                <div class="quality-header">
                  <span class="quality-title">质量评分</span>
                  <el-tag :type="codeQualityType" size="small">
                    {{ dashboard?.code_quality?.overall_score?.toFixed(1) || 0 }} 分
                  </el-tag>
                </div>
                <div class="quality-items">
                  <div class="quality-item">
                    <span class="quality-label">可维护性指数</span>
                    <el-progress
                      :percentage="dashboard?.code_quality?.maintainability_index || 0"
                      :color="getProgressColor(dashboard?.code_quality?.maintainability_index)"
                    />
                  </div>
                  <div class="quality-item">
                    <span class="quality-label">圈复杂度</span>
                    <span class="quality-value">{{ dashboard?.code_quality?.cyclomatic_complexity?.toFixed(1) || 0 }}</span>
                  </div>
                  <div class="quality-item">
                    <span class="quality-label">代码重复率</span>
                    <span class="quality-value">{{ dashboard?.code_quality?.code_duplication_percent?.toFixed(1) || 0 }}%</span>
                  </div>
                  <div class="quality-item">
                    <span class="quality-label">技术债务</span>
                    <span class="quality-value">{{ dashboard?.code_quality?.technical_debt_hours?.toFixed(1) || 0 }} 小时</span>
                  </div>
                </div>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="quality-card">
                <div class="quality-header">
                  <span class="quality-title">测试覆盖率</span>
                  <el-tag :type="coverageType" size="small">
                    {{ dashboard?.test_coverage?.line_coverage_percent?.toFixed(1) || 0 }}%
                  </el-tag>
                </div>
                <div class="quality-items">
                  <div class="quality-item">
                    <span class="quality-label">行覆盖率</span>
                    <el-progress
                      :percentage="dashboard?.test_coverage?.line_coverage_percent || 0"
                      :color="getProgressColor(dashboard?.test_coverage?.line_coverage_percent)"
                    />
                  </div>
                  <div class="quality-item">
                    <span class="quality-label">分支覆盖率</span>
                    <el-progress
                      :percentage="dashboard?.test_coverage?.branch_coverage_percent || 0"
                      :color="getProgressColor(dashboard?.test_coverage?.branch_coverage_percent)"
                    />
                  </div>
                  <div class="quality-item">
                    <span class="quality-label">函数覆盖率</span>
                    <el-progress
                      :percentage="dashboard?.test_coverage?.function_coverage_percent || 0"
                      :color="getProgressColor(dashboard?.test_coverage?.function_coverage_percent)"
                    />
                  </div>
                  <div class="quality-item">
                    <span class="quality-label">未覆盖文件</span>
                    <span class="quality-value">{{ dashboard?.test_coverage?.uncovered_files?.length || 0 }} 个</span>
                  </div>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>

        <el-divider v-if="dashboard?.active_alerts?.length" />

        <div v-if="dashboard?.active_alerts?.length" class="alerts-section">
          <div class="section-header">
            <span class="section-title">活跃告警</span>
            <el-badge :value="activeAlertsCount" type="danger" />
          </div>
          <div class="alerts-list">
            <div
              v-for="alert in dashboard.active_alerts"
              :key="alert.alert_id"
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
                <div class="alert-desc">{{ alert.message }}</div>
                <div class="alert-meta">
                  <span class="meta-item">{{ alert.metric_type }}</span>
                  <span class="meta-item">{{ formatTime(alert.timestamp) }}</span>
                </div>
              </div>
              <div class="alert-actions">
                <el-button
                  v-if="!alert.acknowledged"
                  type="primary"
                  size="small"
                  @click="acknowledgeAlert(alert.alert_id)"
                >
                  确认
                </el-button>
                <el-button
                  type="success"
                  size="small"
                  @click="resolveAlert(alert.alert_id)"
                >
                  解决
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <el-divider v-if="realtimeAlerts.length > 0" />

        <div v-if="realtimeAlerts.length > 0" class="realtime-alerts-panel">
          <div class="section-header">
            <span class="section-title">实时告警流 (WebSocket)</span>
            <el-badge :value="realtimeAlerts.length" type="danger" />
            <el-button type="danger" link size="small" @click="realtimeAlerts = []">清空</el-button>
          </div>
          <div class="rt-alerts-scroll">
            <div
              v-for="alert in realtimeAlerts"
              :key="alert.alert_id + '-' + alert.timestamp"
              class="rt-alert-item"
              :class="'rt-' + alert.severity"
            >
              <span class="rt-sev-tag">{{ alert.severity === 'critical' ? '严重' : alert.severity === 'error' ? '错误' : alert.severity === 'warning' ? '警告' : '信息' }}</span>
              <span class="rt-msg">{{ alert.title }}: {{ alert.message }}</span>
              <span class="rt-time">{{ formatRelativeTime(alert.timestamp) }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <el-dialog v-model="trendDialogVisible" title="质量指标趋势" width="80%">
      <div class="trend-controls">
        <el-select v-model="selectedMetricType" placeholder="选择指标类型" style="width: 200px">
          <el-option label="性能" value="performance" />
          <el-option label="错误率" value="error_rate" />
          <el-option label="代码质量" value="code_quality" />
          <el-option label="测试覆盖率" value="test_coverage" />
        </el-select>
        <el-input-number v-model="historyDays" :min="1" :max="30" style="width: 150px; margin-left: 20px" />
        <span style="margin-left: 10px">天</span>
      </div>
      <div id="trend-chart" style="width: 100%; height: 400px; margin-top: 20px"></div>
    </el-dialog>

    <el-dialog v-model="reportDialogVisible" title="生成质量报告" width="60%">
      <el-form :model="reportConfig" label-width="120px">
        <el-form-item label="报告类型">
          <el-select v-model="reportConfig.reportType" style="width: 100%">
            <el-option label="日报" value="daily" />
            <el-option label="周报" value="weekly" />
            <el-option label="月报" value="monthly" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker
            v-model="reportConfig.startDate"
            type="datetime"
            placeholder="选择开始日期"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker
            v-model="reportConfig.endDate"
            type="datetime"
            placeholder="选择结束日期"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reportDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="generatingReport" @click="generateReport">
          生成报告
        </el-button>
      </template>
      <div v-if="reportData" class="report-preview">
        <el-divider />
        <h3>报告预览</h3>
        <div class="report-content">
          <p><strong>报告ID:</strong> {{ reportData.report_id }}</p>
          <p><strong>总体质量分数:</strong> {{ reportData.overall_score?.toFixed(2) }}</p>
          <p><strong>生成时间:</strong> {{ formatTime(reportData.generated_at) }}</p>
          <div v-if="reportData.issues_found?.length">
            <h4>发现的问题:</h4>
            <ul>
              <li v-for="issue in reportData.issues_found" :key="issue.type">
                {{ issue.description }} (严重度: {{ issue.severity }})
              </li>
            </ul>
          </div>
          <div v-if="reportData.recommendations?.length">
            <h4>改进建议:</h4>
            <ul>
              <li v-for="rec in reportData.recommendations" :key="rec">{{ rec }}</li>
            </ul>
          </div>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="benchmarkDialogVisible" title="质量基准对比" width="70%">
      <div class="benchmark-controls">
        <el-select v-model="benchmarkCategory" placeholder="选择类别" clearable style="width: 200px">
          <el-option label="性能" value="performance" />
          <el-option label="质量" value="quality" />
          <el-option label="覆盖率" value="coverage" />
        </el-select>
        <el-button type="primary" @click="loadBenchmarks" style="margin-left: 20px">
          刷新
        </el-button>
      </div>
      <el-table :data="benchmarks" style="width: 100%; margin-top: 20px">
        <el-table-column prop="metric_name" label="指标名称" width="180" />
        <el-table-column prop="current_value" label="当前值" width="120">
          <template #default="{ row }">
            {{ row.current_value?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="benchmark_value" label="基准值" width="120">
          <template #default="{ row }">
            {{ row.benchmark_value?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="deviation" label="偏差(%)" width="120">
          <template #default="{ row }">
            <span :style="{ color: row.deviation > 0 ? '#67c23a' : '#f56c6c' }">
              {{ row.deviation > 0 ? '+' : '' }}{{ row.deviation?.toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tag :color="getBenchmarkStatusColor(row.status)" style="color: white">
              {{ getBenchmarkStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <el-dialog v-model="predictionDialogVisible" title="质量预测" width="60%">
      <el-form :model="predictionConfig" label-width="120px">
        <el-form-item label="指标类型">
          <el-select v-model="predictionConfig.metricType" style="width: 100%">
            <el-option label="性能" value="performance" />
            <el-option label="错误率" value="error_rate" />
            <el-option label="代码质量" value="code_quality" />
            <el-option label="测试覆盖率" value="test_coverage" />
          </el-select>
        </el-form-item>
        <el-form-item label="预测范围">
          <el-select v-model="predictionConfig.predictionHorizon" style="width: 100%">
            <el-option label="1小时" value="1h" />
            <el-option label="24小时" value="24h" />
            <el-option label="7天" value="7d" />
            <el-option label="30天" value="30d" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="predictionDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="predicting" @click="predictQuality">
          开始预测
        </el-button>
      </template>
      <div v-if="predictionResult" class="prediction-result">
        <el-divider />
        <h3>预测结果</h3>
        <div class="prediction-content">
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="prediction-item">
                <span class="label">当前值:</span>
                <span class="value">{{ predictionResult.current_value?.toFixed(2) }}</span>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="prediction-item">
                <span class="label">预测值:</span>
                <span class="value">{{ predictionResult.predicted_value?.toFixed(2) }}</span>
              </div>
            </el-col>
          </el-row>
          <el-row :gutter="20" style="margin-top: 20px">
            <el-col :span="12">
              <div class="prediction-item">
                <span class="label">置信度:</span>
                <span class="value">{{ (predictionResult.confidence * 100)?.toFixed(2) }}%</span>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="prediction-item">
                <span class="label">趋势:</span>
                <el-tag :color="getTrendColor(predictionResult.trend)" style="color: white">
                  {{ getTrendIcon(predictionResult.trend) }} {{ predictionResult.trend }}
                </el-tag>
              </div>
            </el-col>
          </el-row>
          <div v-if="predictionResult.factors?.length" style="margin-top: 20px">
            <h4>影响因素:</h4>
            <ul>
              <li v-for="factor in predictionResult.factors" :key="factor">{{ factor }}</li>
            </ul>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh,
  Timer,
  CircleCheck,
  CircleClose,
  Warning,
  TrendCharts,
  Timer as TimerIcon,
  Connection,
  Cpu,
  Document,
  DataLine,
  Monitor,
  Download,
  TrendCharts as TrendChartsIcon,
  DataAnalysis,
  Aim
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import api from '@/api'
import { realtimeQualityApi, qualityGateApi, reportGenerateApi, type RealtimeSummary, type QualityGateResult, type QualityAlertItem } from '@/api'
import { useWebSocket, ConnectionState } from '@/composables/useWebSocket'

interface PerformanceMetrics {
  avg_response_time_ms: number
  p95_response_time_ms: number
  p99_response_time_ms: number
  throughput_per_sec: number
  error_rate_percent: number
  slow_request_count: number
  total_request_count: number
}

interface ErrorStatistics {
  total_errors: number
  error_rate: number
  recent_errors: Array<any>
}

interface CodeQualityScore {
  overall_score: number
  maintainability_index: number
  cyclomatic_complexity: number
  code_duplication_percent: number
  technical_debt_hours: number
}

interface TestCoverageMetrics {
  line_coverage_percent: number
  branch_coverage_percent: number
  function_coverage_percent: number
  uncovered_files: string[]
}

interface QualityAlert {
  alert_id: string
  metric_type: string
  severity: 'info' | 'warning' | 'error' | 'critical'
  title: string
  message: string
  timestamp: string
  acknowledged: boolean
}

interface QualityDashboard {
  overall_score: number
  performance: PerformanceMetrics
  errors: ErrorStatistics
  code_quality: CodeQualityScore
  test_coverage: TestCoverageMetrics
  active_alerts: QualityAlert[]
  last_updated: string
}

const checking = ref(false)
const autoRefresh = ref(true)
const dashboard = ref<QualityDashboard | null>(null)
const gateChecking = ref(false)
const generatingReport = ref(false)
const realtimeSummary = ref<RealtimeSummary | null>(null)
const gateResult = ref<QualityGateResult | null>(null)
const realtimeAlerts = ref<QualityAlertItem[]>([])

let refreshTimer: ReturnType<typeof setInterval> | null = null
let websocket: WebSocket | null = null
let trendChart: echarts.ECharts | null = null
let errorTrendChart: echarts.ECharts | null = null
let coverageTrendChart: echarts.ECharts | null = null

const trendDialogVisible = ref(false)
const historyDialogVisible = ref(false)
const reportDialogVisible = ref(false)
const benchmarkDialogVisible = ref(false)
const predictionDialogVisible = ref(false)

const selectedMetricType = ref('performance')
const historyDays = ref(7)
const trendData = ref<any[]>([])
const reportConfig = ref({
  reportType: 'daily',
  startDate: null as Date | null,
  endDate: null as Date | null
})
const reportData = ref<any>(null)
const generatingReport = ref(false)

const benchmarkCategory = ref('')
const benchmarks = ref<any[]>([])

const predictionConfig = ref({
  metricType: 'performance',
  predictionHorizon: '24h'
})
const predictionResult = ref<any>(null)
const predicting = ref(false)

const qualityHistory = ref<any[]>([])
const comparisonConfig = ref({
  baselineDate: null as Date | null,
  currentDate: null as Date | null,
  metrics: ['performance', 'error_rate', 'code_quality', 'test_coverage']
})
const comparisonResult = ref<any>(null)
const comparing = ref(false)

const selectedAlerts = ref<string[]>([])

const overallScoreType = computed(() => {
  const score = dashboard.value?.overall_score || 0
  if (score >= 80) return 'success'
  if (score >= 60) return 'primary'
  if (score >= 40) return 'warning'
  return 'danger'
})

const overallScoreLabel = computed(() => {
  const score = dashboard.value?.overall_score || 0
  if (score >= 80) return '优秀'
  if (score >= 60) return '良好'
  if (score >= 40) return '一般'
  return '需改进'
})

const scoreClass = computed(() => {
  const score = dashboard.value?.overall_score || 0
  if (score >= 80) return 'score-excellent'
  if (score >= 60) return 'score-good'
  if (score >= 40) return 'score-fair'
  return 'score-poor'
})

const activeAlertsCount = computed(() => {
  return dashboard.value?.active_alerts?.filter(a => !a.acknowledged).length || 0
})

const performanceStatusType = computed(() => {
  const avgTime = dashboard.value?.performance?.avg_response_time_ms || 0
  if (avgTime <= 200) return 'success'
  if (avgTime <= 500) return 'warning'
  return 'danger'
})

const performanceStatusLabel = computed(() => {
  const avgTime = dashboard.value?.performance?.avg_response_time_ms || 0
  if (avgTime <= 200) return '优秀'
  if (avgTime <= 500) return '一般'
  return '需优化'
})

const errorRateClass = computed(() => {
  const rate = dashboard.value?.errors?.error_rate || 0
  if (rate <= 1) return 'rate-good'
  if (rate <= 5) return 'rate-warning'
  return 'rate-critical'
})

const codeQualityType = computed(() => {
  const score = dashboard.value?.code_quality?.overall_score || 0
  if (score >= 80) return 'success'
  if (score >= 60) return 'warning'
  return 'danger'
})

const coverageType = computed(() => {
  const coverage = dashboard.value?.test_coverage?.line_coverage_percent || 0
  if (coverage >= 80) return 'success'
  if (coverage >= 60) return 'warning'
  return 'danger'
})

const coreMetrics = computed(() => {
  if (!dashboard.value) return []

  return [
    {
      key: 'performance',
      label: '性能',
      value: dashboard.value.performance?.avg_response_time_ms || 0,
      unit: 'ms',
      percentage: Math.max(0, 100 - (dashboard.value.performance?.avg_response_time_ms || 0) / 10),
      status: dashboard.value.performance?.avg_response_time_ms <= 200 ? 'good' : 
              dashboard.value.performance?.avg_response_time_ms <= 500 ? 'warning' : 'critical',
      icon: TrendCharts
    },
    {
      key: 'error_rate',
      label: '错误率',
      value: dashboard.value.errors?.error_rate || 0,
      unit: '%',
      percentage: Math.max(0, 100 - (dashboard.value.errors?.error_rate || 0) * 10),
      status: dashboard.value.errors?.error_rate <= 1 ? 'good' : 
              dashboard.value.errors?.error_rate <= 5 ? 'warning' : 'critical',
      icon: Warning
    },
    {
      key: 'code_quality',
      label: '代码质量',
      value: dashboard.value.code_quality?.overall_score || 0,
      unit: '分',
      percentage: dashboard.value.code_quality?.overall_score || 0,
      status: dashboard.value.code_quality?.overall_score >= 80 ? 'good' : 
              dashboard.value.code_quality?.overall_score >= 60 ? 'warning' : 'critical',
      icon: Document
    },
    {
      key: 'test_coverage',
      label: '测试覆盖率',
      value: dashboard.value.test_coverage?.line_coverage_percent || 0,
      unit: '%',
      percentage: dashboard.value.test_coverage?.line_coverage_percent || 0,
      status: dashboard.value.test_coverage?.line_coverage_percent >= 80 ? 'good' : 
              dashboard.value.test_coverage?.line_coverage_percent >= 60 ? 'warning' : 'critical',
      icon: CircleCheck
    }
  ]
})

const formatTime = (time: string | undefined): string => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const formatRelativeTime = (timestamp: string): string => {
  const date = new Date(timestamp)
  const diff = Date.now() - date.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  return date.toLocaleTimeString('zh-CN')
}

const formatMetricValue = (metric: any): string => {
  return `${metric.value.toFixed(1)}${metric.unit}`
}

const getProgressColor = (value: number | undefined): string => {
  if (value === undefined) return '#909399'
  if (value >= 80) return '#67c23a'
  if (value >= 60) return '#e6a23c'
  return '#f56c6c'
}

const getMetricTagType = (status: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    good: 'success',
    warning: 'warning',
    critical: 'danger'
  }
  return types[status] || 'info'
}

const getMetricStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    good: '良好',
    warning: '一般',
    critical: '需改进'
  }
  return labels[status] || '未知'
}

const getAlertIcon = (severity: string) => {
  const icons: Record<string, any> = {
    info: CircleCheck,
    warning: Warning,
    error: CircleClose,
    critical: CircleClose
  }
  return icons[severity] || Warning
}

const fetchDashboard = async () => {
  try {
    const response = await api.get('/quality/dashboard')
    dashboard.value = response
  } catch (error) {
    console.error('Failed to fetch quality dashboard:', error)
  }
}

const fetchRealtimeData = async () => {
  try {
    const [summary, gate] = await Promise.all([
      realtimeQualityApi.getRealtimeSummary(),
      qualityGateApi.check()
    ])
    realtimeSummary.value = summary
    gateResult.value = gate
  } catch (error) {
    console.error('Failed to fetch realtime data:', error)
  }
}

const quickGateCheck = async () => {
  gateChecking.value = true
  try {
    gateResult.value = await qualityGateApi.forceRecheck()
    ElMessage.success(`门禁检查完成: ${gateResult.value?.overall_status === 'passed' ? '通过' : '未通过'}`)
  } catch (error) {
    console.error('Gate check failed:', error)
    ElMessage.error('门禁检查失败')
  } finally {
    gateChecking.value = false
  }
}

const quickGenerateReport = async () => {
  generatingReport.value = true
  try {
    const result = await reportGenerateApi.generate({
      report_type: 'daily',
      start_date: null,
      end_date: null,
      include_charts: true,
      include_recommendations: true
    })
    ElMessage.success(`报告已生成: ${result.report_id}`)
    reportData.value = result.summary
    reportDialogVisible.value = true
  } catch (error) {
    console.error('Report generation failed:', error)
    ElMessage.error('报告生成失败')
  } finally {
    generatingReport.value = false
  }
}

const triggerQualityCheck = async () => {
  checking.value = true
  try {
    await api.post('/quality/check')
    ElMessage.success('质量检查已触发')
    await fetchDashboard()
  } catch (error) {
    console.error('Failed to trigger quality check:', error)
    ElMessage.error('质量检查失败')
  } finally {
    checking.value = false
  }
}

const acknowledgeAlert = async (alertId: string) => {
  try {
    await api.post(`/quality/alerts/${alertId}/acknowledge`)
    ElMessage.success('告警已确认')
    await fetchDashboard()
  } catch (error) {
    console.error('Failed to acknowledge alert:', error)
    ElMessage.error('确认失败')
  }
}

const generateReport = async () => {
  generatingReport.value = true
  try {
    const response = await api.post('/quality-monitor/report/generate', null, {
      params: {
        report_type: reportConfig.value.reportType,
        start_date: reportConfig.value.startDate,
        end_date: reportConfig.value.endDate
      }
    })
    
    reportData.value = response
    ElMessage.success('报告已生成')
    reportDialogVisible.value = true
  } catch (error) {
    console.error('生成报告失败:', error)
    ElMessage.error('生成报告失败')
  } finally {
    generatingReport.value = false
  }
}

const loadBenchmarks = async () => {
  try {
    const response = await api.get('/quality-monitor/benchmark', {
      params: {
        category: benchmarkCategory.value
      }
    })
    
    benchmarks.value = response
  } catch (error) {
    console.error('加载基准数据失败:', error)
    ElMessage.error('加载基准数据失败')
  }
}

const predictQuality = async () => {
  if (!predictionConfig.value.metricType) {
    ElMessage.warning('请选择指标类型')
    return
  }
  
  predicting.value = true
  try {
    const response = await api.get('/quality-monitor/predict', {
      params: {
        metric_type: predictionConfig.value.metricType,
        prediction_horizon: predictionConfig.value.predictionHorizon
      }
    })
    
    predictionResult.value = response
    ElMessage.success('预测完成')
  } catch (error) {
    console.error('预测失败:', error)
    ElMessage.error('预测失败')
  } finally {
    predicting.value = false
  }
}

const loadQualityHistory = async () => {
  try {
    const response = await api.get('/quality-monitor/score/history', {
      params: {
        days: historyDays.value
      }
    })
    
    qualityHistory.value = response
  } catch (error) {
    console.error('加载历史数据失败:', error)
    ElMessage.error('加载历史数据失败')
  }
}

const compareQuality = async () => {
  if (!comparisonConfig.value.baselineDate || !comparisonConfig.value.currentDate) {
    ElMessage.warning('请选择基准日期和当前日期')
    return
  }
  
  comparing.value = true
  try {
    const response = await api.post('/quality-monitor/compare', {
      baseline_date: comparisonConfig.value.baselineDate,
      current_date: comparisonConfig.value.currentDate,
      metrics: comparisonConfig.value.metrics
    })
    
    comparisonResult.value = response
    ElMessage.success('比较完成')
  } catch (error) {
    console.error('比较失败:', error)
    ElMessage.error('比较失败')
  } finally {
    comparing.value = false
  }
}

const bulkAcknowledgeAlerts = async () => {
  if (selectedAlerts.value.length === 0) {
    ElMessage.warning('请选择要确认的告警')
    return
  }
  
  try {
    await api.post('/quality-monitor/alerts/bulk-acknowledge', null, {
      params: {
        alert_ids: selectedAlerts.value
      }
    })
    
    ElMessage.success(`已确认 ${selectedAlerts.value.length} 个告警`)
    selectedAlerts.value = []
    await fetchDashboard()
  } catch (error) {
    console.error('批量确认失败:', error)
    ElMessage.error('批量确认失败')
  }
}

const bulkResolveAlerts = async () => {
  if (selectedAlerts.value.length === 0) {
    ElMessage.warning('请选择要解决的告警')
    return
  }
  
  try {
    await ElMessageBox.confirm('确定要解决选中的告警吗？', '确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.post('/quality-monitor/alerts/bulk-resolve', null, {
      params: {
        alert_ids: selectedAlerts.value
      }
    })
    
    ElMessage.success(`已解决 ${selectedAlerts.value.length} 个告警`)
    selectedAlerts.value = []
    await fetchDashboard()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量解决失败:', error)
      ElMessage.error('批量解决失败')
    }
  }
}

const showReportDialog = () => {
  reportDialogVisible.value = true
}

const showBenchmarkDialog = () => {
  benchmarkDialogVisible.value = true
  loadBenchmarks()
}

const showPredictionDialog = () => {
  predictionDialogVisible.value = true
}

const showHistoryDialog = () => {
  historyDialogVisible.value = true
  loadQualityHistory()
}

const showComparisonDialog = () => {
  comparisonDialogVisible.value = true
}

const getBenchmarkStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    'excellent': '#67C23A',
    'good': '#409EFF',
    'needs_improvement': '#F56C6C'
  }
  return colors[status] || '#909399'
}

const getBenchmarkStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    'excellent': '优秀',
    'good': '良好',
    'needs_improvement': '需改进'
  }
  return labels[status] || '未知'
}

const getTrendIcon = (trend: string): string => {
  const icons: Record<string, string> = {
    'improving': '↑',
    'stable': '→',
    'declining': '↓'
  }
  return icons[trend] || '→'
}

const getTrendColor = (trend: string): string => {
  const colors: Record<string, string> = {
    'improving': '#67C23A',
    'stable': '#909399',
    'declining': '#F56C6C'
  }
  return colors[trend] || '#909399'
}

const resolveAlert = async (alertId: string) => {
  try {
    await api.post(`/quality/alerts/${alertId}/resolve`)
    ElMessage.success('告警已解决')
    await fetchDashboard()
  } catch (error) {
    console.error('Failed to resolve alert:', error)
    ElMessage.error('解决失败')
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

const startAutoRefresh = () => {
  if (autoRefresh.value && !refreshTimer) {
    refreshTimer = setInterval(fetchDashboard, 10000)
  }
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

const connectWebSocket = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/api/quality/realtime`
  
  websocket = new WebSocket(wsUrl)
  
  websocket.onopen = () => {
    console.log('WebSocket connected')
  }
  
  websocket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'quality_update') {
        dashboard.value = data.data
        if (data.data?.key_metrics) {
          realtimeSummary.value = { ...realtimeSummary.value, key_metrics: data.data.key_metrics, timestamp: data.data.timestamp || new Date().toISOString() } as any
        }
      } else if (data.type === 'alert') {
        ElMessage.warning(`新告警: ${data.data.title}`)
        realtimeAlerts.value.unshift(data.data)
        if (realtimeAlerts.value.length > 30) realtimeAlerts.value.pop()
        fetchDashboard()
      } else if (data.type === 'gate_update') {
        gateResult.value = data.data
      } else if (data.type === 'summary_update') {
        realtimeSummary.value = data.data
      }
    } catch (error) {
      console.error('WebSocket message parse error:', error)
    }
  }
  
  websocket.onerror = (error) => {
    console.error('WebSocket error:', error)
  }
  
  websocket.onclose = () => {
    console.log('WebSocket disconnected')
    setTimeout(() => {
      if (autoRefresh.value) {
        connectWebSocket()
      }
    }, 5000)
  }
}

const disconnectWebSocket = () => {
  if (websocket) {
    websocket.close()
    websocket = null
  }
}

const loadTrendData = async () => {
  try {
    const response = await api.get('/quality/metrics/trend', {
      params: {
        metric_type: selectedMetricType.value,
        hours: historyDays.value * 24
      }
    })
    trendData.value = response.trend || []
    await nextTick()
    renderTrendChart()
  } catch (error) {
    console.error('Failed to load trend data:', error)
    ElMessage.error('加载趋势数据失败')
  }
}

const renderTrendChart = () => {
  const chartDom = document.getElementById('trend-chart')
  if (!chartDom) return
  
  if (!trendChart) {
    trendChart = echarts.init(chartDom)
  }
  
  const option = {
    title: {
      text: '质量指标趋势',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
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
      data: trendData.value.map(item => new Date(item.timestamp).toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      }))
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: selectedMetricType.value,
        type: 'line',
        smooth: true,
        areaStyle: {
          opacity: 0.3
        },
        data: trendData.value.map(item => item.value)
      }
    ]
  }
  
  trendChart.setOption(option)
}

const renderErrorTrendChart = () => {
  if (!dashboard.value?.errors?.error_trend) return
  
  const chartDom = document.getElementById('error-trend-chart')
  if (!chartDom) return
  
  if (!errorTrendChart) {
    errorTrendChart = echarts.init(chartDom)
  }
  
  const trend = dashboard.value.errors.error_trend
  const option = {
    title: {
      text: '错误趋势',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: trend.map((item: any) => item.hour)
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '错误数',
        type: 'bar',
        data: trend.map((item: any) => item.error_count),
        itemStyle: {
          color: '#f56c6c'
        }
      }
    ]
  }
  
  errorTrendChart.setOption(option)
}

const renderCoverageTrendChart = () => {
  if (!dashboard.value?.test_coverage?.coverage_trend) return
  
  const chartDom = document.getElementById('coverage-trend-chart')
  if (!chartDom) return
  
  if (!coverageTrendChart) {
    coverageTrendChart = echarts.init(chartDom)
  }
  
  const trend = dashboard.value.test_coverage.coverage_trend
  const option = {
    title: {
      text: '覆盖率趋势',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['行覆盖率', '分支覆盖率'],
      bottom: 0
    },
    xAxis: {
      type: 'category',
      data: trend.map((item: any) => item.date)
    },
    yAxis: {
      type: 'value',
      max: 100
    },
    series: [
      {
        name: '行覆盖率',
        type: 'line',
        data: trend.map((item: any) => item.line_coverage),
        itemStyle: {
          color: '#67c23a'
        }
      },
      {
        name: '分支覆盖率',
        type: 'line',
        data: trend.map((item: any) => item.branch_coverage),
        itemStyle: {
          color: '#409eff'
        }
      }
    ]
  }
  
  coverageTrendChart.setOption(option)
}

const showTrendDialog = () => {
  trendDialogVisible.value = true
  loadTrendData()
}

const showHistoryDialog = () => {
  historyDialogVisible.value = true
  loadQualityHistory()
}

const showReportDialog = () => {
  reportDialogVisible.value = true
}

const showBenchmarkDialog = () => {
  benchmarkDialogVisible.value = true
  loadBenchmarks()
}

const showPredictionDialog = () => {
  predictionDialogVisible.value = true
}

onMounted(async () => {
  await fetchDashboard()
  await fetchRealtimeData()
  if (autoRefresh.value) {
    startAutoRefresh()
    connectWebSocket()
  }
  await nextTick()
  renderErrorTrendChart()
  renderCoverageTrendChart()
})

onUnmounted(() => {
  stopAutoRefresh()
  disconnectWebSocket()
  if (trendChart) {
    trendChart.dispose()
  }
  if (errorTrendChart) {
    errorTrendChart.dispose()
  }
  if (coverageTrendChart) {
    coverageTrendChart.dispose()
  }
})

watch(selectedMetricType, () => {
  if (trendDialogVisible.value) {
    loadTrendData()
  }
})

watch(historyDays, () => {
  if (trendDialogVisible.value) {
    loadTrendData()
  }
})
</script>

<style scoped>
.quality-dashboard {
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

.score-circle.score-excellent { background: linear-gradient(135deg, #67c23a, #85ce61); }
.score-circle.score-good { background: linear-gradient(135deg, #409eff, #66b1ff); }
.score-circle.score-fair { background: linear-gradient(135deg, #e6a23c, #ebb563); }
.score-circle.score-poor { background: linear-gradient(135deg, #f56c6c, #f78989); }

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

.rate-good { color: #67c23a; }
.rate-warning { color: #e6a23c; }
.rate-critical { color: #f56c6c; }

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

.metric-card.good { background: #f0f9eb; border: 1px solid #c2e7b0; }
.metric-card.warning { background: #fdf6ec; border: 1px solid #faecd8; }
.metric-card.critical { background: #fef0f0; border: 1px solid #fbc4c4; }

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

.performance-section {
  padding: 10px 0;
}

.perf-card {
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.perf-title {
  font-weight: 500;
  margin-bottom: 12px;
  color: #303133;
}

.perf-metrics {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.perf-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.perf-label {
  color: #909399;
  font-size: 13px;
}

.perf-value {
  font-weight: 500;
  font-size: 14px;
}

.perf-warning {
  color: #e6a23c;
}

.quality-section {
  padding: 10px 0;
}

.quality-card {
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.quality-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.quality-title {
  font-weight: 500;
  color: #303133;
}

.quality-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.quality-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.quality-label {
  color: #606266;
  font-size: 13px;
}

.quality-value {
  font-weight: 500;
  font-size: 13px;
}

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
.alert-item.alert-error { background: #fef0f0; border-left: 3px solid #f56c6c; }
.alert-item.alert-critical { background: #fef0f0; border-left: 3px solid #f56c6c; }

.alert-icon {
  font-size: 20px;
  padding-top: 2px;
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

.charts-section {
  padding: 10px 0;
}

.chart-card {
  background: #fff;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.actions-section {
  padding: 10px 0;
}

.trend-controls {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.report-preview {
  margin-top: 20px;
}

.report-content {
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.benchmark-controls {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.prediction-result {
  margin-top: 20px;
}

.prediction-content {
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.prediction-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: #fff;
  border-radius: 4px;
}

.prediction-item .label {
  font-weight: 500;
  color: #606266;
}

.prediction-item .value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

@media (max-width: 1200px) {
  .main-score {
    flex-direction: column;
    align-items: flex-start;
  }
}

.realtime-badge-row {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.realtime-alerts-panel {
  padding: 10px 0;
}

.rt-alerts-scroll {
  max-height: 250px;
  overflow-y: auto;
}

.rt-alert-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  margin-bottom: 6px;
  border-radius: 6px;
  font-size: 13px;
}

.rt-alert-item.rt-critical { background: #fef0f0; border-left: 3px solid #f56c6c; }
.rt-alert-item.rt-error { background: #fef0f0; border-left: 3px solid #f56c6c; }
.rt-alert-item.rt-warning { background: #fdf6ec; border-left: 3px solid #e6a23c; }
.rt-alert-item.rt-info { background: #f4f4f5; border-left: 3px solid #909399; }

.rt-sev-tag {
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 11px;
  white-space: nowrap;
  color: #fff;
}

.rt-critical .rt-sev-tag { background: #f56c6c; }
.rt-error .rt-sev-tag { background: #f56c6c; }
.rt-warning .rt-sev-tag { background: #e6a23c; }
.rt-info .rt-sev-tag { background: #909399; }

.rt-msg {
  flex: 1;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rt-time {
  font-size: 11px;
  color: #909399;
  white-space: nowrap;
}
</style>
