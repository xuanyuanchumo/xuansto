<template>
  <div class="task-management">
    <h2>任务管理</h2>
    
    <el-card>
      <template #header>
        <TaskFilter
          v-model:search-text="searchText"
          v-model:filter-status="filterStatus"
          v-model:filter-priority="filterPriority"
          @search="handleSearch"
        />
      </template>
      
      <TaskList
        :tasks="tasks"
        :loading="loading"
        :total="total"
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        @sort-change="handleSortChange"
        @view-detail="viewTaskDetails"
        @assign="openAssignDialog"
        @view-dependencies="viewDependencies"
      />
    </el-card>

    <AssignDialog
      v-model="assignDialogVisible"
      :form="assignForm"
      :agents="availableAgents"
      :loading="assigning"
      @confirm="handleAssign"
    />

    <DependencyDialog
      v-model="dependenciesDialogVisible"
      :current-task="currentTask"
      :dependencies="dependencies"
      :loading="loadingDependencies"
      @add-dependency="openAddDependencyDialog"
      @remove-dependency="handleRemoveDependency"
    />

    <AddDependencyDialog
      v-model="addDependencyDialogVisible"
      :form="addDependencyForm"
      :available-tasks="availableTasksForDependency"
      :loading="addingDependency"
      @confirm="handleAddDependency"
    />

    <TaskDetailDialog
      v-model="taskDetailDialogVisible"
      :task="currentTaskDetail"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useTasksStore, type Task, type TaskDependency } from '@/stores/tasks'
import type { Dependency } from '@/components/task/DependencyDialog.vue'
import { useAgentsStore, type Agent } from '@/stores/agents'
import TaskFilter from '@/components/task/TaskFilter.vue'
import TaskList from '@/components/task/TaskList.vue'
import TaskDetailDialog from '@/components/task/TaskDetailDialog.vue'
import AssignDialog from '@/components/task/AssignDialog.vue'
import DependencyDialog from '@/components/task/DependencyDialog.vue'
import AddDependencyDialog from '@/components/task/AddDependencyDialog.vue'

const tasksStore = useTasksStore()
const agentsStore = useAgentsStore()

const tasks = ref<Task[]>([])
const availableAgents = ref<Agent[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)

const searchText = ref('')
const filterStatus = ref('')
const filterPriority = ref('')
const sortBy = ref('')
const sortOrder = ref('')

const assignDialogVisible = ref(false)
const assignForm = ref({
  taskId: 0,
  taskName: '',
  agentId: null as number | null,
  estimatedHours: 2
})
const assigning = ref(false)

const dependenciesDialogVisible = ref(false)
const dependencies = ref<TaskDependency[]>([])
const loadingDependencies = ref(false)
const currentTask = ref<Task | null>(null)

const addDependencyDialogVisible = ref(false)
const addDependencyForm = ref({
  currentTaskId: 0,
  currentTaskName: '',
  dependsOnTaskId: null as number | null
})
const addingDependency = ref(false)

const taskDetailDialogVisible = ref(false)
const currentTaskDetail = ref<Task | null>(null)

const availableTasksForDependency = computed(() => {
  return tasks.value.filter(t => t.id !== currentTask.value?.id)
})

const fetchTasks = async () => {
  loading.value = true
  await tasksStore.fetchTasks({
    status: filterStatus.value || undefined,
    priority: filterPriority.value || undefined,
    search: searchText.value || undefined,
    page: currentPage.value,
    page_size: pageSize.value,
    sort_by: sortBy.value || undefined,
    sort_order: sortOrder.value || undefined
  })
  tasks.value = tasksStore.tasks
  total.value = tasksStore.total
  loading.value = false
}

const fetchAgents = async () => {
  await agentsStore.fetchAgents()
  availableAgents.value = agentsStore.agents
}

const handleSearch = () => {
  currentPage.value = 1
  fetchTasks()
}

const handleSortChange = ({ prop, order }: { prop: string; order: string }) => {
  sortBy.value = prop
  sortOrder.value = order
  fetchTasks()
}

const openAssignDialog = (task: Task) => {
  assignForm.value = {
    taskId: task.id,
    taskName: task.name,
    agentId: task.assigned_agent_id,
    estimatedHours: task.estimated_hours || 2
  }
  assignDialogVisible.value = true
}

const handleAssign = async (form: typeof assignForm.value) => {
  if (!form.agentId) {
    ElMessage.warning('请选择 Agent')
    return
  }
  
  assigning.value = true
  const result = await tasksStore.assignTask(
    form.taskId,
    form.agentId,
    form.estimatedHours
  )
  assigning.value = false
  
  if (result) {
    ElMessage.success('任务分配成功')
    assignDialogVisible.value = false
    fetchTasks()
  } else {
    ElMessage.error('任务分配失败')
  }
}

const viewTaskDetails = (task: Task) => {
  currentTaskDetail.value = task
  taskDetailDialogVisible.value = true
}

const viewDependencies = async (task: Task) => {
  currentTask.value = task
  dependenciesDialogVisible.value = true
  loadingDependencies.value = true
  
  const result = await tasksStore.fetchTaskDependencies(task.id)
  dependencies.value = result || []
  loadingDependencies.value = false
}

const openAddDependencyDialog = () => {
  addDependencyForm.value = {
    currentTaskId: currentTask.value?.id || 0,
    currentTaskName: currentTask.value?.name || '',
    dependsOnTaskId: null
  }
  addDependencyDialogVisible.value = true
}

const handleAddDependency = async (form: typeof addDependencyForm.value) => {
  if (!form.dependsOnTaskId) {
    ElMessage.warning('请选择依赖任务')
    return
  }
  
  addingDependency.value = true
  const result = await tasksStore.addTaskDependency(
    form.currentTaskId,
    form.dependsOnTaskId
  )
  addingDependency.value = false
  
  if (result) {
    ElMessage.success('添加依赖成功')
    addDependencyDialogVisible.value = false
    const deps = await tasksStore.fetchTaskDependencies(form.currentTaskId)
    dependencies.value = deps || []
  } else {
    ElMessage.error('添加依赖失败')
  }
}

const handleRemoveDependency = async (dependency: Dependency) => {
  try {
    await ElMessageBox.confirm('确定要移除此依赖关系吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const success = await tasksStore.removeTaskDependency(
      currentTask.value?.id || 0,
      dependency.id
    )
    
    if (success) {
      ElMessage.success('移除依赖成功')
      const deps = await tasksStore.fetchTaskDependencies(currentTask.value?.id || 0)
      dependencies.value = deps || []
    } else {
      ElMessage.error('移除依赖失败')
    }
  } catch {
    // 用户取消
  }
}

onMounted(() => {
  fetchTasks()
  fetchAgents()
})
</script>

<style scoped>
.task-management {
  padding: 20px;
}
</style>
