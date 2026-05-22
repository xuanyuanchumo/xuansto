<template>
  <div class="realtime-evolution-status">
    <el-card class="status-card" :class="{ 'is-running': isRunning }">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span class="title">实时演化状态</span>
            <el-tag :type="statusType" effect="dark">
              {{ statusLabel }}
            </el-tag>
            <div class="connection-indicator" :class="connectionClass">
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
                :loading="rollingBack"
                @click="rollbackEvolution"
              >
                <el-icon><RefreshLeft /></el-icon>
                回滚
              </el-button>
            </el-button-group>
          </div>
        </div>
      </template>

      <div class="status-content">
        <div class="progress-section">
          <div class="progress-header">
            <span class="progress-label">演化进度</span>
            <span class="progress-value">{{ evolutionStatus.progress }}%</span>
          </div>
          <el-progress
            :percentage="evolutionStatus.progress"
            :stroke-width="20"
            :color="progressColor"
            :class="{ 'progress-animate': isRunning }"
          >
            <template #default="{ percentage }">
              <span class="progress-text">{{ percentage }}%</span>
            </template>
          </el-progress>
          <div class="progress-details">
            <div class="detail-item">
              <span class="detail-label">当前阶段</span>
              <span class="detail-value stage-value">{{ currentStageLabel }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">演化类型</span>
              <span class="detail-value">{{ evolutionTypeLabel }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">开始时间</span>
              <span class="detail-value">{{ formatTime(evolutionStatus.started_at) }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">预计完成</span>
              <span class="detail-value">{{ formatTime(evolutionStatus.estimated_completion) }}</span>
            </div>
          </div>
        </div>

        <el-divider />

        <div class="stages-section">
          <div class="section-title">演化阶段</div>
          <el-steps :active="activeStep" align-center>
            <el-step
              v-for="(stage, index) in stages"
              :key="index"
              :title="stage.label"
              :description="stage.status === 'running' ? '进行中...' : getStageStatus(stage.status)"
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

        <div class="logs-section">
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
          <div class="logs-container" ref="logsContainer">
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
            <el-empty v-if="filteredLogs.length === 0" description="暂无日志" :image-size="60" />
          </div>
        </div>

        <div v-if="evolutionStatus.metrics" class="metrics-section">
          <el-divider />
          <div class="section-title">实时指标</div>
          <el-row :gutter="15">
            <el-col :span="6" v-for="(value, key) in evolutionStatus.metrics" :key="key">
              <div class="metric-card">
                <div class="metric-label">{{ getMetricLabel(key) }}</div>
                <div class="metric-value" :class="getMetricClass(key, value)">
                  {{ formatMetricValue(key, value) }}
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
      </div>
    </el-card>

    <el-dialog
      v-model="rollbackDialogVisible"
      title="确认回滚"
      width="400px"
    >
      <el-alert
        type="warning"
        title="回滚警告"
        description="回滚将撤销当前演化的所有更改，此操作不可逆。"
        :closable="false"
        show-icon
        style="margin-bottom: 15px"
      />
      <el-form label-width="80px">
        <el-form-item label="回滚原因">
          <el-input
            v-model="rollbackReason"
            type="textarea"
            :rows="3"
            placeholder="请输入回滚原因（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rollbackDialogVisible = false">取消</el-button>
        <el-button type="danger" :loading="rollingBack" @click="confirmRollback">
          确认回滚
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Connection,
  VideoPause,
  VideoPlay,
  RefreshLeft,
  Download,
  Loading,
  CircleCheck,
  CircleClose,
  Clock
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
}

interface EvolutionStatus {
  status: 'idle' | 'running' | 'paused' | 'completed' | 'failed'
  progress: number
  current_stage: string | null
  evolution_type: string | null
  started_at: string | null
  estimated_completion: string | null
  metrics: Record<string, number>
  stages: EvolutionStage[]
}

interface Props {
  evolutionId?: string
  autoConnect?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  autoConnect: true
})

const emit = defineEmits<{
  (e: 'status-change', status: EvolutionStatus): void
  (e: 'evolution-completed', result: any): void
  (e: 'evolution-failed', error: any): void
  (e: 'error', error: Error): void
}>()

const logLevel = ref('')
const logsContainer = ref<HTMLElement | null>(null)
const rollbackDialogVisible = ref(false)
const rollbackReason = ref('')

const pausing = ref(false)
const resuming = ref(false)
const rollingBack = ref(false)

const evolutionStatus = ref<EvolutionStatus>({
  status: 'idle',
  progress: 0,
  current_stage: null,
  evolution_type: null,
  started_at: null,
  estimated_completion: null,
  metrics: {},
  stages: []
})

const logs = ref<EvolutionLog[]>([])

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

const isRunning = computed(() => evolutionStatus.value.status === 'running')
const isPaused = computed(() => evolutionStatus.value.status === 'paused')

const statusType = computed(() => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    idle: 'info',
    running: 'primary',
    paused: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return types[evolutionStatus.value.status] || 'info'
})

const statusLabel = computed(() => {
  const labels: Record<string, string> = {
    idle: '空闲',
    running: '运行中',
    paused: '已暂停',
    completed: '已完成',
    failed: '失败'
  }
  return labels[evolutionStatus.value.status] || '未知'
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

const progressColor = computed(() => {
  const progress = evolutionStatus.value.progress
  if (progress < 30) return '#f56c6c'
  if (progress < 70) return '#e6a23c'
  return '#67c23a'
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

const stages = computed(() => {
  const defaultStages = [
    { name: 'analysis', label: '分析', status: 'pending' },
    { name: 'planning', label: '规划', status: 'pending' },
    { name: 'execution', label: '执行', status: 'pending' },
    { name: 'validation', label: '验证', status: 'pending' },
    { name: 'deployment', label: '部署', status: 'pending' }
  ]
  return evolutionStatus.value.stages.length > 0 ? evolutionStatus.value.stages : defaultStages
})

const activeStep = computed(() => {
  const stageNames = ['analysis', 'planning', 'execution', 'validation', 'deployment']
  const currentStage = evolutionStatus.value.current_stage
  if (!currentStage) return 0
  const index = stageNames.indexOf(currentStage)
  return index >= 0 ? index : 0
})

const filteredLogs = computed(() => {
  if (!logLevel.value) return logs.value
  return logs.value.filter(log => log.level === logLevel.value)
})

const formatTime = (time: string | null): string => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const getStageStatus = (status: string): string => {
  const labels: Record<string, string> = {
    pending: '待处理',
    running: '进行中',
    completed: '已完成',
    failed: '失败'
  }
  return labels[status] || status
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

const getStageIcon = (status: string) => {
  const icons: Record<string, any> = {
    pending: Clock,
    running: Loading,
    completed: CircleCheck,
    failed: CircleClose
  }
  return icons[status] || Clock
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

const getMetricLabel = (key: string): string => {
  const labels: Record<string, string> = {
    cpu_usage: 'CPU使用率',
    memory_usage: '内存使用率',
    disk_io: '磁盘IO',
    network_io: '网络IO',
    success_rate: '成功率',
    error_count: '错误数',
    throughput: '吞吐量',
    latency: '延迟'
  }
  return labels[key] || key
}

const formatMetricValue = (key: string, value: number): string => {
  if (key.includes('rate') || key.includes('usage')) {
    return `${value.toFixed(1)}%`
  }
  if (key.includes('latency')) {
    return `${value.toFixed(0)}ms`
  }
  if (key.includes('throughput')) {
    return `${value.toFixed(0)}/s`
  }
  return value.toFixed(2)
}

const getMetricClass = (key: string, value: number): string => {
  if (key.includes('usage') && value > 80) return 'metric-warning'
  if (key.includes('error') && value > 0) return 'metric-error'
  if (key.includes('success') && value >= 95) return 'metric-success'
  return ''
}

const handleWebSocketMessage = (data: any) => {
  switch (data.type) {
    case 'initial_state':
    case 'status_update':
      evolutionStatus.value = data.data
      emit('status-change', data.data)
      break
    case 'log':
      addLog(data.data)
      break
    case 'stage_change':
      evolutionStatus.value.current_stage = data.data.stage
      evolutionStatus.value.progress = data.data.progress
      if (evolutionStatus.value.stages.length > 0) {
        const stage = evolutionStatus.value.stages.find(s => s.name === data.data.stage)
        if (stage) stage.status = 'running'
      }
      break
    case 'progress':
      evolutionStatus.value.progress = data.data.progress
      break
    case 'metrics':
      evolutionStatus.value.metrics = data.data
      break
    case 'evolution_completed':
      evolutionStatus.value.status = 'completed'
      ElMessage.success('演化完成')
      emit('evolution-completed', data.data)
      break
    case 'evolution_failed':
      evolutionStatus.value.status = 'failed'
      ElMessage.error(`演化失败: ${data.data.reason || '未知原因'}`)
      emit('evolution-failed', data.data)
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

const addLog = (log: EvolutionLog) => {
  logs.value.push(log)
  if (logs.value.length > 500) {
    logs.value.shift()
  }
  nextTick(() => {
    if (logsContainer.value) {
      logsContainer.value.scrollTop = logsContainer.value.scrollHeight
    }
  })
}

const clearLogs = () => {
  logs.value = []
}

const exportLogs = () => {
  const content = logs.value.map(log =>
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
    evolutionStatus.value.status = 'paused'
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
    evolutionStatus.value.status = 'running'
    ElMessage.success('演化已继续')
  } catch (error) {
    console.error('Failed to resume evolution:', error)
    ElMessage.error('继续失败')
    emit('error', error as Error)
  } finally {
    resuming.value = false
  }
}

const rollbackEvolution = () => {
  rollbackDialogVisible.value = true
}

const confirmRollback = async () => {
  rollingBack.value = true
  try {
    const url = props.evolutionId
      ? `/evolution-status/${props.evolutionId}/rollback`
      : '/evolution-status/rollback'
    await api.post(url, { reason: rollbackReason.value })
    evolutionStatus.value.status = 'idle'
    evolutionStatus.value.progress = 0
    ElMessage.success('演化已回滚')
    rollbackDialogVisible.value = false
    rollbackReason.value = ''
  } catch (error) {
    console.error('Failed to rollback evolution:', error)
    ElMessage.error('回滚失败')
    emit('error', error as Error)
  } finally {
    rollingBack.value = false
  }
}

onMounted(() => {
  if (props.autoConnect) {
    wsConnect()
  }
})

onUnmounted(() => {
  wsDisconnect()
})
</script>

<style scoped>
.realtime-evolution-status {
  width: 100%;
}

.status-card {
  transition: all 0.3s ease;
}

.status-card.is-running {
  box-shadow: 0 0 20px rgba(64, 158, 255, 0.3);
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

.connection-indicator {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
}

.connection-indicator.connected {
  background: #f0f9eb;
  color: #67c23a;
}

.connection-indicator.disconnected {
  background: #fef0f0;
  color: #f56c6c;
}

.status-content {
  padding: 10px 0;
}

.progress-section {
  padding: 10px 0;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
}

.progress-label {
  font-weight: 500;
}

.progress-value {
  font-size: 18px;
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

.progress-details {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
  margin-top: 15px;
}

.detail-item {
  text-align: center;
}

.detail-label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
}

.detail-value {
  font-weight: 500;
}

.stage-value {
  color: #409eff;
}

.section-title {
  font-weight: 500;
  margin-bottom: 15px;
  color: #303133;
}

.stages-section {
  padding: 10px 0;
}

.logs-section {
  margin-top: 20px;
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

.metrics-section {
  margin-top: 20px;
}

.metric-card {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 15px;
  text-align: center;
}

.metric-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.metric-value.metric-success { color: #67c23a; }
.metric-value.metric-warning { color: #e6a23c; }
.metric-value.metric-error { color: #f56c6c; }

@media (max-width: 1200px) {
  .progress-details {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .progress-details {
    grid-template-columns: 1fr;
  }
}
</style>
