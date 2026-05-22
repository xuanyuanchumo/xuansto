<template>
  <div class="statistics">
    <h2>系统统计</h2>
    
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Folder /></el-icon>
              <span>项目总数</span>
            </div>
          </template>
          <el-statistic :value="projectStats.total || 0" />
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Document /></el-icon>
              <span>任务总数</span>
            </div>
          </template>
          <el-statistic :value="taskStats.total || 0" />
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Connection /></el-icon>
              <span>技能调用</span>
            </div>
          </template>
          <el-statistic :value="skillCallStats.total || 0" />
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><User /></el-icon>
              <span>Agent 总数</span>
            </div>
          </template>
          <el-statistic :value="agentStats.total || 0" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <span>项目状态分布</span>
          </template>
          <div class="distribution-list">
            <div 
              v-for="(count, status) in projectStats.status_distribution" 
              :key="status" 
              class="distribution-item"
            >
              <span class="status-label">{{ getStatusLabel(status) }}</span>
              <el-progress 
                :percentage="getPercentage(count, projectStats.total)" 
                :stroke-width="20"
                :color="getProjectStatusColor(status)"
              />
              <span class="count">{{ count }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <span>任务完成情况</span>
          </template>
          <div class="completion-info">
            <el-progress 
              type="dashboard" 
              :percentage="taskStats.completion_rate || 0"
              :width="150"
            >
              <template #default="{ percentage }">
                <span class="percentage-value">{{ percentage }}%</span>
                <span class="percentage-label">完成率</span>
              </template>
            </el-progress>
          </div>
          <div class="distribution-list">
            <div 
              v-for="(count, status) in taskStats.status_distribution" 
              :key="status" 
              class="distribution-item"
            >
              <span class="status-label">{{ getTaskStatusLabel(status) }}</span>
              <el-progress 
                :percentage="getPercentage(count, taskStats.total)" 
                :stroke-width="16"
                :color="getTaskStatusColor(status)"
              />
              <span class="count">{{ count }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <span>技能调用统计</span>
          </template>
          <div class="completion-info">
            <el-progress 
              type="dashboard" 
              :percentage="skillCallStats.success_rate || 0"
              :width="150"
              color="#67c23a"
            >
              <template #default="{ percentage }">
                <span class="percentage-value">{{ percentage }}%</span>
                <span class="percentage-label">成功率</span>
              </template>
            </el-progress>
          </div>
          <div class="distribution-list">
            <div 
              v-for="(count, status) in skillCallStats.status_distribution" 
              :key="status" 
              class="distribution-item"
            >
              <span class="status-label">{{ status }}</span>
              <el-progress 
                :percentage="getPercentage(count, skillCallStats.total)" 
                :stroke-width="16"
              />
              <span class="count">{{ count }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <span>Agent 活跃度</span>
          </template>
          <div class="agent-list">
            <div 
              v-for="agent in agentStats.workload" 
              :key="agent.name" 
              class="agent-item"
            >
              <span class="agent-name">{{ agent.name }}</span>
              <el-progress 
                :percentage="agent.utilization" 
                :stroke-width="16"
                :color="getUtilizationColor(agent.utilization)"
              />
              <span class="load-info">{{ agent.current_load }}/{{ agent.max_load }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card class="chart-card">
          <template #header>
            <span>技能调用分布</span>
          </template>
          <div class="skill-distribution">
            <div 
              v-for="(count, skillName) in skillCallStats.skill_distribution" 
              :key="skillName" 
              class="skill-item"
            >
              <span class="skill-name">{{ skillName }}</span>
              <el-progress 
                :percentage="getPercentage(count, skillCallStats.total)" 
                :stroke-width="16"
              />
              <span class="count">{{ count }} 次</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Folder, Document, Connection, User } from '@element-plus/icons-vue'
import api from '@/api'

interface ProjectStats {
  total: number
  status_distribution: Record<string, number>
}

interface TaskStats {
  total: number
  completed: number
  completion_rate: number
  status_distribution: Record<string, number>
}

interface SkillCallStats {
  total: number
  successful: number
  success_rate: number
  status_distribution: Record<string, number>
  skill_distribution: Record<string, number>
}

interface AgentWorkload {
  name: string
  current_load: number
  max_load: number
  utilization: number
}

interface AgentStats {
  total: number
  active: number
  status_distribution: Record<string, number>
  workload: AgentWorkload[]
}

const projectStats = ref<ProjectStats>({ total: 0, status_distribution: {} })
const taskStats = ref<TaskStats>({ total: 0, completed: 0, completion_rate: 0, status_distribution: {} })
const skillCallStats = ref<SkillCallStats>({ total: 0, successful: 0, success_rate: 0, status_distribution: {}, skill_distribution: {} })
const agentStats = ref<AgentStats>({ total: 0, active: 0, status_distribution: {}, workload: [] })

const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    'REQUIREMENT': '需求分析',
    'DESIGN': '设计',
    'DEVELOPMENT': '开发',
    'TESTING': '测试',
    'DEPLOYMENT': '部署',
    'COMPLETED': '已完成'
  }
  return labels[status] || status
}

const getTaskStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    'PENDING': '待处理',
    'IN_PROGRESS': '进行中',
    'REVIEW': '审核中',
    'COMPLETED': '已完成'
  }
  return labels[status] || status
}

const getProjectStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    'REQUIREMENT': '#909399',
    'DESIGN': '#409eff',
    'DEVELOPMENT': '#e6a23c',
    'TESTING': '#f56c6c',
    'DEPLOYMENT': '#67c23a',
    'COMPLETED': '#67c23a'
  }
  return colors[status] || '#409eff'
}

const getTaskStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    'PENDING': '#909399',
    'IN_PROGRESS': '#409eff',
    'REVIEW': '#e6a23c',
    'COMPLETED': '#67c23a'
  }
  return colors[status] || '#409eff'
}

const getUtilizationColor = (utilization: number): string => {
  if (utilization >= 80) return '#f56c6c'
  if (utilization >= 50) return '#e6a23c'
  return '#67c23a'
}

const getPercentage = (count: number, total: number): number => {
  if (total === 0) return 0
  return Math.round((count / total) * 100)
}

const fetchStatistics = async () => {
  try {
    const [projectRes, taskRes, skillCallRes, agentRes] = await Promise.all([
      api.get('/statistics/projects'),
      api.get('/statistics/tasks'),
      api.get('/statistics/skill-calls'),
      api.get('/statistics/agents')
    ])
    
    projectStats.value = projectRes.data
    taskStats.value = taskRes.data
    skillCallStats.value = skillCallRes.data
    agentStats.value = agentRes.data
  } catch (error) {
    console.error('Failed to fetch statistics:', error)
  }
}

onMounted(() => {
  fetchStatistics()
})
</script>

<style scoped>
.statistics {
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

.chart-card {
  min-height: 300px;
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
  width: 50px;
  text-align: right;
  font-weight: bold;
}

.completion-info {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.percentage-value {
  display: block;
  font-size: 28px;
  font-weight: bold;
}

.percentage-label {
  display: block;
  font-size: 14px;
  color: #909399;
}

.agent-list {
  padding: 10px 0;
}

.agent-item {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 12px;
}

.agent-name {
  width: 100px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.agent-item .el-progress {
  flex: 1;
}

.load-info {
  width: 60px;
  text-align: right;
  font-size: 13px;
  color: #606266;
}

.skill-distribution {
  padding: 10px 0;
}

.skill-item {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 12px;
}

.skill-name {
  width: 150px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.skill-item .el-progress {
  flex: 1;
}

.skill-item .count {
  width: 60px;
  text-align: right;
  font-size: 13px;
  color: #606266;
}
</style>
