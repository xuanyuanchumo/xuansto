<template>
  <div class="pipeline-monitor">
    <div class="page-header">
      <div class="header-left">
        <el-button text @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回项目
        </el-button>
        <h2>流水线监控 - {{ projectName }}</h2>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="refreshPipeline" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button type="success" @click="exportPipelineReport">
          <el-icon><Download /></el-icon>
          导出报告
        </el-button>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col :span="18">
        <el-card class="pipeline-card">
          <div v-loading="loading">
            <PipelineVisualizer
              :stages="pipelineStages"
              :current-stage-id="currentStageId"
              @stage-click="handleStageClick"
              @approval="handleStageApproval"
            />
          </div>
        </el-card>

        <el-card class="stage-control-card">
          <template #header>
            <div class="card-header">
              <span>阶段控制</span>
              <el-tag :type="pipelineStatusType" size="small">
                {{ pipelineStatusLabel }}
              </el-tag>
            </div>
          </template>
          <div class="control-content">
            <div class="stage-list">
              <div
                v-for="stage in pipelineStages"
                :key="stage.id"
                class="stage-control-item"
                :class="{ active: stage.id === currentStageId }"
              >
                <div class="stage-info">
                  <span class="stage-name">{{ stage.name }}</span>
                  <el-tag :type="getStageStatusType(stage.status)" size="small">
                    {{ getStageStatusLabel(stage.status) }}
                  </el-tag>
                </div>
                <div class="stage-actions">
                  <el-button
                    v-if="stage.status === 'pending'"
                    type="primary"
                    size="small"
                    @click="startStage(stage)"
                    :loading="stageStarting[stage.id]"
                  >
                    启动
                  </el-button>
                  <el-button
                    v-if="stage.status === 'running'"
                    type="success"
                    size="small"
                    @click="completeStage(stage)"
                  >
                    完成
                  </el-button>
                  <el-button
                    v-if="stage.status === 'failed'"
                    type="warning"
                    size="small"
                    @click="retryStage(stage)"
                  >
                    重试
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="info-card">
          <template #header>
            <span>流水线信息</span>
          </template>
          <div class="info-content">
            <div class="info-item">
              <span class="label">流水线ID:</span>
              <span class="value">{{ pipelineId || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">创建时间:</span>
              <span class="value">{{ formatTime(pipelineCreatedAt) }}</span>
            </div>
            <div class="info-item">
              <span class="label">总耗时:</span>
              <span class="value">{{ totalDuration }}</span>
            </div>
            <div class="info-item">
              <span class="label">当前阶段:</span>
              <span class="value">{{ currentStageName }}</span>
            </div>
          </div>
        </el-card>

        <el-card class="artifacts-card">
          <template #header>
            <div class="card-header">
              <span>产出物</span>
              <el-tag size="small">{{ artifacts.length }}</el-tag>
            </div>
          </template>
          <div class="artifacts-list">
            <div
              v-for="artifact in artifacts"
              :key="artifact.id"
              class="artifact-item"
              @click="downloadArtifact(artifact)"
            >
              <el-icon><Document /></el-icon>
              <span class="artifact-name">{{ artifact.name }}</span>
              <el-tag size="small" type="info">{{ artifact.stageName }}</el-tag>
            </div>
            <el-empty v-if="artifacts.length === 0" description="暂无产出物" :image-size="60" />
          </div>
        </el-card>

        <el-card class="logs-card">
          <template #header>
            <div class="card-header">
              <span>执行日志</span>
              <el-button type="primary" link size="small" @click="viewFullLogs">
                查看全部
              </el-button>
            </div>
          </template>
          <div class="logs-content">
            <div
              v-for="(log, index) in recentLogs"
              :key="index"
              class="log-item"
              :class="'log-' + log.level"
            >
              <span class="log-time">{{ log.time }}</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
            <el-empty v-if="recentLogs.length === 0" description="暂无日志" :image-size="60" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="logsDialogVisible" title="执行日志" width="800px">
      <div class="full-logs">
        <div
          v-for="(log, index) in allLogs"
          :key="index"
          class="log-line"
          :class="'log-' + log.level"
        >
          <span class="log-time">[{{ log.time }}]</span>
          <span class="log-level">[{{ log.level.toUpperCase() }}]</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Refresh, Download, Document } from '@element-plus/icons-vue'
import PipelineVisualizer from '@/components/PipelineVisualizer.vue'
import { pipelineApi } from '@/api'

const route = useRoute()
const router = useRouter()

const projectId = computed(() => Number(route.params.projectId))
const projectName = ref('加载中...')

const loading = ref(false)
const pipelineId = ref<string | null>(null)
const pipelineCreatedAt = ref<string | null>(null)
const stageStarting = ref<Record<string, boolean>>({})
const logsDialogVisible = ref(false)

interface StageTask {
  id: string
  name: string
  status: string
}

interface StageArtifact {
  id: string
  name: string
  url?: string
}

interface StageLog {
  time: string
  level: string
  message: string
}

interface Stage {
  id: string
  name: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'waiting' | 'skipped'
  needsApproval?: boolean
  description?: string
  duration?: number
  tasks?: StageTask[]
  artifacts?: StageArtifact[]
  logs?: StageLog[]
}

interface Artifact {
  id: string
  name: string
  stageName: string
  url?: string
}

interface Log {
  time: string
  level: 'info' | 'warn' | 'error'
  message: string
}

const pipelineStages = ref<Stage[]>([])
const artifacts = ref<Artifact[]>([])
const allLogs = ref<Log[]>([])

const currentStageId = computed(() => {
  const running = pipelineStages.value.find(s => s.status === 'running')
  if (running) return running.id
  const waiting = pipelineStages.value.find(s => s.status === 'waiting')
  if (waiting) return waiting.id
  return null
})

const currentStageName = computed(() => {
  const stage = pipelineStages.value.find(s => s.id === currentStageId.value)
  return stage?.name || '-'
})

const pipelineStatusType = computed(() => {
  const hasFailed = pipelineStages.value.some(s => s.status === 'failed')
  const isRunning = pipelineStages.value.some(s => s.status === 'running')
  const isWaiting = pipelineStages.value.some(s => s.status === 'waiting')
  const allSuccess = pipelineStages.value.every(s => s.status === 'success' || s.status === 'skipped')
  
  if (hasFailed) return 'danger'
  if (isWaiting) return 'warning'
  if (isRunning) return 'primary'
  if (allSuccess) return 'success'
  return 'info'
})

const pipelineStatusLabel = computed(() => {
  const hasFailed = pipelineStages.value.some(s => s.status === 'failed')
  const isRunning = pipelineStages.value.some(s => s.status === 'running')
  const isWaiting = pipelineStages.value.some(s => s.status === 'waiting')
  const allSuccess = pipelineStages.value.every(s => s.status === 'success' || s.status === 'skipped')
  
  if (hasFailed) return '执行失败'
  if (isWaiting) return '等待审批'
  if (isRunning) return '执行中'
  if (allSuccess) return '执行完成'
  return '待执行'
})

const totalDuration = computed(() => {
  const total = pipelineStages.value.reduce((sum, s) => sum + (s.duration || 0), 0)
  if (total < 1000) return `${total}ms`
  if (total < 60000) return `${(total / 1000).toFixed(1)}s`
  return `${(total / 60000).toFixed(1)}min`
})

const recentLogs = computed(() => allLogs.value.slice(-10))

const stageStatusMap: Record<string, { label: string; type: string }> = {
  pending: { label: '待执行', type: 'info' },
  running: { label: '执行中', type: 'primary' },
  success: { label: '成功', type: 'success' },
  failed: { label: '失败', type: 'danger' },
  waiting: { label: '等待中', type: 'warning' },
  skipped: { label: '已跳过', type: 'info' }
}

const getStageStatusType = (status: string) => stageStatusMap[status]?.type || 'info'
const getStageStatusLabel = (status: string) => stageStatusMap[status]?.label || status

const formatTime = (time?: string | null) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const goBack = () => {
  router.push(`/projects/${projectId.value}`)
}

const fetchPipelineStatus = async () => {
  loading.value = true
  try {
    const response = await pipelineApi.getStatus(projectId.value)
    pipelineId.value = response?.id || `PL-${projectId.value}`
    pipelineCreatedAt.value = response?.createdAt || new Date().toISOString()
    pipelineStages.value = response?.stages || getDefaultStages()
    artifacts.value = response?.artifacts || getDefaultArtifacts()
    allLogs.value = response?.logs || getDefaultLogs()
  } catch (error) {
    console.error('Failed to fetch pipeline status:', error)
    ElMessage.error('获取流水线状态失败')
    pipelineId.value = `PL-${projectId.value}`
    pipelineCreatedAt.value = new Date().toISOString()
    pipelineStages.value = getDefaultStages()
    artifacts.value = getDefaultArtifacts()
    allLogs.value = getDefaultLogs()
  } finally {
    loading.value = false
  }
}

const getDefaultStages = (): Stage[] => [
  {
    id: 'requirement',
    name: '需求分析',
    status: 'success',
    duration: 5000,
    tasks: [
      { id: 't1', name: '需求收集', status: 'success', duration: 2000 },
      { id: 't2', name: '需求评审', status: 'success', duration: 3000 }
    ]
  },
  {
    id: 'design',
    name: '设计阶段',
    status: 'success',
    duration: 8000,
    tasks: [
      { id: 't3', name: '架构设计', status: 'success', duration: 5000 },
      { id: 't4', name: '详细设计', status: 'success', duration: 3000 }
    ]
  },
  {
    id: 'implementation',
    name: '开发实现',
    status: 'success',
    needsApproval: false,
    duration: 15000,
    tasks: [
      { id: 't5', name: '编码实现', status: 'success', duration: 15000 }
    ]
  },
  {
    id: 'testing',
    name: '测试阶段',
    status: 'success',
    needsApproval: true,
    duration: 3000
  },
  {
    id: 'review',
    name: '代码审查',
    status: 'success',
    needsApproval: true,
    duration: 2000
  },
  {
    id: 'deployment',
    name: '部署上线',
    status: 'success',
    needsApproval: true,
    duration: 1000
  }
]

const getDefaultArtifacts = (): Artifact[] => [
  { id: 'a1', name: '需求文档.docx', stageName: '需求分析' },
  { id: 'a2', name: '架构设计.pdf', stageName: '设计阶段' }
]

const getDefaultLogs = (): Log[] => [
  { time: '10:00:00', level: 'info', message: '流水线初始化完成' },
  { time: '10:00:05', level: 'info', message: '需求分析阶段开始' },
  { time: '10:00:10', level: 'info', message: '需求分析阶段完成' },
  { time: '10:00:15', level: 'info', message: '设计阶段开始' },
  { time: '10:00:23', level: 'info', message: '设计阶段完成' },
  { time: '10:00:25', level: 'info', message: '开发实现阶段开始' },
  { time: '10:00:40', level: 'info', message: '开发实现阶段完成' },
  { time: '10:00:45', level: 'info', message: '测试阶段开始' },
  { time: '10:00:48', level: 'info', message: '测试阶段完成' },
  { time: '10:00:50', level: 'info', message: '代码审查阶段开始' },
  { time: '10:00:52', level: 'info', message: '代码审查阶段完成' },
  { time: '10:00:55', level: 'info', message: '部署上线阶段开始' },
  { time: '10:00:56', level: 'info', message: '部署上线阶段完成' },
  { time: '10:00:57', level: 'info', message: '流水线执行完成' }
]

const refreshPipeline = async () => {
  await fetchPipelineStatus()
  ElMessage.success('已刷新')
}

const handleStageClick = (stage: Stage) => {
  if (import.meta.env.DEV) {
    console.log('Stage clicked:', stage)
  }
}

const handleStageApproval = async (stageId: string, action: 'approve' | 'reject') => {
  try {
    ElMessage.success(action === 'approve' ? '审批通过' : '审批拒绝')
    await fetchPipelineStatus()
  } catch (error) {
    console.error('Failed to handle approval:', error)
  }
}

const startStage = async (stage: Stage) => {
  stageStarting.value[stage.id] = true
  try {
    await pipelineApi.startStage(projectId.value, stage.id)
    ElMessage.success(`阶段 ${stage.name} 已启动`)
    await fetchPipelineStatus()
  } catch (error) {
    console.error('Failed to start stage:', error)
    ElMessage.error('启动阶段失败')
  } finally {
    stageStarting.value[stage.id] = false
  }
}

const completeStage = async (stage: Stage) => {
  try {
    await pipelineApi.completeStage(projectId.value, stage.id)
    ElMessage.success(`阶段 ${stage.name} 已完成`)
    await fetchPipelineStatus()
  } catch (error) {
    console.error('Failed to complete stage:', error)
    ElMessage.error('完成阶段失败')
  }
}

const retryStage = async (stage: Stage) => {
  try {
    await pipelineApi.startStage(projectId.value, stage.id)
    ElMessage.success(`阶段 ${stage.name} 已重试`)
    await fetchPipelineStatus()
  } catch (error) {
    console.error('Failed to retry stage:', error)
    ElMessage.error('重试阶段失败')
  }
}

const downloadArtifact = (artifact: Artifact) => {
  ElMessage.success(`下载: ${artifact.name}`)
}

const viewFullLogs = () => {
  logsDialogVisible.value = true
}

const exportPipelineReport = () => {
  const report = {
    projectId: projectId.value,
    pipelineId: pipelineId.value,
    status: pipelineStatusLabel.value,
    stages: pipelineStages.value,
    artifacts: artifacts.value,
    logs: allLogs.value,
    exportedAt: new Date().toISOString()
  }
  
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `pipeline-report-${projectId.value}-${Date.now()}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  
  ElMessage.success('报告已导出')
}

let refreshInterval: number | null = null

onMounted(async () => {
  projectName.value = `项目 ${projectId.value}`
  await fetchPipelineStatus()
  
  refreshInterval = window.setInterval(() => {
    if (pipelineStages.value.some(s => s.status === 'running')) {
      fetchPipelineStatus()
    }
  }, 5000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

<style scoped>
.pipeline-monitor {
  padding: 20px;
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
  gap: 12px;
}

.pipeline-card, .stage-control-card, .info-card, .artifacts-card, .logs-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.control-content {
  padding: 10px 0;
}

.stage-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stage-control-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
  transition: all 0.3s;
}

.stage-control-item.active {
  background: #ecf5ff;
  border-left: 4px solid #409eff;
}

.stage-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stage-name {
  font-weight: 500;
  color: #303133;
}

.stage-actions {
  display: flex;
  gap: 8px;
}

.info-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.info-item .label {
  color: #909399;
}

.info-item .value {
  color: #303133;
  font-weight: 500;
}

.artifacts-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.artifact-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #f5f7fa;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
}

.artifact-item:hover {
  background: #ecf5ff;
}

.artifact-name {
  flex: 1;
  font-size: 13px;
  color: #303133;
}

.logs-content {
  max-height: 200px;
  overflow-y: auto;
}

.log-item {
  display: flex;
  gap: 8px;
  padding: 6px 0;
  font-size: 12px;
  font-family: 'Consolas', monospace;
}

.log-item.log-info {
  color: #606266;
}

.log-item.log-warn {
  color: #e6a23c;
}

.log-item.log-error {
  color: #f56c6c;
}

.log-time {
  color: #909399;
}

.log-message {
  flex: 1;
}

.full-logs {
  max-height: 500px;
  overflow-y: auto;
  padding: 16px;
  background: #1e1e1e;
  border-radius: 8px;
  font-family: 'Consolas', monospace;
  font-size: 12px;
}

.log-line {
  display: flex;
  gap: 8px;
  margin-bottom: 4px;
  color: #d4d4d4;
}

.log-line.log-warn {
  color: #e6a23c;
}

.log-line.log-error {
  color: #f56c6c;
}

.log-level {
  color: #569cd6;
}
</style>
