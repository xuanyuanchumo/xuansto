import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useNotificationsStore } from '@/stores/notifications'

vi.mock('@/composables/useWebSocket', () => ({
  useWebSocket: vi.fn(() => ({
    connect: vi.fn(),
    disconnect: vi.fn(),
    send: vi.fn(),
    reconnect: vi.fn(),
    connectionState: { value: 'disconnected' },
    isConnected: { value: false },
    isReconnecting: { value: false },
    queuedMessageCount: { value: 0 },
    getMetrics: vi.fn(() => ({
      latency: 0,
      reconnectCount: 0,
      messageCount: 0,
      lastMessageTime: null,
      connectionDuration: 0,
      uptime: 0
    }))
  })),
  ConnectionState: {
    DISCONNECTED: 'disconnected',
    CONNECTED: 'connected',
    RECONNECTING: 'reconnecting'
  }
}))

describe('Notifications Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorage.clear()
  })

  describe('initial state', () => {
    it('should have correct initial state', () => {
      const store = useNotificationsStore()
      
      expect(store.notifications).toEqual([])
      expect(store.error).toBeNull()
      expect(store.unreadCount).toBe(0)
    })
  })

  describe('addNotification', () => {
    it('should add notification successfully', () => {
      const store = useNotificationsStore()
      
      store.addNotification({
        type: 'status_change',
        entity_type: 'project',
        entity_id: 1,
        message: 'Project status changed',
        timestamp: '2024-01-01T10:00:00',
        data: { old_status: 'pending', new_status: 'active' }
      })
      
      expect(store.notifications).toHaveLength(1)
      expect(store.notifications[0].read).toBe(false)
      expect(store.notifications[0].message).toBe('Project status changed')
    })

    it('should limit notifications to 100', () => {
      const store = useNotificationsStore()
      
      for (let i = 0; i < 110; i++) {
        store.addNotification({
          type: 'status_change',
          entity_type: 'project',
          entity_id: i,
          message: `Notification ${i}`,
          timestamp: `2024-01-01T10:00:${i.toString().padStart(2, '0')}`,
          data: {}
        })
      }
      
      expect(store.notifications).toHaveLength(100)
    })

    it('should generate unique id', () => {
      const store = useNotificationsStore()
      
      store.addNotification({
        type: 'status_change',
        entity_type: 'project',
        entity_id: 1,
        message: 'Test 1',
        timestamp: '2024-01-01T10:00:00',
        data: {}
      })
      
      store.addNotification({
        type: 'status_change',
        entity_type: 'project',
        entity_id: 2,
        message: 'Test 2',
        timestamp: '2024-01-01T10:01:00',
        data: {}
      })
      
      expect(store.notifications[0].id).not.toBe(store.notifications[1].id)
    })
  })

  describe('unreadCount', () => {
    it('should count unread notifications correctly', () => {
      const store = useNotificationsStore()
      
      store.addNotification({
        type: 'status_change',
        entity_type: 'project',
        entity_id: 1,
        message: 'Test 1',
        timestamp: '2024-01-01T10:00:00',
        data: {}
      })
      
      store.addNotification({
        type: 'status_change',
        entity_type: 'project',
        entity_id: 2,
        message: 'Test 2',
        timestamp: '2024-01-01T10:01:00',
        data: {}
      })
      
      expect(store.unreadCount).toBe(2)
      
      store.markAsRead(store.notifications[0].id)
      expect(store.unreadCount).toBe(1)
    })
  })

  describe('unreadNotifications', () => {
    it('should return only unread notifications', () => {
      const store = useNotificationsStore()
      
      store.addNotification({
        type: 'status_change',
        entity_type: 'project',
        entity_id: 1,
        message: 'Test 1',
        timestamp: '2024-01-01T10:00:00',
        data: {}
      })
      
      store.addNotification({
        type: 'status_change',
        entity_type: 'project',
        entity_id: 2,
        message: 'Test 2',
        timestamp: '2024-01-01T10:01:00',
        data: {}
      })
      
      expect(store.unreadNotifications).toHaveLength(2)
      
      const firstNotificationId = store.notifications[1].id
      store.markAsRead(firstNotificationId)
      
      expect(store.unreadNotifications).toHaveLength(1)
      expect(store.unreadNotifications[0].message).toBe('Test 2')
    })
  })

  describe('recentNotifications', () => {
    it('should return sorted notifications by timestamp', () => {
      const store = useNotificationsStore()
      
      store.addNotification({
        type: 'status_change',
        entity_type: 'project',
        entity_id: 1,
        message: 'Old',
        timestamp: '2024-01-01T10:00:00',
        data: {}
      })
      
      store.addNotification({
        type: 'status_change',
        entity_type: 'project',
        entity_id: 2,
        message: 'New',
        timestamp: '2024-01-01T11:00:00',
        data: {}
      })
      
      expect(store.recentNotifications[0].message).toBe('New')
      expect(store.recentNotifications[1].message).toBe('Old')
    })
  })

  describe('markAsRead', () => {
    it('should mark notification as read', () => {
      const store = useNotificationsStore()
      
      store.addNotification({
        type: 'status_change',
        entity_type: 'project',
        entity_id: 1,
        message: 'Test',
        timestamp: '2024-01-01T10:00:00',
        data: {}
      })
      
      const notificationId = store.notifications[0].id
      store.markAsRead(notificationId)
      
      expect(store.notifications[0].read).toBe(true)
    })

    it('should do nothing for non-existent notification', () => {
      const store = useNotificationsStore()
      
      store.addNotification({
        type: 'status_change',
        entity_type: 'project',
        entity_id: 1,
        message: 'Test',
        timestamp: '2024-01-01T10:00:00',
        data: {}
      })
      
      store.markAsRead('non-existent-id')
      
      expect(store.notifications[0].read).toBe(false)
    })
  })

  describe('markAllAsRead', () => {
    it('should mark all notifications as read', () => {
      const store = useNotificationsStore()
      
      store.addNotification({
        type: 'status_change',
        entity_type: 'project',
        entity_id: 1,
        message: 'Test 1',
        timestamp: '2024-01-01T10:00:00',
        data: {}
      })
      
      store.addNotification({
        type: 'status_change',
        entity_type: 'project',
        entity_id: 2,
        message: 'Test 2',
        timestamp: '2024-01-01T10:01:00',
        data: {}
      })
      
      store.markAllAsRead()
      
      expect(store.notifications.every(n => n.read)).toBe(true)
      expect(store.unreadCount).toBe(0)
    })
  })

  describe('removeNotification', () => {
    it('should remove notification', () => {
      const store = useNotificationsStore()
      
      store.addNotification({
        type: 'status_change',
        entity_type: 'project',
        entity_id: 1,
        message: 'Test',
        timestamp: '2024-01-01T10:00:00',
        data: {}
      })
      
      const notificationId = store.notifications[0].id
      store.removeNotification(notificationId)
      
      expect(store.notifications).toHaveLength(0)
    })

    it('should do nothing for non-existent notification', () => {
      const store = useNotificationsStore()
      
      store.addNotification({
        type: 'status_change',
        entity_type: 'project',
        entity_id: 1,
        message: 'Test',
        timestamp: '2024-01-01T10:00:00',
        data: {}
      })
      
      store.removeNotification('non-existent-id')
      
      expect(store.notifications).toHaveLength(1)
    })
  })

  describe('clearAll', () => {
    it('should clear all notifications', () => {
      const store = useNotificationsStore()
      
      store.addNotification({
        type: 'status_change',
        entity_type: 'project',
        entity_id: 1,
        message: 'Test 1',
        timestamp: '2024-01-01T10:00:00',
        data: {}
      })
      
      store.addNotification({
        type: 'status_change',
        entity_type: 'project',
        entity_id: 2,
        message: 'Test 2',
        timestamp: '2024-01-01T10:01:00',
        data: {}
      })
      
      store.clearAll()
      
      expect(store.notifications).toHaveLength(0)
    })
  })

  describe('getNotificationsByType', () => {
    it('should filter notifications by type', () => {
      const store = useNotificationsStore()
      
      store.addNotification({
        type: 'status_change',
        entity_type: 'project',
        entity_id: 1,
        message: 'Status Change',
        timestamp: '2024-01-01T10:00:00',
        data: {}
      })
      
      store.addNotification({
        type: 'task_assigned',
        entity_type: 'task',
        entity_id: 1,
        message: 'Task Assigned',
        timestamp: '2024-01-01T10:01:00',
        data: {}
      })
      
      const statusChanges = store.getNotificationsByType('status_change')
      expect(statusChanges).toHaveLength(1)
      expect(statusChanges[0].type).toBe('status_change')
    })
  })

  describe('getNotificationsByEntityType', () => {
    it('should filter notifications by entity type', () => {
      const store = useNotificationsStore()
      
      store.addNotification({
        type: 'status_change',
        entity_type: 'project',
        entity_id: 1,
        message: 'Project',
        timestamp: '2024-01-01T10:00:00',
        data: {}
      })
      
      store.addNotification({
        type: 'status_change',
        entity_type: 'task',
        entity_id: 1,
        message: 'Task',
        timestamp: '2024-01-01T10:01:00',
        data: {}
      })
      
      const projectNotifications = store.getNotificationsByEntityType('project')
      expect(projectNotifications).toHaveLength(1)
      expect(projectNotifications[0].entity_type).toBe('project')
    })
  })

  describe('loadFromLocalStorage', () => {
    it('should load notifications from localStorage', () => {
      const savedNotifications = [
        {
          id: '1',
          type: 'status_change',
          entity_type: 'project',
          entity_id: 1,
          message: 'Saved notification',
          timestamp: '2024-01-01T10:00:00',
          data: {},
          read: false
        }
      ]
      
      localStorage.setItem('notifications', JSON.stringify(savedNotifications))
      
      const store = useNotificationsStore()
      store.loadFromLocalStorage()
      
      expect(store.notifications).toHaveLength(1)
      expect(store.notifications[0].message).toBe('Saved notification')
    })

    it('should handle empty localStorage', () => {
      const store = useNotificationsStore()
      store.loadFromLocalStorage()
      
      expect(store.notifications).toEqual([])
    })
  })

  describe('isConnected', () => {
    it('should return false initially', () => {
      const store = useNotificationsStore()
      expect(store.isConnected).toBe(false)
    })
  })

  describe('metrics', () => {
    it('should return default metrics when not connected', () => {
      const store = useNotificationsStore()
      
      expect(store.metrics).toEqual({
        latency: 0,
        reconnectCount: 0,
        messageCount: 0,
        lastMessageTime: null,
        connectionDuration: 0,
        uptime: 0
      })
    })
  })
})
