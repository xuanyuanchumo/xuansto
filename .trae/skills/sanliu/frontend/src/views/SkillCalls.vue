<template>
  <div class="skill-calls">
    <h2>技能调用记录</h2>
    
    <el-card>
      <template #header>
        <div class="filter-bar">
          <el-input v-model="searchSkill" placeholder="搜索技能名称" style="width: 200px" clearable />
          <el-select v-model="filterStatus" placeholder="状态筛选" clearable style="width: 150px">
            <el-option label="开始" value="started" />
            <el-option label="完成" value="completed" />
            <el-option label="失败" value="failed" />
          </el-select>
          <el-button type="primary" @click="fetchCalls">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
        </div>
      </template>
      
      <el-table :data="calls" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="skill_name" label="技能名称" />
        <el-table-column prop="caller" label="调用者" />
        <el-table-column prop="status" label="状态">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ scope.row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间">
          <template #default="scope">
            {{ formatTime(scope.row.start_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="end_time" label="结束时间">
          <template #default="scope">
            {{ formatTime(scope.row.end_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="scope">
            <el-button link type="primary" @click="viewTree(scope.row.id)">
              查看树
            </el-button>
            <el-button link type="primary" @click="viewDetail(scope.row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="treeDialogVisible" title="调用树" width="600px">
      <SkillCallTree :tree-data="currentTree" />
    </el-dialog>

    <el-drawer
      v-model="detailDrawerVisible"
      :title="`技能调用详情 - ${selectedCall?.skill_name || ''}`"
      size="60%"
      direction="rtl"
    >
      <div v-if="selectedCall" class="detail-container">
        <el-tabs v-model="activeDetailTab" type="border-card">
          <el-tab-pane label="基本信息" name="basic">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="ID">{{ selectedCall.id }}</el-descriptions-item>
              <el-descriptions-item label="技能名称">{{ selectedCall.skill_name }}</el-descriptions-item>
              <el-descriptions-item label="调用者">{{ selectedCall.caller }}</el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="getStatusType(selectedCall.status)">
                  {{ selectedCall.status }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="开始时间">{{ formatTime(selectedCall.start_time) }}</el-descriptions-item>
              <el-descriptions-item label="结束时间">{{ formatTime(selectedCall.end_time) }}</el-descriptions-item>
              <el-descriptions-item label="父调用ID" :span="2">
                {{ selectedCall.parent_call_id || '无' }}
              </el-descriptions-item>
              <el-descriptions-item label="参数" :span="2">
                <pre class="code-block">{{ formatJson(selectedCall.parameters) }}</pre>
              </el-descriptions-item>
              <el-descriptions-item label="结果" :span="2">
                <pre class="code-block">{{ formatJson(selectedCall.result) }}</pre>
              </el-descriptions-item>
            </el-descriptions>
          </el-tab-pane>

          <el-tab-pane label="决策日志" name="decisions">
            <div v-loading="loadingDecisions">
              <DecisionLogViewer :decisions="decisionLogs" />
            </div>
          </el-tab-pane>

          <el-tab-pane label="输入输出" name="io">
            <div v-loading="loadingIO">
              <InputOutputViewer
                :input-data="ioTrace?.input"
                :output-data="ioTrace?.output"
              />
            </div>
          </el-tab-pane>

          <el-tab-pane label="代码变更" name="changes">
            <div v-loading="loadingChanges">
              <CodeChangeViewer :changes="codeChanges" />
            </div>
          </el-tab-pane>

          <el-tab-pane label="推理过程" name="reasoning">
            <div v-loading="loadingReasoning">
              <ReasoningVisualizer :steps="reasoningSteps" />
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { useSkillCallsStore } from '@/stores/skillCalls'
import { decisionLogsApi, ioTracesApi, codeChangesApi } from '@/api'
import SkillCallTree from '@/components/SkillCallTree.vue'
import DecisionLogViewer from '@/components/DecisionLogViewer.vue'
import InputOutputViewer from '@/components/InputOutputViewer.vue'
import CodeChangeViewer from '@/components/CodeChangeViewer.vue'
import ReasoningVisualizer from '@/components/ReasoningVisualizer.vue'

interface SkillCallParameters {
  [key: string]: unknown
}

interface SkillCallResult {
  success: boolean
  data?: unknown
  error?: string
}

interface SkillCall {
  id: number
  skill_name: string
  caller: string
  status: string
  start_time: string
  end_time: string
  parent_call_id?: number
  parameters?: SkillCallParameters
  result?: SkillCallResult
}

const skillCallsStore = useSkillCallsStore()

const calls = ref([])
const searchSkill = ref('')
const filterStatus = ref('')
const treeDialogVisible = ref(false)
const currentTree = ref(null)
const detailDrawerVisible = ref(false)
const selectedCall = ref<SkillCall | null>(null)
const activeDetailTab = ref('basic')

const loadingDecisions = ref(false)
const loadingIO = ref(false)
const loadingChanges = ref(false)
const loadingReasoning = ref(false)

interface IOTraceData {
  input?: Record<string, unknown>
  output?: Record<string, unknown>
}

const decisionLogs = ref([])
const ioTrace = ref<IOTraceData | null>(null)
const codeChanges = ref([])
const reasoningSteps = ref([])

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    started: 'primary',
    completed: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

const formatTime = (time: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const formatJson = (data: unknown) => {
  if (!data) return '无'
  try {
    return JSON.stringify(data, null, 2)
  } catch {
    return String(data)
  }
}

const fetchCalls = async () => {
  await skillCallsStore.fetchCalls({
    skill_name: searchSkill.value || undefined,
    status: filterStatus.value || undefined
  })
  calls.value = skillCallsStore.calls
}

const viewTree = async (rootId: number) => {
  await skillCallsStore.fetchCallTree(rootId)
  currentTree.value = skillCallsStore.currentTree
  treeDialogVisible.value = true
}

const viewDetail = async (call: SkillCall) => {
  selectedCall.value = call
  activeDetailTab.value = 'basic'
  detailDrawerVisible.value = true
  
  resetDetailData()
}

const resetDetailData = () => {
  decisionLogs.value = []
  ioTrace.value = null
  codeChanges.value = []
  reasoningSteps.value = []
}

const fetchDecisionLogs = async (skillCallId: number) => {
  loadingDecisions.value = true
  try {
    const response = await decisionLogsApi.getBySkillCall(skillCallId)
    decisionLogs.value = response || []
  } catch (error) {
    console.error('Failed to fetch decision logs:', error)
    decisionLogs.value = []
  } finally {
    loadingDecisions.value = false
  }
}

const fetchIOTrace = async (skillCallId: number) => {
  loadingIO.value = true
  try {
    const response = await ioTracesApi.getBySkillCall(skillCallId)
    ioTrace.value = response || null
  } catch (error) {
    console.error('Failed to fetch IO trace:', error)
    ioTrace.value = null
  } finally {
    loadingIO.value = false
  }
}

const fetchCodeChanges = async (skillCallId: number) => {
  loadingChanges.value = true
  try {
    const response = await codeChangesApi.getBySkillCall(skillCallId)
    codeChanges.value = response || []
  } catch (error) {
    console.error('Failed to fetch code changes:', error)
    codeChanges.value = []
  } finally {
    loadingChanges.value = false
  }
}

interface DecisionLog {
  id?: number
  name?: string
  basis?: string
  timestamp?: string
  reasoning?: { description?: string; title?: string }[]
  confidence?: number
  type?: string
}

const fetchReasoningSteps = async (skillCallId: number) => {
  loadingReasoning.value = true
  try {
    const response = await decisionLogsApi.getBySkillCall(skillCallId)
    const steps = (response || []).map((decision: DecisionLog, index: number) => ({
      id: decision.id || index,
      name: decision.name || `决策 #${index + 1}`,
      description: decision.basis,
      status: 'success',
      timestamp: decision.timestamp,
      reasoning: decision.reasoning?.map((r: { description?: string; title?: string }) => r.description || r.title || r) || [],
      confidence: decision.confidence,
      isKeyDecision: decision.type === 'architecture' || decision.type === 'risk'
    }))
    reasoningSteps.value = steps
  } catch (error) {
    console.error('Failed to fetch reasoning steps:', error)
    reasoningSteps.value = []
  } finally {
    loadingReasoning.value = false
  }
}

const handleTabChange = async (tabName: string) => {
  if (!selectedCall.value) return
  
  switch (tabName) {
    case 'decisions':
      if (decisionLogs.value.length === 0) {
        await fetchDecisionLogs(selectedCall.value.id)
      }
      break
    case 'io':
      if (!ioTrace.value) {
        await fetchIOTrace(selectedCall.value.id)
      }
      break
    case 'changes':
      if (codeChanges.value.length === 0) {
        await fetchCodeChanges(selectedCall.value.id)
      }
      break
    case 'reasoning':
      if (reasoningSteps.value.length === 0) {
        await fetchReasoningSteps(selectedCall.value.id)
      }
      break
  }
}

onMounted(() => {
  fetchCalls()
})
</script>

<style scoped>
.skill-calls {
  padding: 20px;
}

.filter-bar {
  display: flex;
  gap: 15px;
  align-items: center;
}

.detail-container {
  padding: 10px;
}

.code-block {
  margin: 0;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 200px;
  overflow: auto;
}
</style>
