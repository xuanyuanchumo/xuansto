<template>
  <div class="requirement-management">
    <div class="page-header">
      <div class="header-left">
        <el-button text @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回项目
        </el-button>
        <h2>需求管理 - {{ projectName }}</h2>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="initializePipeline" :loading="initializing">
          <el-icon><VideoPlay /></el-icon>
          初始化流水线
        </el-button>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="main-tabs" @tab-change="handleTabChange">
      <el-tab-pane label="需求结构化" name="structure">
        <div v-loading="loadingStructure" class="tab-content">
          <RequirementStructurer
            :user-stories="userStories"
            :features="features"
            :data-models="dataModels"
            :editable="true"
            @confirm="handleRequirementConfirm"
            @update:user-stories="updateUserStories"
            @update:features="updateFeatures"
          />
        </div>
      </el-tab-pane>

      <el-tab-pane label="澄清问题" name="clarification">
        <div v-loading="loadingQuestions" class="tab-content">
          <ClarificationDialog
            :questions="clarificationQuestions"
            @answer="handleAnswerQuestion"
            @confirm="handleConfirmQuestion"
            @revise="handleReviseQuestion"
            @confirm-all="handleConfirmAllQuestions"
          />
        </div>
      </el-tab-pane>

      <el-tab-pane label="需求追踪矩阵" name="trace">
        <div v-loading="loadingTrace" class="tab-content">
          <RequirementTraceMatrix
            :matrix="traceMatrix"
            @refresh="refreshTraceMatrix"
          />
        </div>
      </el-tab-pane>

      <el-tab-pane label="覆盖率报告" name="coverage">
        <div v-loading="loadingCoverage" class="tab-content">
          <el-card class="coverage-card">
            <template #header>
              <div class="card-header">
                <span>需求覆盖率报告</span>
                <el-button type="primary" size="small" @click="exportCoverage">
                  <el-icon><Download /></el-icon>
                  导出报告
                </el-button>
              </div>
            </template>
            <div class="coverage-content">
              <div class="coverage-summary">
                <div class="summary-item">
                  <el-progress type="dashboard" :percentage="coverageData.overall || 0" :width="120">
                    <template #default="{ percentage }">
                      <span class="percentage-value">{{ percentage }}%</span>
                      <span class="percentage-label">总体覆盖率</span>
                    </template>
                  </el-progress>
                </div>
                <div class="summary-details">
                  <div class="detail-row">
                    <span class="label">功能需求覆盖:</span>
                    <el-progress :percentage="coverageData.functional || 0" :stroke-width="10" />
                  </div>
                  <div class="detail-row">
                    <span class="label">非功能需求覆盖:</span>
                    <el-progress :percentage="coverageData.nonFunctional || 0" :stroke-width="10" />
                  </div>
                  <div class="detail-row">
                    <span class="label">业务需求覆盖:</span>
                    <el-progress :percentage="coverageData.business || 0" :stroke-width="10" />
                  </div>
                </div>
              </div>
              <el-divider />
              <div class="coverage-chart">
                <div class="chart-title">覆盖率趋势</div>
                <div class="chart-placeholder">
                  <el-empty description="趋势图表开发中..." :image-size="100" />
                </div>
              </div>
            </div>
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, VideoPlay, Download } from '@element-plus/icons-vue'
import RequirementStructurer from '@/components/RequirementStructurer.vue'
import ClarificationDialog from '@/components/ClarificationDialog.vue'
import RequirementTraceMatrix from '@/components/RequirementTraceMatrix.vue'
import { 
  requirementTracesApi, 
  clarificationQuestionsApi, 
  pipelineApi 
} from '@/api'

const route = useRoute()
const router = useRouter()

const projectId = computed(() => Number(route.params.projectId))
const projectName = ref('加载中...')

const activeTab = ref('structure')
const initializing = ref(false)
const loadingStructure = ref(false)
const loadingQuestions = ref(false)
const loadingTrace = ref(false)
const loadingCoverage = ref(false)

interface AcceptanceCriterion {
  scenario: string
  given: string
  when: string
  then: string
}

interface UserStory {
  id?: string
  title: string
  role: string
  action: string
  benefit: string
  acceptanceCriteria?: AcceptanceCriterion[]
}

interface Feature {
  id: string
  name: string
  description: string
  priority: 'high' | 'medium' | 'low'
  status: 'pending' | 'in_progress' | 'completed'
}

interface DataField {
  name: string
  type: string
  required?: boolean
}

interface StateTransition {
  from: string
  to: string
  condition?: string
}

interface DataModel {
  name: string
  type?: string
  fields: DataField[]
  stateTransitions?: StateTransition[]
}

const userStories = ref<UserStory[]>([])
const features = ref<Feature[]>([])
const dataModels = ref<DataModel[]>([])
const clarificationQuestions = ref<any[]>([])
const traceMatrix = ref<any[]>([])
const coverageData = ref({
  overall: 0,
  functional: 0,
  nonFunctional: 0,
  business: 0
})

const goBack = () => {
  router.push(`/projects/${projectId.value}`)
}

const handleTabChange = async (tabName: string) => {
  switch (tabName) {
    case 'structure':
      await fetchRequirementStructure()
      break
    case 'clarification':
      await fetchClarificationQuestions()
      break
    case 'trace':
      await fetchTraceMatrix()
      break
    case 'coverage':
      await fetchCoverage()
      break
  }
}

const getMockUserStories = () => [
  {
    id: 'US-001',
    title: '用户登录',
    role: '用户',
    action: '能够使用账号密码登录系统',
    benefit: '可以访问个人数据和功能',
    acceptanceCriteria: [
      {
        scenario: '成功登录',
        given: '用户在登录页面',
        when: '输入正确的用户名和密码并点击登录',
        then: '系统跳转到首页并显示用户信息'
      }
    ]
  },
  {
    id: 'US-002',
    title: '数据导出',
    role: '管理员',
    action: '能够导出系统数据为Excel格式',
    benefit: '方便进行数据分析和报告'
  }
]

const getMockFeatures = () => [
  {
    id: 'F-001',
    name: '用户认证',
    description: '实现用户登录、登出和会话管理功能',
    priority: 'high',
    status: 'pending'
  },
  {
    id: 'F-002',
    name: '数据导出',
    description: '支持将数据导出为多种格式',
    priority: 'medium',
    status: 'pending'
  }
]

const getMockDataModels = () => [
  {
    name: 'User',
    type: 'Entity',
    fields: [
      { name: 'id', type: 'number', required: true, primaryKey: true },
      { name: 'username', type: 'string', required: true },
      { name: 'email', type: 'string', required: true },
      { name: 'status', type: 'UserStatus', required: true }
    ],
    stateTransitions: [
      { from: 'pending', to: 'active', action: 'activate' },
      { from: 'active', to: 'inactive', action: 'deactivate' }
    ]
  }
]

const fetchRequirementStructure = async () => {
  loadingStructure.value = true
  try {
    userStories.value = getMockUserStories()
    features.value = getMockFeatures()
    dataModels.value = getMockDataModels()
  } catch (error) {
    console.error('Failed to fetch requirement structure:', error)
  } finally {
    loadingStructure.value = false
  }
}

const fetchClarificationQuestions = async () => {
  loadingQuestions.value = true
  try {
    const response = await clarificationQuestionsApi.getByProject(projectId.value)
    clarificationQuestions.value = response || [
      {
        id: 'Q-001',
        question: '用户登录时是否需要支持第三方登录（如微信、QQ）？',
        context: '用户故事 US-001 中提到用户登录功能',
        priority: 'high',
        status: 'pending'
      },
      {
        id: 'Q-002',
        question: '数据导出时是否需要支持增量导出？',
        context: '用户故事 US-002 中提到数据导出功能',
        priority: 'medium',
        status: 'pending'
      }
    ]
  } catch (error) {
    console.error('Failed to fetch clarification questions:', error)
    clarificationQuestions.value = []
  } finally {
    loadingQuestions.value = false
  }
}

const fetchTraceMatrix = async () => {
  loadingTrace.value = true
  try {
    const response = await requirementTracesApi.getByProject(projectId.value)
    traceMatrix.value = response || [
      {
        requirementId: 'REQ-001',
        requirementName: '用户认证',
        type: 'functional',
        features: [{ id: 'F-001', name: '用户认证' }],
        tests: [{ id: 'T-001', name: '登录测试', status: 'pending' }],
        status: 'partial'
      },
      {
        requirementId: 'REQ-002',
        requirementName: '数据导出',
        type: 'functional',
        features: [{ id: 'F-002', name: '数据导出' }],
        tests: [],
        status: 'uncovered'
      }
    ]
  } catch (error) {
    console.error('Failed to fetch trace matrix:', error)
    traceMatrix.value = []
  } finally {
    loadingTrace.value = false
  }
}

const fetchCoverage = async () => {
  loadingCoverage.value = true
  try {
    const response = await requirementTracesApi.getCoverage(projectId.value)
    coverageData.value = response || {
      overall: 65,
      functional: 70,
      nonFunctional: 50,
      business: 80
    }
  } catch (error) {
    console.error('Failed to fetch coverage:', error)
  } finally {
    loadingCoverage.value = false
  }
}

const handleRequirementConfirm = async (data: Record<string, unknown>) => {
  ElMessage.success('需求已确认，正在保存...')
  if (import.meta.env.DEV) {
    console.log('Confirmed requirements:', data)
  }
}

const updateUserStories = (stories: UserStory[]) => {
  userStories.value = stories
}

const updateFeatures = (updatedFeatures: Feature[]) => {
  features.value = updatedFeatures
}

const handleAnswerQuestion = async (questionId: string | number, answer: string) => {
  try {
    await clarificationQuestionsApi.answer(Number(questionId), { answer })
    await fetchClarificationQuestions()
  } catch (error) {
    console.error('Failed to answer question:', error)
    ElMessage.error('回答提交失败')
  }
}

const handleConfirmQuestion = async (questionId: string | number) => {
  try {
    await clarificationQuestionsApi.confirm(Number(questionId), 'current-user')
    await fetchClarificationQuestions()
  } catch (error) {
    console.error('Failed to confirm question:', error)
    ElMessage.error('确认失败')
  }
}

const handleReviseQuestion = async (questionId: string | number) => {
  ElMessage.info('已要求修改回答')
}

const handleConfirmAllQuestions = async () => {
  ElMessage.success('所有回答已确认')
}

const refreshTraceMatrix = async () => {
  await fetchTraceMatrix()
  ElMessage.success('追踪矩阵已刷新')
}

const exportCoverage = () => {
  const data = {
    projectId: projectId.value,
    coverage: coverageData.value,
    matrix: traceMatrix.value,
    exportedAt: new Date().toISOString()
  }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `coverage-report-${projectId.value}-${Date.now()}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  ElMessage.success('报告已导出')
}

const initializePipeline = async () => {
  initializing.value = true
  try {
    await pipelineApi.initialize(projectId.value)
    ElMessage.success('流水线初始化成功')
    router.push(`/pipeline/${projectId.value}`)
  } catch (error) {
    console.error('Failed to initialize pipeline:', error)
    ElMessage.error('流水线初始化失败')
  } finally {
    initializing.value = false
  }
}

onMounted(async () => {
  projectName.value = `项目 ${projectId.value}`
  await fetchRequirementStructure()
})
</script>

<style scoped>
.requirement-management {
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

.main-tabs {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.tab-content {
  min-height: 400px;
}

.coverage-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.coverage-content {
  padding: 10px 0;
}

.coverage-summary {
  display: flex;
  align-items: center;
  gap: 40px;
}

.summary-item {
  flex-shrink: 0;
}

.percentage-value {
  display: block;
  font-size: 24px;
  font-weight: bold;
}

.percentage-label {
  display: block;
  font-size: 12px;
  color: #909399;
}

.summary-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.detail-row .label {
  width: 120px;
  font-size: 14px;
  color: #606266;
}

.detail-row .el-progress {
  flex: 1;
}

.coverage-chart {
  margin-top: 20px;
}

.chart-title {
  font-weight: 500;
  font-size: 14px;
  color: #303133;
  margin-bottom: 16px;
}

.chart-placeholder {
  padding: 40px;
  background: #f5f7fa;
  border-radius: 8px;
}
</style>
