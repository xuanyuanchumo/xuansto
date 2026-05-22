<template>
  <div class="approval-center">
    <div class="page-header">
      <h2>人工确认中心</h2>
      <div class="header-stats">
        <el-tag type="warning" size="large" class="stat-tag">
          {{ pendingApprovals.length }} 待审批
        </el-tag>
        <el-tag type="success" size="large" class="stat-tag">
          {{ approvedCount }} 已通过
        </el-tag>
        <el-tag type="danger" size="large" class="stat-tag">
          {{ rejectedCount }} 已拒绝
        </el-tag>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col :span="16">
        <el-card class="main-card">
          <template #header>
            <div class="card-header">
              <span>待处理审批</span>
              <div class="header-actions">
                <el-select v-model="filterProject" placeholder="筛选项目" clearable size="small">
                  <el-option
                    v-for="project in projects"
                    :key="project.id"
                    :label="project.name"
                    :value="project.id"
                  />
                </el-select>
                <el-button type="primary" size="small" @click="refreshApprovals" :loading="loading">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
            </div>
          </template>

          <div v-loading="loading">
            <HumanApprovalGate
              :proposals="filteredProposals"
              @approve="handleApprove"
              @reject="handleReject"
              @modify="handleModify"
            />
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="stats-card">
          <template #header>
            <span>审批统计</span>
          </template>
          <div class="stats-content">
            <div class="stat-item" data-stat-type="pending">
              <div class="stat-icon pending">
                <el-icon><Clock /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ pendingApprovals.length }}</div>
                <div class="stat-label">待处理</div>
              </div>
            </div>
            <div class="stat-item" data-stat-type="approved">
              <div class="stat-icon approved">
                <el-icon><CircleCheck /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ approvedCount }}</div>
                <div class="stat-label">已通过</div>
              </div>
            </div>
            <div class="stat-item" data-stat-type="rejected">
              <div class="stat-icon rejected">
                <el-icon><CircleClose /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ rejectedCount }}</div>
                <div class="stat-label">已拒绝</div>
              </div>
            </div>
          </div>
        </el-card>

        <el-card class="quick-actions-card">
          <template #header>
            <span>快捷操作</span>
          </template>
          <div class="actions-list">
            <el-button 
              type="success" 
              class="action-btn" 
              @click="approveAll"
              :disabled="pendingApprovals.length === 0"
            >
              <el-icon><Check /></el-icon>
              批量通过
            </el-button>
            <el-button 
              type="primary" 
              class="action-btn" 
              @click="viewHistory"
            >
              <el-icon><Document /></el-icon>
              审批历史
            </el-button>
            <el-button 
              class="action-btn" 
              @click="exportApprovals"
            >
              <el-icon><Download /></el-icon>
              导出记录
            </el-button>
          </div>
        </el-card>

        <el-card class="risk-summary-card">
          <template #header>
            <span>风险分布</span>
          </template>
          <div class="risk-chart">
            <div class="risk-item">
              <div class="risk-bar high" :style="{ width: riskHighPercent + '%' }"></div>
              <span class="risk-label">高风险: {{ riskHighCount }}</span>
            </div>
            <div class="risk-item">
              <div class="risk-bar medium" :style="{ width: riskMediumPercent + '%' }"></div>
              <span class="risk-label">中风险: {{ riskMediumCount }}</span>
            </div>
            <div class="risk-item">
              <div class="risk-bar low" :style="{ width: riskLowPercent + '%' }"></div>
              <span class="risk-label">低风险: {{ riskLowCount }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="historyDialogVisible" title="审批历史" width="800px">
      <el-table :data="approvalHistory" stripe>
        <el-table-column prop="id" label="ID" width="100" />
        <el-table-column prop="title" label="提案标题" min-width="150" />
        <el-table-column prop="projectName" label="所属项目" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getHistoryStatusType(row.status)" size="small">
              {{ getHistoryStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="processedAt" label="处理时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.processedAt) }}
          </template>
        </el-table-column>
        <el-table-column prop="approver" label="审批人" width="100" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Refresh, 
  Clock, 
  CircleCheck, 
  CircleClose, 
  Check, 
  Document, 
  Download 
} from '@element-plus/icons-vue'
import HumanApprovalGate, { type Proposal, type Change } from '@/components/HumanApprovalGate.vue'
import { humanApprovalsApi, type HumanApproval } from '@/api'

interface ProposalChange extends Change {
  details?: string
}

interface ExtendedProposal extends Proposal {
  projectId?: number
  projectName?: string
}

interface ApprovalHistoryItem {
  id: string
  title: string
  projectName: string
  status: 'approved' | 'rejected' | 'modified'
  processedAt: string
  approver: string
  description?: string
  riskLevel?: 'low' | 'medium' | 'high'
}

const loading = ref(false)
const filterProject = ref<number | null>(null)
const historyDialogVisible = ref(false)

const proposals = ref<ExtendedProposal[]>([])
const approvalHistory = ref<ApprovalHistoryItem[]>([])
const projects = ref<{ id: number; name: string }[]>([])

const pendingApprovals = computed(() => 
  proposals.value.filter(p => p.status === 'pending')
)

const approvedCount = computed(() => 
  proposals.value.filter(p => p.status === 'approved').length
)

const rejectedCount = computed(() => 
  proposals.value.filter(p => p.status === 'rejected').length
)

const filteredProposals = computed<Proposal[]>(() => {
  if (!filterProject.value) return pendingApprovals.value
  return pendingApprovals.value.filter(p => p.projectId === filterProject.value)
})

const riskHighCount = computed(() => 
  pendingApprovals.value.filter(p => p.riskLevel === 'high').length
)

const riskMediumCount = computed(() => 
  pendingApprovals.value.filter(p => p.riskLevel === 'medium').length
)

const riskLowCount = computed(() => 
  pendingApprovals.value.filter(p => p.riskLevel === 'low').length
)

const totalRisk = computed(() => 
  riskHighCount.value + riskMediumCount.value + riskLowCount.value
)

const riskHighPercent = computed(() => 
  totalRisk.value > 0 ? (riskHighCount.value / totalRisk.value) * 100 : 0
)

const riskMediumPercent = computed(() => 
  totalRisk.value > 0 ? (riskMediumCount.value / totalRisk.value) * 100 : 0
)

const riskLowPercent = computed(() => 
  totalRisk.value > 0 ? (riskLowCount.value / totalRisk.value) * 100 : 0
)

const statusMap: Record<string, { label: string; type: string }> = {
  approved: { label: '已通过', type: 'success' },
  rejected: { label: '已拒绝', type: 'danger' },
  modified: { label: '已修改', type: 'warning' },
  pending: { label: '待处理', type: 'info' }
}

const mapHumanApprovalToProposal = (approval: HumanApproval): ExtendedProposal => ({
  id: String(approval.id),
  title: approval.description || '未命名审批',
  description: approval.description,
  riskLevel: 'medium',
  status: approval.status as 'pending' | 'approved' | 'rejected' | 'modified',
  createdAt: approval.created_at,
  processedAt: approval.decided_at || undefined,
  approver: approval.decided_by || undefined,
  projectId: approval.project_id,
  changes: []
})

const getHistoryStatusType = (status: string) => statusMap[status]?.type || 'info'
const getHistoryStatusLabel = (status: string) => statusMap[status]?.label || status

const formatTime = (time?: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const fetchApprovals = async () => {
  loading.value = true
  try {
    const response = await humanApprovalsApi.getPending()
    proposals.value = response?.map(mapHumanApprovalToProposal) || getDefaultProposals()
  } catch (error) {
    console.error('Failed to fetch approvals:', error)
    ElMessage.error('获取审批列表失败')
    proposals.value = getDefaultProposals()
  } finally {
    loading.value = false
  }

  const uniqueProjects = new Map()
  proposals.value.forEach(p => {
    if (p.projectId && p.projectName) {
      uniqueProjects.set(p.projectId, { id: p.projectId, name: p.projectName })
    }
  })
  projects.value = Array.from(uniqueProjects.values())
}

const getDefaultProposals = (): ExtendedProposal[] => [
  {
    id: 'AP-001',
    title: '用户认证模块代码变更',
    description: '新增OAuth2.0认证支持',
    riskLevel: 'medium',
    changes: [
      { type: 'modify', file: 'auth.py', description: '添加OAuth2.0认证逻辑' },
      { type: 'add', file: 'oauth_handler.py', description: '新增OAuth处理器' }
    ],
    impact: '影响用户登录流程，需要更新相关测试用例',
    status: 'pending',
    createdAt: new Date().toISOString(),
    projectId: 1,
    projectName: '电商平台'
  },
  {
    id: 'AP-002',
    title: '数据库迁移脚本',
    description: '添加用户表字段扩展',
    riskLevel: 'high',
    changes: [
      { type: 'add', file: 'migrations/001_add_user_fields.py', description: '新增迁移脚本' }
    ],
    impact: '高风险：涉及生产数据库变更，需要备份',
    status: 'pending',
    createdAt: new Date(Date.now() - 3600000).toISOString(),
    projectId: 1,
    projectName: '电商平台'
  },
  {
    id: 'AP-003',
    title: '前端样式调整',
    description: '优化登录页面UI',
    riskLevel: 'low',
    changes: [
      { type: 'modify', file: 'Login.vue', description: '调整样式' }
    ],
    status: 'pending',
    createdAt: new Date(Date.now() - 7200000).toISOString(),
    projectId: 2,
    projectName: '管理系统'
  }
]

const refreshApprovals = async () => {
  await fetchApprovals()
  ElMessage.success('已刷新')
}

const handleApprove = async (proposalId: string) => {
  try {
    await humanApprovalsApi.decide(Number(proposalId), {
      decision: 'approved',
      decided_by: 'current-user'
    })
    await fetchApprovals()
  } catch (error) {
    console.error('Failed to approve:', error)
    ElMessage.error('审批失败')
  }
}

const handleReject = async (proposalId: string, reason: string) => {
  try {
    await humanApprovalsApi.decide(Number(proposalId), {
      decision: 'rejected',
      decided_by: 'current-user',
      reason
    })
    await fetchApprovals()
  } catch (error) {
    console.error('Failed to reject:', error)
    ElMessage.error('拒绝失败')
  }
}

const handleModify = async (proposalId: string, suggestion: string, expectedResult: string) => {
  try {
    await humanApprovalsApi.decide(Number(proposalId), {
      decision: 'modified',
      decided_by: 'current-user',
      reason: `建议: ${suggestion}; 预期结果: ${expectedResult}`
    })
    await fetchApprovals()
  } catch (error) {
    console.error('Failed to modify:', error)
    ElMessage.error('修改请求失败')
  }
}

const approveAll = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要批量通过 ${pendingApprovals.value.length} 个待审批项吗？`,
      '批量审批确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    for (const proposal of pendingApprovals.value) {
      await humanApprovalsApi.decide(Number(proposal.id), {
        decision: 'approved',
        decided_by: 'current-user'
      })
    }
    
    await fetchApprovals()
    ElMessage.success('批量审批完成')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to approve all:', error)
      ElMessage.error('批量审批失败')
    }
  }
}

const viewHistory = async () => {
  historyDialogVisible.value = true
  approvalHistory.value = [
    {
      id: 'AP-H001',
      title: 'API接口优化',
      projectName: '电商平台',
      status: 'approved',
      processedAt: new Date(Date.now() - 86400000).toISOString(),
      approver: '张三'
    },
    {
      id: 'AP-H002',
      title: '缓存策略调整',
      projectName: '电商平台',
      status: 'rejected',
      processedAt: new Date(Date.now() - 172800000).toISOString(),
      approver: '李四'
    }
  ]
}

const exportApprovals = () => {
  const data = proposals.value.map(p => ({
    ID: p.id,
    标题: p.title,
    风险等级: p.riskLevel,
    状态: getHistoryStatusLabel(p.status),
    创建时间: p.createdAt,
    处理时间: p.processedAt || '-',
    审批人: p.approver || '-'
  }))
  
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `approvals-${Date.now()}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  
  ElMessage.success('导出成功')
}

onMounted(() => {
  fetchApprovals()
})
</script>

<style scoped>
.approval-center {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
}

.header-stats {
  display: flex;
  gap: 12px;
}

.main-card, .stats-card, .quick-actions-card, .risk-summary-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.stats-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 24px;
}

.stat-icon.pending {
  background: #fdf6ec;
  color: #e6a23c;
}

.stat-icon.approved {
  background: #f0f9eb;
  color: #67c23a;
}

.stat-icon.rejected {
  background: #fef0f0;
  color: #f56c6c;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 13px;
  color: #909399;
}

.actions-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-btn {
  width: 100%;
  justify-content: flex-start;
}

.risk-chart {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.risk-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.risk-bar {
  height: 8px;
  border-radius: 4px;
  transition: width 0.3s;
}

.risk-bar.high {
  background: #f56c6c;
}

.risk-bar.medium {
  background: #e6a23c;
}

.risk-bar.low {
  background: #67c23a;
}

.risk-label {
  font-size: 13px;
  color: #606266;
}
</style>
