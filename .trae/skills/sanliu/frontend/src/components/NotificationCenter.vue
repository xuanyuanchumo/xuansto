<template>
  <div class="notification-center">
    <el-dropdown trigger="click" @visible-change="handleDropdownVisible">
      <div class="notification-trigger">
        <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99">
          <el-button :icon="Bell" circle />
        </el-badge>
      </div>
      <template #dropdown>
        <el-dropdown-menu class="notification-dropdown">
          <div class="notification-header">
            <span class="title">通知中心</span>
            <el-button
              v-if="unreadCount > 0"
              type="primary"
              link
              size="small"
              @click="handleMarkAllRead"
            >
              全部已读
            </el-button>
          </div>
          
          <el-scrollbar max-height="400px">
            <div v-if="notifications.length === 0" class="empty-state">
              <el-empty description="暂无通知" :image-size="80" />
            </div>
            <div v-else class="notification-list">
              <div
                v-for="notification in notifications"
                :key="notification.id"
                class="notification-item"
                :class="{ unread: !notification.read }"
                @click="handleNotificationClick(notification)"
              >
                <div class="notification-icon">
                  <el-icon :size="20" :color="getIconColor(notification.type)">
                    <component :is="getIcon(notification.type)" />
                  </el-icon>
                </div>
                <div class="notification-content">
                  <div class="notification-message">{{ notification.message }}</div>
                  <div class="notification-meta">
                    <el-tag
                      :type="getTagType(notification.type)"
                      size="small"
                    >
                      {{ getTypeLabel(notification.type) }}
                    </el-tag>
                    <span class="notification-time">{{ formatTime(notification.timestamp) }}</span>
                  </div>
                </div>
                <div class="notification-actions">
                  <el-button
                    type="primary"
                    link
                    size="small"
                    @click.stop="handleRemove(notification.id)"
                  >
                    <el-icon><Close /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>
          </el-scrollbar>
          
          <div v-if="notifications.length > 0" class="notification-footer">
            <el-button type="danger" link size="small" @click="handleClearAll">
              清空全部
            </el-button>
          </div>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { Bell, Close, Document, User, Flag } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useNotificationsStore, type Notification, type NotificationType } from '@/stores/notifications'

const notificationsStore = useNotificationsStore()

const notifications = computed(() => notificationsStore.recentNotifications)
const unreadCount = computed(() => notificationsStore.unreadCount)

const getIcon = (type: NotificationType) => {
  const icons: Record<NotificationType, typeof Document> = {
    status_change: Document,
    task_assigned: User,
    milestone_completed: Flag
  }
  return icons[type] || Document
}

const getIconColor = (type: NotificationType) => {
  const colors: Record<NotificationType, string> = {
    status_change: '#409eff',
    task_assigned: '#67c23a',
    milestone_completed: '#e6a23c'
  }
  return colors[type] || '#909399'
}

const getTagType = (type: NotificationType) => {
  const types: Record<NotificationType, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
    status_change: 'primary',
    task_assigned: 'success',
    milestone_completed: 'warning'
  }
  return types[type] || 'info'
}

const getTypeLabel = (type: NotificationType) => {
  const labels: Record<NotificationType, string> = {
    status_change: '状态变更',
    task_assigned: '任务分配',
    milestone_completed: '里程碑完成'
  }
  return labels[type] || '通知'
}

const formatTime = (timestamp: string) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60000) {
    return '刚刚'
  } else if (diff < 3600000) {
    return `${Math.floor(diff / 60000)} 分钟前`
  } else if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)} 小时前`
  } else if (diff < 604800000) {
    return `${Math.floor(diff / 86400000)} 天前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}

const handleDropdownVisible = (visible: boolean) => {
  if (visible) {
    notificationsStore.loadFromLocalStorage()
  }
}

const handleNotificationClick = (notification: Notification) => {
  notificationsStore.markAsRead(notification.id)
  ElMessage.info(`查看 ${notification.entity_type} #${notification.entity_id}`)
}

const handleMarkAllRead = () => {
  notificationsStore.markAllAsRead()
  ElMessage.success('已全部标记为已读')
}

const handleRemove = (notificationId: string) => {
  notificationsStore.removeNotification(notificationId)
}

const handleClearAll = () => {
  notificationsStore.clearAll()
  ElMessage.success('已清空所有通知')
}

let pingInterval: number

onMounted(() => {
  notificationsStore.loadFromLocalStorage()
  notificationsStore.connect(1)
  
  pingInterval = window.setInterval(() => {
    notificationsStore.sendPing()
  }, 30000)
})

onUnmounted(() => {
  if (pingInterval) {
    clearInterval(pingInterval)
  }
  notificationsStore.disconnect()
})
</script>

<style scoped>
.notification-center {
  display: inline-block;
}

.notification-trigger {
  cursor: pointer;
}

.notification-dropdown {
  width: 380px;
  padding: 0;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #ebeef5;
}

.notification-header .title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.empty-state {
  padding: 20px;
}

.notification-list {
  max-height: 400px;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background-color 0.2s;
}

.notification-item:hover {
  background-color: #f5f7fa;
}

.notification-item.unread {
  background-color: #ecf5ff;
}

.notification-item.unread:hover {
  background-color: #d9ecff;
}

.notification-icon {
  flex-shrink: 0;
  margin-right: 12px;
  padding-top: 2px;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-message {
  font-size: 14px;
  color: #303133;
  line-height: 1.5;
  word-break: break-word;
}

.notification-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
}

.notification-time {
  font-size: 12px;
  color: #909399;
}

.notification-actions {
  flex-shrink: 0;
  margin-left: 8px;
}

.notification-footer {
  display: flex;
  justify-content: center;
  padding: 12px;
  border-top: 1px solid #ebeef5;
}
</style>
