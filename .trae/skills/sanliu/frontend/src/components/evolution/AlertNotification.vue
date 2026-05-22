<template>
  <div class="alert-notification">
    <el-card class="alert-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span class="title">告警通知</span>
            <el-badge :value="pendingCount" :hidden="pendingCount === 0" type="danger">
              <el-icon><Bell /></el-icon>
            </el-badge>
          </div>
          <div class="header-actions">
            <el-select
              v-model="filterLevel"
              size="small"
              placeholder="告警级别"
              clearable
              style="width: 120px"
            >
              <el-option label="全部" value="" />
              <el-option label="信息" value="info" />
              <el-option label="警告" value="warning" />
              <el-option label="错误" value="error" />
              <el-option label="严重" value="critical" />
            </el-select>
            <el-select
              v-model="filterStatus"
              size="small"
              placeholder="状态"
              clearable
              style="width: 100px"
            >
              <el-option label="全部" value="" />
              <el-option label="待处理" value="pending" />
              <el-option label="已确认" value="acknowledged" />
              <el-option label="已解决" value="resolved" />
            </el-select>
            <el-button
              v-if="selectedAlerts.length > 0"
              type="primary"
              size="small"
              @click="batchHandle('acknowledge')"
            >
              批量确认 ({{ selectedAlerts.length }})
            </el-button>
            <el-button
              v-if="selectedAlerts.length > 0"
              type="success"
              size="small"
              @click="batchHandle('resolve')"
            >
              批量解决
            </el-button>
          </div>
        </div>
      </template>

      <div class="alert-list">
        <el-checkbox-group v-model="selectedAlerts">
          <div
            v-for="alert in filteredAlerts"
            :key="alert.id"
            class="alert-item"
            :class="['alert-' + alert.level, { 'alert-selected': selectedAlerts.includes(alert.id) }]"
          >
            <div class="alert-checkbox">
              <el-checkbox :label="alert.id">
                <span></span>
              </el-checkbox>
            </div>
            <div class="alert-content" @click="showAlertDetail(alert)">
              <div class="alert-header">
                <div class="alert-meta">
                  <el-tag :type="getLevelType(alert.level)" size="small" effect="dark">
                    {{ getLevelLabel(alert.level) }}
                  </el-tag>
                  <el-tag v-if="alert.project_name" size="small" type="info">
                    {{ alert.project_name }}
                  </el-tag>
                  <span class="alert-time">{{ formatAlertTime(alert.timestamp) }}</span>
                </div>
                <div class="alert-status">
                  <el-tag
                    :type="getStatusType(alert.status)"
                    size="small"
                  >
                    {{ getStatusLabel(alert.status) }}
                  </el-tag>
                </div>
              </div>
              <div class="alert-message">{{ alert.message }}</div>
              <div v-if="alert.source" class="alert-source">
                来源: {{ alert.source }}
              </div>
            </div>
            <div class="alert-actions">
              <template v-if="alert.status === 'pending'">
                <el-button
                  type="primary"
                  size="small"
                  @click.stop="handleAlert(alert.id, 'acknowledge')"
                >
                  确认
                </el-button>
                <el-button
                  type="success"
                  size="small"
                  @click.stop="handleAlert(alert.id, 'resolve')"
                >
                  解决
                </el-button>
              </template>
              <template v-else-if="alert.status === 'acknowledged'">
                <el-button
                  type="success"
                  size="small"
                  @click.stop="handleAlert(alert.id, 'resolve')"
                >
                  解决
                </el-button>
              </template>
              <el-button
                type="info"
                size="small"
                link
                @click.stop="showAlertDetail(alert)"
              >
                详情
              </el-button>
            </div>
          </div>
        </el-checkbox-group>

        <el-empty v-if="filteredAlerts.length === 0" description="暂无告警" :image-size="80" />
      </div>

      <div v-if="totalAlerts > pageSize" class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="totalAlerts"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchAlerts"
          @current-change="fetchAlerts"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="detailDialogVisible"
      :title="currentAlert ? '告警详情' : ''"
      width="600px"
      destroy-on-close
    >
      <div v-if="currentAlert" class="alert-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="告警ID">
            {{ currentAlert.id }}
          </el-descriptions-item>
          <el-descriptions-item label="告警级别">
            <el-tag :type="getLevelType(currentAlert.level)" effect="dark">
              {{ getLevelLabel(currentAlert.level) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentAlert.status)">
              {{ getStatusLabel(currentAlert.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="触发时间">
            {{ formatTime(currentAlert.timestamp) }}
          </el-descriptions-item>
          <el-descriptions-item label="项目" :span="2">
            {{ currentAlert.project_name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="来源" :span="2">
            {{ currentAlert.source || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="告警信息" :span="2">
            {{ currentAlert.message }}
          </el-descriptions-item>
          <el-descriptions-item v-if="currentAlert.details" label="详细信息" :span="2">
            <pre class="detail-json">{{ JSON.stringify(currentAlert.details, null, 2) }}</pre>
          </el-descriptions-item>
          <el-descriptions-item v-if="currentAlert.acknowledged_by" label="确认人">
            {{ currentAlert.acknowledged_by }}
          </el-descriptions-item>
          <el-descriptions-item v-if="currentAlert.acknowledged_at" label="确认时间">
            {{ formatTime(currentAlert.acknowledged_at) }}
          </el-descriptions-item>
          <el-descriptions-item v-if="currentAlert.resolved_by" label="解决人">
            {{ currentAlert.resolved_by }}
          </el-descriptions-item>
          <el-descriptions-item v-if="currentAlert.resolved_at" label="解决时间">
            {{ formatTime(currentAlert.resolved_at) }}
          </el-descriptions-item>
          <el-descriptions-item v-if="currentAlert.resolution_note" label="解决说明" :span="2">
            {{ currentAlert.resolution_note }}
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="currentAlert.history && currentAlert.history.length > 0" class="alert-history">
          <div class="history-title">处理历史</div>
          <el-timeline>
            <el-timeline-item
              v-for="(item, index) in currentAlert.history"
              :key="index"
              :timestamp="formatTime(item.timestamp)"
              placement="top"
            >
              <div class="history-item">
                <el-tag size="small">{{ item.action }}</el-tag>
                <span v-if="item.user" class="history-user">{{ item.user }}</span>
                <div v-if="item.note" class="history-note">{{ item.note }}</div>
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <template v-if="currentAlert && currentAlert.status === 'pending'">
            <el-button type="primary" @click="handleAlertFromDetail('acknowledge')">
              确认告警
            </el-button>
            <el-button type="success" @click="showResolveDialog">
              解决告警
            </el-button>
          </template>
          <template v-else-if="currentAlert && currentAlert.status === 'acknowledged'">
            <el-button type="success" @click="showResolveDialog">
              解决告警
            </el-button>
          </template>
          <el-button @click="detailDialogVisible = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      v-model="resolveDialogVisible"
      title="解决告警"
      width="400px"
    >
      <el-form :model="resolveForm" label-width="80px">
        <el-form-item label="解决说明">
          <el-input
            v-model="resolveForm.note"
            type="textarea"
            :rows="4"
            placeholder="请输入解决说明"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resolveDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmResolve" :loading="resolving">
          确认解决
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Bell } from '@element-plus/icons-vue'
import { useWebSocket, ConnectionState } from '@/composables/useWebSocket'
import api from '@/api'

interface AlertHistory {
  timestamp: string
  action: string
  user?: string
  note?: string
}

interface Alert {
  id: string
  level: 'info' | 'warning' | 'error' | 'critical'
  message: string
  timestamp: string
  status: 'pending' | 'acknowledged' | 'resolved'
  source?: string
  project_id?: number
  project_name?: string
  details?: Record<string, any>
  acknowledged_by?: string
  acknowledged_at?: string
  resolved_by?: string
  resolved_at?: string
  resolution_note?: string
  history?: AlertHistory[]
}

interface Props {
  projectId?: number
  autoRefresh?: boolean
  refreshInterval?: number
  maxHeight?: string
}

const props = withDefaults(defineProps<Props>(), {
  autoRefresh: true,
  refreshInterval: 10000,
  maxHeight: '500px'
})

const emit = defineEmits<{
  (e: 'alert-received', alert: Alert): void
  (e: 'alert-handled', alertId: string, action: string): void
  (e: 'error', error: Error): void
}>()

const loading = ref(false)
const resolving = ref(false)
const filterLevel = ref('')
const filterStatus = ref('')
const selectedAlerts = ref<string[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const totalAlerts = ref(0)
const detailDialogVisible = ref(false)
const resolveDialogVisible = ref(false)
const currentAlert = ref<Alert | null>(null)
const resolveForm = ref({
  note: ''
})

const alerts = ref<Alert[]>([])

let refreshTimer: ReturnType<typeof setInterval> | null = null

const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
const wsHost = window.location.host
const wsUrl = `${wsProtocol}//${wsHost}/api/evolution-monitor/ws`

const {
  connectionState,
  isConnected,
  connect: wsConnect,
  disconnect: wsDisconnect
} = useWebSocket({
  url: wsUrl,
  heartbeatInterval: 30000,
  onMessage: handleWebSocketMessage,
  onStateChange: handleConnectionStateChange
})

const pendingCount = computed(() => {
  return alerts.value.filter(a => a.status === 'pending').length
})

const filteredAlerts = computed(() => {
  let result = alerts.value

  if (filterLevel.value) {
    result = result.filter(a => a.level === filterLevel.value)
  }

  if (filterStatus.value) {
    result = result.filter(a => a.status === filterStatus.value)
  }

  return result
})

const getLevelType = (level: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    info: 'info',
    warning: 'warning',
    error: 'danger',
    critical: 'danger'
  }
  return types[level] || 'info'
}

const getLevelLabel = (level: string): string => {
  const labels: Record<string, string> = {
    info: '信息',
    warning: '警告',
    error: '错误',
    critical: '严重'
  }
  return labels[level] || level
}

const getStatusType = (status: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    pending: 'warning',
    acknowledged: 'info',
    resolved: 'success'
  }
  return types[status] || 'info'
}

const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    pending: '待处理',
    acknowledged: '已确认',
    resolved: '已解决'
  }
  return labels[status] || status
}

const formatAlertTime = (timestamp: string): string => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return date.toLocaleString('zh-CN')
}

const formatTime = (time: string): string => {
  return new Date(time).toLocaleString('zh-CN')
}

const fetchAlerts = async () => {
  if (loading.value) return

  loading.value = true
  try {
    const params: Record<string, any> = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value
    }

    if (props.projectId) {
      params.project_id = props.projectId
    }
    if (filterLevel.value) {
      params.level = filterLevel.value
    }
    if (filterStatus.value) {
      params.status = filterStatus.value
    }

    const response = await api.get('/evolution-monitor/alerts', { params }) as { total: number; items: Alert[] }
    alerts.value = response.items
    totalAlerts.value = response.total
  } catch (error) {
    console.error('Failed to fetch alerts:', error)
    emit('error', error as Error)
  } finally {
    loading.value = false
  }
}

const handleAlert = async (alertId: string, action: 'acknowledge' | 'resolve') => {
  try {
    await api.post(`/evolution-monitor/alerts/${alertId}/${action}`)
    const alert = alerts.value.find(a => a.id === alertId)
    if (alert) {
      if (action === 'acknowledge') {
        alert.status = 'acknowledged'
        alert.acknowledged_at = new Date().toISOString()
      } else {
        alert.status = 'resolved'
        alert.resolved_at = new Date().toISOString()
      }
    }
    ElMessage.success(action === 'acknowledge' ? '告警已确认' : '告警已解决')
    emit('alert-handled', alertId, action)
  } catch (error) {
    console.error('Failed to handle alert:', error)
    ElMessage.error('操作失败')
  }
}

const batchHandle = async (action: 'acknowledge' | 'resolve') => {
  if (selectedAlerts.value.length === 0) return

  try {
    await api.post('/evolution-monitor/alerts/batch-handle', {
      alert_ids: selectedAlerts.value,
      action
    })

    selectedAlerts.value.forEach(id => {
      const alert = alerts.value.find(a => a.id === id)
      if (alert) {
        if (action === 'acknowledge') {
          alert.status = 'acknowledged'
        } else {
          alert.status = 'resolved'
        }
      }
    })

    selectedAlerts.value = []
    ElMessage.success(`已批量${action === 'acknowledge' ? '确认' : '解决'}告警`)
  } catch (error) {
    console.error('Failed to batch handle alerts:', error)
    ElMessage.error('批量操作失败')
  }
}

const showAlertDetail = async (alert: Alert) => {
  try {
    const response = await api.get(`/evolution-monitor/alerts/${alert.id}`)
    currentAlert.value = response as Alert
    detailDialogVisible.value = true
  } catch (error) {
    console.error('Failed to fetch alert detail:', error)
    currentAlert.value = alert
    detailDialogVisible.value = true
  }
}

const handleAlertFromDetail = async (action: 'acknowledge' | 'resolve') => {
  if (!currentAlert.value) return

  await handleAlert(currentAlert.value.id, action)

  if (action === 'acknowledge') {
    currentAlert.value.status = 'acknowledged'
  }
}

const showResolveDialog = () => {
  resolveForm.value.note = ''
  resolveDialogVisible.value = true
}

const confirmResolve = async () => {
  if (!currentAlert.value) return

  resolving.value = true
  try {
    await api.post(`/evolution-monitor/alerts/${currentAlert.value.id}/resolve`, {
      note: resolveForm.value.note
    })

    currentAlert.value.status = 'resolved'
    currentAlert.value.resolution_note = resolveForm.value.note
    currentAlert.value.resolved_at = new Date().toISOString()

    const alert = alerts.value.find(a => a.id === currentAlert.value!.id)
    if (alert) {
      alert.status = 'resolved'
      alert.resolution_note = resolveForm.value.note
    }

    resolveDialogVisible.value = false
    detailDialogVisible.value = false
    ElMessage.success('告警已解决')
    emit('alert-handled', currentAlert.value.id, 'resolve')
  } catch (error) {
    console.error('Failed to resolve alert:', error)
    ElMessage.error('解决失败')
  } finally {
    resolving.value = false
  }
}

const handleWebSocketMessage = (data: any) => {
  if (data.type === 'alert') {
    const newAlert: Alert = {
      id: data.data.id || `alert-${Date.now()}`,
      level: data.data.level,
      message: data.data.message,
      timestamp: data.data.timestamp || new Date().toISOString(),
      status: 'pending',
      source: data.data.source,
      project_id: data.data.project_id,
      project_name: data.data.project_name,
      details: data.data.details
    }

    alerts.value.unshift(newAlert)
    emit('alert-received', newAlert)

    if (newAlert.level === 'critical' || newAlert.level === 'error') {
      ElMessage({
        type: 'error',
        message: newAlert.message,
        duration: 0,
        showClose: true
      })
    }
  }
}

const handleConnectionStateChange = (state: ConnectionState) => {
  if (state === ConnectionState.CONNECTED) {
    ElMessage.success('WebSocket 已连接')
  } else if (state === ConnectionState.DISCONNECTED) {
    ElMessage.warning('WebSocket 连接断开')
  }
}

const startAutoRefresh = () => {
  if (props.autoRefresh && !refreshTimer && !isConnected.value) {
    refreshTimer = setInterval(fetchAlerts, props.refreshInterval)
  }
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

onMounted(() => {
  fetchAlerts()
  wsConnect()
  if (props.autoRefresh && !isConnected.value) {
    startAutoRefresh()
  }
})

onUnmounted(() => {
  wsDisconnect()
  stopAutoRefresh()
})
</script>

<style scoped>
.alert-notification {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title {
  font-size: 16px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.alert-list {
  max-height: v-bind(maxHeight);
  overflow-y: auto;
}

.alert-item {
  display: flex;
  align-items: flex-start;
  padding: 15px;
  margin-bottom: 10px;
  border-radius: 8px;
  background: #f5f7fa;
  border-left: 4px solid #909399;
  transition: all 0.3s ease;
}

.alert-item:hover {
  background: #ecf5ff;
}

.alert-item.alert-selected {
  background: #ecf5ff;
}

.alert-item.alert-info {
  border-left-color: #909399;
}

.alert-item.alert-warning {
  border-left-color: #e6a23c;
}

.alert-item.alert-error {
  border-left-color: #f56c6c;
}

.alert-item.alert-critical {
  border-left-color: #f56c6c;
  background: #fef0f0;
}

.alert-checkbox {
  margin-right: 10px;
  padding-top: 3px;
}

.alert-content {
  flex: 1;
  cursor: pointer;
}

.alert-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.alert-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.alert-time {
  font-size: 12px;
  color: #909399;
}

.alert-message {
  font-size: 14px;
  color: #303133;
  margin-bottom: 5px;
}

.alert-source {
  font-size: 12px;
  color: #909399;
}

.alert-actions {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-left: 15px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.alert-detail {
  padding: 10px 0;
}

.detail-json {
  background: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  font-size: 12px;
  overflow-x: auto;
  margin: 0;
}

.alert-history {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.history-title {
  font-weight: 500;
  margin-bottom: 15px;
}

.history-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.history-user {
  font-size: 12px;
  color: #909399;
}

.history-note {
  font-size: 13px;
  color: #606266;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

@media (max-width: 768px) {
  .header-actions {
    flex-wrap: wrap;
  }

  .alert-item {
    flex-direction: column;
  }

  .alert-actions {
    flex-direction: row;
    margin-left: 0;
    margin-top: 10px;
  }
}
</style>
