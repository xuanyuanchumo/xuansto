<template>
  <div class="human-intervention-section" v-if="approvals.length > 0">
    <div class="section-title">
      <el-icon class="warning-icon"><Warning /></el-icon>
      待人工介入
    </div>
    <div class="approval-list">
      <div
        v-for="approval in approvals"
        :key="approval.id"
        class="approval-item"
      >
        <div class="approval-info">
          <span class="approval-stage">{{ approval.stageName }}</span>
          <span class="approval-reason">{{ approval.reason }}</span>
        </div>
        <div class="approval-actions">
          <el-button type="success" size="small" @click="handleApproval(approval, 'approve')">
            通过
          </el-button>
          <el-button type="danger" size="small" @click="handleApproval(approval, 'reject')">
            拒绝
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'
import { Warning } from '@element-plus/icons-vue'

interface Approval {
  id: string
  stageId: string
  stageName: string
  reason: string
}

defineProps<{
  approvals: Approval[]
}>()

const emit = defineEmits<{
  (e: 'approval', approvalId: string, action: 'approve' | 'reject'): void
}>()

const handleApproval = (approval: Approval, action: 'approve' | 'reject') => {
  emit('approval', approval.id, action)
}
</script>

<style scoped>
.human-intervention-section {
  margin-top: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  font-size: 14px;
  color: #303133;
  margin-bottom: 12px;
}

.warning-icon {
  color: #e6a23c;
}

.approval-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.approval-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #fdf6ec;
  border-radius: 8px;
  border-left: 4px solid #e6a23c;
}

.approval-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.approval-stage {
  font-weight: 500;
  color: #303133;
}

.approval-reason {
  font-size: 13px;
  color: #909399;
}

.approval-actions {
  display: flex;
  gap: 8px;
}
</style>
