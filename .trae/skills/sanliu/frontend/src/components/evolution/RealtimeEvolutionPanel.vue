<template>
  <div class="realtime-evolution-panel">
    <el-card class="panel-card" :class="{ 'is-running': isRunning, 'is-paused': isPaused }">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span class="title">实时演化状态</span>
            <el-tag :type="statusType" effect="dark" size="large">
              {{ statusLabel }}
            </el-tag>
            <div class="connection-status" :class="connectionClass">
              <el-icon><Connection /></el-icon>
              <span>{{ connectionLabel }}</span>
            </div>
          </div>
          <div class="header-actions">
            <el-button-group>
              <el-button
                v-if="isRunning"
                type="warning"
                size="small"
                :loading="pausing"
                @click="pauseEvolution"
              >
                <el-icon><VideoPause /></el-icon>
                暂停
              </el-button>
              <el-button
                v-if="isPaused"
                type="success"
                size="small"
                :loading="resuming"
                @click="resumeEvolution"
              >
                <el-icon><VideoPlay /></el-icon>
                继续
              </el-button>
              <el-button
                v-if="isRunning || isPaused"
                type="danger"
                size="small"
                :loading="stopping"
                @click="stopEvolution"
              >
                <el-icon><CircleClose /></el-icon>
                停止
              </el-button>
            </el-button-group>
          </div>
        </div>
      </template>

      <div class="panel-content">
        <div class="progress-section">
          <div class="progress-header">
            <span class="progress-label">演化进度</span>
            <span class="progress-value">{{ evolutionState.progress }}%</span>
          </div>
          <el-progress
            :percentage="evolutionState.progress"
            :stroke-width="24"
            :color="progressColors"
            :class="{ 'progress-animate': isRunning }"
          >
            <template #default="{ percentage }">
              <span class="progress-text">{{ percentage }}%</span>
            </template>
          </el-progress>
          <div class="progress-info">
            <div class="info-item">
              <span class="info-label">开始时间</span>
              <span class="info-value">{{ formatTime(evolutionState.started_at) }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">预计完成</span>
              <span class="info-value">{{ formatTime(evolutionState.estimated_completion) }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">已用时间</span>
              <span class="info-value">{{ elapsed_time }}</span>
            </div>
          </div>
        </div>

        <el-divider />

        <div class="stage-section">
          <div class="section-title">当前阶段</div>
          <div class="current-stage">
            <div class="stage-icon" :class="`stage-${currentStageStatus}`">
              <el-icon :size="32">
                <component :is="getStageIcon(currentStageStatus)" />
              </el-icon>
            </div>
            <div class="stage-info">
              <div class="stage-name">{{ currentStageLabel }}</div>
              <div class="stage-status">{{ getStageStatusLabel(currentStageStatus) }}</div>
            </div>
          </div>
          <el-steps :active="activeStepIndex" align-center class="stage-steps">
            <el-step
              v-for="stage in stageList"
              :key="stage.name"
              :title="stage.label"
              :description="getStageDescription(stage)"
              :status="getStepStatus(stage.status)"
            >
              <template #icon>
                <el-icon :class="{ 'is-loading': stage.status === 'running' }">
                  <component :is="getStageIcon(stage.status)" />
                </el-icon>
              </template>
            </el-step>
          </el-steps>
        </div>

        <el-divider />

        <div class="metrics-section">
          <div class="section-title">实时指标</div>
          <el-row :gutter="16">
            <el-col :span="6" v-for="metric in displayMetrics" :key="metric.key">
              <div class="metric-card" :class="getMetricClass(metric)">
                <div class="metric-icon">
                  <el-icon :size="24">
                    <component :is="metric.icon" />
                  </el-icon>
                </div>
                <div class="metric-content">
                  <div class="metric-label">{{ metric.label }}</div>
                  <div class="metric-value">{{ formatMetricValue(metric) }}</div>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>

        <div v-if="evolutionState.logs?.length" class="logs-section">
          <el-divider />
          <div class="section-header">
            <span class="section-title">演化日志</span>
            <div class="log-actions">
              <el-select v-model="logLevel" size="small" style="width: 100px">
                <el-option label="全部" value="" />
                <el-option label="信息" value="info" />
                <el-option label="警告" value="warning" />
                <el-option label="错误" value="error" />
              </el-select>
              <el-button size="small" @click="clearLogs">清空</el-button>
              <el-button size="small" @click="exportLogs">
                <el-icon><Download /></el-icon>
                导出
              </el-button>
            </div>
          </div>
          <div class="logs-container" ref="logsContainerRef">
            <div
              v-for="(log, index) in filteredLogs"
              :key="index"
              class="log-item"
              :class="`log-${log.level}`"
            >
              <span class="log-time">{{ formatTime(log.timestamp) }}</span>
              <el-tag :type="getLogLevelType(log.level)" size="small">
                {{ log.level.toUpperCase() }}
              </el-tag>
              <span class="log-stage" v-if="log.stage">[{{ log.stage }}]</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Connection,
  VideoPause,
  VideoPlay,
  CircleClose,
  Download,
  Loading,
  CircleCheck,
  Clock,
  Monitor,
  Timer,
  DataAnalysis,
  Cpu,
  DocumentChecked,
  Setting
} from '@element-plus/icons-vue'
import { useWebSocket, ConnectionState } from '@/composables/useWebSocket'
import api from '@/api'

interface EvolutionLog {
  timestamp: string
  level: 'info' | 'warning' | 'error' | 'debug'
  stage?: string
  message: string
}

interface EvolutionStage {
  name: string
  label: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress?: number
}

interface EvolutionMetrics {
  cpu_usage?: number
  memory_usage?: number
  success_rate?: number
  error_count?: number
  throughput?: number
  latency?: number
}

interface EvolutionState {
  status: 'idle' | 'running' | 'paused' | 'stopped' | 'completed' | 'failed'
  progress: number
  current_stage: string | null
  evolution_type: string | null
  started_at: string | null
  estimated_completion: string | null
  stages: EvolutionStage[]
  metrics: EvolutionMetrics
  logs: EvolutionLog[]
}

interface Props {
  evolutionId?: string
  autoConnect?: boolean
  showLogs?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  autoConnect: true,
  showLogs: true
})

const emit = defineEmits<{
  (e: 'status-change', status: EvolutionState): void
  (e: 'stage-change', stage: string): void
  (e: 'progress-update', progress: number): void
  (e: 'evolution-completed', result: any): void
  (e: 'evolution-failed', error: any): void
  (e: 'error', error: Error): void
}>()

const logLevel = ref('')
const logsContainerRef = ref<HTMLElement | null>(null)
const pausing = ref(false)
const resuming = ref(false)
const stopping = ref(false)
const elapsed_time = ref('0s')

const evolutionState = ref<EvolutionState>({
  status: 'idle',
  progress: 0,
  current_stage: null,
  evolution_type: null,
  started_at: null,
  estimated_completion: null,
  stages: [],
  metrics: {},
  logs: []
})

let elapsedTimer: ReturnType<typeof setInterval> | null = null

const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
const wsHost = window.location.host
const wsUrl = `${wsProtocol}//${wsHost}/api/evolution-status/ws${props.evolutionId ? `?evolution_id=${props.evolutionId}` : ''}`

const {
  connectionState,
  isConnected,
  connect: wsConnect,
  disconnect: wsDisconnect
} = useWebSocket({
  url: wsUrl,
  heartbeatInterval: 30000,
  onMessage: handleWebSocketMessage,
  onStateChange: handleConnectionStateChange
})

const isRunning = computed(() => evolutionState.value.status === 'running')
const isPaused = computed(() => evolutionState.value.status === 'paused')

const statusType = computed(() => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    idle: 'info',
    running: 'primary',
    paused: 'warning',
    stopped: 'danger',
    completed: 'success',
    failed: 'danger'
  }
  return types[evolutionState.value.status] || 'info'
})

const statusLabel = computed(() => {
  const labels: Record<string, string> = {
    idle: '空闲',
    running: '运行中',
    paused: '已暂停',
    stopped: '已停止',
    completed: '已完成',
    failed: '失败'
  }
  return labels[evolutionState.value.status] || '未知'
})

const connectionClass = computed(() => ({
  connected: isConnected.value,
  disconnected: !isConnected.value
}))

const connectionLabel = computed(() => {
  const labels: Record<ConnectionState, string> = {
    [ConnectionState.CONNECTING]: '连接中',
    [ConnectionState.CONNECTED]: '已连接',
    [ConnectionState.DISCONNECTED]: '已断开',
    [ConnectionState.RECONNECTING]: '重连中'
  }
  return labels[connectionState.value] || '未知'
})

const progressColors = computed(() => {
  const progress = evolutionState.value.progress
  if (progress < 30) return '#f56c6c'
  if (progress < 70) return '#e6a23c'
  return '#67c23a'
})

const stageList = computed(() => {
  const defaultStages: EvolutionStage[] = [
    { name: 'monitor', label: '监控', status: 'pending' },
    { name: 'analysis', label: '分析', status: 'pending' },
    { name: 'planning', label: '规划', status: 'pending' },
    { name: 'execution', label: '执行', status: 'pending' },
    { name: 'validation', label: '验证', status: 'pending' }
  ]
  return evolutionState.value.stages.length > 0 ? evolutionState.value.stages : defaultStages
})

const currentStageLabel = computed(() => {
  const stage = stageList.value.find(s => s.name === evolutionState.value.current_stage)
  return stage?.label || '无'
})

const currentStageStatus = computed(() => {
  const stage = stageList.value.find(s => s.name === evolutionState.value.current_stage)
  return stage?.status || 'pending'
})

const activeStepIndex = computed(() => {
  const currentStage = evolutionState.value.current_stage
  if (!currentStage) return 0
  const index = stageList.value.findIndex(s => s.name === currentStage)
  return index >= 0 ? index : 0
})

const displayMetrics = computed(() => {
  const metrics = evolutionState.value.metrics
  return [
    { key: 'cpu_usage', label: 'CPU使用率', value: metrics.cpu_usage || 0, icon: Cpu, unit: '%' },
    { key: 'memory_usage', label: '内存使用', value: metrics.memory_usage || 0, icon: Monitor, unit: '%' },
    { key: 'success_rate', label: '成功率', value: metrics.success_rate || 0, icon: CircleCheck, unit: '%' },
    { key: 'latency', label: '延迟', value: metrics.latency || 0, icon: Timer, unit: 'ms' }
  ]
})

const filteredLogs = computed(() => {
  if (!logLevel.value) return evolutionState.value.logs
  return evolutionState.value.logs.filter(log => log.level === logLevel.value)
})

const formatTime = (time: string | null): string => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const getStageIcon = (status: string) => {
  const icons: Record<string, any> = {
    pending: Clock,
    running: Loading,
    completed: CircleCheck,
    failed: CircleClose
  }
  return icons[status] || Clock
}

const getStageStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    pending: '待处理',
    running: '进行中...',
    completed: '已完成',
    failed: '失败'
  }
  return labels[status] || status
}

const getStageDescription = (stage: EvolutionStage): string => {
  if (stage.status === 'running') return '进行中...'
  if (stage.progress !== undefined) return `${stage.progress}%`
  return getStageStatusLabel(stage.status)
}

const getStepStatus = (status: string): '' | 'process' | 'finish' | 'error' | 'wait' => {
  const types: Record<string, '' | 'process' | 'finish' | 'error' | 'wait'> = {
    pending: 'wait',
    running: 'process',
    completed: 'finish',
    failed: 'error'
  }
  return types[status] || 'wait'
}

const getMetricClass = (metric: any): string => {
  if (metric.key === 'cpu_usage' && metric.value > 80) return 'metric-warning'
  if (metric.key === 'memory_usage' && metric.value > 80) return 'metric-warning'
  if (metric.key === 'success_rate' && metric.value >= 95) return 'metric-success'
  if (metric.key === 'success_rate' && metric.value < 80) return 'metric-error'
  return ''
}

const formatMetricValue = (metric: any): string => {
  return `${metric.value.toFixed(1)}${metric.unit}`
}

const getLogLevelType = (level: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    info: 'info',
    warning: 'warning',
    error: 'danger',
    debug: ''
  }
  return types[level] || 'info'
}

const handleWebSocketMessage = (data: any) => {
  switch (data.type) {
    case 'initial_state':
    case 'status_update':
      evolutionState.value = { ...evolutionState.value, ...data.data }
      emit('status-change', evolutionState.value)
      break
    case 'stage_change':
      evolutionState.value.current_stage = data.data.stage
      evolutionState.value.progress = data.data.progress
      updateStageStatus(data.data.stage, 'running')
      emit('stage-change', data.data.stage)
      emit('progress-update', data.data.progress)
      break
    case 'progress':
      evolutionState.value.progress = data.data.progress
      emit('progress-update', data.data.progress)
      break
    case 'metrics':
      evolutionState.value.metrics = data.data
      break
    case 'log':
      addLog(data.data)
      break
    case 'evolution_completed':
      evolutionState.value.status = 'completed'
      evolutionState.value.progress = 100
      ElMessage.success('演化完成')
      emit('evolution-completed', data.data)
      stopElapsedTime()
      break
    case 'evolution_failed':
      evolutionState.value.status = 'failed'
      ElMessage.error(`演化失败: ${data.data.reason || '未知原因'}`)
      emit('evolution-failed', data.data)
      stopElapsedTime()
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

const updateStageStatus = (stageName: string, status: EvolutionStage['status']) => {
  const stage = evolutionState.value.stages.find(s => s.name === stageName)
  if (stage) {
    stage.status = status
  }
}

const addLog = (log: EvolutionLog) => {
  evolutionState.value.logs.push(log)
  if (evolutionState.value.logs.length > 500) {
    evolutionState.value.logs.shift()
  }
  nextTick(() => {
    if (logsContainerRef.value) {
      logsContainerRef.value.scrollTop = logsContainerRef.value.scrollHeight
    }
  })
}

const clearLogs = () => {
  evolutionState.value.logs = []
}

const exportLogs = () => {
  const content = evolutionState.value.logs.map(log =>
    `[${log.timestamp}] [${log.level.toUpperCase()}]${log.stage ? ` [${log.stage}]` : ''} ${log.message}`
  ).join('\n')

  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `evolution-logs-${new Date().toISOString()}.txt`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('日志已导出')
}

const pauseEvolution = async () => {
  pausing.value = true
  try {
    const url = props.evolutionId
      ? `/evolution-status/${props.evolutionId}/pause`
      : '/evolution-status/pause'
    await api.post(url)
    evolutionState.value.status = 'paused'
    ElMessage.success('演化已暂停')
  } catch (error) {
    console.error('Failed to pause evolution:', error)
    ElMessage.error('暂停失败')
    emit('error', error as Error)
  } finally {
    pausing.value = false
  }
}

const resumeEvolution = async () => {
  resuming.value = true
  try {
    const url = props.evolutionId
      ? `/evolution-status/${props.evolutionId}/resume`
      : '/evolution-status/resume'
    await api.post(url)
    evolutionState.value.status = 'running'
    ElMessage.success('演化已继续')
  } catch (error) {
    console.error('Failed to resume evolution:', error)
    ElMessage.error('继续失败')
    emit('error', error as Error)
  } finally {
    resuming.value = false
  }
}

const stopEvolution = async () => {
  try {
    await ElMessageBox.confirm(
      '停止演化将中断当前操作，确定要停止吗？',
      '确认停止',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    stopping.value = true
    const url = props.evolutionId
      ? `/evolution-status/${props.evolutionId}/stop`
      : '/evolution-status/stop'
    await api.post(url)
    evolutionState.value.status = 'stopped'
    ElMessage.success('演化已停止')
    stopElapsedTime()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Failed to stop evolution:', error)
      ElMessage.error('停止失败')
      emit('error', error as Error)
    }
  } finally {
    stopping.value = false
  }
}

const startElapsedTime = () => {
  if (elapsedTimer) clearInterval(elapsedTimer)
  elapsedTimer = setInterval(() => {
    if (evolutionState.value.started_at) {
      const start = new Date(evolutionState.value.started_at).getTime()
      const now = Date.now()
      const elapsed = Math.floor((now - start) / 1000)
      const hours = Math.floor(elapsed / 3600)
      const minutes = Math.floor((elapsed % 3600) / 60)
      const seconds = elapsed % 60
      if (hours > 0) {
        elapsed_time.value = `${hours}h ${minutes}m ${seconds}s`
      } else if (minutes > 0) {
        elapsed_time.value = `${minutes}m ${seconds}s`
      } else {
        elapsed_time.value = `${seconds}s`
      }
    }
  }, 1000)
}

const stopElapsedTime = () => {
  if (elapsedTimer) {
    clearInterval(elapsedTimer)
    elapsedTimer = null
  }
}

onMounted(() => {
  if (props.autoConnect) {
    wsConnect()
  }
  if (isRunning.value) {
    startElapsedTime()
  }
})

onUnmounted(() => {
  wsDisconnect()
  stopElapsedTime()
})
</script>

<style scoped>
.realtime-evolution-panel {
  width: 100%;
}

.panel-card {
  transition: all 0.3s ease;
}

.panel-card.is-running {
  box-shadow: 0 0 30px rgba(64, 158, 255, 0.3);
  border-color: #409eff;
}

.panel-card.is-paused {
  box-shadow: 0 0 20px rgba(230, 162, 60, 0.3);
  border-color: #e6a23c;
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

.connection-status {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 4px;
}

.connection-status.connected {
  background: #f0f9eb;
  color: #67c23a;
}

.connection-status.disconnected {
  background: #fef0f0;
  color: #f56c6c;
}

.panel-content {
  padding: 10px 0;
}

.progress-section {
  padding: 15px 0;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}

.progress-label {
  font-weight: 500;
  font-size: 14px;
}

.progress-value {
  font-size: 20px;
  font-weight: 600;
  color: #409eff;
}

.progress-text {
  font-weight: 600;
}

.progress-animate :deep(.el-progress-bar__inner) {
  animation: progress-flow 2s linear infinite;
}

@keyframes progress-flow {
  0% { background-position: 0 0; }
  100% { background-position: 50px 0; }
}

.progress-info {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  margin-top: 15px;
}

.info-item {
  text-align: center;
}

.info-label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
}

.info-value {
  font-weight: 500;
  font-size: 14px;
}

.section-title {
  font-weight: 500;
  margin-bottom: 15px;
  color: #303133;
  font-size: 15px;
}

.stage-section {
  padding: 10px 0;
}

.current-stage {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.stage-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.stage-icon.stage-running {
  background: linear-gradient(135deg, #409eff, #66b1ff);
}

.stage-icon.stage-completed {
  background: linear-gradient(135deg, #67c23a, #85ce61);
}

.stage-icon.stage-failed {
  background: linear-gradient(135deg, #f56c6c, #f78989);
}

.stage-icon.stage-pending {
  background: linear-gradient(135deg, #909399, #c0c4cc);
}

.stage-info {
  flex: 1;
}

.stage-name {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 5px;
}

.stage-status {
  font-size: 14px;
  color: #909399;
}

.stage-steps {
  margin-top: 20px;
}

.metrics-section {
  padding: 10px 0;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.metric-card.metric-warning {
  background: #fdf6ec;
  border: 1px solid #e6a23c;
}

.metric-card.metric-error {
  background: #fef0f0;
  border: 1px solid #f56c6c;
}

.metric-card.metric-success {
  background: #f0f9eb;
  border: 1px solid #67c23a;
}

.metric-icon {
  color: #409eff;
}

.metric-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.metric-value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.logs-section {
  margin-top: 15px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.log-actions {
  display: flex;
  gap: 10px;
}

.logs-container {
  max-height: 300px;
  overflow-y: auto;
  background: #f5f7fa;
  border-radius: 8px;
  padding: 10px;
}

.log-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px;
  border-bottom: 1px solid #ebeef5;
  font-size: 13px;
}

.log-item:last-child {
  border-bottom: none;
}

.log-item.log-error {
  background: #fef0f0;
}

.log-item.log-warning {
  background: #fdf6ec;
}

.log-time {
  color: #909399;
  white-space: nowrap;
  font-family: monospace;
  font-size: 12px;
}

.log-stage {
  color: #409eff;
  font-weight: 500;
}

.log-message {
  flex: 1;
  word-break: break-all;
}

@media (max-width: 1200px) {
  .progress-info {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .progress-info {
    grid-template-columns: 1fr;
  }
}
</style>
