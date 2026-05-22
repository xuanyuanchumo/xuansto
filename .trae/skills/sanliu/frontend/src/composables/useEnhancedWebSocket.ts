/**
 * 增强型WebSocket Composable v3.3.0
 *
 * 特性：
 * 1. 智能断线重连（指数退避算法）
 * 2. 消息队列（保证有序性）
 * 3. 数据压缩（JSON紧凑化）
 * 4. 心跳检测
 * 5. 连接状态管理
 * 6. 多频道订阅
 * 7. 带宽优化
 */

import { ref, reactive, onMounted, onUnmounted, watch, type Ref } from 'vue'

export type ConnectionState = 'connecting' | 'connected' | 'reconnecting' | 'disconnected'

export interface WebSocketOptions {
  maxReconnectAttempts?: number
  reconnectBaseDelay?: number
  reconnectMaxDelay?: number
  heartbeatInterval?: number
  heartbeatTimeout?: number
  enableCompression?: boolean
  messageQueueSize?: number
  autoConnect?: boolean
  protocols?: string | string[]
}

export interface WebSocketStats {
  totalMessagesSent: number
  totalMessagesReceived: number
  bytesSent: number
  bytesReceived: number
  reconnectCount: number
  lastMessageTime: Date | null
  averageLatencyMs: number
  uptimeSeconds: number
  connectionTime: Date | null
}

export interface QueuedMessage {
  id: string
  data: any
  channel: string
  timestamp: number
  priority: number
  attempts: number
}

export interface EnhancedWebSocketReturn {
  connect: () => Promise<void>
  disconnect: (code?: number, reason?: string) => void
  send: (data: any, channel?: string) => boolean
  subscribe: (channel: string) => void
  unsubscribe: (channel: string) => void
  reconnect: () => Promise<void>
  status: Readonly<Ref<ConnectionState>>
  stats: Readonly<WebSocketStats>
  subscribedChannels: Readonly<Ref<string[]>>
  isConnected: Readonly<Ref<boolean>>
  isReconnecting: Readonly<Ref<boolean>>
  onMessage: (callback: (data: any, channel: string) => void) => () => void
  onStatusChange: (callback: (status: ConnectionState) => void) => () => void
  onError: (callback: (error: Event) => void) => () => void
  clearQueue: () => void
  getQueueLength: () => number
}

const DEFAULT_OPTIONS: Required<WebSocketOptions> = {
  maxReconnectAttempts: 10,
  reconnectBaseDelay: 1000,
  reconnectMaxDelay: 30000,
  heartbeatInterval: 30000,
  heartbeatTimeout: 60000,
  enableCompression: true,
  messageQueueSize: 200,
  autoConnect: true,
  protocols: '',
}

let globalMessageId = 0

function generateMessageId(): string {
  return `msg_${Date.now()}_${++globalMessageId}`
}

function calculateReconnectDelay(attempt: number, baseDelay: number, maxDelay: number): number {
  const exponentialDelay = Math.min(baseDelay * Math.pow(2, attempt), maxDelay)
  const jitter = Math.random() * baseDelay * 0.5
  return exponentialDelay + jitter
}

function compressData(data: any): string {
  if (typeof data === 'string') return data
  return JSON.stringify(data)
}

function decompressData(raw: string): any {
  try {
    return JSON.parse(raw)
  } catch {
    return raw
  }
}

export function useEnhancedWebSocket(
  url: string,
  options: WebSocketOptions = {}
): EnhancedWebSocketReturn {
  const opts = { ...DEFAULT_OPTIONS, ...options }

  const status = ref<ConnectionState>('disconnected')
  const isConnected = ref(false)
  const isReconnecting = ref(false)
  const subscribedChannels = ref<string[]>([])

  let wsInstance: WebSocket | null = null
  let reconnectAttempt = 0
  let heartbeatTimer: ReturnType<typeof setInterval> | null = null
  let heartbeatTimeoutTimer: ReturnType<typeof setTimeout> | null = null
  let lastHeartbeatResponse = Date.now()
  const messageQueue: QueuedMessage[] = []
  const messageHandlers: Array<(data: any, channel: string) => void> = []
  const statusChangeHandlers: Array<(status: ConnectionState) => void> = []
  const errorHandlers: Array<(error: Event) => void> = []

  const stats = reactive<WebSocketStats>({
    totalMessagesSent: 0,
    totalMessagesReceived: 0,
    bytesSent: 0,
    bytesReceived: 0,
    reconnectCount: 0,
    lastMessageTime: null,
    averageLatencyMs: 0,
    uptimeSeconds: 0,
    connectionTime: null,
  })

  function updateStatus(newState: ConnectionState) {
    if (status.value !== newState) {
      status.value = newState
      isConnected.value = newState === 'connected'
      isReconnecting.value = newState === 'reconnecting'
      statusChangeHandlers.forEach(cb => trySafe(() => cb(newState)))
    }
  }

  function trySafe(fn: () => void) {
    try { fn() } catch { /* ignore */ }
  }

  function enqueueMessage(data: any, channel: string, priority: number = 0): boolean {
    const msg: QueuedMessage = {
      id: generateMessageId(),
      data,
      channel,
      timestamp: Date.now(),
      priority,
      attempts: 0,
    }

    if (messageQueue.length >= opts.messageQueueSize) {
      const lowestPriorityIdx = messageQueue.findIndex(m => m.priority === Math.min(...messageQueue.map(q => q.priority)))
      if (lowestPriorityIdx !== -1 && messageQueue[lowestPriorityIdx].priority > priority) {
        messageQueue.splice(lowestPriorityIdx, 1)
      } else {
        console.warn('[EnhancedWS] Message queue full, dropping low-priority message')
        return false
      }
    }

    messageQueue.push(msg)
    messageQueue.sort((a, b) => b.priority - a.priority)

    if (isConnected.value && wsInstance?.readyState === WebSocket.OPEN) {
      processQueue()
    }

    return true
  }

  function processQueue(): void {
    while (messageQueue.length > 0 && wsInstance?.readyState === WebSocket.OPEN) {
      const msg = messageQueue.shift()
      if (!msg) break

      try {
        const payload = opts.enableCompression ? compressData(msg.data) : JSON.stringify(msg.data)
        const wrappedPayload = JSON.stringify({
          type: 'message',
          id: msg.id,
          channel: msg.channel,
          data: typeof msg.data === 'string' ? msg.data : msg.data,
          timestamp: Date.now(),
        })

        wsInstance.send(wrappedPayload)
        stats.totalMessagesSent++
        stats.bytesSent += new Blob([wrappedPayload]).size
        stats.lastMessageTime = new Date()
      } catch (err) {
        console.error('[EnhancedWS] Send failed:', err)
        msg.attempts++
        if (msg.attempts < 3) {
          messageQueue.unshift(msg)
        }
        break
      }
    }
  }

  function startHeartbeat(): void {
    stopHeartbeat()
    heartbeatTimer = setInterval(() => {
      if (wsInstance?.readyState === WebSocket.OPEN) {
        try {
          wsInstance.send(JSON.stringify({
            type: 'ping',
            timestamp: Date.now(),
          }))
          lastHeartbeatResponse = Date.now()

          heartbeatTimeoutTimer = setTimeout(() => {
            console.warn('[EnhancedWS] Heartbeat timeout, closing connection')
            wsInstance?.close(4001, 'Heartbeat timeout')
          }, opts.heartbeatTimeout)
        } catch (e) {
          console.warn('[EnhancedWS] Heartbeat send failed:', e)
        }
      }
    }, opts.heartbeatInterval)
  }

  function stopHeartbeat(): void {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
    if (heartbeatTimeoutTimer) {
      clearTimeout(heartbeatTimeoutTimer)
      heartbeatTimeoutTimer = null
    }
  }

  function handleOpen(): void {
    updateStatus('connected')
    reconnectAttempt = 0
    stats.connectionTime = new Date()
    processQueue()
    startHeartbeat()

    subscribedChannels.value.forEach(ch => {
      if (wsInstance?.readyState === WebSocket.OPEN) {
        wsInstance.send(JSON.stringify({ type: 'subscribe', channels: [ch] }))
      }
    })
  }

  function handleMessage(event: MessageEvent): void {
    try {
      const parsed = decompressData(event.data as string)
      stats.totalMessagesReceived++
      stats.bytesReceived += event.data.size || (event.data as string).length
      stats.lastMessageTime = new Date()

      if (parsed.type === 'pong') {
        if (heartbeatTimeoutTimer) {
          clearTimeout(heartbeatTimeoutTimer)
          heartbeatTimeoutTimer = null
        }
        const latency = Date.now() - (parsed.timestamp || lastHeartbeatResponse)
        stats.averageLatencyMs = stats.averageLatencyMs === 0
          ? latency
          : Math.round(stats.averageLatencyMs * 0.9 + latency * 0.1)
        return
      }

      if (parsed.type === 'server_heartbeat') {
        return
      }

      const channel = parsed.channel || '__default__'
      messageHandlers.forEach(cb => trySafe(() => cb(parsed.data || parsed, channel)))
    } catch (err) {
      console.warn('[EnhancedWS] Failed to parse message:', err)
      messageHandlers.forEach(cb => trySafe(() => cb(event.data as string, '__raw__')))
    }
  }

  function handleClose(event: CloseEvent): void {
    stopHeartbeat()
    updateStatus('disconnected')

    if (event.code !== 1000 && reconnectAttempt < opts.maxReconnectAttempts) {
      scheduleReconnect()
    }
  }

  function handleError(event: Event): void {
    errorHandlers.forEach(cb => trySafe(() => cb(event)))
  }

  function scheduleReconnect(): void {
    if (isReconnecting.value) return

    updateStatus('reconnecting')
    stats.reconnectCount++
    reconnectAttempt++

    const delay = calculateReconnectDelay(reconnectAttempt - 1, opts.reconnectBaseDelay, opts.reconnectMaxDelay)

    console.log(`[EnhancedWS] Reconnecting in ${Math.round(delay)}ms (attempt ${reconnectAttempt}/${opts.maxReconnectAttempts})`)

    setTimeout(async () => {
      if (!isConnected.value) {
        await connectInternal()
      }
    }, delay)
  }

  async function connectInternal(): Promise<void> {
    if (wsInstance?.readyState === WebSocket.OPEN || status.value === 'connecting') return

    updateStatus('connecting')

    try {
      const wsUrl = url.startsWith('ws') ? url : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${url.replace(/^https?:\/\//, '')}`

      wsInstance = new WebSocket(wsUrl, opts.protocols || undefined)
      wsInstance.binaryType = 'arraybuffer'

      wsInstance.onopen = handleOpen
      wsInstance.onmessage = handleMessage
      wsInstance.onclose = handleClose
      wsInstance.onerror = handleError
    } catch (err) {
      console.error('[EnhancedWS] Connection failed:', err)
      updateStatus('disconnected')
      scheduleReconnect()
    }
  }

  async function connect(): Promise<void> {
    await connectInternal()
  }

  function disconnect(code: number = 1000, reason: string = 'Normal closure'): void {
    stopHeartbeat()
    reconnectAttempt = opts.maxReconnectAttempts

    if (wsInstance) {
      try {
        wsInstance.close(code, reason)
      } catch { /* ignore */ }
      wsInstance = null
    }

    updateStatus('disconnected')
  }

  function send(data: any, channel: string = '__default__'): boolean {
    if (!isConnected.value || !wsInstance || wsInstance.readyState !== WebSocket.OPEN) {
      return enqueueMessage(data, channel)
    }

    try {
      const payload = JSON.stringify({
        type: 'message',
        id: generateMessageId(),
        channel,
        data,
        timestamp: Date.now(),
      })
      wsInstance.send(payload)
      stats.totalMessagesSent++
      stats.bytesSent += payload.length
      stats.lastMessageTime = new Date()
      return true
    } catch (err) {
      console.error('[EnhancedWS] Send error:', err)
      return enqueueMessage(data, channel)
    }
  }

  function subscribe(channel: string): void {
    if (!subscribedChannels.value.includes(channel)) {
      subscribedChannels.value.push(channel)
      if (isConnected.value && wsInstance?.readyState === WebSocket.OPEN) {
        wsInstance.send(JSON.stringify({ type: 'subscribe', channels: [channel] }))
      }
    }
  }

  function unsubscribe(channel: string): void {
    const idx = subscribedChannels.value.indexOf(channel)
    if (idx !== -1) {
      subscribedChannels.value.splice(idx, 1)
      if (isConnected.value && wsInstance?.readyState === WebSocket.OPEN) {
        wsInstance.send(JSON.stringify({ type: 'unsubscribe', channels: [channel] }))
      }
    }
  }

  async function reconnect(): Promise<void> {
    disconnect()
    reconnectAttempt = 0
    await connect()
  }

  function onMessage(callback: (data: any, channel: string) => void): () => void {
    messageHandlers.push(callback)
    return () => {
      const idx = messageHandlers.indexOf(callback)
      if (idx !== -1) messageHandlers.splice(idx, 1)
    }
  }

  function onStatusChange(callback: (status: ConnectionState) => void): () => void {
    statusChangeHandlers.push(callback)
    return () => {
      const idx = statusChangeHandlers.indexOf(callback)
      if (idx !== -1) statusChangeHandlers.splice(idx, 1)
    }
  }

  function onError(callback: (error: Event) => void): () => void {
    errorHandlers.push(callback)
    return () => {
      const idx = errorHandlers.indexOf(callback)
      if (idx !== -1) errorHandlers.splice(idx, 1)
    }
  }

  function clearQueue(): void {
    messageQueue.length = 0
  }

  function getQueueLength(): number {
    return messageQueue.length
  }

  let uptimeInterval: ReturnType<typeof setInterval> | null = null

  onMounted(() => {
    if (opts.autoConnect) {
      connect()
    }

    uptimeInterval = setInterval(() => {
      if (stats.connectionTime) {
        stats.uptimeSeconds = Math.floor((Date.now() - stats.connectionTime.getTime()) / 1000)
      }
    }, 1000)
  })

  onUnmounted(() => {
    disconnect()
    if (uptimeInterval) {
      clearInterval(uptimeInterval)
      uptimeInterval = null
    }
    messageHandlers.length = 0
    statusChangeHandlers.length = 0
    errorHandlers.length = 0
    messageQueue.length = 0
  })

  return {
    connect,
    disconnect,
    send,
    subscribe,
    unsubscribe,
    reconnect,
    status: status as Readonly<Ref<ConnectionState>>,
    stats: stats as unknown as Readonly<WebSocketStats>,
    subscribedChannels: subscribedChannels as Readonly<Ref<string[]>>,
    isConnected: isConnected as Readonly<Ref<boolean>>,
    isReconnecting: isReconnecting as Readonly<Ref<boolean>>,
    onMessage,
    onStatusChange,
    onError,
    clearQueue,
    getQueueLength,
  }
}
