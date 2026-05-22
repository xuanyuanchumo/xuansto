<template>
  <el-card class="human-approval-gate" shadow="hover">
    <template #header>
      <div class="card-header">
        <span class="title">人工确认门禁</span>
        <div class="header-stats">
          <el-tag v-if="pendingProposals > 0" type="warning" size="small">
            {{ pendingProposals }} 待审批
          </el-tag>
          <el-tag v-if="approvedProposals > 0" type="success" size="small">
            {{ approvedProposals }} 已通过
          </el-tag>
          <el-tag v-if="rejectedProposals > 0" type="danger" size="small">
            {{ rejectedProposals }} 已拒绝
          </el-tag>
        </div>
      </div>
    </template>

    <div v-if="!proposals || proposals.length === 0" class="empty-container">
      <el-empty description="暂无变更提案" :image-size="80" />
    </div>

    <div v-else class="proposals-container">
      <div class="pending-section" v-if="pendingProposals > 0">
        <div class="section-title">
          <el-icon class="warning-icon"><Warning /></el-icon>
          待审批提案
        </div>
        <div class="proposals-list">
          <div
            v-for="proposal in pendingList"
            :key="proposal.id"
            class="proposal-card"
            :class="'risk-' + (proposal.riskLevel || 'medium')"
          >
            <div class="proposal-header">
              <div class="proposal-meta">
                <span class="proposal-id">{{ proposal.id }}</span>
                <el-tag :type="getRiskTag(proposal.riskLevel || 'medium')" size="small" effect="dark">
                  {{ getRiskLabel(proposal.riskLevel || 'medium') }}风险
                </el-tag>
              </div>
              <span class="proposal-time">{{ formatTime(proposal.createdAt) }}</span>
            </div>

            <div class="proposal-content">
              <div class="proposal-title">{{ proposal.title || '未命名审批' }}</div>
              <div class="proposal-desc">{{ proposal.description }}</div>
            </div>

            <div v-if="proposal.changes && proposal.changes.length > 0" class="proposal-changes">
              <div class="changes-title">变更内容</div>
              <div class="changes-list">
                <div
                  v-for="(change, index) in proposal.changes"
                  :key="index"
                  class="change-item"
                >
                  <el-tag :type="getChangeTypeTag(change.type)" size="small">
                    {{ getChangeTypeLabel(change.type) }}
                  </el-tag>
                  <span class="change-file">{{ change.file }}</span>
                  <span class="change-desc">{{ change.description }}</span>
                </div>
              </div>
            </div>

            <div v-if="proposal.impact" class="proposal-impact">
              <div class="impact-title">影响分析</div>
              <div class="impact-content">{{ proposal.impact }}</div>
            </div>

            <div class="approval-actions">
              <el-button type="success" @click="handleApprove(proposal)">
                <el-icon><Check /></el-icon>
                确认
              </el-button>
              <el-button type="danger" @click="showRejectDialog(proposal)">
                <el-icon><Close /></el-icon>
                拒绝
              </el-button>
              <el-button type="warning" @click="showModifyDialog(proposal)">
                <el-icon><Edit /></el-icon>
                修改
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <div class="history-section" v-if="historyList.length > 0">
        <div class="section-title">
          <el-icon><Clock /></el-icon>
          审批历史
        </div>
        <el-timeline>
          <el-timeline-item
            v-for="item in historyList"
            :key="item.id"
            :type="getHistoryType(item.status)"
            :timestamp="formatTime(item.processedAt)"
            placement="top"
          >
            <div class="history-item">
              <div class="history-header">
                <span class="history-title">{{ item.title }}</span>
                <el-tag :type="getHistoryType(item.status)" size="small">
                  {{ getHistoryStatusLabel(item.status) }}
                </el-tag>
              </div>
              <div v-if="item.comment" class="history-comment">
                {{ item.comment }}
              </div>
              <div class="history-approver">
                审批人：{{ item.approver || '系统' }}
              </div>
            </div>
          </el-timeline-item>
        </el-timeline>
      </div>
    </div>

    <el-dialog v-model="rejectDialogVisible" title="拒绝原因" width="400px">
      <el-input
        v-model="rejectReason"
        type="textarea"
        :rows="4"
        placeholder="请输入拒绝原因..."
      />
      <template #footer>
        <el-button @click="rejectDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmReject">确认拒绝</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="modifyDialogVisible" title="修改建议" width="500px">
      <el-form :model="modifyForm" label-width="80px">
        <el-form-item label="修改说明">
          <el-input
            v-model="modifyForm.suggestion"
            type="textarea"
            :rows="4"
            placeholder="请输入修改建议..."
          />
        </el-form-item>
        <el-form-item label="期望结果">
          <el-input
            v-model="modifyForm.expectedResult"
            type="textarea"
            :rows="2"
            placeholder="请描述期望的结果..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="modifyDialogVisible = false">取消</el-button>
        <el-button type="warning" @click="confirmModify">提交修改</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup lang="ts">
/**
 * HumanApprovalGate 组件
 * 
 * 用于显示和管理需要人工审批的变更提案列表。
 * 支持审批通过、拒绝、修改建议等操作。
 * 
 * @component HumanApprovalGate
 * @example
 * <HumanApprovalGate
 *   :proposals="proposalList"
 *   @approve="handleApprove"
 *   @reject="handleReject"
 *   @modify="handleModify"
 * />
 */

import { ref, computed, defineProps, defineEmits } from 'vue'
import { ElMessage } from 'element-plus'
import { Warning, Check, Close, Edit, Clock } from '@element-plus/icons-vue'

/**
 * 变更项接口
 * @interface Change
 */
export interface Change {
  /** 变更类型：新增、修改、删除 */
  type: 'add' | 'modify' | 'delete'
  /** 文件路径 */
  file: string
  /** 变更描述 */
  description: string
}

/**
 * 提案接口
 * @interface Proposal
 */
export interface Proposal {
  /** 提案唯一标识 */
  id: string
  /** 提案标题 */
  title?: string
  /** 提案描述 */
  description: string
  /** 风险等级 */
  riskLevel?: 'low' | 'medium' | 'high'
  /** 变更列表 */
  changes?: Change[]
  /** 影响分析 */
  impact?: string
  /** 状态 */
  status: 'pending' | 'approved' | 'rejected' | 'modified'
  /** 创建时间 */
  createdAt?: string
  /** 处理时间 */
  processedAt?: string
  /** 审批人 */
  approver?: string
  /** 审批意见 */
  comment?: string
}

/**
 * 组件属性
 */
const props = defineProps<{
  /** 提案列表 */
  proposals: Proposal[]
}>()

/**
 * 组件事件
 */
const emit = defineEmits<{
  /** 审批通过事件 */
  (e: 'approve', proposalId: string): void
  /** 拒绝事件 */
  (e: 'reject', proposalId: string, reason: string): void
  /** 修改建议事件 */
  (e: 'modify', proposalId: string, suggestion: string, expectedResult: string): void
}>()

const rejectDialogVisible = ref(false)
const modifyDialogVisible = ref(false)
const currentProposal = ref<Proposal | null>(null)
const rejectReason = ref('')
const modifyForm = ref({
  suggestion: '',
  expectedResult: ''
})

const pendingProposals = computed(() =>
  props.proposals.filter(p => p.status === 'pending').length
)

const approvedProposals = computed(() =>
  props.proposals.filter(p => p.status === 'approved').length
)

const rejectedProposals = computed(() =>
  props.proposals.filter(p => p.status === 'rejected').length
)

const pendingList = computed(() =>
  props.proposals.filter(p => p.status === 'pending')
)

const historyList = computed(() =>
  props.proposals.filter(p => p.status !== 'pending').sort((a, b) =>
    new Date(b.processedAt || 0).getTime() - new Date(a.processedAt || 0).getTime()
  )
)

const riskMap: Record<string, { label: string; type: string }> = {
  low: { label: '低', type: 'success' },
  medium: { label: '中', type: 'warning' },
  high: { label: '高', type: 'danger' }
}

const changeTypeMap: Record<string, { label: string; type: string }> = {
  add: { label: '新增', type: 'success' },
  modify: { label: '修改', type: 'warning' },
  delete: { label: '删除', type: 'danger' }
}

const statusMap: Record<string, { label: string; type: string }> = {
  approved: { label: '已通过', type: 'success' },
  rejected: { label: '已拒绝', type: 'danger' },
  modified: { label: '已修改', type: 'warning' }
}

const getRiskTag = (level: string) => riskMap[level]?.type || 'info'
const getRiskLabel = (level: string) => riskMap[level]?.label || level
const getChangeTypeTag = (type: string) => changeTypeMap[type]?.type || 'info'
const getChangeTypeLabel = (type: string) => changeTypeMap[type]?.label || type
const getHistoryType = (status: string) => statusMap[status]?.type || 'info'
const getHistoryStatusLabel = (status: string) => statusMap[status]?.label || status

const formatTime = (time?: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const handleApprove = (proposal: Proposal) => {
  emit('approve', proposal.id)
  ElMessage.success('提案已通过')
}

const showRejectDialog = (proposal: Proposal) => {
  currentProposal.value = proposal
  rejectReason.value = ''
  rejectDialogVisible.value = true
}

const confirmReject = () => {
  if (!rejectReason.value) {
    ElMessage.warning('请输入拒绝原因')
    return
  }
  if (currentProposal.value) {
    emit('reject', currentProposal.value.id, rejectReason.value)
    rejectDialogVisible.value = false
    ElMessage.success('提案已拒绝')
  }
}

const showModifyDialog = (proposal: Proposal) => {
  currentProposal.value = proposal
  modifyForm.value = { suggestion: '', expectedResult: '' }
  modifyDialogVisible.value = true
}

const confirmModify = () => {
  if (!modifyForm.value.suggestion) {
    ElMessage.warning('请输入修改建议')
    return
  }
  if (currentProposal.value) {
    emit('modify', currentProposal.value.id, modifyForm.value.suggestion, modifyForm.value.expectedResult)
    modifyDialogVisible.value = false
    ElMessage.success('修改建议已提交')
  }
}
</script>

<style scoped>
.human-approval-gate {
  margin-bottom: 15px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-weight: bold;
  font-size: 16px;
}

.header-stats {
  display: flex;
  gap: 8px;
}

.empty-container {
  padding: 20px 0;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  font-size: 14px;
  color: #303133;
  margin-bottom: 16px;
  padding-left: 10px;
  border-left: 3px solid #409eff;
}

.warning-icon {
  color: #e6a23c;
}

.proposals-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.proposal-card {
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #fff;
  transition: all 0.3s;
}

.proposal-card.risk-low {
  border-left: 4px solid #67c23a;
}

.proposal-card.risk-medium {
  border-left: 4px solid #e6a23c;
}

.proposal-card.risk-high {
  border-left: 4px solid #f56c6c;
  background: #fef0f0;
}

.proposal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.proposal-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.proposal-id {
  font-weight: 500;
  color: #606266;
}

.proposal-time {
  font-size: 12px;
  color: #909399;
}

.proposal-content {
  margin-bottom: 12px;
}

.proposal-title {
  font-weight: 500;
  font-size: 15px;
  color: #303133;
  margin-bottom: 8px;
}

.proposal-desc {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}

.proposal-changes {
  margin-bottom: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.changes-title {
  font-size: 13px;
  font-weight: 500;
  color: #606266;
  margin-bottom: 10px;
}

.changes-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.change-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}

.change-file {
  color: #303133;
  font-weight: 500;
}

.change-desc {
  color: #606266;
  flex: 1;
}

.proposal-impact {
  margin-bottom: 12px;
  padding: 12px;
  background: #fdf6ec;
  border-radius: 6px;
  border-left: 3px solid #e6a23c;
}

.impact-title {
  font-size: 13px;
  font-weight: 500;
  color: #e6a23c;
  margin-bottom: 8px;
}

.impact-content {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}

.approval-actions {
  display: flex;
  gap: 10px;
  padding-top: 12px;
  border-top: 1px dashed #ebeef5;
}

.history-section {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #ebeef5;
}

.history-item {
  padding: 8px 0;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.history-title {
  font-weight: 500;
  color: #303133;
}

.history-comment {
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
}

.history-approver {
  font-size: 12px;
  color: #909399;
}
</style>
