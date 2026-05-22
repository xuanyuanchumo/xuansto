<template>
  <div class="agents">
    <h2>Agent 管理</h2>
    
    <el-card>
      <template #header>
        <div class="filter-bar">
          <el-select v-model="filterStatus" placeholder="状态筛选" clearable style="width: 150px">
            <el-option label="空闲" value="idle" />
            <el-option label="忙碌" value="busy" />
            <el-option label="离线" value="offline" />
          </el-select>
          <el-button type="primary" @click="fetchAgents" :loading="loading">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="resetFilter">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </div>
      </template>
      
      <el-alert
        v-if="error"
        :title="error"
        type="error"
        closable
        @close="clearError"
        style="margin-bottom: 16px"
      />
      
      <el-table :data="agents" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="role" label="角色" />
        <el-table-column prop="status" label="状态">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="current_load" label="负载">
          <template #default="scope">
            <el-progress 
              :percentage="getLoadPercentage(scope.row)" 
              :stroke-width="15"
              :color="getLoadColor(scope.row)"
              :format="() => `${scope.row.current_load}/${scope.row.max_load}`"
            />
          </template>
        </el-table-column>
        <el-table-column prop="current_task" label="当前任务">
          <template #default="scope">
            {{ scope.row.current_task || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="skills" label="技能">
          <template #default="scope">
            <el-tag v-for="skill in (scope.row.skills || [])" :key="skill" size="small" style="margin-right: 5px">
              {{ skill }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      
      <el-empty v-if="!loading && agents.length === 0" description="暂无 Agent 数据" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAgentsStore } from '@/stores/agents'

const agentsStore = useAgentsStore()

const agents = computed(() => agentsStore.agents)
const loading = computed(() => agentsStore.loading)
const error = computed(() => agentsStore.error)

const filterStatus = ref('')

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    idle: 'success',
    busy: 'warning',
    offline: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    idle: '空闲',
    busy: '忙碌',
    offline: '离线'
  }
  return texts[status] || status
}

const getLoadPercentage = (agent: { current_load: number; max_load: number }) => {
  if (!agent.max_load || agent.max_load === 0) return 0
  return Math.min(100, (agent.current_load / agent.max_load) * 100)
}

const getLoadColor = (agent: { current_load: number; max_load: number }) => {
  const percentage = getLoadPercentage(agent)
  if (percentage >= 90) return '#f56c6c'
  if (percentage >= 70) return '#e6a23c'
  return '#67c23a'
}

const fetchAgents = async () => {
  await agentsStore.fetchAgents(filterStatus.value || undefined)
  if (!error.value && agents.value.length > 0) {
    ElMessage.success(`已加载 ${agents.value.length} 个 Agent`)
  }
}

const resetFilter = () => {
  filterStatus.value = ''
  agentsStore.clearError()
  fetchAgents()
}

const clearError = () => {
  agentsStore.clearError()
}

let refreshInterval: number

onMounted(() => {
  fetchAgents()
  refreshInterval = window.setInterval(fetchAgents, 10000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

<style scoped>
.agents {
  padding: 20px;
}

.filter-bar {
  display: flex;
  gap: 15px;
  align-items: center;
}
</style>
