<template>
  <el-dialog
    v-model="visible"
    title="任务详情"
    width="800px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading" :size="40"><Loading /></el-icon>
    </div>
    
    <div v-else-if="taskDetail" class="task-detail">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="任务标题" :span="2">
          <span class="task-title">{{ taskDetail.title }}</span>
        </el-descriptions-item>
        
        <el-descriptions-item label="任务状态">
          <el-tag :type="getStatusType(taskDetail.status)">
            {{ getStatusLabel(taskDetail.status) }}
          </el-tag>
        </el-descriptions-item>
        
        <el-descriptions-item label="优先级">
          <el-tag :type="getPriorityType(taskDetail.priority)">
            {{ getPriorityLabel(taskDetail.priority) }}
          </el-tag>
        </el-descriptions-item>
        
        <el-descriptions-item label="所需技能">
          {{ taskDetail.required_skill || '-' }}
        </el-descriptions-item>
        
        <el-descriptions-item label="所属项目">
          项目 #{{ taskDetail.project_id }}
        </el-descriptions-item>
        
        <el-descriptions-item label="预估工时">
          {{ taskDetail.estimated_hours ? `${taskDetail.estimated_hours} 小时` : '-' }}
        </el-descriptions-item>
        
        <el-descriptions-item label="实际工时">
          {{ taskDetail.actual_hours ? `${taskDetail.actual_hours} 小时` : '-' }}
        </el-descriptions-item>
        
        <el-descriptions-item label="创建时间">
          {{ formatTime(taskDetail.created_at) }}
        </el-descriptions-item>
        
        <el-descriptions-item label="完成时间">
          {{ taskDetail.completed_at ? formatTime(taskDetail.completed_at) : '-' }}
        </el-descriptions-item>
        
        <el-descriptions-item label="任务描述" :span="2">
          <div class="task-description">
            {{ taskDetail.description || '暂无描述' }}
          </div>
        </el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">分配 Agent</el-divider>
      
      <div v-if="taskDetail.agent" class="agent-info">
        <el-card shadow="hover">
          <div class="agent-content">
            <el-icon :size="24"><User /></el-icon>
            <div class="agent-details">
              <div class="agent-name">{{ taskDetail.agent.name }}</div>
              <div class="agent-role">{{ taskDetail.agent.role || '未分配角色' }}</div>
            </div>
            <el-tag :type="getAgentStatusType(taskDetail.agent.status)" size="small">
              {{ taskDetail.agent.status }}
            </el-tag>
          </div>
        </el-card>
      </div>
      <el-empty v-else description="暂未分配 Agent" :image-size="60" />

      <el-divider content-position="left">任务依赖</el-divider>
      
      <div v-if="taskDetail.dependencies_detail && taskDetail.dependencies_detail.length > 0" class="dependencies-tree">
        <el-tree
          :data="dependencyTreeData"
          :props="{ label: 'title', children: 'children' }"
          default-expand-all
          :expand-on-click-node="false"
        >
          <template #default="{ node, data }">
            <span class="dependency-node">
              <span class="node-title">{{ data.title }}</span>
              <el-tag :type="getStatusType(data.status)" size="small">
                {{ getStatusLabel(data.status) }}
              </el-tag>
            </span>
          </template>
        </el-tree>
      </div>
      <el-empty v-else description="无依赖任务" :image-size="60" />

      <el-divider content-position="left">状态变更历史</el-divider>
      
      <div v-if="taskDetail.status_history_detail && taskDetail.status_history_detail.length > 0" class="status-history">
        <el-timeline>
          <el-timeline-item
            v-for="(history, index) in taskDetail.status_history_detail"
            :key="index"
            :timestamp="formatTime(history.timestamp)"
            placement="top"
            :type="getTimelineType(history.status)"
          >
            <el-card shadow="hover">
              <div class="history-content">
                <el-tag :type="getStatusType(history.status)" size="small">
                  {{ getStatusLabel(history.status) }}
                </el-tag>
                <span v-if="history.from_status" class="status-change">
                  从 <el-tag size="small" type="info">{{ getStatusLabel(history.from_status) }}</el-tag> 变更
                </span>
                <span v-if="history.comment" class="history-comment">
                  {{ history.comment }}
                </span>
              </div>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </div>
      <el-empty v-else description="暂无状态变更记录" :image-size="60" />
    </div>
    
    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, shallowRef, onUnmounted } from 'vue'
import { Loading, User } from '@element-plus/icons-vue'
import axios from 'axios'

interface Agent {
  id: number
  name: string
  role?: string
  status: string
}

interface Dependency {
  id: number
  title: string
  status: string
}

interface StatusHistory {
  timestamp: string
  status: string
  from_status?: string
  comment?: string
}

interface TaskDetailData {
  title: string
  status: string
  priority: string
  required_skill?: string
  project_id: number
  estimated_hours?: number
  actual_hours?: number
  created_at: string
  completed_at?: string
  description?: string
  agent?: Agent
  dependencies_detail?: Dependency[]
  status_history_detail?: StatusHistory[]
}

interface Props {
  modelValue: boolean
  taskId: number | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const loading = ref(false)
const taskDetail = shallowRef<TaskDetailData | null>(null)

const STATUS_MAP: Record<string, { label: string; type: string }> = Object.freeze({
  PENDING: { label: '待处理', type: 'info' },
  IN_PROGRESS: { label: '进行中', type: 'primary' },
  REVIEW: { label: '审核中', type: 'warning' },
  COMPLETED: { label: '已完成', type: 'success' }
})

const PRIORITY_MAP: Record<string, { label: string; type: string }> = Object.freeze({
  high: { label: '高', type: 'danger' },
  medium: { label: '中', type: 'warning' },
  low: { label: '低', type: 'info' }
})

const AGENT_STATUS_TYPES: Record<string, string> = Object.freeze({
  idle: 'success',
  busy: 'warning',
  offline: 'danger'
})

const TIMELINE_TYPES: Record<string, string> = Object.freeze({
  PENDING: 'primary',
  IN_PROGRESS: 'primary',
  REVIEW: 'warning',
  COMPLETED: 'success'
})

const getStatusType = (status: string) => STATUS_MAP[status]?.type || 'info'
const getStatusLabel = (status: string) => STATUS_MAP[status]?.label || status
const getPriorityType = (priority: string) => PRIORITY_MAP[priority]?.type || 'info'
const getPriorityLabel = (priority: string) => PRIORITY_MAP[priority]?.label || priority
const getAgentStatusType = (status: string) => AGENT_STATUS_TYPES[status] || 'info'
const getTimelineType = (status: string) => TIMELINE_TYPES[status] || 'info'

const timeFormatCache = new Map<string, string>()

const formatTime = (time: string) => {
  if (!time) return '-'
  
  const cached = timeFormatCache.get(time)
  if (cached) return cached
  
  const formatted = new Date(time).toLocaleString('zh-CN')
  if (timeFormatCache.size < 500) {
    timeFormatCache.set(time, formatted)
  }
  return formatted
}

const dependencyTreeData = computed(() => {
  if (!taskDetail.value?.dependencies_detail) return []
  return taskDetail.value.dependencies_detail.map((dep: Dependency) => ({
    id: dep.id,
    title: dep.title,
    status: dep.status,
    children: []
  }))
})

let abortController: AbortController | null = null

const fetchTaskDetail = async () => {
  if (!props.taskId) return
  
  if (abortController) {
    abortController.abort()
  }
  abortController = new AbortController()
  
  loading.value = true
  try {
    const response = await axios.get(`/api/tasks/${props.taskId}`, {
      signal: abortController.signal
    })
    taskDetail.value = response.data
  } catch (error) {
    if (axios.isCancel(error)) {
      return
    }
    console.error('Failed to fetch task detail:', error)
  } finally {
    loading.value = false
  }
}

watch(() => props.modelValue, (newVal) => {
  if (newVal && props.taskId) {
    fetchTaskDetail()
  }
})

const handleClose = () => {
  visible.value = false
  taskDetail.value = null
  if (abortController) {
    abortController.abort()
    abortController = null
  }
}

onUnmounted(() => {
  if (abortController) {
    abortController.abort()
  }
  timeFormatCache.clear()
})
</script>

<style scoped>
.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.task-detail {
  padding: 10px 0;
}

.task-title {
  font-size: 16px;
  font-weight: 600;
}

.task-description {
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 150px;
  overflow-y: auto;
}

.agent-info {
  margin-bottom: 10px;
}

.agent-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.agent-details {
  flex: 1;
}

.agent-name {
  font-weight: 600;
  font-size: 14px;
}

.agent-role {
  color: #909399;
  font-size: 12px;
}

.dependencies-tree {
  background-color: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
}

.dependency-node {
  display: flex;
  align-items: center;
  gap: 8px;
}

.node-title {
  font-weight: 500;
}

.status-history {
  max-height: 300px;
  overflow-y: auto;
}

.history-content {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.status-change {
  color: #909399;
  font-size: 12px;
}

.history-comment {
  color: #606266;
  font-size: 13px;
}

.el-divider {
  margin: 20px 0 15px;
}
</style>
