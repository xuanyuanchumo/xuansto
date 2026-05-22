<template>
  <div class="task-list">
    <el-table
      :data="tasks"
      style="width: 100%"
      @sort-change="handleSortChange"
      v-loading="loading"
      :row-key="rowKey"
      :scrollbar-always-on="false"
    >
      <el-table-column prop="id" label="ID" width="80" sortable="custom" />
      <el-table-column prop="name" label="任务名称" min-width="180">
        <template #default="scope">
          <el-link type="primary" @click="emit('view-detail', scope.row)">
            {{ scope.row.name }}
          </el-link>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100" sortable="custom">
        <template #default="scope">
          <el-tag :type="getStatusType(scope.row.status)">
            {{ getStatusText(scope.row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="priority" label="优先级" width="100" sortable="custom">
        <template #default="scope">
          <el-tag :type="getPriorityType(scope.row.priority)" effect="dark">
            {{ getPriorityText(scope.row.priority) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="assigned_agent_name" label="负责人" width="120">
        <template #default="scope">
          {{ scope.row.assigned_agent_name || '未分配' }}
        </template>
      </el-table-column>
      <el-table-column prop="estimated_hours" label="预估工时" width="100" sortable="custom">
        <template #default="scope">
          {{ scope.row.estimated_hours ? `${scope.row.estimated_hours}h` : '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="actual_hours" label="实际工时" width="100" sortable="custom">
        <template #default="scope">
          {{ scope.row.actual_hours ? `${scope.row.actual_hours}h` : '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="160" sortable="custom">
        <template #default="scope">
          {{ formatTime(scope.row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="scope">
          <el-button 
            link 
            type="primary" 
            @click="emit('assign', scope.row)" 
            :disabled="scope.row.status === 'completed'"
          >
            分配
          </el-button>
          <el-button link type="primary" @click="emit('view-dependencies', scope.row)">
            依赖
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="localCurrentPage"
        v-model:page-size="localPageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, shallowRef, onMounted } from 'vue'
import type { Task } from '@/stores/tasks'

interface Props {
  tasks: Task[]
  loading?: boolean
  total: number
  currentPage: number
  pageSize: number
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<{
  (e: 'update:currentPage', value: number): void
  (e: 'update:pageSize', value: number): void
  (e: 'sort-change', params: { prop: string; order: string }): void
  (e: 'view-detail', task: Task): void
  (e: 'assign', task: Task): void
  (e: 'view-dependencies', task: Task): void
}>()

const localCurrentPage = ref(props.currentPage)
const localPageSize = ref(props.pageSize)

const STATUS_TYPES: Record<string, string> = Object.freeze({
  pending: 'info',
  in_progress: 'primary',
  review: 'warning',
  completed: 'success'
})

const STATUS_TEXTS: Record<string, string> = Object.freeze({
  pending: '待分配',
  in_progress: '进行中',
  review: '待审核',
  completed: '已完成'
})

const PRIORITY_TYPES: Record<string, string> = Object.freeze({
  low: 'info',
  medium: '',
  high: 'warning',
  urgent: 'danger'
})

const PRIORITY_TEXTS: Record<string, string> = Object.freeze({
  low: '低',
  medium: '中',
  high: '高',
  urgent: '紧急'
})

const rowKey = (row: Task) => row.id

const timeFormatterCache = new Map<string, string>()

watch(() => props.currentPage, (val) => {
  localCurrentPage.value = val
})

watch(() => props.pageSize, (val) => {
  localPageSize.value = val
})

const getStatusType = (status: string) => STATUS_TYPES[status] || 'info'
const getStatusText = (status: string) => STATUS_TEXTS[status] || status
const getPriorityType = (priority: string) => PRIORITY_TYPES[priority] || 'info'
const getPriorityText = (priority: string) => PRIORITY_TEXTS[priority] || priority

const formatTime = (time: string) => {
  if (!time) return '-'
  
  const cached = timeFormatterCache.get(time)
  if (cached) return cached
  
  const formatted = new Date(time).toLocaleString('zh-CN')
  if (timeFormatterCache.size < 1000) {
    timeFormatterCache.set(time, formatted)
  }
  return formatted
}

const handleSortChange = ({ prop, order }: { prop: string; order: string | null }) => {
  emit('sort-change', {
    prop,
    order: order === 'ascending' ? 'asc' : order === 'descending' ? 'desc' : ''
  })
}

const handleSizeChange = (size: number) => {
  emit('update:pageSize', size)
  emit('update:currentPage', 1)
}

const handlePageChange = (page: number) => {
  emit('update:currentPage', page)
}

onMounted(() => {
  setInterval(() => {
    if (timeFormatterCache.size > 500) {
      timeFormatterCache.clear()
    }
  }, 60000)
})
</script>

<style scoped>
.task-list {
  width: 100%;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
