<template>
  <div class="auto-fix-progress">
    <el-card class="progress-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span class="title">自动修复进度</span>
            <el-tag :type="overallStatusType" effect="dark">
              {{ overallStatusLabel }}
            </el-tag>
            <span class="task-count">{{ activeTasks.length }} 个任务进行中</span>
          </div>
          <div class="header-actions">
            <el-button
              v-if="hasRunningTasks"
              type="warning"
              size="small"
              :loading="pausingAll"
              @click="pauseAllTasks"
            >
              <el-icon><VideoPause /></el-icon>
              全部暂停
            </el-button>
            <el-button
              v-if="hasPausedTasks"
              type="success"
              size="small"
              :loading="resumingAll"
              @click="resumeAllTasks"
            >
              <el-icon><VideoPlay /></el-icon>
              全部继续
            </el-button>
            <el-button type="primary" size="small" @click="showHistory = !showHistory">
              <el-icon><Clock /></el-icon>
              {{ showHistory ? '隐藏历史' : '查看历史' }}
            </el-button>
          </div>
        </div>
      </template>

      <div class="progress-content">
        <div class="overall-progress">
          <div class="progress-header">
            <span class="progress-label">总体进度</span>
            <span class="progress-value">{{ overallProgress }}%</span>
          </div>
          <el-progress
            :percentage="overallProgress"
            :stroke-width="20"
            :color="getProgressColor(overallProgress)"
          />
          <div class="progress-stats">
            <div class="stat-item">
              <span class="stat-label">已完成</span>
              <span class="stat-value completed">{{ completedCount }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">进行中</span>
              <span class="stat-value running">{{ runningCount }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">已暂停</span>
              <span class="stat-value paused">{{ pausedCount }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">失败</span>
              <span class="stat-value failed">{{ failedCount }}</span>
            </div>
          </div>
        </div>

        <el-divider />

        <div class="tasks-section">
          <div class="section-header">
            <span class="section-title">修复任务列表</span>
            <el-input
              v-model="taskFilter"
              placeholder="搜索任务..."
              prefix-icon="Search"
              clearable
              size="small"
              style="width: 200px"
            />
          </div>
          <div class="tasks-list" v-loading="loading">
            <div
              v-for="task in filteredTasks"
              :key="task.id"
              class="task-item"
              :class="`task-${task.status}`"
            >
              <div class="task-header">
                <div class="task-info">
                  <el-icon class="task-icon" :class="`status-${task.status}`">
                    <component :is="getTaskIcon(task.status)" />
                  </el-icon>
                  <div class="task-title">
                    <span class="title-text">{{ task.title }}</span>
                    <el-tag :type="getTaskTypeTag(task.type)" size="small">
                      {{ getTaskTypeLabel(task.type) }}
                    </el-tag>
                  </div>
                </div>
                <div class="task-actions">
                  <el-button
                    v-if="task.status === 'running'"
                    type="warning"
                    size="small"
                    :loading="task.pausing"
                    @click="pauseTask(task)"
                  >
                    暂停
                  </el-button>
                  <el-button
                    v-if="task.status === 'paused'"
                    type="success"
                    size="small"
                    :loading="task.resuming"
                    @click="resumeTask(task)"
                  >
                    继续
                  </el-button>
                  <el-button
                    v-if="task.status === 'failed'"
                    type="primary"
                    size="small"
                    :loading="task.retrying"
                    @click="retryTask(task)"
                  >
                    重试
                  </el-button>
                  <el-button
                    v-if="['running', 'paused'].includes(task.status)"
                    type="danger"
                    size="small"
                    :loading="task.cancelling"
                    @click="cancelTask(task)"
                  >
                    取消
                  </el-button>
                </div>
              </div>

              <div class="task-progress">
                <el-progress
                  :percentage="task.progress"
                  :stroke-width="12"
                  :color="getProgressColor(task.progress)"
                  :status="getProgressStatus(task.status)"
                />
                <div class="progress-info">
                  <span class="info-item">{{ task.progress }}%</span>
                  <span class="info-item" v-if="task.estimated_time">
                    预计剩余: {{ formatTime(task.estimated_time - task.elapsed_time) }}
                  </span>
                </div>
              </div>

              <div class="task-details">
                <div class="detail-row">
                  <span class="detail-label">问题描述:</span>
                  <span class="detail-value">{{ task.description }}</span>
                </div>
                <div class="detail-row" v-if="task.target_file">
                  <span class="detail-label">目标文件:</span>
                  <span class="detail-value file-path">{{ task.target_file }}</span>
                </div>
                <div class="detail-row" v-if="task.current_step">
                  <span class="detail-label">当前步骤:</span>
                  <span class="detail-value">{{ task.current_step }}</span>
                </div>
              </div>

              <div class="task-footer">
                <div class="task-meta">
                  <span class="meta-item">
                    <el-icon><Clock /></el-icon>
                    开始: {{ formatDateTime(task.started_at) }}
                  </span>
                  <span class="meta-item" v-if="task.completed_at">
                    <el-icon><CircleCheck /></el-icon>
                    完成: {{ formatDateTime(task.completed_at) }}
                  </span>
                </div>
                <el-button
                  type="primary"
                  link
                  size="small"
                  @click="showTaskDetail(task)"
                >
                  查看详情
                </el-button>
              </div>
            </div>
            <el-empty v-if="filteredTasks.length === 0 && !loading" description="暂无修复任务" />
          </div>
        </div>

        <el-collapse-transition>
          <div v-show="showHistory" class="history-section">
            <el-divider />
            <div class="section-title">修复历史</div>
            <el-table :data="historyTasks" style="width: 100%" max-height="300">
              <el-table-column prop="title" label="任务名称" min-width="200" />
              <el-table-column prop="type" label="类型" width="100">
                <template #default="{ row }">
                  <el-tag :type="getTaskTypeTag(row.type)" size="small">
                    {{ getTaskTypeLabel(row.type) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="getStatusTag(row.status)" size="small">
                    {{ getStatusLabel(row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="progress" label="进度" width="100">
                <template #default="{ row }">
                  {{ row.progress }}%
                </template>
              </el-table-column>
              <el-table-column prop="completed_at" label="完成时间" width="180">
                <template #default="{ row }">
                  {{ formatDateTime(row.completed_at) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100" fixed="right">
                <template #default="{ row }">
                  <el-button type="primary" link size="small" @click="viewHistoryDetail(row)">
                    详情
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-collapse-transition>
      </div>
    </el-card>

    <el-dialog
      v-model="taskDetailVisible"
      :title="selectedTask?.title"
      width="700px"
    >
      <div class="task-detail-dialog" v-if="selectedTask">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务ID">{{ selectedTask.id }}</el-descriptions-item>
          <el-descriptions-item label="类型">
            <el-tag :type="getTaskTypeTag(selectedTask.type)">
              {{ getTaskTypeLabel(selectedTask.type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusTag(selectedTask.status)">
              {{ getStatusLabel(selectedTask.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="进度">{{ selectedTask.progress }}%</el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ formatDateTime(selectedTask.started_at) }}</el-descriptions-item>
          <el-descriptions-item label="完成时间">{{ formatDateTime(selectedTask.completed_at) }}</el-descriptions-item>
        </el-descriptions>

        <el-divider />

        <div class="detail-section">
          <div class="detail-title">问题描述</div>
          <div class="detail-content">{{ selectedTask.description }}</div>
        </div>

        <div class="detail-section" v-if="selectedTask.target_file">
          <div class="detail-title">目标文件</div>
          <div class="detail-content file-path">{{ selectedTask.target_file }}</div>
        </div>

        <div class="detail-section" v-if="selectedTask.steps?.length">
          <div class="detail-title">修复步骤</div>
          <el-steps :active="getActiveStep(selectedTask)" finish-status="success">
            <el-step
              v-for="(step, index) in selectedTask.steps"
              :key="index"
              :title="step.name"
              :description="step.status"
              :status="getStepStatus(step.status)"
            />
          </el-steps>
        </div>

        <div class="detail-section" v-if="selectedTask.logs?.length">
          <div class="detail-title">执行日志</div>
          <div class="logs-container">
            <div
              v-for="(log, index) in selectedTask.logs"
              :key="index"
              class="log-item"
              :class="`log-${log.level}`"
            >
              <span class="log-time">{{ formatDateTime(log.timestamp) }}</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  VideoPause,
  VideoPlay,
  Clock,
  CircleCheck,
  CircleClose,
  Loading,
  Search,
  Document,
  Cpu,
  Setting,
  Warning
} from '@element-plus/icons-vue'
import { useWebSocket, ConnectionState } from '@/composables/useWebSocket'
import api from '@/api'

interface TaskStep {
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed'
}

interface TaskLog {
  timestamp: string
  level: 'info' | 'warning' | 'error'
  message: string
}

interface FixTask {
  id: number
  title: string
  type: 'bug_fix' | 'optimization' | 'refactor' | 'security' | 'performance'
  description: string
  target_file?: string
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled'
  progress: number
  current_step?: string
  steps?: TaskStep[]
  logs?: TaskLog[]
  started_at: string
  completed_at?: string
  estimated_time?: number
  elapsed_time?: number
  pausing?: boolean
  resuming?: boolean
  cancelling?: boolean
  retrying?: boolean
}

interface Props {
  autoRefresh?: boolean
  refreshInterval?: number
}

const props = withDefaults(defineProps<Props>(), {
  autoRefresh: true,
  refreshInterval: 5000
})

const emit = defineEmits<{
  (e: 'task-completed', task: FixTask): void
  (e: 'task-failed', task: FixTask): void
  (e: 'error', error: Error): void
}>()

const loading = ref(false)
const taskFilter = ref('')
const showHistory = ref(false)
const pausingAll = ref(false)
const resumingAll = ref(false)
const tasks = ref<FixTask[]>([])
const historyTasks = ref<FixTask[]>([])
const selectedTask = ref<FixTask | null>(null)
const taskDetailVisible = ref(false)

let refreshTimer: ReturnType<typeof setInterval> | null = null

const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
const wsHost = window.location.host
const wsUrl = `${wsProtocol}//${wsHost}/api/auto-fix/ws`

const {
  connectionState,
  isConnected,
  connect: wsConnect,
  disconnect: wsDisconnect
} = useWebSocket({
  url: wsUrl,
  heartbeatInterval: 30000,
  onMessage: handleWebSocketMessage
})

const activeTasks = computed(() => tasks.value.filter(t => ['running', 'paused'].includes(t.status)))
const hasRunningTasks = computed(() => tasks.value.some(t => t.status === 'running'))
const hasPausedTasks = computed(() => tasks.value.some(t => t.status === 'paused'))

const overallProgress = computed(() => {
  if (tasks.value.length === 0) return 0
  const totalProgress = tasks.value.reduce((sum, t) => sum + t.progress, 0)
  return Math.round(totalProgress / tasks.value.length)
})

const overallStatusType = computed(() => {
  if (hasRunningTasks.value) return 'primary'
  if (hasPausedTasks.value) return 'warning'
  if (tasks.value.some(t => t.status === 'failed')) return 'danger'
  return 'success'
})

const overallStatusLabel = computed(() => {
  if (hasRunningTasks.value) return '修复中'
  if (hasPausedTasks.value) return '已暂停'
  if (tasks.value.every(t => t.status === 'completed')) return '全部完成'
  if (tasks.value.some(t => t.status === 'failed')) return '部分失败'
  return '空闲'
})

const completedCount = computed(() => tasks.value.filter(t => t.status === 'completed').length)
const runningCount = computed(() => tasks.value.filter(t => t.status === 'running').length)
const pausedCount = computed(() => tasks.value.filter(t => t.status === 'paused').length)
const failedCount = computed(() => tasks.value.filter(t => t.status === 'failed').length)

const filteredTasks = computed(() => {
  if (!taskFilter.value) return tasks.value
  const keyword = taskFilter.value.toLowerCase()
  return tasks.value.filter(t =>
    t.title.toLowerCase().includes(keyword) ||
    t.description.toLowerCase().includes(keyword) ||
    t.target_file?.toLowerCase().includes(keyword)
  )
})

const formatDateTime = (time: string | undefined): string => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const formatTime = (seconds: number | undefined): string => {
  if (!seconds || seconds < 0) return '-'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}分${secs}秒`
}

const getProgressColor = (progress: number): string => {
  if (progress < 30) return '#f56c6c'
  if (progress < 70) return '#e6a23c'
  return '#67c23a'
}

const getProgressStatus = (status: string): '' | 'success' | 'warning' | 'exception' => {
  const statuses: Record<string, '' | 'success' | 'warning' | 'exception'> = {
    completed: 'success',
    paused: 'warning',
    failed: 'exception',
    cancelled: 'exception'
  }
  return statuses[status] || ''
}

const getTaskIcon = (status: string) => {
  const icons: Record<string, any> = {
    pending: Clock,
    running: Loading,
    paused: VideoPause,
    completed: CircleCheck,
    failed: CircleClose,
    cancelled: CircleClose
  }
  return icons[status] || Clock
}

const getTaskTypeTag = (type: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const tags: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    bug_fix: 'danger',
    optimization: 'warning',
    refactor: 'primary',
    security: 'danger',
    performance: 'warning'
  }
  return tags[type] || 'info'
}

const getTaskTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    bug_fix: 'Bug修复',
    optimization: '优化',
    refactor: '重构',
    security: '安全修复',
    performance: '性能优化'
  }
  return labels[type] || type
}

const getStatusTag = (status: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const tags: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    completed: 'success',
    running: 'primary',
    paused: 'warning',
    failed: 'danger',
    cancelled: 'info'
  }
  return tags[status] || 'info'
}

const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    pending: '待处理',
    running: '运行中',
    paused: '已暂停',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return labels[status] || status
}

const getActiveStep = (task: FixTask): number => {
  if (!task.steps) return 0
  return task.steps.filter(s => s.status === 'completed').length
}

const getStepStatus = (status: string): '' | 'process' | 'finish' | 'error' | 'wait' => {
  const statuses: Record<string, '' | 'process' | 'finish' | 'error' | 'wait'> = {
    pending: 'wait',
    running: 'process',
    completed: 'finish',
    failed: 'error'
  }
  return statuses[status] || 'wait'
}

const fetchTasks = async () => {
  loading.value = true
  try {
    const response = await api.get('/auto-fix/tasks')
    tasks.value = (response.active || []).map((t: FixTask) => ({
      ...t,
      pausing: false,
      resuming: false,
      cancelling: false,
      retrying: false
    }))
    historyTasks.value = response.history || []
  } catch (error) {
    console.error('Failed to fetch tasks:', error)
    emit('error', error as Error)
  } finally {
    loading.value = false
  }
}

const pauseTask = async (task: FixTask) => {
  task.pausing = true
  try {
    await api.post(`/auto-fix/tasks/${task.id}/pause`)
    task.status = 'paused'
    ElMessage.success(`任务 "${task.title}" 已暂停`)
  } catch (error) {
    console.error('Failed to pause task:', error)
    ElMessage.error('暂停失败')
    emit('error', error as Error)
  } finally {
    task.pausing = false
  }
}

const resumeTask = async (task: FixTask) => {
  task.resuming = true
  try {
    await api.post(`/auto-fix/tasks/${task.id}/resume`)
    task.status = 'running'
    ElMessage.success(`任务 "${task.title}" 已继续`)
  } catch (error) {
    console.error('Failed to resume task:', error)
    ElMessage.error('继续失败')
    emit('error', error as Error)
  } finally {
    task.resuming = false
  }
}

const cancelTask = async (task: FixTask) => {
  try {
    await ElMessageBox.confirm(
      `确定要取消任务 "${task.title}" 吗？`,
      '确认取消',
      { type: 'warning' }
    )
    task.cancelling = true
    await api.post(`/auto-fix/tasks/${task.id}/cancel`)
    task.status = 'cancelled'
    ElMessage.success(`任务 "${task.title}" 已取消`)
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Failed to cancel task:', error)
      ElMessage.error('取消失败')
      emit('error', error as Error)
    }
  } finally {
    task.cancelling = false
  }
}

const retryTask = async (task: FixTask) => {
  task.retrying = true
  try {
    await api.post(`/auto-fix/tasks/${task.id}/retry`)
    task.status = 'running'
    task.progress = 0
    ElMessage.success(`任务 "${task.title}" 已重新开始`)
  } catch (error) {
    console.error('Failed to retry task:', error)
    ElMessage.error('重试失败')
    emit('error', error as Error)
  } finally {
    task.retrying = false
  }
}

const pauseAllTasks = async () => {
  pausingAll.value = true
  try {
    await api.post('/auto-fix/tasks/pause-all')
    tasks.value.forEach(t => {
      if (t.status === 'running') t.status = 'paused'
    })
    ElMessage.success('所有任务已暂停')
  } catch (error) {
    console.error('Failed to pause all tasks:', error)
    ElMessage.error('暂停失败')
    emit('error', error as Error)
  } finally {
    pausingAll.value = false
  }
}

const exportFixHistory = async () => {
  exportingHistory.value = true
  try {
    const response = await api.post('/evolution-monitor/autofix/export', {
      export_type: exportConfig.value.exportType,
      include_details: exportConfig.value.includeDetails,
      date_range: exportConfig.value.dateRange
    })
    
    ElMessage.success('导出任务已创建')
    
    if ((response as any).download_url) {
      window.open((response as any).download_url, '_blank')
    }
    
    exportDialogVisible.value = false
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  } finally {
    exportingHistory.value = false
  }
}

const analyzeFixPatterns = async () => {
  analyzingPatterns.value = true
  try {
    const response = await api.get('/evolution-monitor/autofix/patterns', {
      params: {
        time_range: patternConfig.value.timeRange,
        issue_types: patternConfig.value.issueTypes
      }
    })
    
    patternAnalysis.value = response
    ElMessage.success('模式分析完成')
    patternDialogVisible.value = true
  } catch (error) {
    console.error('模式分析失败:', error)
    ElMessage.error('模式分析失败')
  } finally {
    analyzingPatterns.value = false
  }
}

const getFixRecommendations = async () => {
  loadingRecommendations.value = true
  try {
    const response = await api.get('/evolution-monitor/autofix/recommendations', {
      params: {
        context: recommendationConfig.value.context,
        current_issues: recommendationConfig.value.currentIssues
      }
    })
    
    recommendations.value = response
    ElMessage.success('推荐已加载')
    recommendationDialogVisible.value = true
  } catch (error) {
    console.error('获取推荐失败:', error)
    ElMessage.error('获取推荐失败')
  } finally {
    loadingRecommendations.value = false
  }
}

const scheduleAutoFix = async () => {
  if (!scheduleConfig.value.scheduledTime) {
    ElMessage.warning('请选择计划时间')
    return
  }
  
  scheduling.value = true
  try {
    await api.post('/evolution-monitor/autofix/schedule', {
      scheduled_time: scheduleConfig.value.scheduledTime,
      issue_types: scheduleConfig.value.issueTypes,
      priority: scheduleConfig.value.priority,
      auto_start: scheduleConfig.value.autoStart
    })
    
    ElMessage.success('自动修复已计划')
    scheduleDialogVisible.value = false
  } catch (error) {
    console.error('计划失败:', error)
    ElMessage.error('计划失败')
  } finally {
    scheduling.value = false
  }
}

const getFixStatistics = async () => {
  try {
    const response = await api.get('/evolution-monitor/autofix/statistics', {
      params: {
        period: statisticsPeriod.value
      }
    })
    
    statistics.value = response
  } catch (error) {
    console.error('获取统计失败:', error)
    ElMessage.error('获取统计失败')
  }
}

const showExportDialog = () => {
  exportDialogVisible.value = true
}

const showPatternDialog = () => {
  patternDialogVisible.value = true
  analyzeFixPatterns()
}

const showRecommendationDialog = () => {
  recommendationDialogVisible.value = true
  getFixRecommendations()
}

const showScheduleDialog = () => {
  scheduleDialogVisible.value = true
}

const showStatisticsDialog = () => {
  statisticsDialogVisible.value = true
  getFixStatistics()
}

const getPriorityColor = (priority: string): string => {
  const colors: Record<string, string> = {
    'critical': '#F56C6C',
    'high': '#E6A23C',
    'medium': '#409EFF',
    'low': '#909399'
  }
  return colors[priority] || '#909399'
}

const getPriorityLabel = (priority: string): string => {
  const labels: Record<string, string> = {
    'critical': '紧急',
    'high': '高',
    'medium': '中',
    'low': '低'
  }
  return labels[priority] || '未知'
}

const getPatternTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    'recurring': '重复性',
    'systematic': '系统性',
    'random': '随机性',
    'dependency': '依赖性'
  }
  return labels[type] || type
}

const formatDuration = (seconds: number): string => {
  if (seconds < 60) return `${seconds}秒`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟`
  return `${Math.floor(seconds / 3600)}小时${Math.floor((seconds % 3600) / 60)}分钟`
}

const resumeAllTasks = async () => {
  resumingAll.value = true
  try {
    await api.post('/auto-fix/tasks/resume-all')
    tasks.value.forEach(t => {
      if (t.status === 'paused') t.status = 'running'
    })
    ElMessage.success('所有任务已继续')
  } catch (error) {
    console.error('Failed to resume all tasks:', error)
    ElMessage.error('继续失败')
    emit('error', error as Error)
  } finally {
    resumingAll.value = false
  }
}

const showTaskDetail = (task: FixTask) => {
  selectedTask.value = task
  taskDetailVisible.value = true
}

const viewHistoryDetail = (task: FixTask) => {
  selectedTask.value = task
  taskDetailVisible.value = true
}

const handleWebSocketMessage = (data: any) => {
  switch (data.type) {
    case 'task_created':
      tasks.value.unshift({
        ...data.data,
        pausing: false,
        resuming: false,
        cancelling: false,
        retrying: false
      })
      break
    case 'task_progress':
      const task = tasks.value.find(t => t.id === data.data.id)
      if (task) {
        task.progress = data.data.progress
        task.current_step = data.data.current_step
        task.elapsed_time = data.data.elapsed_time
      }
      break
    case 'task_completed':
      const completedTask = tasks.value.find(t => t.id === data.data.id)
      if (completedTask) {
        completedTask.status = 'completed'
        completedTask.progress = 100
        completedTask.completed_at = data.data.completed_at
        historyTasks.value.unshift({ ...completedTask })
        tasks.value = tasks.value.filter(t => t.id !== data.data.id)
        ElMessage.success(`任务 "${completedTask.title}" 已完成`)
        emit('task-completed', completedTask)
      }
      break
    case 'task_failed':
      const failedTask = tasks.value.find(t => t.id === data.data.id)
      if (failedTask) {
        failedTask.status = 'failed'
        ElMessage.error(`任务 "${failedTask.title}" 失败`)
        emit('task-failed', failedTask)
      }
      break
    case 'task_log':
      const logTask = tasks.value.find(t => t.id === data.data.id)
      if (logTask) {
        if (!logTask.logs) logTask.logs = []
        logTask.logs.push(data.data.log)
      }
      break
  }
}

const startAutoRefresh = () => {
  if (props.autoRefresh && !refreshTimer && !isConnected.value) {
    refreshTimer = setInterval(fetchTasks, props.refreshInterval)
  }
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

onMounted(() => {
  fetchTasks()
  wsConnect()
  startAutoRefresh()
})

onUnmounted(() => {
  wsDisconnect()
  stopAutoRefresh()
})
</script>

<style scoped>
.auto-fix-progress {
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

.task-count {
  font-size: 13px;
  color: #909399;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.progress-content {
  padding: 10px 0;
}

.overall-progress {
  padding: 15px 0;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}

.progress-label {
  font-weight: 500;
}

.progress-value {
  font-size: 18px;
  font-weight: 600;
  color: #409eff;
}

.progress-stats {
  display: flex;
  justify-content: space-around;
  margin-top: 20px;
}

.stat-item {
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
}

.stat-value.completed { color: #67c23a; }
.stat-value.running { color: #409eff; }
.stat-value.paused { color: #e6a23c; }
.stat-value.failed { color: #f56c6c; }

.section-title {
  font-weight: 500;
  margin-bottom: 15px;
  color: #303133;
  font-size: 15px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.tasks-list {
  max-height: 500px;
  overflow-y: auto;
}

.task-item {
  padding: 15px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  margin-bottom: 12px;
  transition: all 0.3s ease;
}

.task-item.task-running {
  border-left: 3px solid #409eff;
  background: #ecf5ff;
}

.task-item.task-paused {
  border-left: 3px solid #e6a23c;
  background: #fdf6ec;
}

.task-item.task-completed {
  border-left: 3px solid #67c23a;
  background: #f0f9eb;
}

.task-item.task-failed {
  border-left: 3px solid #f56c6c;
  background: #fef0f0;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.task-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.task-icon {
  font-size: 20px;
}

.task-icon.status-running { color: #409eff; }
.task-icon.status-paused { color: #e6a23c; }
.task-icon.status-completed { color: #67c23a; }
.task-icon.status-failed { color: #f56c6c; }

.task-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-text {
  font-weight: 500;
  font-size: 15px;
}

.task-actions {
  display: flex;
  gap: 8px;
}

.task-progress {
  margin-bottom: 12px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

.task-details {
  background: #fff;
  border-radius: 6px;
  padding: 10px;
  margin-bottom: 12px;
}

.detail-row {
  display: flex;
  margin-bottom: 8px;
}

.detail-row:last-child {
  margin-bottom: 0;
}

.detail-label {
  color: #909399;
  width: 80px;
  flex-shrink: 0;
}

.detail-value {
  color: #303133;
}

.file-path {
  font-family: monospace;
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
}

.task-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-meta {
  display: flex;
  gap: 15px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
}

.history-section {
  margin-top: 15px;
}

.task-detail-dialog {
  padding: 10px;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-title {
  font-weight: 500;
  margin-bottom: 10px;
  color: #303133;
}

.detail-content {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
  line-height: 1.6;
}

.logs-container {
  max-height: 200px;
  overflow-y: auto;
  background: #f5f7fa;
  border-radius: 6px;
  padding: 10px;
}

.log-item {
  display: flex;
  gap: 10px;
  padding: 6px 0;
  font-size: 12px;
  border-bottom: 1px solid #ebeef5;
}

.log-item:last-child {
  border-bottom: none;
}

.log-item.log-error {
  color: #f56c6c;
}

.log-item.log-warning {
  color: #e6a23c;
}

.log-time {
  color: #909399;
  white-space: nowrap;
}

.log-message {
  flex: 1;
}
</style>
