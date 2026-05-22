<template>
  <el-dialog 
    v-model="dialogVisible" 
    title="任务依赖关系" 
    width="700px"
    @close="handleClose"
  >
    <div class="dependencies-header">
      <span class="task-name">任务: {{ currentTask?.name }}</span>
      <el-button type="primary" size="small" @click="emit('add-dependency')">
        添加依赖
      </el-button>
    </div>
    
    <el-table :data="dependencies" style="width: 100%" v-loading="loading">
      <el-table-column prop="depends_on_task_id" label="依赖任务ID" width="120" />
      <el-table-column prop="task_name" label="依赖任务名称" />
      <el-table-column prop="status" label="依赖状态" width="120">
        <template #default="scope">
          <el-tag :type="scope.row.dependency_completed ? 'success' : 'warning'">
            {{ scope.row.dependency_completed ? '已完成' : '未完成' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100">
        <template #default="scope">
          <el-button link type="danger" @click="emit('remove-dependency', scope.row)">
            移除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <div v-if="dependencies.length === 0 && !loading" class="no-dependencies">
      暂无依赖关系
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Task } from '@/stores/tasks'

export interface Dependency {
  id: number
  depends_on_task_id: number
  task_name?: string
  dependency_completed?: boolean
}

interface Props {
  modelValue: boolean
  currentTask: Task | null
  dependencies: Dependency[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'add-dependency'): void
  (e: 'remove-dependency', dependency: Dependency): void
}>()

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const handleClose = () => {
  emit('update:modelValue', false)
}
</script>

<style scoped>
.dependencies-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.task-name {
  font-weight: 500;
  font-size: 14px;
}

.no-dependencies {
  text-align: center;
  color: #909399;
  padding: 40px 0;
}
</style>
