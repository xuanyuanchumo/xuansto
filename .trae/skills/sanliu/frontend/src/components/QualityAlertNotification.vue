<template>
  <div class="quality-alert-notification">
    <transition-group name="notification" tag="div" class="notification-container">
      <div
        v-for="notification in notifications"
        :key="notification.id"
        class="notification-item"
        :class="`notification-${notification.severity}`"
        @click="handleNotificationClick(notification)"
      >
        <div class="notification-icon">
          <el-icon :size="24">
            <component :is="getNotificationIcon(notification.severity)" />
          </el-icon>
        </div>
        <div class="notification-content">
          <div class="notification-title">{{ notification.title }}</div>
          <div class="notification-message">{{ notification.message }}</div>
          <div class="notification-time">{{ formatTime(notification.timestamp) }}</div>
        </div>
        <div class="notification-actions">
          <el-button
            type="primary"
            size="small"
            text
            @click.stop="handleAcknowledge(notification.id)"
          >
            确认
          </el-button>
          <el-button
            size="small"
            text
            @click.stop="handleDismiss(notification.id)"
          >
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </div>
    </transition-group>

    <div v-if="notifications.length > 0" class="notification-badge">
      <el-badge :value="notifications.length" type="danger">
        <el-button
          :icon="Bell"
          circle
          @click="toggleNotificationPanel"
        />
      </el-badge>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElNotification } from 'element-plus'
import {
  Bell,
  Close,
  Warning,
  CircleClose,
  InfoFilled,
  CircleCheck
} from '@element-plus/icons-vue'
import api from '@/api'

interface QualityNotification {
  id: string
  severity: 'info' | 'warning' | 'error' | 'critical'
  title: string
  message: string
  timestamp: string
  metricType: string
  currentValue: number
  threshold: number
  acknowledged: boolean
}

const notifications = ref<QualityNotification[]>([])
const showPanel = ref(false)
let pollTimer: ReturnType<typeof setInterval> | null = null
let lastCheckTime: string = new Date().toISOString()

const getNotificationIcon = (severity: string) => {
  const icons: Record<string, any> = {
    info: InfoFilled,
    warning: Warning,
    error: CircleClose,
    critical: CircleClose
  }
  return icons[severity] || Warning
}

const formatTime = (time: string): string => {
  const date = new Date(time)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60000) {
    return '刚刚'
  } else if (diff < 3600000) {
    return `${Math.floor(diff / 60000)}分钟前`
  } else if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)}小时前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}

const fetchNewAlerts = async () => {
  try {
    const response = await api.get('/quality/alerts', {
      params: {
        severity: 'critical,error,warning',
        since: lastCheckTime
      }
    })
    
    const newAlerts = response || []
    
    if (newAlerts.length > 0) {
      for (const alert of newAlerts) {
        if (!alert.acknowledged) {
          const notification: QualityNotification = {
            id: alert.alert_id,
            severity: alert.severity,
            title: alert.title,
            message: alert.message,
            timestamp: alert.timestamp,
            metricType: alert.metric_type,
            currentValue: alert.current_value,
            threshold: alert.threshold,
            acknowledged: false
          }
          
          notifications.value.unshift(notification)
          
          showDesktopNotification(notification)
        }
      }
      
      lastCheckTime = new Date().toISOString()
    }
  } catch (error) {
    console.error('Failed to fetch alerts:', error)
  }
}

const showDesktopNotification = (notification: QualityNotification) => {
  if ('Notification' in window && Notification.permission === 'granted') {
    new Notification(notification.title, {
      body: notification.message,
      icon: '/favicon.ico',
      tag: notification.id
    })
  }
  
  ElNotification({
    title: notification.title,
    message: notification.message,
    type: notification.severity === 'critical' || notification.severity === 'error' 
      ? 'error' 
      : notification.severity === 'warning' 
        ? 'warning' 
        : 'info',
    duration: 0,
    position: 'top-right',
    onClick: () => handleNotificationClick(notification)
  })
}

const handleNotificationClick = (notification: QualityNotification) => {
  ElMessage.info(`查看告警详情: ${notification.title}`)
}

const handleAcknowledge = async (notificationId: string) => {
  try {
    await api.post(`/quality/alerts/${notificationId}/acknowledge`)
    
    const index = notifications.value.findIndex(n => n.id === notificationId)
    if (index !== -1) {
      notifications.value.splice(index, 1)
    }
    
    ElMessage.success('告警已确认')
  } catch (error) {
    console.error('Failed to acknowledge alert:', error)
    ElMessage.error('确认失败')
  }
}

const handleDismiss = (notificationId: string) => {
  const index = notifications.value.findIndex(n => n.id === notificationId)
  if (index !== -1) {
    notifications.value.splice(index, 1)
  }
}

const toggleNotificationPanel = () => {
  showPanel.value = !showPanel.value
}

const requestNotificationPermission = async () => {
  if ('Notification' in window && Notification.permission === 'default') {
    await Notification.requestPermission()
  }
}

const startPolling = () => {
  if (!pollTimer) {
    fetchNewAlerts()
    pollTimer = setInterval(fetchNewAlerts, 10000)
  }
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

onMounted(async () => {
  await requestNotificationPermission()
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.quality-alert-notification {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  max-width: 400px;
}

.notification-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 15px;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  cursor: pointer;
  transition: all 0.3s ease;
  max-width: 380px;
}

.notification-item:hover {
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
  transform: translateY(-2px);
}

.notification-item.notification-info {
  border-left: 4px solid #909399;
}

.notification-item.notification-warning {
  border-left: 4px solid #e6a23c;
}

.notification-item.notification-error {
  border-left: 4px solid #f56c6c;
}

.notification-item.notification-critical {
  border-left: 4px solid #f56c6c;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 4px 12px rgba(245, 108, 108, 0.3);
  }
  50% {
    box-shadow: 0 4px 20px rgba(245, 108, 108, 0.6);
  }
}

.notification-icon {
  flex-shrink: 0;
  padding-top: 2px;
}

.notification-item.notification-info .notification-icon {
  color: #909399;
}

.notification-item.notification-warning .notification-icon {
  color: #e6a23c;
}

.notification-item.notification-error .notification-icon {
  color: #f56c6c;
}

.notification-item.notification-critical .notification-icon {
  color: #f56c6c;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
  margin-bottom: 4px;
}

.notification-message {
  font-size: 13px;
  color: #606266;
  margin-bottom: 6px;
  line-height: 1.4;
}

.notification-time {
  font-size: 12px;
  color: #909399;
}

.notification-actions {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex-shrink: 0;
}

.notification-badge {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 9998;
}

.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s ease;
}

.notification-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.notification-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>
