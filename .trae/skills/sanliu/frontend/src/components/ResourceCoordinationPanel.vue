<template>
  <div class="resource-coordination-panel">
    <el-card shadow="hover">
      <template #header>
        <div class="panel-header">
          <el-icon><Connection /></el-icon>
          <span>MARC-Lite 资源协调器</span>
          <el-tag :type="overallStatusType" size="small" class="status-tag">
            {{ overallStatus }}
          </el-tag>
        </div>
      </template>

      <el-tabs v-model="activeTab" type="border-card">
        <el-tab-pane label="锁持有情况" name="locks">
          <div v-loading="loading.locks">
            <el-table :data="lockData" stripe style="width: 100%" max-height="400">
              <el-table-column prop="resource_id" label="资源ID" min-width="150" />
              <el-table-column prop="resource_type" label="类型" width="100">
                <template #default="{ row }">
                  <el-tag :type="getResourceTypeColor(row.resource_type)" size="small">
                    {{ row.resource_type }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="lock_count" label="锁数量" width="80" align="center" />
              <el-table-column prop="holders" label="持有者" min-width="120">
                <template #default="{ row }">
                  <span v-for="(holder, idx) in row.holders" :key="idx">
                    <el-tag size="small" type="info">{{ holder }}</el-tag>
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100" align="center">
                <template #default="{ row }">
                  <el-button link type="primary" size="small" @click="showResourceDetail(row)">
                    详情
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="!loading.locks && lockData.length === 0" description="暂无锁持有记录" />
          </div>
        </el-tab-pane>

        <el-tab-pane label="队列状态" name="queue">
          <div v-loading="loading.queue">
            <el-row :gutter="20" class="queue-stats">
              <el-col :span="6">
                <el-statistic title="等待任务数" :value="queueStatus.waiting_count" />
              </el-col>
              <el-col :span="6">
                <el-statistic title="高优先级" :value="queueStatus.high_priority">
                  <template #prefix>
                    <span style="color: #f56c6c">●</span>
                  </template>
                </el-statistic>
              </el-col>
              <el-col :span="6">
                <el-statistic title="中优先级" :value="queueStatus.medium_priority">
                  <template #prefix>
                    <span style="color: #e6a23c">●</span>
                  </template>
                </el-statistic>
              </el-col>
              <el-col :span="6">
                <el-statistic title="低优先级" :value="queueStatus.low_priority">
                  <template #prefix>
                    <span style="color: #67c23a">●</span>
                  </template>
                </el-statistic>
              </el-col>
            </el-row>

            <div class="queue-visualization">
              <h4>队列可视化</h4>
              <div class="queue-items">
                <div
                  v-for="(item, idx) in queueItems"
                  :key="idx"
                  class="queue-item"
                  :class="`priority-${item.priority}`"
                >
                  <div class="task-id">{{ item.task_id }}</div>
                  <div class="agent-info">{{ item.agent_id }}</div>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="告警信息" name="alerts">
          <div v-loading="loading.alerts">
            <div class="alert-list" ref="alertContainer">
              <el-alert
                v-for="(alert, idx) in alerts"
                :key="idx"
                :title="alert.message"
                :type="getAlertType(alert.level)"
                :closable="false"
                show-icon
                class="alert-item"
              >
                <template #default>
                  <div class="alert-detail">
                    <span class="alert-time">{{ formatTime(alert.timestamp) }}</span>
                    <span>{{ alert.message }}</span>
                  </div>
                </template>
              </el-alert>
            </div>
            <el-empty v-if="!loading.alerts && alerts.length === 0" description="暂无告警信息" />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { Connection } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

interface LockInfo {
  resource_id: string
  resource_type: string
  lock_count: number
  holders: string[]
}

interface QueueItem {
  task_id: string
  agent_id: string
  priority: string
}

interface Alert {
  timestamp: string
  level: string
  message: string
}

const activeTab = ref('locks')
const loading = reactive({
  locks: false,
  queue: false,
  alerts: false
})

const lockData = ref<LockInfo[]>([])
const queueStatus = reactive({
  waiting_count: 0,
  high_priority: 0,
  medium_priority: 0,
  low_priority: 0
})
const queueItems = ref<QueueItem[]>([])
const alerts = ref<Alert[]>([])

let refreshInterval: number

const overallStatus = ref('正常')
const overallStatusType = ref<'success' | 'warning' | 'danger' | 'info'>('success')

const getResourceTypeColor = (type: string): string => {
  const colors: Record<string, string> = {
    file: '',
    api: 'success',
    compute: 'warning',
    terminal: 'info',
    secret: 'danger'
  }
  return colors[type] || ''
}

const getAlertType = (level: string): 'success' | 'warning' | 'info' | 'error' => {
  const types: Record<string, 'success' | 'warning' | 'info' | 'error'> = {
    INFO: 'info',
    WARNING: 'warning',
    ERROR: 'error',
    CRITICAL: 'error'
  }
  return types[level] || 'info'
}

const formatTime = (time: string): string => {
  if (!time) return ''
  return new Date(time).toLocaleString('zh-CN')
}

const showResourceDetail = (row: LockInfo) => {
  ElMessage.info(`查看资源 ${row.resource_id} 的详细信息`)
}

const fetchLockStatus = async () => {
  loading.locks = true
  try {
    const response = await api.get('/resources/deadlock/detect')
    const statusResponse = await api.get('/resources/queue')
    
    queueStatus.waiting_count = statusResponse.data.waiting_count || 0
    queueStatus.high_priority = statusResponse.data.high_priority || 0
    queueStatus.medium_priority = statusResponse.data.medium_priority || 0
    queueStatus.low_priority = statusResponse.data.low_priority || 0
    
    if (response.data.has_deadlock_risk) {
      overallStatus.value = '存在风险'
      overallStatusType.value = 'danger'
    } else {
      overallStatus.value = '正常'
      overallStatusType.value = 'success'
    }
    
    lockData.value = [
      { resource_id: 'file_001', resource_type: 'file', lock_count: 2, holders: ['agent_01', 'agent_02'] },
      { resource_id: 'api_001', resource_type: 'api', lock_count: 1, holders: ['agent_03'] },
      { resource_id: 'compute_001', resource_type: 'compute', lock_count: 0, holders: [] }
    ]
  } catch (error) {
    console.error('获取锁状态失败:', error)
  } finally {
    loading.locks = false
  }
}

const fetchQueueStatus = async () => {
  loading.queue = true
  try {
    const response = await api.get('/resources/queue')
    
    queueStatus.waiting_count = response.data.waiting_count || 0
    queueStatus.high_priority = response.data.high_priority || 0
    queueStatus.medium_priority = response.data.medium_priority || 0
    queueStatus.low_priority = response.data.low_priority || 0
    
    queueItems.value = (response.data.queue_items || []).map((item: any) => ({
      task_id: item.task_id || `task_${Math.random().toString(36).substr(2, 9)}`,
      agent_id: item.agent_id || 'unknown',
      priority: item.priority || 'medium'
    }))
  } catch (error) {
    console.error('获取队列状态失败:', error)
  } finally {
    loading.queue = false
  }
}

const fetchAlerts = async () => {
  loading.alerts = true
  try {
    const mockAlerts: Alert[] = [
      { timestamp: new Date().toISOString(), level: 'WARNING', message: 'Agent agent_01 文件锁使用率达到80%' },
      { timestamp: new Date(Date.now() - 300000).toISOString(), level: 'INFO', message: '新资源 secret_002 已注册' },
      { timestamp: new Date(Date.now() - 600000).toISOString(), level: 'ERROR', message: '资源 compute_001 获取锁超时' }
    ]
    alerts.value = mockAlerts
  } catch (error) {
    console.error('获取告警信息失败:', error)
  } finally {
    loading.alerts = false
  }
}

onMounted(async () => {
  await Promise.all([
    fetchLockStatus(),
    fetchQueueStatus(),
    fetchAlerts()
  ])
  
  refreshInterval = window.setInterval(async () => {
    await Promise.all([
      fetchQueueStatus(),
      fetchAlerts()
    ])
  }, 10000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

<style scoped>
.resource-coordination-panel {
  padding: 20px;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: bold;
}

.status-tag {
  margin-left: auto;
}

.queue-stats {
  margin-bottom: 20px;
  text-align: center;
}

.queue-visualization h4 {
  margin-bottom: 15px;
  color: #606266;
}

.queue-items {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
  min-height: 80px;
}

.queue-item {
  padding: 10px 15px;
  border-radius: 6px;
  background: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  min-width: 140px;
  border-left: 4px solid;
}

.queue-item.priority-high {
  border-left-color: #f56c6c;
}

.queue-item.priority-medium {
  border-left-color: #e6a23c;
}

.queue-item.priority-low {
  border-left-color: #67c23a;
}

.queue-item .task-id {
  font-weight: bold;
  font-size: 12px;
  color: #303133;
  margin-bottom: 4px;
}

.queue-item .agent-info {
  font-size: 11px;
  color: #909399;
}

.alert-list {
  max-height: 400px;
  overflow-y: auto;
}

.alert-item {
  margin-bottom: 10px;
}

.alert-detail {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

.alert-time {
  color: #909399;
  font-size: 12px;
  white-space: nowrap;
  margin-right: 15px;
}
</style>
