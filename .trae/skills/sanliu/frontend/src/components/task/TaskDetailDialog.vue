<template>
  <el-dialog 
    v-model="dialogVisible" 
    title="任务详情" 
    width="600px"
    @close="handleClose"
  >
    <el-descriptions :column="2" border v-if="task">
      <el-descriptions-item label="任务ID">{{ task.id }}</el-descriptions-item>
      <el-descriptions-item label="任务名称">{{ task.name }}</el-descriptions-item>
      <el-descriptions-item label="状态">
        <el-tag :type="getStatusType(task.status)">
          {{ getStatusText(task.status) }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="优先级">
        <el-tag :type="getPriorityType(task.priority)" effect="dark">
          {{ getPriorityText(task.priority) }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="负责人">{{ task.assigned_agent_name || '未分配' }}</el-descriptions-item>
      <el-descriptions-item label="预估工时">{{ task.estimated_hours ? `${task.estimated_hours}h` : '-' }}</el-descriptions-item>
      <el-descriptions-item label="实际工时">{{ task.actual_hours ? `${task.actual_hours}h` : '-' }}</el-descriptions-item>
      <el-descriptions-item label="创建时间">{{ formatTime(task.created_at) }}</el-descriptions-item>
      <el-descriptions-item label="描述" :span="2">{{ task.description || '无描述' }}</el-descriptions-item>
    </el-descriptions>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Task } from '@/stores/tasks'

interface Props {
  modelValue: boolean
  task: Task | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    pending: 'info',
    in_progress: 'primary',
    review: 'warning',
    completed: 'success'
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '待分配',
    in_progress: '进行中',
    review: '待审核',
    completed: '已完成'
  }
  return texts[status] || status
}

const getPriorityType = (priority: string) => {
  const types: Record<string, string> = {
    low: 'info',
    medium: '',
    high: 'warning',
    urgent: 'danger'
  }
  return types[priority] || 'info'
}

const getPriorityText = (priority: string) => {
  const texts: Record<string, string> = {
    low: '低',
    medium: '中',
    high: '高',
    urgent: '紧急'
  }
  return texts[priority] || priority
}

const formatTime = (time: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const handleClose = () => {
  emit('update:modelValue', false)
}
</script>
