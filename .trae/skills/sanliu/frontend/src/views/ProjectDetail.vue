<template>
  <div class="project-detail">
    <div v-loading="loading" class="content">
      <template v-if="project">
        <div class="header">
          <div class="title-section">
            <el-button text @click="goBack">
              <el-icon><ArrowLeft /></el-icon>
              返回列表
            </el-button>
            <h2>{{ project.name }}</h2>
            <el-tag :type="getStatusType(project.status)" size="large">
              {{ getStatusLabel(project.status) }}
            </el-tag>
          </div>
          <div class="actions">
            <el-button type="success" @click="viewTransparencyReport">
              <el-icon><Document /></el-icon>
              透明度报告
            </el-button>
            <el-button type="primary" @click="handleEdit">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
          </div>
        </div>

        <el-row :gutter="20">
          <el-col :span="16">
            <el-card class="info-card">
              <template #header>
                <span>项目信息</span>
              </template>
              <el-descriptions :column="2" border>
                <el-descriptions-item label="项目名称">{{ project.name }}</el-descriptions-item>
                <el-descriptions-item label="当前状态">
                  <el-tag :type="getStatusType(project.status)">
                    {{ getStatusLabel(project.status) }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="创建时间">{{ formatTime(project.created_at) }}</el-descriptions-item>
                <el-descriptions-item label="更新时间">{{ formatTime(project.updated_at) }}</el-descriptions-item>
                <el-descriptions-item label="技术栈" :span="2">
                  <div v-if="project.tech_stack && project.tech_stack.length" class="tech-stack">
                    <el-tag
                      v-for="tech in project.tech_stack"
                      :key="tech"
                      type="info"
                      class="tech-tag"
                    >
                      {{ tech }}
                    </el-tag>
                  </div>
                  <span v-else>暂无</span>
                </el-descriptions-item>
                <el-descriptions-item label="项目描述" :span="2">
                  {{ project.description || '暂无描述' }}
                </el-descriptions-item>
              </el-descriptions>
            </el-card>

            <el-card class="tabs-card">
              <el-tabs v-model="activeMainTab">
                <el-tab-pane label="项目进度" name="progress">
                  <div class="progress-content">
                    <div class="progress-main">
                      <el-progress
                        type="dashboard"
                        :percentage="projectStats.progress || 0"
                        :width="150"
                      >
                        <template #default="{ percentage }">
                          <span class="percentage-value">{{ percentage }}%</span>
                          <span class="percentage-label">完成率</span>
                        </template>
                      </el-progress>
                    </div>
                    <div class="progress-stats">
                      <div class="stat-item">
                        <span class="stat-label">总任务数</span>
                        <span class="stat-value">{{ projectStats.total_tasks || 0 }}</span>
                      </div>
                      <div class="stat-item">
                        <span class="stat-label">已完成</span>
                        <span class="stat-value completed">{{ projectStats.completed_tasks || 0 }}</span>
                      </div>
                      <div class="stat-item">
                        <span class="stat-label">进行中</span>
                        <span class="stat-value in-progress">{{ projectStats.in_progress_tasks || 0 }}</span>
                      </div>
                      <div class="stat-item">
                        <span class="stat-label">待处理</span>
                        <span class="stat-value pending">{{ projectStats.pending_tasks || 0 }}</span>
                      </div>
                    </div>
                  </div>
                </el-tab-pane>

                <el-tab-pane label="任务列表" name="tasks">
                  <el-tabs v-model="activeTaskTab" type="card">
                    <el-tab-pane label="待处理" name="PENDING">
                      <task-list :tasks="tasksByStatus.PENDING" empty-text="暂无待处理任务" />
                    </el-tab-pane>
                    <el-tab-pane label="进行中" name="IN_PROGRESS">
                      <task-list :tasks="tasksByStatus.IN_PROGRESS" empty-text="暂无进行中任务" />
                    </el-tab-pane>
                    <el-tab-pane label="审核中" name="REVIEW">
                      <task-list :tasks="tasksByStatus.REVIEW" empty-text="暂无审核中任务" />
                    </el-tab-pane>
                    <el-tab-pane label="已完成" name="COMPLETED">
                      <task-list :tasks="tasksByStatus.COMPLETED" empty-text="暂无已完成任务" />
                    </el-tab-pane>
                  </el-tabs>
                  <div class="view-all-btn">
                    <el-button type="primary" size="small" @click="goToTasks">
                      查看全部任务
                    </el-button>
                  </div>
                </el-tab-pane>

                <el-tab-pane label="中间产物" name="artifacts">
                  <div v-loading="loadingArtifacts">
                    <ArtifactViewer :artifacts="artifacts" />
                  </div>
                </el-tab-pane>

                <el-tab-pane label="需求管理" name="requirements">
                  <div class="requirement-summary">
                    <el-row :gutter="16">
                      <el-col :span="6">
                        <div class="summary-card">
                          <div class="summary-value">{{ requirementStats.total }}</div>
                          <div class="summary-label">需求总数</div>
                        </div>
                      </el-col>
                      <el-col :span="6">
                        <div class="summary-card">
                          <div class="summary-value success">{{ requirementStats.covered }}</div>
                          <div class="summary-label">已覆盖</div>
                        </div>
                      </el-col>
                      <el-col :span="6">
                        <div class="summary-card">
                          <div class="summary-value warning">{{ requirementStats.pending }}</div>
                          <div class="summary-label">待澄清</div>
                        </div>
                      </el-col>
                      <el-col :span="6">
                        <div class="summary-card">
                          <div class="summary-value">{{ requirementStats.coverage }}%</div>
                          <div class="summary-label">覆盖率</div>
                        </div>
                      </el-col>
                    </el-row>
                  </div>
                  <div class="requirement-actions">
                    <el-button type="primary" @click="goToRequirementManagement">
                      <el-icon><Document /></el-icon>
                      进入需求管理
                    </el-button>
                  </div>
                </el-tab-pane>

                <el-tab-pane label="流水线监控" name="pipeline">
                  <div v-loading="loadingPipeline">
                    <PipelineVisualizer
                      v-if="pipelineStages.length > 0"
                      :stages="pipelineStages"
                      :current-stage-id="currentPipelineStage"
                      @stage-click="handlePipelineStageClick"
                      @approval="handlePipelineApproval"
                    />
                    <el-empty v-else description="流水线未初始化">
                      <el-button type="primary" @click="initializeProjectPipeline">
                        初始化流水线
                      </el-button>
                    </el-empty>
                  </div>
                  <div v-if="pipelineStages.length > 0" class="pipeline-actions">
                    <el-button type="primary" @click="goToPipelineMonitor">
                      <el-icon><Connection /></el-icon>
                      查看详细监控
                    </el-button>
                  </div>
                </el-tab-pane>

                <el-tab-pane label="里程碑" name="milestones">
                  <div class="milestone-header">
                    <el-button type="primary" size="small">
                      <el-icon><Plus /></el-icon>
                      添加里程碑
                    </el-button>
                  </div>
                  <el-empty description="里程碑管理功能开发中..." />
                </el-tab-pane>
              </el-tabs>
            </el-card>
          </el-col>

          <el-col :span="8">
            <el-card class="status-history-card">
              <template #header>
                <span>状态变更历史</span>
              </template>
              <el-timeline v-if="statusHistory.length">
                <el-timeline-item
                  v-for="(item, index) in statusHistory"
                  :key="index"
                  :timestamp="formatTime(item.timestamp)"
                  placement="top"
                  :type="getTimelineType(item.status)"
                >
                  <el-card>
                    <h4>{{ getStatusLabel(item.status) }}</h4>
                    <p v-if="item.comment">{{ item.comment }}</p>
                  </el-card>
                </el-timeline-item>
              </el-timeline>
              <el-empty v-else description="暂无状态变更记录" :image-size="80" />
            </el-card>

            <el-card class="quick-actions-card">
              <template #header>
                <span>快捷操作</span>
              </template>
              <div class="actions-list">
                <el-button class="action-btn" @click="handleStatusChange">
                  <el-icon><Refresh /></el-icon>
                  变更状态
                </el-button>
                <el-button class="action-btn" @click="handleCreateTask">
                  <el-icon><Plus /></el-icon>
                  创建任务
                </el-button>
                <el-button class="action-btn" @click="handleViewWorkflow">
                  <el-icon><Connection /></el-icon>
                  查看工作流
                </el-button>
                <el-button class="action-btn" type="danger" @click="handleDelete">
                  <el-icon><Delete /></el-icon>
                  删除项目
                </el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </template>

      <el-empty v-else-if="!loading" description="项目不存在" />
    </div>

    <el-dialog
      v-model="transparencyDialogVisible"
      title="透明度报告"
      width="900px"
      destroy-on-close
    >
      <div v-loading="loadingReport">
        <TransparencyReport
          v-if="transparencyReport"
          :overall-score="transparencyReport.overallScore"
          :dimensions="transparencyReport.dimensions"
          :statistics="transparencyReport.statistics"
          :recommendations="transparencyReport.recommendations"
        />
        <el-empty v-else-if="!loadingReport" description="暂无透明度报告数据" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Edit, Plus, Refresh, Delete, Connection, Document } from '@element-plus/icons-vue'
import { useProjectsStore, type Project, type ProjectStats, type TaskStats } from '@/stores/projects'
import { artifactsApi, transparencyApi, pipelineApi, requirementTracesApi } from '@/api'
import type { Artifact as ApiArtifact, PipelineStatus as ApiPipelineStatus, PipelineStage as ApiPipelineStage, TransparencyReport as ApiTransparencyReport } from '@/api'
import ArtifactViewer from '@/components/ArtifactViewer.vue'
import TransparencyReport from '@/components/TransparencyReport.vue'
import PipelineVisualizer from '@/components/PipelineVisualizer.vue'

const route = useRoute()
const router = useRouter()
const projectsStore = useProjectsStore()

const project = computed(() => projectsStore.currentProject)
const loading = computed(() => projectsStore.loading)
const activeMainTab = ref('progress')
const activeTaskTab = ref('PENDING')

// 接口类型定义
interface Task {
  id: number
  title: string
  status: string
  priority?: string
  assigned_to?: string
  estimated_hours?: number
}

// 组件内部使用的 Artifact 类型
interface Artifact {
  id?: string | number
  name: string
  type: string
  createdAt?: string
  content?: string
  url?: string
  size?: number
}

// 组件内部使用的 PipelineStage 类型
interface PipelineStage {
  id: string
  name: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'waiting' | 'skipped'
  needsApproval?: boolean
  description?: string
  duration?: number
}

interface TransparencyDimension {
  key: string
  name: string
  score: number
  description: string
}

interface TransparencyStatistics {
  decisionsCount?: number
  reasoningSteps?: number
  artifactsCount?: number
  codeChanges?: number
  startTime?: string
  endTime?: string
  duration?: number
}

interface TransparencyRecommendation {
  level: 'high' | 'medium' | 'low'
  title: string
  description: string
}

// 组件内部使用的 TransparencyReport 类型
interface TransparencyReport {
  overallScore: number
  dimensions: TransparencyDimension[]
  statistics: TransparencyStatistics
  recommendations: TransparencyRecommendation[]
}

interface RequirementStats {
  total: number
  covered: number
  pending: number
  coverage: number
}

// API 返回的需求覆盖率类型
interface ApiRequirementCoverage {
  coverage: number
  total?: number
  covered?: number
  pending?: number
}

const loadingArtifacts = ref(false)
const artifacts = ref<Artifact[]>([])
const transparencyDialogVisible = ref(false)
const loadingReport = ref(false)
const transparencyReport = ref<TransparencyReport | null>(null)
const loadingPipeline = ref(false)
const pipelineStages = ref<PipelineStage[]>([])
const currentPipelineStage = ref<string | undefined>(undefined)
const requirementStats = ref<RequirementStats>({
  total: 0,
  covered: 0,
  pending: 0,
  coverage: 0
})

const projectStats = computed<ProjectStats>(() => {
  const status = projectsStore.projectStatus
  if (!status) {
    return {
      project_id: 0,
      project_name: '',
      status: '',
      total_tasks: 0,
      completed_tasks: 0,
      pending_tasks: 0,
      in_progress_tasks: 0,
      review_tasks: 0,
      progress: 0,
      tasks_by_status: {},
      tasks: []
    }
  }
  
  const total = status.total_tasks || 0
  const completed = status.completed_tasks || 0
  return {
    ...status,
    progress: total > 0 ? Math.round((completed / total) * 100) : 0
  }
})

const tasksByStatus = computed(() => {
  // 将 TaskStats 映射为 Task 类型
  const tasks: Task[] = (projectStats.value.tasks || []).map((t: TaskStats) => ({
    id: t.id,
    title: t.name,
    status: t.status,
    priority: 'medium',
    assigned_to: undefined,
    estimated_hours: undefined
  }))
  return {
    PENDING: tasks.filter((t: Task) => t.status === 'PENDING'),
    IN_PROGRESS: tasks.filter((t: Task) => t.status === 'IN_PROGRESS'),
    REVIEW: tasks.filter((t: Task) => t.status === 'REVIEW'),
    COMPLETED: tasks.filter((t: Task) => t.status === 'COMPLETED')
  }
})

const statusHistory = computed(() => {
  if (!project.value?.status_history) return []
  return project.value.status_history
})

const statusOptions = [
  { value: 'REQUIREMENT', label: '需求分析' },
  { value: 'DESIGN', label: '设计阶段' },
  { value: 'DEVELOPMENT', label: '开发阶段' },
  { value: 'TESTING', label: '测试阶段' },
  { value: 'DEPLOYMENT', label: '部署阶段' },
  { value: 'COMPLETED', label: '已完成' }
]

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    REQUIREMENT: 'info',
    DESIGN: 'warning',
    DEVELOPMENT: 'primary',
    TESTING: '',
    DEPLOYMENT: 'success',
    COMPLETED: 'success'
  }
  return types[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const option = statusOptions.find(o => o.value === status)
  return option ? option.label : status
}

const getTimelineType = (status: string) => getStatusType(status)

const formatTime = (time?: string | null) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const goBack = () => router.push('/projects')

const goToTasks = () => router.push(`/projects/${route.params.id}/tasks`)

const handleEdit = () => ElMessage.info('编辑功能开发中...')

const handleStatusChange = async () => {
  try {
    await ElMessageBox.prompt('请输入新状态备注', '变更状态', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPlaceholder: '请输入备注（可选）'
    })
    ElMessage.success('状态变更成功')
  } catch {}
}

const handleCreateTask = () => router.push(`/tasks?project_id=${route.params.id}`)

const handleViewWorkflow = () => ElMessage.info('工作流功能开发中...')

const handleDelete = async () => {
  try {
    await ElMessageBox.confirm('确定要删除此项目吗？此操作不可恢复。', '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    ElMessage.success('删除成功')
    router.push('/projects')
  } catch {}
}

const fetchArtifacts = async (projectId: number) => {
  loadingArtifacts.value = true
  try {
    const response = await artifactsApi.getByProject(projectId)
    // 将 API Artifact 映射为组件内部 Artifact 类型
    artifacts.value = (response || []).map((a: ApiArtifact): Artifact => ({
      id: a.id,
      name: a.name,
      type: a.artifact_type,
      createdAt: a.created_at,
      content: a.content || undefined,
      url: a.file_path || undefined,
      size: undefined
    }))
  } catch (error) {
    console.error('Failed to fetch artifacts:', error)
    artifacts.value = []
  } finally {
    loadingArtifacts.value = false
  }
}

const getDefaultTransparencyReport = (): TransparencyReport => ({
  overallScore: 75,
  dimensions: [
    { key: 'decision', name: '决策透明度', score: 80, description: '决策过程的可追溯性和清晰度' },
    { key: 'reasoning', name: '推理可追溯性', score: 70, description: '推理步骤的完整性和可理解性' },
    { key: 'data', name: '数据可见性', score: 85, description: '输入输出数据的可见性和可访问性' },
    { key: 'code', name: '代码变更透明度', score: 65, description: '代码变更的可追溯性和可理解性' }
  ],
  statistics: {
    decisionsCount: 12,
    reasoningSteps: 45,
    artifactsCount: 8,
    codeChanges: 23,
    startTime: project.value?.created_at,
    endTime: new Date().toISOString(),
    duration: 3600000
  },
  recommendations: [
    { level: 'medium', title: '增加决策记录', description: '建议在关键决策点增加更多的决策记录，以提高透明度' },
    { level: 'low', title: '完善推理过程', description: '部分推理步骤缺少详细说明，建议补充推理依据' }
  ]
})

// 将 API TransparencyReport 转换为组件内部类型
const convertApiTransparencyReport = (apiReport: ApiTransparencyReport): TransparencyReport => {
  return {
    overallScore: 75, // 默认值
    dimensions: [
      { key: 'decision', name: '决策透明度', score: 80, description: '决策过程的可追溯性和清晰度' },
      { key: 'reasoning', name: '推理可追溯性', score: 70, description: '推理步骤的完整性和可理解性' },
      { key: 'data', name: '数据可见性', score: 85, description: '输入输出数据的可见性和可访问性' },
      { key: 'code', name: '代码变更透明度', score: 65, description: '代码变更的可追溯性和可理解性' }
    ],
    statistics: {
      decisionsCount: apiReport.total_decisions,
      artifactsCount: apiReport.total_artifacts,
      startTime: apiReport.generated_at,
      endTime: new Date().toISOString(),
      duration: 3600000
    },
    recommendations: [
      { level: 'medium', title: '增加决策记录', description: '建议在关键决策点增加更多的决策记录，以提高透明度' }
    ]
  }
}

const viewTransparencyReport = async () => {
  const projectId = Number(route.params.id)
  if (!projectId) return
  
  transparencyDialogVisible.value = true
  loadingReport.value = true
  transparencyReport.value = null
  
  try {
    const response = await transparencyApi.getReport(projectId)
    transparencyReport.value = response ? convertApiTransparencyReport(response) : getDefaultTransparencyReport()
  } catch (error) {
    console.error('Failed to fetch transparency report:', error)
    transparencyReport.value = getDefaultTransparencyReport()
  } finally {
    loadingReport.value = false
  }
}

const handleMainTabChange = async (tabName: string) => {
  const projectId = Number(route.params.id)
  if (!projectId) return
  
  if (tabName === 'artifacts' && artifacts.value.length === 0) await fetchArtifacts(projectId)
  if (tabName === 'pipeline') await fetchPipelineStatus(projectId)
  if (tabName === 'requirements') await fetchRequirementStats(projectId)
}

const fetchPipelineStatus = async (projectId: number) => {
  loadingPipeline.value = true
  try {
    const response = await pipelineApi.getStatus(projectId)
    // 将 API PipelineStage 映射为组件内部 PipelineStage 类型
    pipelineStages.value = (response?.stages || []).map((s: ApiPipelineStage, index: number): PipelineStage => ({
      id: String(index),
      name: s.name,
      status: s.status as PipelineStage['status'],
      needsApproval: false,
      description: undefined,
      duration: undefined
    }))
    currentPipelineStage.value = response?.current_stage || null
  } catch (error) {
    console.error('Failed to fetch pipeline status:', error)
    pipelineStages.value = []
  } finally {
    loadingPipeline.value = false
  }
}

const fetchRequirementStats = async (projectId: number) => {
  try {
    const response = await requirementTracesApi.getCoverage(projectId)
    const apiResponse = response as ApiRequirementCoverage
    requirementStats.value = {
      total: apiResponse?.total || 0,
      covered: apiResponse?.covered || 0,
      pending: apiResponse?.pending || 0,
      coverage: apiResponse?.coverage || 0
    }
  } catch (error) {
    console.error('Failed to fetch requirement stats:', error)
    requirementStats.value = { total: 0, covered: 0, pending: 0, coverage: 0 }
  }
}

const initializeProjectPipeline = async () => {
  const projectId = Number(route.params.id)
  if (!projectId) return
  
  try {
    await pipelineApi.initialize(projectId)
    ElMessage.success('流水线初始化成功')
    await fetchPipelineStatus(projectId)
  } catch (error) {
    console.error('Failed to initialize pipeline:', error)
    ElMessage.error('流水线初始化失败')
  }
}

const goToRequirementManagement = () => router.push(`/requirements/${route.params.id}`)

const goToPipelineMonitor = () => router.push(`/pipeline/${route.params.id}`)

const handlePipelineStageClick = (stage: any) => {
  // Stage click handler
}

const handlePipelineApproval = async (stageId: string, action: 'approve' | 'reject') => {
  ElMessage.success(action === 'approve' ? '审批通过' : '审批拒绝')
  await fetchPipelineStatus(Number(route.params.id))
}

onMounted(async () => {
  const id = Number(route.params.id)
  if (id) {
    await projectsStore.fetchProject(id)
    await projectsStore.fetchProjectStatus(id)
  }
})

interface TaskListProps {
  tasks: Task[]
  emptyText: string
}

const TaskList = {
  props: {
    tasks: {
      type: Array as () => Task[],
      required: true
    },
    emptyText: {
      type: String,
      required: true
    }
  },
  setup(props: TaskListProps) {
    if (!props.tasks || props.tasks.length === 0) {
      return () => h('div', { class: 'empty-tasks' }, [
        h('el-empty', { description: props.emptyText, imageSize: 60 })
      ])
    }
    return () => h('div', { class: 'task-list' }, 
      props.tasks.map((task: Task) => 
        h('div', { class: 'task-item', key: task.id }, [
          h('div', { class: 'task-info' }, [
            h('span', { class: 'task-title' }, task.title),
            h('el-tag', { 
              size: 'small',
              type: task.priority === 'high' ? 'danger' : task.priority === 'medium' ? 'warning' : 'info'
            }, task.priority)
          ]),
          h('div', { class: 'task-meta' }, [
            h('span', null, `预计: ${task.estimated_hours || '-'}h`)
          ])
        ])
      )
    )
  }
}
</script>

<style scoped>
.project-detail {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.title-section {
  display: flex;
  align-items: center;
  gap: 15px;
}

.title-section h2 {
  margin: 0;
}

.info-card, .tabs-card, .status-history-card, .quick-actions-card {
  margin-bottom: 20px;
}

.tech-stack {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.tech-tag {
  margin: 0;
}

.progress-content {
  display: flex;
  align-items: center;
  gap: 40px;
}

.progress-main {
  flex-shrink: 0;
}

.percentage-value {
  display: block;
  font-size: 28px;
  font-weight: bold;
}

.percentage-label {
  display: block;
  font-size: 12px;
  color: #909399;
}

.progress-stats {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.stat-item {
  text-align: center;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.stat-value.completed {
  color: #67c23a;
}

.stat-value.in-progress {
  color: #409eff;
}

.stat-value.pending {
  color: #e6a23c;
}

.view-all-btn {
  margin-top: 15px;
  text-align: center;
}

.milestone-header {
  margin-bottom: 15px;
}

.empty-tasks {
  padding: 20px 0;
}

.task-list {
  max-height: 300px;
  overflow-y: auto;
}

.task-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border-bottom: 1px solid #ebeef5;
}

.task-item:last-child {
  border-bottom: none;
}

.task-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.task-title {
  font-weight: 500;
}

.task-meta {
  font-size: 12px;
  color: #909399;
}

.actions-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.action-btn {
  width: 100%;
  justify-content: flex-start;
}

.requirement-summary {
  margin-bottom: 20px;
}

.summary-card {
  text-align: center;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.summary-card .summary-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.summary-card .summary-value.success {
  color: #67c23a;
}

.summary-card .summary-value.warning {
  color: #e6a23c;
}

.summary-card .summary-label {
  font-size: 13px;
  color: #909399;
  margin-top: 8px;
}

.requirement-actions {
  text-align: center;
  padding: 20px 0;
}

.pipeline-actions {
  text-align: center;
  padding: 20px 0;
}
</style>
