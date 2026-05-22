<template>
  <el-card class="department-card" :class="{ busy: loadPercent > 80 }" shadow="hover">
    <template #header>
      <div class="card-header">
        <span class="dept-name">{{ deptName }}</span>
        <el-tag size="small">{{ pinyin }}</el-tag>
      </div>
    </template>
    
    <div class="card-content">
      <div class="stat-item">
        <span class="label">任务数:</span>
        <span class="value">{{ taskCount }}</span>
      </div>
      
      <div class="stat-item">
        <span class="label">Agent 负载:</span>
        <el-progress 
          :percentage="loadPercent" 
          :status="loadPercent > 80 ? 'exception' : undefined"
          :stroke-width="10"
        />
      </div>
      
      <div class="stat-item">
        <span class="label">状态:</span>
        <el-tag :type="statusType" size="small">{{ statusText }}</el-tag>
      </div>
    </div>
    
    <div class="card-footer">
      <el-button type="primary" size="small" @click="$emit('view-detail', pinyin)">
        查看详情
      </el-button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed, defineProps, defineEmits } from 'vue'

const props = defineProps<{
  deptName: string
  pinyin: string
  taskCount: number
  loadPercent: number
  status: string
}>()

defineEmits<{
  (e: 'view-detail', pinyin: string): void
}>()

const statusType = computed(() => {
  const types: Record<string, string> = {
    active: 'success',
    idle: 'info',
    busy: 'warning',
    error: 'danger'
  }
  return types[props.status] || 'info'
})

const statusText = computed(() => {
  const texts: Record<string, string> = {
    active: '活跃',
    idle: '空闲',
    busy: '忙碌',
    error: '异常'
  }
  return texts[props.status] || props.status
})
</script>

<style scoped>
.department-card {
  margin-bottom: 15px;
}

.department-card.busy {
  border-color: #f56c6c;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dept-name {
  font-weight: bold;
  font-size: 16px;
}

.card-content {
  padding: 10px 0;
}

.stat-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.stat-item .label {
  width: 100px;
  color: #606266;
}

.stat-item .value {
  font-weight: bold;
}

.card-footer {
  text-align: right;
  padding-top: 10px;
  border-top: 1px solid #ebeef5;
}
</style>
