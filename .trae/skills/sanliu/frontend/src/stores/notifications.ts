import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useWebSocket, ConnectionState } from '@/composables/useWebSocket'

export type NotificationType = 'status_change' | 'task_assigned' | 'milestone_completed'
export type EntityType = 'project' | 'task' | 'milestone'

export interface NotificationData {
  old_status?: string
  new_status?: string
  entity_name?: string
  task_id?: number
  task_name?: string
  agent_id?: number
  agent_name?: string
  assigned_by?: string
  milestone_id?: number
  milestone_name?: string
  project_id?: number
  project_name?: string
  completed_by?: string
  [key: string]: unknown
}

export interface Notification {
  id: string
  type: NotificationType
  entity_type: EntityType
  entity_id: number
  message: string
  timestamp: string
  data: NotificationData
  read: boolean
}

// 类型守卫函数：验证 WebSocketMessage 是否为有效的 Notification 数据
const isValidNotificationData = (data: unknown): data is Omit<Notification, 'id' | 'read'> => {
  if (typeof data !== 'object' || data === null) {
    return false
  }
  const d = data as Record<string, unknown>
  return (
    typeof d.type === 'string' &&
    typeof d.entity_type === 'string' &&
    typeof d.entity_id === 'number' &&
    typeof d.message === 'string' &&
    typeof d.timestamp === 'string' &&
    typeof d.data === 'object' && d.data !== null
  )
}

export const useNotificationsStore = defineStore('notifications', () => {
  const notifications = ref<Notification[]>([])
  const error = ref<string | null>(null)
  
  let websocketInstance: ReturnType<typeof useWebSocket> | null = null

  const unreadCount = computed(() => {
    return notifications.value.filter(n => !n.read).length
  })

  const unreadNotifications = computed(() => {
    return notifications.value.filter(n => !n.read)
  })

  const recentNotifications = computed(() => {
    return [...notifications.value]
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, 20)
  })

  const connectionState = computed(() => 
    websocketInstance?.connectionState.value || ConnectionState.DISCONNECTED
  )
  
  const isConnected = computed(() => 
    websocketInstance?.isConnected.value || false
  )
  
  const isReconnecting = computed(() => 
    websocketInstance?.isReconnecting.value || false
  )
  
  const metrics = computed(() => 
    websocketInstance?.getMetrics() || {
      latency: 0,
      reconnectCount: 0,
      messageCount: 0,
      lastMessageTime: null,
      connectionDuration: 0,
      uptime: 0
    }
  )

  const connect = (userId: number, wsBaseUrl: string = import.meta.env.VITE_WS_BASE_URL || `ws://${window.location.host}/api/ws`) => {
    if (websocketInstance && isConnected.value) {
      return
    }

    const url = `${wsBaseUrl}/notifications/${userId}`
    
    websocketInstance = useWebSocket({
      url,
      heartbeatInterval: 30000,
      reconnectInterval: 1000,
      maxReconnectAttempts: 10,
      maxReconnectInterval: 30000,
      messageQueueSize: 100,
      onMessage: (data) => {
        if (data.type === 'pong' || data.type === 'heartbeat') {
          return
        }
        if (isValidNotificationData(data)) {
          addNotification(data)
        } else {
          console.warn('Received invalid notification data:', data)
        }
      },
      onStateChange: (state) => {
        if (state === ConnectionState.DISCONNECTED) {
          error.value = 'WebSocket 连接已断开'
        } else if (state === ConnectionState.CONNECTED) {
          error.value = null
        } else if (state === ConnectionState.RECONNECTING) {
          error.value = '正在重新连接...'
        }
      },
      onError: () => {
        error.value = 'WebSocket 连接错误'
      }
    })

    websocketInstance.connect()
  }

  const disconnect = () => {
    if (websocketInstance) {
      websocketInstance.disconnect()
      websocketInstance = null
    }
  }

  const sendPing = () => {
    if (websocketInstance && isConnected.value) {
      websocketInstance.send({ type: 'ping' })
    }
  }

  const reconnect = () => {
    if (websocketInstance) {
      websocketInstance.reconnect()
    }
  }

  const getQueuedMessageCount = () => {
    return websocketInstance?.queuedMessageCount.value || 0
  }

  const addNotification = (data: Omit<Notification, 'id' | 'read'>) => {
    const notification: Notification = {
      ...data,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      read: false
    }
    notifications.value.unshift(notification)
    if (notifications.value.length > 100) {
      notifications.value = notifications.value.slice(0, 100)
    }
    saveToLocalStorage()
  }

  const markAsRead = (notificationId: string) => {
    const notification = notifications.value.find(n => n.id === notificationId)
    if (notification) {
      notification.read = true
      saveToLocalStorage()
    }
  }

  const markAllAsRead = () => {
    notifications.value.forEach(n => {
      n.read = true
    })
    saveToLocalStorage()
  }

  const removeNotification = (notificationId: string) => {
    const index = notifications.value.findIndex(n => n.id === notificationId)
    if (index !== -1) {
      notifications.value.splice(index, 1)
      saveToLocalStorage()
    }
  }

  const clearAll = () => {
    notifications.value = []
    saveToLocalStorage()
  }

  const saveToLocalStorage = () => {
    try {
      localStorage.setItem('notifications', JSON.stringify(notifications.value))
    } catch (e) {
      console.error('Failed to save notifications to localStorage:', e)
    }
  }

  const loadFromLocalStorage = () => {
    try {
      const saved = localStorage.getItem('notifications')
      if (saved) {
        notifications.value = JSON.parse(saved)
      }
    } catch (e) {
      console.error('Failed to load notifications from localStorage:', e)
    }
  }

  const getNotificationsByType = (type: NotificationType) => {
    return notifications.value.filter(n => n.type === type)
  }

  const getNotificationsByEntityType = (entityType: EntityType) => {
    return notifications.value.filter(n => n.entity_type === entityType)
  }

  return {
    notifications,
    error,
    unreadCount,
    unreadNotifications,
    recentNotifications,
    connectionState,
    isConnected,
    isReconnecting,
    metrics,
    connect,
    disconnect,
    sendPing,
    reconnect,
    getQueuedMessageCount,
    addNotification,
    markAsRead,
    markAllAsRead,
    removeNotification,
    clearAll,
    loadFromLocalStorage,
    getNotificationsByType,
    getNotificationsByEntityType
  }
})
