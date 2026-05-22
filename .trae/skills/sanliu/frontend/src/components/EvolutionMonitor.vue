<template>
  <div class="evolution-monitor" :class="{ 'dark-theme': isDarkTheme }">
    <div class="page-header">
      <div class="header-left">
        <h2>演化监控</h2>
        <el-tag :type="connectionStatusType" size="small">
          {{ connectionStatusLabel }}
        </el-tag>
      </div>
      <div class="header-actions">
        <el-switch
          v-model="isDarkTheme"
          active-text="深色"
          inactive-text="浅色"
          @change="handleThemeChange"
        />
        <el-button type="primary" @click="refreshAll" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col :span="16">
        <el-card class="status-card">
          <template #header>
            <div class="card-header">
              <span>演化状态</span>
              <el-tag :type="evolutionStatusType" effect="dark">
                {{ evolutionStatusLabel }}
              </el-tag>
            </div>
          </template>
          <div class="status-content">
            <el-row :gutter="20">
              <el-col :span="8">
                <div class="status-item">
                  <div class="status-label">当前阶段</div>
                  <div class="status-value">{{ currentStageLabel }}</div>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="status-item">
                  <div class="status-label">演化进度</div>
                  <el-progress
                    :percentage="evolutionStatus.progress"
                    :stroke-width="20"
                    :color="progressColor"
                  />
                </div>
              </el-col>
              <el-col :span="8">
                <div class="status-item">
                  <div class="status-label">演化类型</div>
                  <div class="status-value">{{ evolutionTypeLabel }}</div>
                </div>
              </el-col>
            </el-row>

            <el-divider />

            <div class="metrics-grid">
              <div
                v-for="(value, key) in evolutionStatus.current_metrics"
                :key="key"
                class="metric-item"
              >
                <div class="metric-label">{{ getMetricLabel(key) }}</div>
                <div class="metric-value">{{ formatMetricValue(key, value) }}</div>
              </div>
            </div>

            <el-divider />

            <div class="active-changes" v-if="evolutionStatus.active_changes?.length">
              <div class="changes-title">正在进行的变更</div>
              <el-timeline>
                <el-timeline-item
                  v-for="(change, index) in evolutionStatus.active_changes"
                  :key="index"
                  :type="getChangeType(change.status)"
                >
                  <div class="change-item">
                    <span class="change-type">{{ change.type }}</span>
                    <el-tag size="small" :type="getChangeType(change.status)">
                      {{ change.status }}
                    </el-tag>
                  </div>
                </el-timeline-item>
              </el-timeline>
            </div>

            <el-divider />

            <div class="cycle-stage-viz">
              <div class="stage-title">循环阶段进度</div>
              <div class="stage-bar-wrapper">
                <div
                  v-for="(stage, idx) in cycleStages"
                  :key="stage.key"
                  class="stage-segment"
                  :class="{ 'stage-active': isStageActive(stage.key), 'stage-done': isStageDone(stage.key) }"
                  :style="{ flex: 1 }"
                >
                  <div class="stage-label">{{ stage.label }}</div>
                  <div class="stage-indicator" :class="'phase-' + stage.color"></div>
                </div>
              </div>
              <el-progress
                :percentage="evolutionStatus.progress"
                :stroke-width="16"
                :color="progressColor"
                :show-text="true"
                style="margin-top: 12px"
              />
            </div>

            <el-divider />

            <div class="capabilities-panel" v-if="evolutionOverview?.capabilities">
              <div class="cap-title">四大能力状态</div>
              <el-row :gutter="12">
                <el-col :span="12" v-for="(cap, key) in evolutionOverview.capabilities" :key="key">
                  <div class="cap-card" :class="cap.enabled ? 'cap-enabled' : 'cap-disabled'">
                    <div class="cap-header-row">
                      <div class="cap-icon-wrap" :class="cap.enabled ? 'icon-on' : 'icon-off'">
                        <el-icon :size="22"><component :is="getCapIcon(key)" /></el-icon>
                      </div>
                      <div class="cap-name">{{ getCapName(key) }}</div>
                      <el-tag :type="cap.enabled ? 'success' : 'info'" size="small" effect="dark">
                        {{ cap.enabled ? cap.status || '运行中' : '未启用' }}
                      </el-tag>
                    </div>
                    <div class="cap-meta" v-if="cap.last_run">
                      <span>上次运行: {{ formatTime(cap.last_run) }}</span>
                    </div>
                  </div>
                </el-col>
              </el-row>
            </div>
          </div>
        </el-card>

        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>演化趋势</span>
              <el-radio-group v-model="selectedPeriod" size="small" @change="fetchTrends">
                <el-radio-button label="24h">24小时</el-radio-button>
                <el-radio-button label="7d">7天</el-radio-button>
                <el-radio-button label="30d">30天</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div class="chart-container" ref="chartContainer">
            <div v-if="!chartReady" class="chart-loading">
              <el-icon class="is-loading"><Loading /></el-icon>
              <span>加载图表...</span>
            </div>
          </div>
          <div class="trend-info" v-if="trendData">
            <el-row :gutter="20">
              <el-col :span="8">
                <div class="trend-stat">
                  <div class="trend-label">趋势方向</div>
                  <div class="trend-value" :class="trendData.trend_direction">
                    <el-icon v-if="trendData.trend_direction === 'upward'"><Top /></el-icon>
                    <el-icon v-else-if="trendData.trend_direction === 'downward'"><Bottom /></el-icon>
                    <el-icon v-else><Minus /></el-icon>
                    {{ trendDirectionLabel }}
                  </div>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="trend-stat">
                  <div class="trend-label">变化百分比</div>
                  <div class="trend-value">{{ trendData.change_percentage.toFixed(2) }}%</div>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="trend-stat">
                  <div class="trend-label">预测值</div>
                  <div class="trend-value">{{ trendData.prediction?.toFixed(2) || '-' }}</div>
                  <div class="confidence" v-if="trendData.confidence">
                    置信度: {{ (trendData.confidence * 100).toFixed(0) }}%
                  </div>
                </div>
              </el-col>
            </el-row>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="control-card">
          <template #header>
            <span>演化控制</span>
          </template>
          <div class="control-buttons">
            <el-button
              type="success"
              :disabled="evolutionStatus.status === 'running'"
              @click="triggerEvolution"
              :loading="triggering"
            >
              <el-icon><VideoPlay /></el-icon>
              触发演化
            </el-button>
            <el-button
              type="warning"
              :disabled="evolutionStatus.status !== 'running'"
              @click="pauseEvolution"
            >
              <el-icon><VideoPause /></el-icon>
              暂停
            </el-button>
            <el-button
              type="primary"
              :disabled="evolutionStatus.status !== 'paused'"
              @click="resumeEvolution"
            >
              <el-icon><VideoPlay /></el-icon>
              恢复
            </el-button>
            <el-button
              type="danger"
              :disabled="!canCancel"
              @click="cancelEvolution"
            >
              <el-icon><Close /></el-icon>
              取消
            </el-button>
          </div>
        </el-card>

        <el-card class="info-card">
          <template #header>
            <span>演化信息</span>
          </template>
          <div class="info-list">
            <div class="info-item">
              <span class="info-label">开始时间</span>
              <span class="info-value">{{ formatTime(evolutionStatus.started_at) }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">预计完成</span>
              <span class="info-value">{{ formatTime(evolutionStatus.estimated_completion) }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">上次演化</span>
              <span class="info-value">{{ formatTime(evolutionStatus.last_evolution) }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">下次计划</span>
              <span class="info-value">{{ formatTime(evolutionStatus.next_scheduled) }}</span>
            </div>
          </div>
        </el-card>

        <el-card class="metrics-summary-card">
          <template #header>
            <span>指标汇总</span>
          </template>
          <div class="summary-list" v-if="metricsSummary">
            <div class="summary-item">
              <span class="summary-label">总演化次数</span>
              <span class="summary-value">{{ metricsSummary.total_evolutions }}</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">成功次数</span>
              <span class="summary-value success">{{ metricsSummary.successful_evolutions }}</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">失败次数</span>
              <span class="summary-value danger">{{ metricsSummary.failed_evolutions }}</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">成功率</span>
              <span class="summary-value">{{ metricsSummary.success_rate.toFixed(2) }}%</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">平均耗时</span>
              <span class="summary-value">{{ formatDuration(metricsSummary.average_duration) }}</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">最近24小时</span>
              <span class="summary-value">{{ metricsSummary.last_24h_count }} 次</span>
            </div>
          </div>
        </el-card>

        <el-card class="alerts-card">
          <template #header>
            <div class="card-header">
              <span>演化告警</span>
              <el-badge :value="alertCount" :hidden="alertCount === 0" type="danger">
                <el-icon><Bell /></el-icon>
              </el-badge>
            </div>
          </template>
          <div class="alerts-list">
            <div
              v-for="alert in alerts"
              :key="alert.id"
              class="alert-item"
              :class="'alert-' + alert.level"
            >
              <div class="alert-header">
                <el-tag :type="getAlertType(alert.level)" size="small">
                  {{ alert.level }}
                </el-tag>
                <span class="alert-time">{{ formatAlertTime(alert.timestamp) }}</span>
              </div>
              <div class="alert-message">{{ alert.message }}</div>
              <div class="alert-actions" v-if="alert.status === 'pending'">
                <el-button size="small" type="primary" @click="handleAlert(alert.id, 'acknowledge')">
                  确认
                </el-button>
                <el-button size="small" type="success" @click="handleAlert(alert.id, 'resolve')">
                  解决
                </el-button>
              </div>
              <div class="alert-status" v-else>
                <el-tag size="small" :type="alert.status === 'resolved' ? 'success' : 'info'">
                  {{ alert.status === 'acknowledged' ? '已确认' : '已解决' }}
                </el-tag>
              </div>
            </div>
            <el-empty v-if="alerts.length === 0" description="暂无告警" :image-size="60" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="history-card">
      <template #header>
        <div class="card-header">
          <span>演化历史</span>
          <el-button type="primary" link @click="viewAllHistory">
            查看全部
          </el-button>
        </div>
      </template>
      <el-table :data="historyItems" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="evolution_type" label="类型" width="150">
          <template #default="{ row }">
            <el-tag size="small">{{ getEvolutionTypeLabel(row.evolution_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="trigger_type" label="触发方式" width="120">
          <template #default="{ row }">
            {{ getTriggerTypeLabel(row.trigger_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="started_at" label="开始时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.started_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="duration_seconds" label="耗时" width="100">
          <template #default="{ row }">
            {{ row.duration_seconds ? formatDuration(row.duration_seconds) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="success_rate" label="成功率" width="100">
          <template #default="{ row }">
            {{ (row.success_rate * 100).toFixed(1) }}%
          </template>
        </el-table-column>
        <el-table-column prop="summary" label="摘要" min-width="200" show-overflow-tooltip />
      </el-table>
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="totalHistory"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchHistory"
          @current-change="fetchHistory"
        />
      </div>
    </el-card>

    <el-dialog v-model="triggerDialogVisible" title="触发演化" width="500px">
      <el-form :model="triggerForm" label-width="100px">
        <el-form-item label="演化类型">
          <el-select v-model="triggerForm.evolution_type" placeholder="请选择演化类型">
            <el-option label="技能优化" value="skill_optimization" />
            <el-option label="工作流适配" value="workflow_adaptation" />
            <el-option label="资源重平衡" value="resource_rebalance" />
            <el-option label="知识更新" value="knowledge_update" />
            <el-option label="性能调优" value="performance_tuning" />
          </el-select>
        </el-form-item>
        <el-form-item label="触发原因">
          <el-input
            v-model="triggerForm.reason"
            type="textarea"
            :rows="3"
            placeholder="请输入触发原因"
          />
        </el-form-item>
        <el-form-item label="优先级">
          <el-radio-group v-model="triggerForm.priority">
            <el-radio label="high">高</el-radio>
            <el-radio label="normal">普通</el-radio>
            <el-radio label="low">低</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="模拟运行">
          <el-switch v-model="triggerForm.dry_run" />
          <span class="form-hint">开启后不会执行实际变更</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="triggerDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmTrigger" :loading="triggering">
          确认触发
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Refresh,
  VideoPlay,
  VideoPause,
  Close,
  Bell,
  Top,
  Bottom,
  Minus,
  Loading,
  Cpu,
  MagicStick,
  SetUp,
  CircleCheck
} from '@element-plus/icons-vue'
import { useWebSocket, ConnectionState } from '@/composables/useWebSocket'
import api from '@/api'
import { evolutionStatusApi, type EvolutionStatusOverview } from '@/api'

interface EvolutionStatusData {
  status: 'idle' | 'running' | 'completed' | 'failed' | 'paused'
  current_stage: string | null
  evolution_type: string | null
  progress: number
  started_at: string | null
  estimated_completion: string | null
  current_metrics: Record<string, number>
  active_changes: Array<{ type: string; status: string }>
  last_evolution: string | null
  next_scheduled: string | null
}

interface TrendDataPoint {
  timestamp: string
  value: number
  label?: string
}

interface TrendData {
  metric_name: string
  period: string
  data_points: TrendDataPoint[]
  trend_direction: string
  change_percentage: number
  prediction?: number
  confidence?: number
}

interface MetricsSummary {
  total_evolutions: number
  successful_evolutions: number
  failed_evolutions: number
  average_duration: number
  success_rate: number
  most_common_type: string | null
  last_24h_count: number
  last_7d_count: number
}

interface HistoryItem {
  id: number
  evolution_type: string
  trigger_type: string
  status: string
  started_at: string
  completed_at: string | null
  duration_seconds: number | null
  changes_count: number
  success_rate: number
  metrics_before: Record<string, number>
  metrics_after: Record<string, number>
  summary: string
}

interface Alert {
  id: string
  level: 'info' | 'warning' | 'error' | 'critical'
  message: string
  timestamp: string
  status: 'pending' | 'acknowledged' | 'resolved'
}

const loading = ref(false)
const triggering = ref(false)
const isDarkTheme = ref(false)
const selectedPeriod = ref('7d')
const selectedMetric = ref('performance')
const triggerDialogVisible = ref(false)
const chartContainer = ref<HTMLElement | null>(null)
const chartReady = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const totalHistory = ref(0)

const evolutionStatus = ref<EvolutionStatusData>({
  status: 'idle',
  current_stage: null,
  evolution_type: null,
  progress: 0,
  started_at: null,
  estimated_completion: null,
  current_metrics: {},
  active_changes: [],
  last_evolution: null,
  next_scheduled: null
})

const evolutionOverview = ref<EvolutionStatusOverview | null>(null)

const trendData = ref<TrendData | null>(null)
const metricsSummary = ref<MetricsSummary | null>(null)
const historyItems = ref<HistoryItem[]>([])
const alerts = ref<Alert[]>([])

const triggerForm = ref({
  evolution_type: 'skill_optimization',
  reason: '',
  priority: 'normal',
  dry_run: false
})

let echartsInstance: any = null
let echarts: any = null

const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
const wsHost = window.location.host
const wsUrl = `${wsProtocol}//${wsHost}/api/evolution-monitor/ws`

const {
  connectionState,
  isConnected,
  connect: wsConnect,
  disconnect: wsDisconnect,
  send: wsSend
} = useWebSocket({
  url: wsUrl,
  heartbeatInterval: 30000,
  onMessage: handleWebSocketMessage,
  onStateChange: handleConnectionStateChange
})

const connectionStatusType = computed(() => {
  switch (connectionState.value) {
    case ConnectionState.CONNECTED:
      return 'success'
    case ConnectionState.CONNECTING:
    case ConnectionState.RECONNECTING:
      return 'warning'
    default:
      return 'danger'
  }
})

const connectionStatusLabel = computed(() => {
  switch (connectionState.value) {
    case ConnectionState.CONNECTED:
      return '已连接'
    case ConnectionState.CONNECTING:
      return '连接中...'
    case ConnectionState.RECONNECTING:
      return '重连中...'
    default:
      return '未连接'
  }
})

const evolutionStatusType = computed(() => {
  switch (evolutionStatus.value.status) {
    case 'running':
      return 'primary'
    case 'completed':
      return 'success'
    case 'failed':
      return 'danger'
    case 'paused':
      return 'warning'
    default:
      return 'info'
  }
})

const evolutionStatusLabel = computed(() => {
  const labels: Record<string, string> = {
    idle: '空闲',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    paused: '已暂停'
  }
  return labels[evolutionStatus.value.status] || evolutionStatus.value.status
})

const currentStageLabel = computed(() => {
  const labels: Record<string, string> = {
    analysis: '分析阶段',
    planning: '规划阶段',
    execution: '执行阶段',
    validation: '验证阶段',
    deployment: '部署阶段'
  }
  return labels[evolutionStatus.value.current_stage || ''] || '无'
})

const evolutionTypeLabel = computed(() => {
  const labels: Record<string, string> = {
    skill_optimization: '技能优化',
    workflow_adaptation: '工作流适配',
    resource_rebalance: '资源重平衡',
    knowledge_update: '知识更新',
    performance_tuning: '性能调优'
  }
  return labels[evolutionStatus.value.evolution_type || ''] || '无'
})

const progressColor = computed(() => {
  if (evolutionStatus.value.progress < 30) return '#f56c6c'
  if (evolutionStatus.value.progress < 70) return '#e6a23c'
  return '#67c23a'
})

const trendDirectionLabel = computed(() => {
  const labels: Record<string, string> = {
    upward: '上升',
    downward: '下降',
    stable: '稳定'
  }
  return labels[trendData.value?.trend_direction || 'stable'] || '稳定'
})

const canCancel = computed(() => {
  return ['running', 'paused'].includes(evolutionStatus.value.status)
})

const alertCount = computed(() => {
  return alerts.value.filter(a => a.status === 'pending').length
})

const cycleStages = computed(() => [
  { key: 'analysis', label: '分析', color: 'red' },
  { key: 'planning', label: '规划', color: 'green' },
  { key: 'execution', label: '执行', color: 'blue' },
  { key: 'validation', label: '验证', color: 'yellow' },
  { key: 'review', label: '评审', color: 'purple' }
])

const stageOrder = ['analysis', 'planning', 'execution', 'validation', 'review']

function isStageActive(key: string): boolean {
  return evolutionStatus.value.current_stage === key
}

function isStageDone(key: string): boolean {
  const currentIdx = stageOrder.indexOf(evolutionStatus.value.current_stage || '')
  const thisIdx = stageOrder.indexOf(key)
  return currentIdx > thisIdx
}

const getMetricLabel = (key: string): string => {
  const labels: Record<string, string> = {
    skill_success_rate: '技能成功率',
    avg_response_time: '平均响应时间',
    active_agents: '活跃Agent',
    pending_tasks: '待处理任务',
    performance: '性能',
    efficiency: '效率'
  }
  return labels[key] || key
}

const formatMetricValue = (key: string, value: number): string => {
  if (key.includes('rate') || key.includes('success')) {
    return `${value.toFixed(1)}%`
  }
  if (key.includes('time')) {
    return `${value.toFixed(2)}s`
  }
  return value.toString()
}

const formatTime = (time: string | null): string => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const formatDuration = (seconds: number): string => {
  if (seconds < 60) return `${seconds.toFixed(0)}秒`
  if (seconds < 3600) return `${(seconds / 60).toFixed(1)}分钟`
  return `${(seconds / 3600).toFixed(1)}小时`
}

const formatAlertTime = (timestamp: string): string => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return date.toLocaleString('zh-CN')
}

const getChangeType = (status: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    completed: 'success',
    running: 'primary',
    pending: 'info',
    failed: 'danger'
  }
  return types[status] || 'info'
}

const getAlertType = (level: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    info: 'info',
    warning: 'warning',
    error: 'danger',
    critical: 'danger'
  }
  return types[level] || 'info'
}

function getCapIcon(key: string) {
  const icons: Record<string, any> = { self_iteration: Cpu, self_optimization: MagicStick, self_repair: SetUp, self_improvement: CircleCheck }
  return icons[key] || Cpu
}

function getCapName(key: string): string {
  const names: Record<string, string> = { self_iteration: '自迭代', self_optimization: '自优化', self_repair: '自修复', self_improvement: '自完善' }
  return names[key] || key
}

const getEvolutionTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    skill_optimization: '技能优化',
    workflow_adaptation: '工作流适配',
    resource_rebalance: '资源重平衡',
    knowledge_update: '知识更新',
    performance_tuning: '性能调优'
  }
  return labels[type] || type
}

const getTriggerTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    automatic: '自动',
    manual: '手动',
    scheduled: '计划',
    threshold_based: '阈值触发'
  }
  return labels[type] || type
}

const getStatusType = (status: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    completed: 'success',
    running: 'primary',
    failed: 'danger',
    paused: 'warning',
    idle: 'info'
  }
  return types[status] || 'info'
}

const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    idle: '空闲',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    paused: '已暂停'
  }
  return labels[status] || status
}

const handleWebSocketMessage = (data: any) => {
  switch (data.type) {
    case 'initial_state':
    case 'status_update':
      evolutionStatus.value = data.data
      break
    case 'evolution_started':
      ElMessage.info(`演化已开始: ${data.data.evolution_type}`)
      fetchStatus()
      break
    case 'evolution_progress':
      evolutionStatus.value.current_stage = data.data.stage
      evolutionStatus.value.progress = data.data.progress
      break
    case 'evolution_completed':
      ElMessage.success('演化已完成')
      fetchStatus()
      fetchHistory()
      fetchMetricsSummary()
      break
    case 'evolution_failed':
      ElMessage.error('演化失败')
      addAlert('error', `演化失败: ${data.data.reason || '未知原因'}`)
      fetchStatus()
      break
    case 'evolution_paused':
      ElMessage.warning('演化已暂停')
      fetchStatus()
      break
    case 'evolution_resumed':
      ElMessage.info('演化已恢复')
      fetchStatus()
      break
    case 'evolution_cancelled':
      ElMessage.info('演化已取消')
      fetchStatus()
      break
    case 'alert':
      addAlert(data.data.level, data.data.message)
      break
  }
}

const handleConnectionStateChange = (state: ConnectionState) => {
  if (state === ConnectionState.CONNECTED) {
    ElMessage.success('WebSocket 已连接')
  } else if (state === ConnectionState.DISCONNECTED) {
    ElMessage.warning('WebSocket 连接断开')
  }
}

const addAlert = (level: Alert['level'], message: string) => {
  const alert: Alert = {
    id: `alert-${Date.now()}`,
    level,
    message,
    timestamp: new Date().toISOString(),
    status: 'pending'
  }
  alerts.value.unshift(alert)
  if (alerts.value.length > 50) {
    alerts.value.pop()
  }
}

const handleAlert = async (alertId: string, action: 'acknowledge' | 'resolve') => {
  const alert = alerts.value.find(a => a.id === alertId)
  if (alert) {
    alert.status = action === 'acknowledge' ? 'acknowledged' : 'resolved'
    ElMessage.success(action === 'acknowledge' ? '已确认告警' : '已解决告警')
  }
}

const handleThemeChange = (dark: boolean) => {
  if (echartsInstance) {
    echartsInstance.dispose()
    echartsInstance = null
    nextTick(() => {
      initChart()
    })
  }
}

const fetchStatus = async () => {
  try {
    const response = await api.get('/evolution-monitor/status')
    evolutionStatus.value = response as EvolutionStatusData
  } catch (error) {
    console.error('Failed to fetch evolution status:', error)
  }
}

const fetchEvolutionOverview = async () => {
  try {
    const overview = await evolutionStatusApi.getStatus()
    evolutionOverview.value = overview
    if (overview.current_metrics) {
      evolutionStatus.value.current_metrics = {
        ...evolutionStatus.value.current_metrics,
        ...Object.fromEntries(
          Object.entries(overview.current_metrics || {}).map(([k, v]) => [k, v as number])
        )
      }
    }
    if (overview.progress !== undefined) {
      evolutionStatus.value.progress = overview.progress
    }
    if (overview.current_phase) {
      evolutionStatus.value.current_stage = overview.current_phase
    }
    if (overview.status) {
      evolutionStatus.value.status = overview.status
    }
  } catch (error) {
    console.error('Failed to fetch evolution overview:', error)
  }
}

const fetchTrends = async () => {
  try {
    const response = await api.get('/evolution-monitor/trends', {
      params: {
        metric: selectedMetric.value,
        period: selectedPeriod.value
      }
    })
    trendData.value = response as TrendData
    await nextTick()
    updateChart()
  } catch (error) {
    console.error('Failed to fetch trends:', error)
  }
}

const fetchMetricsSummary = async () => {
  try {
    const response = await api.get('/evolution-monitor/metrics/summary')
    metricsSummary.value = response as MetricsSummary
  } catch (error) {
    console.error('Failed to fetch metrics summary:', error)
  }
}

const fetchHistory = async () => {
  try {
    const response = await api.get('/evolution-monitor/history', {
      params: {
        skip: (currentPage.value - 1) * pageSize.value,
        limit: pageSize.value
      }
    }) as { total: number; items: HistoryItem[] }
    historyItems.value = response.items
    totalHistory.value = response.total
  } catch (error) {
    console.error('Failed to fetch history:', error)
  }
}

const fetchAll = async () => {
  loading.value = true
  try {
    await Promise.all([
      fetchStatus(),
      fetchEvolutionOverview(),
      fetchTrends(),
      fetchMetricsSummary(),
      fetchHistory()
    ])
  } finally {
    loading.value = false
  }
}

const refreshAll = async () => {
  await fetchAll()
  ElMessage.success('已刷新')
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

    echartsInstance = echarts.init(chartContainer.value, isDarkTheme.value ? 'dark' : undefined)
    chartReady.value = true
    
    if (trendData.value) {
      updateChart()
    }
  } catch (error) {
    console.error('Failed to initialize ECharts:', error)
    chartReady.value = false
  }
}

const updateChart = () => {
  if (!echartsInstance || !trendData.value) return

  const data = trendData.value.data_points
  const times = data.map(d => new Date(d.timestamp).toLocaleString('zh-CN'))
  const values = data.map(d => d.value)

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: isDarkTheme.value ? '#1f1f1f' : '#fff',
      borderColor: isDarkTheme.value ? '#333' : '#ddd',
      textStyle: {
        color: isDarkTheme.value ? '#fff' : '#333'
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
          color: isDarkTheme.value ? '#555' : '#ccc'
        }
      },
      axisLabel: {
        color: isDarkTheme.value ? '#aaa' : '#666',
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      axisLine: {
        lineStyle: {
          color: isDarkTheme.value ? '#555' : '#ccc'
        }
      },
      axisLabel: {
        color: isDarkTheme.value ? '#aaa' : '#666'
      },
      splitLine: {
        lineStyle: {
          color: isDarkTheme.value ? '#333' : '#eee'
        }
      }
    },
    series: [
      {
        name: trendData.value.metric_name,
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
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

const triggerEvolution = () => {
  triggerDialogVisible.value = true
}

const confirmTrigger = async () => {
  if (!triggerForm.value.reason) {
    ElMessage.warning('请输入触发原因')
    return
  }

  triggering.value = true
  try {
    await api.post('/evolution-monitor/trigger', triggerForm.value)
    ElMessage.success('演化已触发')
    triggerDialogVisible.value = false
    triggerForm.value.reason = ''
    await fetchStatus()
  } catch (error: any) {
    ElMessage.error(error?.message || '触发演化失败')
  } finally {
    triggering.value = false
  }
}

const pauseEvolution = async () => {
  try {
    await api.post('/evolution-monitor/pause')
    ElMessage.success('演化已暂停')
    await fetchStatus()
  } catch (error: any) {
    ElMessage.error(error?.message || '暂停演化失败')
  }
}

const resumeEvolution = async () => {
  try {
    await api.post('/evolution-monitor/resume')
    ElMessage.success('演化已恢复')
    await fetchStatus()
  } catch (error: any) {
    ElMessage.error(error?.message || '恢复演化失败')
  }
}

const cancelEvolution = async () => {
  try {
    await api.post('/evolution-monitor/cancel')
    ElMessage.success('演化已取消')
    await fetchStatus()
  } catch (error: any) {
    ElMessage.error(error?.message || '取消演化失败')
  }
}

const viewAllHistory = () => {
  ElMessage.info('查看全部历史记录')
}

const handleResize = () => {
  if (echartsInstance) {
    echartsInstance.resize()
  }
}

onMounted(async () => {
  await fetchAll()
  wsConnect()
  await nextTick()
  await initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  wsDisconnect()
  if (echartsInstance) {
    echartsInstance.dispose()
    echartsInstance = null
  }
  window.removeEventListener('resize', handleResize)
})

watch(trendData, () => {
  if (chartReady.value) {
    updateChart()
  }
})
</script>

<style scoped>
.evolution-monitor {
  padding: 20px;
  min-height: 100vh;
  background: #f5f7fa;
  transition: background 0.3s;
}

.evolution-monitor.dark-theme {
  background: #1a1a1a;
  color: #e0e0e0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.header-left h2 {
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-card,
.chart-card,
.control-card,
.info-card,
.metrics-summary-card,
.alerts-card,
.history-card {
  margin-bottom: 20px;
}

.dark-theme .el-card {
  background: #2d2d2d;
  border-color: #3d3d3d;
}

.status-content {
  padding: 10px 0;
}

.status-item {
  text-align: center;
}

.status-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.dark-theme .status-label {
  color: #aaa;
}

.status-value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.dark-theme .status-value {
  color: #e0e0e0;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.metric-item {
  text-align: center;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.dark-theme .metric-item {
  background: #3d3d3d;
}

.metric-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.dark-theme .metric-label {
  color: #aaa;
}

.metric-value {
  font-size: 20px;
  font-weight: 600;
  color: #409eff;
}

.active-changes {
  margin-top: 15px;
}

.changes-title {
  font-weight: 500;
  margin-bottom: 10px;
  color: #303133;
}

.dark-theme .changes-title {
  color: #e0e0e0;
}

.change-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.change-type {
  font-size: 14px;
}

.chart-container {
  height: 300px;
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

.trend-info {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.dark-theme .trend-info {
  border-top-color: #3d3d3d;
}

.trend-stat {
  text-align: center;
}

.trend-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.dark-theme .trend-label {
  color: #aaa;
}

.trend-value {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
}

.dark-theme .trend-value {
  color: #e0e0e0;
}

.trend-value.upward {
  color: #67c23a;
}

.trend-value.downward {
  color: #f56c6c;
}

.confidence {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.control-buttons {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.info-label {
  color: #909399;
}

.dark-theme .info-label {
  color: #aaa;
}

.info-value {
  color: #303133;
  font-weight: 500;
}

.dark-theme .info-value {
  color: #e0e0e0;
}

.summary-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.summary-label {
  color: #909399;
}

.dark-theme .summary-label {
  color: #aaa;
}

.summary-value {
  font-weight: 600;
  color: #303133;
}

.dark-theme .summary-value {
  color: #e0e0e0;
}

.summary-value.success {
  color: #67c23a;
}

.summary-value.danger {
  color: #f56c6c;
}

.alerts-list {
  max-height: 300px;
  overflow-y: auto;
}

.alert-item {
  padding: 12px;
  margin-bottom: 10px;
  border-radius: 8px;
  background: #f5f7fa;
  border-left: 4px solid #909399;
}

.dark-theme .alert-item {
  background: #3d3d3d;
}

.alert-item.alert-warning {
  border-left-color: #e6a23c;
}

.alert-item.alert-error,
.alert-item.alert-critical {
  border-left-color: #f56c6c;
}

.alert-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.alert-time {
  font-size: 12px;
  color: #909399;
}

.dark-theme .alert-time {
  color: #aaa;
}

.alert-message {
  font-size: 14px;
  color: #303133;
  margin-bottom: 8px;
}

.dark-theme .alert-message {
  color: #e0e0e0;
}

.alert-actions {
  display: flex;
  gap: 8px;
}

.alert-status {
  text-align: right;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.form-hint {
  margin-left: 10px;
  font-size: 12px;
  color: #909399;
}

@media (max-width: 1200px) {
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .evolution-monitor {
    padding: 10px;
  }

  .page-header {
    flex-direction: column;
    gap: 15px;
  }

  .header-left,
  .header-actions {
    width: 100%;
    justify-content: space-between;
  }

  .metrics-grid {
    grid-template-columns: 1fr;
  }

  .control-buttons {
    grid-template-columns: 1fr;
  }
}

.cycle-stage-viz {
  margin-top: 12px;
}

.stage-title,
.cap-title {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
  margin-bottom: 12px;
}

.dark-theme .stage-title,
.dark-theme .cap-title { color: #e0e0e0; }

.stage-bar-wrapper {
  display: flex;
  gap: 4px;
  background: #f0f2f5;
  border-radius: 8px;
  padding: 8px;
}

.dark-theme .stage-bar-wrapper { background: #3a3a3a; }

.stage-segment {
  text-align: center;
  padding: 6px 4px;
  border-radius: 6px;
  transition: all 0.3s ease;
  position: relative;
}

.stage-segment.stage-done {
  background: #e1f3d8;
}

.stage-segment.stage-active {
  background: #ecf5ff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.3);
}

.stage-label {
  font-size: 11px;
  color: #606266;
  margin-bottom: 4px;
  font-weight: 500;
}

.stage-indicator {
  width: 24px;
  height: 6px;
  border-radius: 3px;
  margin: 0 auto;
}

.phase-red { background: linear-gradient(90deg, #f56c6c, #f78989); }
.phase-green { background: linear-gradient(90deg, #67c23a, #85ce61); }
.phase-blue { background: linear-gradient(90deg, #409eff, #66b1ff); }
.phase-yellow { background: linear-gradient(90deg, #e6a23c, #ebb563); }
.phase-purple { background: linear-gradient(90deg, #909399, #b1b3b8); }

.capabilities-panel {
  margin-top: 4px;
}

.cap-card {
  padding: 12px 14px;
  border-radius: 8px;
  margin-bottom: 10px;
  transition: all 0.25s ease;
}

.cap-enabled { background: #f0f9eb; border: 1px solid #e1f3d8; }
.cap-disabled { background: #f4f4f5; border: 1px solid #e4e7ed; }

.dark-theme .cap-enabled { background: #1a3a1a; border-color: #2d5a2d; }
.dark-theme .cap-disabled { background: #333; border-color: #444; }

.cap-header-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.cap-icon-wrap {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.icon-on { background: #e1f3d8; color: #67c23a; }
.icon-off { background: #ebeef5; color: #909399; }

.cap-name {
  flex: 1;
  font-weight: 500;
  font-size: 13px;
  color: #303133;
}

.dark-theme .cap-name { color: #e0e0e0; }

.cap-meta {
  margin-top: 6px;
  font-size: 11px;
  color: #909399;
}
</style>
