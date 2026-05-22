<template>
  <div class="evolution-status-panel">
    <el-card class="status-card" :class="{ 'is-running': isRunning }">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span class="title">演化状态</span>
            <el-tag :type="statusType" effect="dark" size="small">
              {{ statusLabel }}
            </el-tag>
          </div>
          <el-button
            v-if="showHistory"
            type="primary"
            link
            @click="toggleHistory"
          >
            <el-icon><Clock /></el-icon>
            {{ historyVisible ? '隐藏历史' : '查看历史' }}
          </el-button>
        </div>
      </template>

      <div class="status-content">
        <div class="current-status">
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="status-item">
                <div class="status-label">当前阶段</div>
                <div class="status-value" :class="{ 'stage-animate': isRunning }">
                  {{ currentStageLabel }}
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="status-item">
                <div class="status-label">演化进度</div>
                <el-progress
                  :percentage="progress"
                  :stroke-width="20"
                  :color="progressColor"
                  :class="{ 'progress-animate': isRunning }"
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
        </div>

        <el-divider />

        <div class="metrics-section">
          <div class="section-title">当前指标</div>
          <div class="metrics-grid">
            <div
              v-for="(value, key) in currentMetrics"
              :key="key"
              class="metric-item"
              :class="{ 'metric-changed': changedMetrics.includes(key) }"
            >
              <div class="metric-label">{{ getMetricLabel(key) }}</div>
              <div class="metric-value">
                {{ formatMetricValue(key, value) }}
              </div>
              <div v-if="previousMetrics[key] !== undefined" class="metric-change">
                <span :class="getChangeClass(key, value, previousMetrics[key])">
                  {{ formatChange(key, value, previousMetrics[key]) }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div v-if="activeChanges.length > 0" class="changes-section">
          <el-divider />
          <div class="section-title">正在进行的变更</div>
          <el-timeline>
            <el-timeline-item
              v-for="(change, index) in activeChanges"
              :key="index"
              :type="getChangeType(change.status)"
              :class="{ 'change-animate': change.status === 'running' }"
            >
              <div class="change-item">
                <span class="change-type">{{ change.type }}</span>
                <el-tag size="small" :type="getChangeType(change.status)">
                  {{ getChangeStatusLabel(change.status) }}
                </el-tag>
              </div>
              <div v-if="change.description" class="change-description">
                {{ change.description }}
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>
      </div>
    </el-card>

    <el-collapse-transition>
      <el-card v-show="historyVisible" class="history-card">
        <template #header>
          <div class="card-header">
            <span>状态历史</span>
            <el-button type="primary" link @click="clearHistory">
              清空历史
            </el-button>
          </div>
        </template>
        <div class="history-list">
          <el-timeline>
            <el-timeline-item
              v-for="(item, index) in statusHistory"
              :key="index"
              :timestamp="formatTime(item.timestamp)"
              :type="getHistoryType(item.status)"
              placement="top"
            >
              <div class="history-item">
                <div class="history-header">
                  <el-tag :type="getStatusTagType(item.status)" size="small">
                    {{ getStatusLabel(item.status) }}
                  </el-tag>
                  <span v-if="item.stage" class="history-stage">
                    {{ getStageLabel(item.stage) }}
                  </span>
                </div>
                <div v-if="item.message" class="history-message">
                  {{ item.message }}
                </div>
                <div v-if="item.progress !== undefined" class="history-progress">
                  进度: {{ item.progress }}%
                </div>
              </div>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-if="statusHistory.length === 0" description="暂无历史记录" :image-size="60" />
        </div>
      </el-card>
    </el-collapse-transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Clock } from '@element-plus/icons-vue'
import { useWebSocket, ConnectionState } from '@/composables/useWebSocket'
import api from '@/api'

interface EvolutionChange {
  type: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  description?: string
}

interface EvolutionStatusData {
  status: 'idle' | 'running' | 'completed' | 'failed' | 'paused'
  current_stage: string | null
  evolution_type: string | null
  progress: number
  started_at: string | null
  estimated_completion: string | null
  current_metrics: Record<string, number>
  active_changes: EvolutionChange[]
  last_evolution: string | null
  next_scheduled: string | null
}

interface StatusHistoryItem {
  timestamp: string
  status: string
  stage?: string
  progress?: number
  message?: string
}

interface Props {
  projectId?: number
  showHistory?: boolean
  autoRefresh?: boolean
  refreshInterval?: number
}

const props = withDefaults(defineProps<Props>(), {
  showHistory: true,
  autoRefresh: true,
  refreshInterval: 5000
})

const emit = defineEmits<{
  (e: 'status-change', status: EvolutionStatusData): void
  (e: 'stage-change', stage: string): void
  (e: 'progress-update', progress: number): void
  (e: 'error', error: Error): void
}>()

const loading = ref(false)
const historyVisible = ref(false)
const changedMetrics = ref<string[]>([])
const previousMetrics = ref<Record<string, number>>({})
const statusHistory = ref<StatusHistoryItem[]>([])

const status = ref<EvolutionStatusData>({
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

let refreshTimer: ReturnType<typeof setInterval> | null = null

const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
const wsHost = window.location.host
const wsUrl = `${wsProtocol}//${wsHost}/api/evolution-monitor/ws`

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

const isRunning = computed(() => status.value.status === 'running')

const statusType = computed(() => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    running: 'primary',
    completed: 'success',
    failed: 'danger',
    paused: 'warning',
    idle: 'info'
  }
  return types[status.value.status] || 'info'
})

const statusLabel = computed(() => {
  const labels: Record<string, string> = {
    idle: '空闲',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    paused: '已暂停'
  }
  return labels[status.value.status] || status.value.status
})

const currentStageLabel = computed(() => {
  const labels: Record<string, string> = {
    analysis: '分析阶段',
    planning: '规划阶段',
    execution: '执行阶段',
    validation: '验证阶段',
    deployment: '部署阶段'
  }
  return labels[status.value.current_stage || ''] || '无'
})

const evolutionTypeLabel = computed(() => {
  const labels: Record<string, string> = {
    skill_optimization: '技能优化',
    workflow_adaptation: '工作流适配',
    resource_rebalance: '资源重平衡',
    knowledge_update: '知识更新',
    performance_tuning: '性能调优'
  }
  return labels[status.value.evolution_type || ''] || '无'
})

const progress = computed(() => Math.min(100, Math.max(0, status.value.progress)))

const progressColor = computed(() => {
  if (status.value.progress < 30) return '#f56c6c'
  if (status.value.progress < 70) return '#e6a23c'
  return '#67c23a'
})

const currentMetrics = computed(() => status.value.current_metrics)

const getMetricLabel = (key: string): string => {
  const labels: Record<string, string> = {
    skill_success_rate: '技能成功率',
    avg_response_time: '平均响应时间',
    active_agents: '活跃Agent',
    pending_tasks: '待处理任务',
    performance: '性能',
    efficiency: '效率',
    error_rate: '错误率',
    throughput: '吞吐量'
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
  if (key.includes('throughput')) {
    return `${value.toFixed(0)}/s`
  }
  return value.toFixed(2)
}

const getChangeClass = (key: string, current: number, previous: number): string => {
  const diff = current - previous
  if (diff > 0) return 'change-up'
  if (diff < 0) return 'change-down'
  return 'change-stable'
}

const formatChange = (key: string, current: number, previous: number): string => {
  const diff = current - previous
  const percent = previous !== 0 ? ((diff / previous) * 100).toFixed(1) : '0'
  const prefix = diff > 0 ? '+' : ''
  return `${prefix}${percent}%`
}

const getChangeType = (changeStatus: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    completed: 'success',
    running: 'primary',
    pending: 'info',
    failed: 'danger'
  }
  return types[changeStatus] || 'info'
}

const getChangeStatusLabel = (changeStatus: string): string => {
  const labels: Record<string, string> = {
    pending: '待处理',
    running: '运行中',
    completed: '已完成',
    failed: '失败'
  }
  return labels[changeStatus] || changeStatus
}

const getStageLabel = (stage: string): string => {
  const labels: Record<string, string> = {
    analysis: '分析阶段',
    planning: '规划阶段',
    execution: '执行阶段',
    validation: '验证阶段',
    deployment: '部署阶段'
  }
  return labels[stage] || stage
}

const getStatusLabel = (statusValue: string): string => {
  const labels: Record<string, string> = {
    idle: '空闲',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    paused: '已暂停'
  }
  return labels[statusValue] || statusValue
}

const getStatusTagType = (statusValue: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    completed: 'success',
    running: 'primary',
    failed: 'danger',
    paused: 'warning',
    idle: 'info'
  }
  return types[statusValue] || 'info'
}

const getHistoryType = (statusValue: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    completed: 'success',
    running: 'primary',
    failed: 'danger',
    paused: 'warning',
    idle: 'info'
  }
  return types[statusValue] || 'info'
}

const formatTime = (time: string): string => {
  return new Date(time).toLocaleString('zh-CN')
}

const toggleHistory = () => {
  historyVisible.value = !historyVisible.value
}

const clearHistory = () => {
  statusHistory.value = []
  ElMessage.success('历史记录已清空')
}

const addHistoryItem = (item: StatusHistoryItem) => {
  statusHistory.value.unshift(item)
  if (statusHistory.value.length > 100) {
    statusHistory.value.pop()
  }
}

const handleWebSocketMessage = (data: any) => {
  switch (data.type) {
    case 'initial_state':
    case 'status_update':
      updateStatus(data.data)
      break
    case 'evolution_started':
      addHistoryItem({
        timestamp: new Date().toISOString(),
        status: 'running',
        stage: data.data.stage,
        message: `演化开始: ${data.data.evolution_type}`
      })
      updateStatus(data.data)
      break
    case 'evolution_progress':
      status.value.current_stage = data.data.stage
      status.value.progress = data.data.progress
      emit('stage-change', data.data.stage)
      emit('progress-update', data.data.progress)
      addHistoryItem({
        timestamp: new Date().toISOString(),
        status: 'running',
        stage: data.data.stage,
        progress: data.data.progress
      })
      break
    case 'evolution_completed':
      addHistoryItem({
        timestamp: new Date().toISOString(),
        status: 'completed',
        message: '演化完成'
      })
      updateStatus(data.data)
      break
    case 'evolution_failed':
      addHistoryItem({
        timestamp: new Date().toISOString(),
        status: 'failed',
        message: data.data.reason || '演化失败'
      })
      updateStatus(data.data)
      break
    case 'evolution_paused':
      addHistoryItem({
        timestamp: new Date().toISOString(),
        status: 'paused',
        message: '演化已暂停'
      })
      updateStatus(data.data)
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

const updateStatus = (newStatus: EvolutionStatusData) => {
  const oldStatus = status.value.status
  const oldStage = status.value.current_stage

  previousMetrics.value = { ...status.value.current_metrics }
  status.value = newStatus

  const changed: string[] = []
  for (const key in newStatus.current_metrics) {
    if (previousMetrics.value[key] !== undefined &&
        previousMetrics.value[key] !== newStatus.current_metrics[key]) {
      changed.push(key)
    }
  }
  changedMetrics.value = changed

  setTimeout(() => {
    changedMetrics.value = []
  }, 1000)

  if (oldStatus !== newStatus.status) {
    emit('status-change', newStatus)
  }
  if (oldStage !== newStatus.current_stage && newStatus.current_stage) {
    emit('stage-change', newStatus.current_stage)
  }
}

const fetchStatus = async () => {
  if (loading.value) return

  loading.value = true
  try {
    const url = props.projectId
      ? `/evolution-monitor/status?project_id=${props.projectId}`
      : '/evolution-monitor/status'
    const response = await api.get(url)
    updateStatus(response as EvolutionStatusData)
  } catch (error) {
    console.error('Failed to fetch evolution status:', error)
    emit('error', error as Error)
  } finally {
    loading.value = false
  }
}

const predictEvolution = async () => {
  if (!predictionConfig.value.evolutionType) {
    ElMessage.warning('请选择演化类型')
    return
  }
  
  try {
    const response = await api.post('/evolution-monitor/predict', null, {
      params: {
        evolution_type: predictionConfig.value.evolutionType,
        target_components: predictionConfig.value.targetComponents,
        prediction_horizon: predictionConfig.value.predictionHorizon
      }
    })
    
    predictionResult.value = response
    ElMessage.success('预测完成')
  } catch (error) {
    console.error('预测失败:', error)
    ElMessage.error('预测失败')
  }
}

const compareEvolution = async () => {
  if (!comparisonConfig.value.evolutionId) {
    ElMessage.warning('请输入演化ID')
    return
  }
  
  try {
    const response = await api.post('/evolution-monitor/compare', null, {
      params: {
        evolution_id: comparisonConfig.value.evolutionId
      }
    })
    
    comparisonResult.value = response
    ElMessage.success('比较完成')
  } catch (error) {
    console.error('比较失败:', error)
    ElMessage.error('比较失败')
  }
}

const rollbackEvolution = async () => {
  if (!rollbackConfig.value.evolutionId) {
    ElMessage.warning('请输入演化ID')
    return
  }
  
  if (!rollbackConfig.value.reason) {
    ElMessage.warning('请输入回滚原因')
    return
  }
  
  try {
    await ElMessageBox.confirm('确定要回滚此演化吗？此操作不可撤销。', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.post('/evolution-monitor/rollback', null, {
      params: {
        evolution_id: rollbackConfig.value.evolutionId,
        reason: rollbackConfig.value.reason,
        trigger_type: rollbackConfig.value.triggerType
      }
    })
    
    ElMessage.success('回滚已启动')
    fetchStatus()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('回滚失败:', error)
      ElMessage.error('回滚失败')
    }
  }
}

const exportEvolutionData = async () => {
  try {
    const response = await api.post('/evolution-monitor/export', null, {
      params: {
        export_type: exportConfig.value.exportType,
        data_scope: exportConfig.value.dataScope,
        filters: exportConfig.value.filters
      }
    })
    
    ElMessage.success('导出任务已创建')
    
    if ((response as any).download_url) {
      window.open((response as any).download_url, '_blank')
    }
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

const showPredictionDialog = () => {
  predictionDialogVisible.value = true
}

const showComparisonDialog = () => {
  comparisonDialogVisible.value = true
}

const showRollbackDialog = () => {
  rollbackDialogVisible.value = true
}

const showExportDialog = () => {
  exportDialogVisible.value = true
}

const formatPredictionResult = (result: any): string => {
  if (!result) return ''
  return JSON.stringify(result, null, 2)
}

const getImprovementColor = (value: number): string => {
  if (value > 20) return '#67C23A'
  if (value > 10) return '#409EFF'
  if (value > 0) return '#E6A23C'
  return '#F56C6C'
}

const getRiskLevelColor = (level: string): string => {
  const colors: Record<string, string> = {
    'low': '#67C23A',
    'medium': '#E6A23C',
    'high': '#F56C6C'
  }
  return colors[level] || '#909399'
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

watch(isConnected, (connected) => {
  if (connected) {
    stopAutoRefresh()
  } else if (props.autoRefresh) {
    startAutoRefresh()
  }
})

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
.evolution-status-panel {
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

.status-value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.stage-animate {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.progress-animate :deep(.el-progress-bar__inner) {
  animation: progress-flow 2s linear infinite;
}

@keyframes progress-flow {
  0% { background-position: 0 0; }
  100% { background-position: 50px 0; }
}

.section-title {
  font-weight: 500;
  margin-bottom: 15px;
  color: #303133;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
}

.metric-item {
  text-align: center;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.metric-item.metric-changed {
  animation: metric-flash 0.5s ease;
  background: #ecf5ff;
}

@keyframes metric-flash {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.metric-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 20px;
  font-weight: 600;
  color: #409eff;
}

.metric-change {
  font-size: 12px;
  margin-top: 5px;
}

.change-up {
  color: #67c23a;
}

.change-down {
  color: #f56c6c;
}

.change-stable {
  color: #909399;
}

.changes-section {
  margin-top: 15px;
}

.change-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.change-type {
  font-size: 14px;
}

.change-description {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.change-animate {
  animation: change-pulse 1.5s infinite;
}

@keyframes change-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.history-card {
  margin-top: 20px;
}

.history-list {
  max-height: 400px;
  overflow-y: auto;
}

.history-item {
  padding: 8px 0;
}

.history-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 5px;
}

.history-stage {
  font-size: 13px;
  color: #606266;
}

.history-message {
  font-size: 13px;
  color: #606266;
  margin-top: 5px;
}

.history-progress {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

@media (max-width: 1200px) {
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}
</style>
