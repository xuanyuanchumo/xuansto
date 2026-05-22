import { ref, computed, onUnmounted } from 'vue'

export enum ConnectionState {
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  RECONNECTING = 'reconnecting'
}

export interface WebSocketMessage {
  type: string
  [key: string]: unknown
}

export interface WebSocketOptions {
  url: string
  heartbeatInterval?: number
  reconnectInterval?: number
  maxReconnectAttempts?: number
  maxReconnectInterval?: number
  messageQueueSize?: number
  onMessage?: (data: WebSocketMessage) => void
  onStateChange?: (state: ConnectionState) => void
  onError?: (error: Event) => void
}

export interface ConnectionMetrics {
  latency: number
  reconnectCount: number
  messageCount: number
  lastMessageTime: number | null
  connectionDuration: number
  uptime: number
}

export interface QueuedMessage {
  id: string
  data: WebSocketMessage
  timestamp: number
  attempts: number
}

export interface SubscriptionInfo {
  metricTypes: Set<string>
  subscribedAt: number
}

const DEFAULT_HEARTBEAT_INTERVAL = 30000
const DEFAULT_RECONNECT_INTERVAL = 1000
const DEFAULT_MAX_RECONNECT_ATTEMPTS = 10
const DEFAULT_MAX_RECONNECT_INTERVAL = 30000
const DEFAULT_MESSAGE_QUEUE_SIZE = 100

export function useWebSocket(options: WebSocketOptions) {
  const {
    url,
    heartbeatInterval = DEFAULT_HEARTBEAT_INTERVAL,
    reconnectInterval = DEFAULT_RECONNECT_INTERVAL,
    maxReconnectAttempts = DEFAULT_MAX_RECONNECT_ATTEMPTS,
    maxReconnectInterval = DEFAULT_MAX_RECONNECT_INTERVAL,
    messageQueueSize = DEFAULT_MESSAGE_QUEUE_SIZE,
    onMessage,
    onStateChange,
    onError
  } = options

  const ws = ref<WebSocket | null>(null)
  const connectionState = ref<ConnectionState>(ConnectionState.DISCONNECTED)
  const reconnectAttempts = ref(0)
  const messageQueue = ref<QueuedMessage[]>([])
  const metrics = ref<ConnectionMetrics>({
    latency: 0,
    reconnectCount: 0,
    messageCount: 0,
    lastMessageTime: null,
    connectionDuration: 0,
    uptime: 0
  })
  const subscriptions = ref<SubscriptionInfo>({
    metricTypes: new Set<string>(),
    subscribedAt: Date.now()
  })

  let heartbeatTimer: ReturnType<typeof setInterval> | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let connectionStartTime: number | null = null
  let lastHeartbeatSent: number | null = null

  const isConnected = computed(() => connectionState.value === ConnectionState.CONNECTED)
  const isReconnecting = computed(() => connectionState.value === ConnectionState.RECONNECTING)
  const queuedMessageCount = computed(() => messageQueue.value.length)

  const updateState = (newState: ConnectionState) => {
    if (connectionState.value !== newState) {
      connectionState.value = newState
      onStateChange?.(newState)
    }
  }

  const generateMessageId = (): string => {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }

  const calculateReconnectDelay = (): number => {
    const baseDelay = reconnectInterval
    const exponentialDelay = baseDelay * Math.pow(2, reconnectAttempts.value)
    const jitter = Math.random() * 1000
    return Math.min(exponentialDelay + jitter, maxReconnectInterval)
  }

  const startHeartbeat = () => {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
    }

    heartbeatTimer = setInterval(() => {
      if (ws.value && isConnected.value) {
        lastHeartbeatSent = Date.now()
        ws.value.send(JSON.stringify({ type: 'heartbeat' }))
      }
    }, heartbeatInterval)
  }

  const stopHeartbeat = () => {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
  }

  const processMessageQueue = async () => {
    if (!ws.value || !isConnected.value || messageQueue.value.length === 0) {
      return
    }

    const messagesToSend = [...messageQueue.value]
    messageQueue.value = []

    messagesToSend.forEach(queuedMsg => {
      sendQueuedMessage(queuedMsg)
    })
  }

  const sendQueuedMessage = (queuedMsg: QueuedMessage) => {
    try {
      ws.value!.send(JSON.stringify(queuedMsg.data))
      metrics.value.messageCount++
    } catch (error) {
      handleSendError(queuedMsg)
    }
  }

  const handleSendError = (queuedMsg: QueuedMessage) => {
    queuedMsg.attempts++
    if (queuedMsg.attempts < 3) {
      messageQueue.value.push(queuedMsg)
    }
  }

  const queueMessage = (data: WebSocketMessage) => {
    if (isConnected.value && ws.value) {
      if (sendMessageDirect(data)) {
        return
      }
    }
    addToQueue(data)
  }

  const sendMessageDirect = (data: WebSocketMessage): boolean => {
    try {
      ws.value!.send(JSON.stringify(data))
      metrics.value.messageCount++
      return true
    } catch (error) {
      console.error('Failed to send message, queuing:', error)
      return false
    }
  }

  const addToQueue = (data: WebSocketMessage) => {
    if (messageQueue.value.length >= messageQueueSize) {
      messageQueue.value.shift()
    }
    messageQueue.value.push({
      id: generateMessageId(),
      data,
      timestamp: Date.now(),
      attempts: 0
    })
  }

  const handleWebSocketOpen = () => {
    updateState(ConnectionState.CONNECTED)
    reconnectAttempts.value = 0
    metrics.value.reconnectCount++
    
    if (connectionStartTime) {
      metrics.value.connectionDuration = Date.now() - connectionStartTime
    }

    startHeartbeat()
    resubscribeAll()
    processMessageQueue()
  }

  const handleWebSocketMessage = (event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data)
      
      if (data.type === 'pong' || data.type === 'heartbeat') {
        if (lastHeartbeatSent) {
          metrics.value.latency = Date.now() - lastHeartbeatSent
          lastHeartbeatSent = null
        }
        return
      }

      metrics.value.lastMessageTime = Date.now()
      metrics.value.messageCount++
      onMessage?.(data)
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error)
    }
  }

  const handleWebSocketClose = () => {
    stopHeartbeat()
    
    if (connectionState.value !== ConnectionState.RECONNECTING) {
      updateState(ConnectionState.DISCONNECTED)
    }

    if (reconnectAttempts.value < maxReconnectAttempts) {
      scheduleReconnect()
    } else {
      console.error('Max reconnect attempts reached')
      updateState(ConnectionState.DISCONNECTED)
    }
  }

  const connect = () => {
    if (ws.value && (isConnected.value || isReconnecting.value)) {
      return
    }

    updateState(ConnectionState.CONNECTING)
    connectionStartTime = Date.now()

    try {
      ws.value = new WebSocket(url)
      ws.value.onopen = handleWebSocketOpen
      ws.value.onmessage = handleWebSocketMessage
      ws.value.onerror = (error) => {
        console.error('WebSocket error:', error)
        onError?.(error)
      }
      ws.value.onclose = handleWebSocketClose
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      updateState(ConnectionState.DISCONNECTED)
      scheduleReconnect()
    }
  }

  const scheduleReconnect = () => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
    }

    if (reconnectAttempts.value >= maxReconnectAttempts) {
      return
    }

    updateState(ConnectionState.RECONNECTING)
    const delay = calculateReconnectDelay()
    
    reconnectTimer = setTimeout(() => {
      reconnectAttempts.value++
      connect()
    }, delay)
  }

  const disconnect = () => {
    stopHeartbeat()
    
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }

    if (ws.value) {
      ws.value.close()
      ws.value = null
    }

    updateState(ConnectionState.DISCONNECTED)
    reconnectAttempts.value = 0
  }

  const reconnect = () => {
    disconnect()
    reconnectAttempts.value = 0
    connect()
  }

  const send = (data: WebSocketMessage) => {
    queueMessage(data)
  }

  const clearQueue = () => {
    messageQueue.value = []
  }

  const subscribe = (metricType: string) => {
    subscriptions.value.metricTypes.add(metricType)
    if (isConnected.value && ws.value) {
      send({
        type: 'subscribe',
        metric_type: metricType
      })
    }
  }

  const unsubscribe = (metricType: string) => {
    subscriptions.value.metricTypes.delete(metricType)
    if (isConnected.value && ws.value) {
      send({
        type: 'unsubscribe',
        metric_type: metricType
      })
    }
  }

  const subscribeMultiple = (metricTypes: string[]) => {
    metricTypes.forEach(t => subscriptions.value.metricTypes.add(t))
    if (isConnected.value && ws.value) {
      send({
        type: 'subscribe',
        metric_types: metricTypes
      })
    }
  }

  const unsubscribeAll = () => {
    if (isConnected.value && ws.value) {
      send({
        type: 'unsubscribe_all'
      })
    }
    subscriptions.value.metricTypes.clear()
  }

  const resubscribeAll = () => {
    if (!isConnected.value || !ws.value) return
    const types = Array.from(subscriptions.value.metricTypes)
    if (types.length > 0) {
      send({
        type: 'subscribe',
        metric_types: types
      })
    }
  }

  const getSubscriptions = (): string[] => {
    return Array.from(subscriptions.value.metricTypes)
  }

  const getMetrics = (): ConnectionMetrics => {
    if (connectionStartTime && isConnected.value) {
      metrics.value.uptime = Date.now() - connectionStartTime
    }
    return { ...metrics.value }
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    ws,
    connectionState,
    reconnectAttempts,
    messageQueue,
    metrics,
    isConnected,
    isReconnecting,
    queuedMessageCount,
    connect,
    disconnect,
    reconnect,
    send,
    clearQueue,
    getMetrics,
    subscribe,
    unsubscribe,
    subscribeMultiple,
    unsubscribeAll,
    getSubscriptions,
    resubscribeAll,
    ConnectionState
  }
}
