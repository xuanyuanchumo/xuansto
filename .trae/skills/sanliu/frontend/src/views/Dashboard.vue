<template>
  <div class="dashboard">
    <h2>三省六部协同开发系统 - 仪表盘</h2>
    
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Document /></el-icon>
              <span>技能调用总数</span>
            </div>
          </template>
          <div class="stat-value">{{ stats.total_skill_calls || 0 }}</div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><User /></el-icon>
              <span>活跃 Agent</span>
            </div>
          </template>
          <div class="stat-value">{{ stats.active_agents || 0 }} / {{ stats.total_agents || 0 }}</div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><List /></el-icon>
              <span>待处理任务</span>
            </div>
          </template>
          <div class="stat-value">{{ stats.pending_tasks || 0 }}</div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Connection /></el-icon>
              <span>活跃分配</span>
            </div>
          </template>
          <div class="stat-value">{{ stats.active_assignments || 0 }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-card class="recent-calls">
          <template #header>
            <span>最近技能调用</span>
          </template>
          <el-table :data="stats.recent_calls || []" style="width: 100%">
            <el-table-column prop="skill_name" label="技能名称" />
            <el-table-column prop="status" label="状态">
              <template #default="scope">
                <el-tag :type="getStatusType(scope.row.status)">
                  {{ scope.row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="开始时间">
              <template #default="scope">
                {{ formatTime(scope.row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card class="status-distribution">
          <template #header>
            <span>状态分布</span>
          </template>
          <div class="distribution-list">
            <div v-for="(count, status) in stats.status_distribution" :key="status" class="distribution-item">
              <span class="status-label">{{ status }}</span>
              <el-progress :percentage="getPercentage(count)" :stroke-width="20" />
              <span class="count">{{ count }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { Document, User, List, Connection } from '@element-plus/icons-vue'
import { useDashboardStore, type DashboardStats } from '@/stores/dashboard'

const dashboardStore = useDashboardStore()
const stats = ref<DashboardStats>({
  total_skill_calls: 0,
  active_agents: 0,
  total_agents: 0,
  pending_tasks: 0,
  active_assignments: 0,
  recent_calls: [],
  status_distribution: {}
})

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    started: 'primary',
    completed: 'success',
    failed: 'danger',
    update: 'warning'
  }
  return types[status] || 'info'
}

const formatTime = (time: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const getPercentage = (count: number) => {
  const total = Object.values(stats.value.status_distribution || {}).reduce((a: number, b) => a + (b as number), 0)
  return total > 0 ? Math.round((count / total) * 100) : 0
}

let refreshInterval: number

onMounted(async () => {
  await dashboardStore.fetchStats()
  stats.value = dashboardStore.stats
  
  refreshInterval = window.setInterval(async () => {
    await dashboardStore.fetchStats()
    stats.value = dashboardStore.stats
  }, 5000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #409eff;
  text-align: center;
  padding: 10px 0;
}

.recent-calls, .status-distribution {
  height: 400px;
}

.distribution-list {
  padding: 10px 0;
}

.distribution-item {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
}

.status-label {
  width: 80px;
  font-weight: 500;
}

.distribution-item .el-progress {
  flex: 1;
}

.count {
  width: 40px;
  text-align: right;
  font-weight: bold;
}
</style>
