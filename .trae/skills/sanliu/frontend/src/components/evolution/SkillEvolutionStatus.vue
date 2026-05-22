<template>
  <div class="skill-evolution-status">
    <el-card class="status-card" :class="statusCardClass">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="status-icon" :class="statusIconClass">
              <component :is="statusIcon" />
            </el-icon>
            <span class="title">技能演化状态</span>
            <el-tag :type="statusType" effect="dark" size="small">
              {{ statusLabel }}
            </el-tag>
          </div>
          <div class="header-right">
            <el-tooltip content="WebSocket连接状态" placement="top">
              <el-badge
                :type="isConnected ? 'success' : 'danger'"
                :value="isConnected ? '已连接' : '未连接'"
                class="connection-badge"
              />
            </el-tooltip>
          </div>
        </div>
      </template>

      <div class="status-content">
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="status-item">
              <div class="status-label">演化运行状态</div>
              <div class="status-value" :class="{ 'pulse-animation': isRunning }">
                <el-icon><component :is="runningStatusIcon" /></el-icon>
                {{ runningStatusLabel }}
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="status-item">
              <div class="status-label">当前演化阶段</div>
              <div class="status-value">{{ currentStageLabel }}</div>
              <el-progress
                v-if="isRunning"
                :percentage="stageProgress"
                :stroke-width="6"
                :show-text="false"
                class="stage-progress"
              />
            </div>
          </el-col>
          <el-col :span="6">
            <div class="status-item">
              <div class="status-label">最近演化时间</div>
              <div class="status-value">{{ lastEvolutionTime }}</div>
              <div class="status-sub" v-if="status.last_evolution_duration">
                耗时: {{ formatDuration(status.last_evolution_duration) }}
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="status-item">
              <div class="status-label">成功率</div>
              <div class="status-value" :class="successRateClass">
                {{ successRate.toFixed(1) }}%
              </div>
              <div class="status-sub">
                {{ status.successful_evolutions }}/{{ status.total_evolutions }} 次
              </div>
            </div>
          </el-col>
        </el-row>

        <el-divider />

        <div class="monitors-section">
          <div class="section-header">
            <span class="section-title">活跃监控器</span>
            <el-tag size="small" type="info">{{ activeMonitors.length }} 个</el-tag>
          </div>
          <div class="monitors-grid">
            <div
              v-for="monitor in activeMonitors"
              :key="monitor.id"
              class="monitor-item"
              :class="{ 'monitor-alert': monitor.has_alert }"
            >
              <div class="monitor-header">
                <el-icon :class="monitorStatusClass(monitor.status)">
                  <component :is="monitorIcon(monitor.type)" />
                </el-icon>
                <span class="monitor-name">{{ monitor.name }}</span>
              </div>
              <div class="monitor-status">
                <el-tag size="small" :type="monitorStatusType(monitor.status)">
                  {{ monitorStatusLabel(monitor.status) }}
                </el-tag>
                <span class="monitor-value">{{ monitor.current_value }}</span>
              </div>
              <el-progress
                v-if="monitor.threshold"
                :percentage="monitorProgress(monitor)"
                :stroke-width="4"
                :color="monitorColor(monitor)"
                :show-text="false"
              />
            </div>
          </div>
        </div>

        <el-divider v-if="recentEvents.length > 0" />

        <div v-if="recentEvents.length > 0" class="events-section">
          <div class="section-header">
            <span class="section-title">最近事件</span>
            <el-button type="primary" link size="small" @click="showAllEvents">
              查看全部
            </el-button>
          </div>
          <el-timeline>
            <el-timeline-item
              v-for="event in recentEvents.slice(0, 5)"
              :key="event.id"
              :type="eventTypeColor(event.type)"
              :timestamp="formatTime(event.timestamp)"
              placement="top"
            >
              <div class="event-item">
                <span class="event-type">{{ event.type_label }}</span>
                <span class="event-message">{{ event.message }}</span>
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>
      </div>
    </el-card>

    <el-drawer
      v-model="eventsDrawerVisible"
      title="全部事件"
      direction="rtl"
      size="500px"
    >
      <el-timeline>
        <el-timeline-item
          v-for="event in allEvents"
          :key="event.id"
          :type="eventTypeColor(event.type)"
          :timestamp="formatTime(event.timestamp)"
          placement="top"
        >
          <div class="event-item">
            <div class="event-header">
              <el-tag size="small" :type="eventTypeTag(event.type)">
                {{ event.type_label }}
              </el-tag>
              <span class="event-stage" v-if="event.stage">{{ event.stage }}</span>
            </div>
            <div class="event-message">{{ event.message }}</div>
            <div class="event-details" v-if="event.details">
              <el-descriptions :column="1" size="small" border>
                <el-descriptions-item
                  v-for="(value, key) in event.details"
                  :key="key"
                  :label="key"
                >
                  {{ value }}
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </div>
        </el-timeline-item>
      </el-timeline>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  VideoPlay,
  VideoPause,
  CircleClose,
  Monitor,
  DataAnalysis,
  Timer,
  Warning,
  CircleCheck
} from '@element-plus/icons-vue'
import { useWebSocket, ConnectionState } from '@/composables/useWebSocket'
import api from '@/api'

interface EvolutionMonitor {
  id: string
  name: string
  type: 'performance' | 'quality' | 'resource' | 'security'
  status: 'active' | 'idle' | 'alert' | 'disabled'
  current_value: string
  threshold?: number
  current_threshold?: number
  has_alert: boolean
}

interface EvolutionEvent {
  id: string
  type: 'start' | 'progress' | 'complete' | 'fail' | 'alert' | 'rollback'
  type_label: string
  message: string
  timestamp: string
  stage?: string
  details?: Record<string, string>
}

interface SkillEvolutionStatusData {
  status: 'running' | 'paused' | 'stopped' | 'idle'
  current_stage: string | null
  stage_progress: number
  last_evolution: string | null
  last_evolution_duration: number | null
  success_rate: number
  successful_evolutions: number
  total_evolutions: number
  active_monitors: EvolutionMonitor[]
  recent_events: EvolutionEvent[]
}

interface Props {
  projectId?: number
  autoRefresh?: boolean
  refreshInterval?: number
}

const props = withDefaults(defineProps<Props>(), {
  autoRefresh: true,
  refreshInterval: 5000
})

const emit = defineEmits<{
  (e: 'status-update', status: SkillEvolutionStatusData): void
  (e: 'monitor-alert', monitor: EvolutionMonitor): void
  (e: 'event', event: EvolutionEvent): void
}>()

const loading = ref(false)
const eventsDrawerVisible = ref(false)
const allEvents = ref<EvolutionEvent[]>([])

const status = ref<SkillEvolutionStatusData>({
  status: 'idle',
  current_stage: null,
  stage_progress: 0,
  last_evolution: null,
  last_evolution_duration: null,
  success_rate: 0,
  successful_evolutions: 0,
  total_evolutions: 0,
  active_monitors: [],
  recent_events: []
})

let refreshTimer: ReturnType<typeof setInterval> | null = null

const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
const wsHost = window.location.host
const wsUrl = `${wsProtocol}//${wsHost}/api/evolution-monitor/skill-status/ws`

const handleWebSocketMessage = (data: any) => {
  switch (data.type) {
    case 'initial_state':
    case 'status_update':
      status.value = data.data
      emit('status-update', data.data)
      break
    case 'monitor_alert':
      const alertMonitor = data.data as EvolutionMonitor
      emit('monitor-alert', alertMonitor)
      ElMessage.warning(`监控器告警: ${alertMonitor.name}`)
      break
    case 'event':
      const event = data.data as EvolutionEvent
      emit('event', event)
      status.value.recent_events.unshift(event)
      if (status.value.recent_events.length > 20) {
        status.value.recent_events.pop()
      }
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

const {
  isConnected,
  connect: wsConnect,
  disconnect: wsDisconnect
} = useWebSocket({
  url: wsUrl,
  heartbeatInterval: 30000,
  onMessage: handleWebSocketMessage,
  onStateChange: handleConnectionStateChange
})

const isRunning = computed(() => status.value.status === 'running')
const isPaused = computed(() => status.value.status === 'paused')

const statusCardClass = computed(() => ({
  'status-running': isRunning.value,
  'status-paused': isPaused.value,
  'status-stopped': status.value.status === 'stopped'
}))

const statusIconClass = computed(() => ({
  'icon-running': isRunning.value,
  'icon-paused': isPaused.value
}))

const statusIcon = computed(() => {
  switch (status.value.status) {
    case 'running':
      return VideoPlay
    case 'paused':
      return VideoPause
    case 'stopped':
      return CircleClose
    default:
      return Monitor
  }
})

const statusType = computed(() => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    running: 'success',
    paused: 'warning',
    stopped: 'danger',
    idle: 'info'
  }
  return types[status.value.status] || 'info'
})

const statusLabel = computed(() => {
  const labels: Record<string, string> = {
    running: '运行中',
    paused: '已暂停',
    stopped: '已停止',
    idle: '空闲'
  }
  return labels[status.value.status] || '未知'
})

const runningStatusIcon = computed(() => {
  switch (status.value.status) {
    case 'running':
      return VideoPlay
    case 'paused':
      return VideoPause
    case 'stopped':
      return CircleClose
    default:
      return CircleCheck
  }
})

const runningStatusLabel = computed(() => {
  const labels: Record<string, string> = {
    running: '运行中',
    paused: '已暂停',
    stopped: '已停止',
    idle: '空闲'
  }
  return labels[status.value.status] || '未知'
})

const currentStageLabel = computed(() => {
  const labels: Record<string, string> = {
    initialization: '初始化',
    analysis: '分析阶段',
    planning: '规划阶段',
    execution: '执行阶段',
    validation: '验证阶段',
    deployment: '部署阶段',
    cleanup: '清理阶段'
  }
  return labels[status.value.current_stage || ''] || '无'
})

const stageProgress = computed(() => status.value.stage_progress || 0)

const lastEvolutionTime = computed(() => {
  if (!status.value.last_evolution) return '无'
  return formatTime(status.value.last_evolution)
})

const successRate = computed(() => status.value.success_rate || 0)

const successRateClass = computed(() => {
  if (successRate.value >= 90) return 'rate-excellent'
  if (successRate.value >= 70) return 'rate-good'
  if (successRate.value >= 50) return 'rate-warning'
  return 'rate-danger'
})

const activeMonitors = computed(() => status.value.active_monitors || [])

const recentEvents = computed(() => status.value.recent_events || [])

const monitorIcon = (type: string) => {
  const icons: Record<string, any> = {
    performance: DataAnalysis,
    quality: CircleCheck,
    resource: Timer,
    security: Warning
  }
  return icons[type] || Monitor
}

const monitorStatusClass = (monitorStatus: string) => ({
  'status-active': monitorStatus === 'active',
  'status-idle': monitorStatus === 'idle',
  'status-alert': monitorStatus === 'alert'
})

const monitorStatusType = (monitorStatus: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    active: 'success',
    idle: 'info',
    alert: 'danger',
    disabled: 'info'
  }
  return types[monitorStatus] || 'info'
}

const monitorStatusLabel = (monitorStatus: string): string => {
  const labels: Record<string, string> = {
    active: '活跃',
    idle: '空闲',
    alert: '告警',
    disabled: '禁用'
  }
  return labels[monitorStatus] || monitorStatus
}

const monitorProgress = (monitor: EvolutionMonitor): number => {
  if (!monitor.threshold || !monitor.current_threshold) return 0
  return Math.min(100, (monitor.current_threshold / monitor.threshold) * 100)
}

const monitorColor = (monitor: EvolutionMonitor): string => {
  const progress = monitorProgress(monitor)
  if (progress >= 90) return '#f56c6c'
  if (progress >= 70) return '#e6a23c'
  return '#67c23a'
}

const eventTypeColor = (type: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const colors: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    start: '',
    progress: 'info',
    complete: 'success',
    fail: 'danger',
    alert: 'warning',
    rollback: 'warning'
  }
  return colors[type] || 'info'
}

const eventTypeTag = (type: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  return eventTypeColor(type)
}

const formatTime = (time: string): string => {
  return new Date(time).toLocaleString('zh-CN')
}

const formatDuration = (ms: number): string => {
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${(ms / 60000).toFixed(1)}min`
}

const showAllEvents = () => {
  fetchAllEvents()
  eventsDrawerVisible.value = true
}

const fetchStatus = async () => {
  if (loading.value) return

  loading.value = true
  try {
    const url = props.projectId
      ? `/evolution-monitor/skill-status?project_id=${props.projectId}`
      : '/evolution-monitor/skill-status'
    const response = await api.get(url)
    status.value = response.data as SkillEvolutionStatusData
    emit('status-update', status.value)
  } catch (error) {
    console.error('Failed to fetch skill evolution status:', error)
  } finally {
    loading.value = false
  }
}

const fetchAllEvents = async () => {
  try {
    const url = props.projectId
      ? `/evolution-monitor/skill-status/events?project_id=${props.projectId}`
      : '/evolution-monitor/skill-status/events'
    const response = await api.get(url)
    allEvents.value = response.data as EvolutionEvent[]
  } catch (error) {
    console.error('Failed to fetch events:', error)
  }
}

const startAutoRefresh = () => {
  if (props.autoRefresh && !refreshTimer && !isConnected.value) {
    refreshTimer = setInterval(fetchStatus, props.refreshInterval)
  }
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

onMounted(() => {
  fetchStatus()
  wsConnect()
  if (props.autoRefresh && !isConnected.value) {
    startAutoRefresh()
  }
})

onUnmounted(() => {
  wsDisconnect()
  stopAutoRefresh()
})
</script>

<style scoped>
.skill-evolution-status {
  width: 100%;
}

.status-card {
  transition: all 0.3s ease;
}

.status-card.status-running {
  box-shadow: 0 0 20px rgba(103, 194, 58, 0.3);
  border-color: #67c23a;
}

.status-card.status-paused {
  box-shadow: 0 0 20px rgba(230, 162, 60, 0.3);
  border-color: #e6a23c;
}

.status-card.status-stopped {
  box-shadow: 0 0 20px rgba(245, 108, 108, 0.3);
  border-color: #f56c6c;
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

.status-icon {
  font-size: 24px;
}

.status-icon.icon-running {
  color: #67c23a;
  animation: pulse 1.5s infinite;
}

.status-icon.icon-paused {
  color: #e6a23c;
}

.title {
  font-size: 16px;
  font-weight: 600;
}

.connection-badge {
  margin-left: 10px;
}

.status-content {
  padding: 10px 0;
}

.status-item {
  text-align: center;
  padding: 10px;
}

.status-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}

.status-value {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.status-value.pulse-animation {
  animation: pulse 1.5s infinite;
}

.status-sub {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.stage-progress {
  margin-top: 8px;
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

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.section-title {
  font-weight: 500;
  font-size: 14px;
  color: #303133;
}

.monitors-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
}

.monitor-item {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.monitor-item.monitor-alert {
  background: #fef0f0;
  border: 1px solid #fbc4c4;
}

.monitor-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.monitor-name {
  font-size: 13px;
  font-weight: 500;
}

.monitor-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.monitor-value {
  font-size: 12px;
  color: #606266;
}

.status-active {
  color: #67c23a;
}

.status-idle {
  color: #909399;
}

.status-alert {
  color: #f56c6c;
}

.events-section {
  margin-top: 10px;
}

.event-item {
  padding: 4px 0;
}

.event-type {
  font-weight: 500;
  margin-right: 8px;
}

.event-message {
  color: #606266;
}

.event-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.event-stage {
  font-size: 12px;
  color: #909399;
}

.event-details {
  margin-top: 10px;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

@media (max-width: 1200px) {
  .monitors-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .monitors-grid {
    grid-template-columns: 1fr;
  }
}
</style>
