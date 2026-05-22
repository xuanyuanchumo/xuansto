export const PROJECT_STATUS_OPTIONS = [
  { value: 'REQUIREMENT', label: '需求分析', type: 'info' },
  { value: 'DESIGN', label: '设计阶段', type: 'warning' },
  { value: 'DEVELOPMENT', label: '开发阶段', type: 'primary' },
  { value: 'TESTING', label: '测试阶段', type: '' },
  { value: 'DEPLOYMENT', label: '部署阶段', type: 'success' },
  { value: 'COMPLETED', label: '已完成', type: 'success' }
]

export const TASK_STATUS_OPTIONS = [
  { value: 'PENDING', label: '待处理', type: 'info' },
  { value: 'IN_PROGRESS', label: '进行中', type: 'primary' },
  { value: 'REVIEW', label: '审核中', type: 'warning' },
  { value: 'COMPLETED', label: '已完成', type: 'success' },
  { value: 'CANCELLED', label: '已取消', type: 'danger' }
]

export const TASK_PRIORITY_OPTIONS = [
  { value: 'high', label: '高', type: 'danger' },
  { value: 'medium', label: '中', type: 'warning' },
  { value: 'low', label: '低', type: 'info' }
]

export const AGENT_STATUS_OPTIONS = [
  { value: 'idle', label: '空闲', type: 'success' },
  { value: 'busy', label: '忙碌', type: 'warning' },
  { value: 'offline', label: '离线', type: 'danger' }
]

export const SKILL_CALL_STATUS_OPTIONS = [
  { value: 'started', label: '已启动', type: 'info' },
  { value: 'running', label: '运行中', type: 'primary' },
  { value: 'completed', label: '已完成', type: 'success' },
  { value: 'failed', label: '失败', type: 'danger' },
  { value: 'cancelled', label: '已取消', type: 'warning' }
]

export function getStatusLabel(status: string, options: { value: string; label: string }[]) {
  const option = options.find(o => o.value === status)
  return option ? option.label : status
}

export function getStatusType(status: string, options: { value: string; type: string }[]) {
  const option = options.find(o => o.value === status)
  return option ? option.type : 'info'
}

export function getProjectStatusLabel(status: string) {
  return getStatusLabel(status, PROJECT_STATUS_OPTIONS)
}

export function getProjectStatusType(status: string) {
  return getStatusType(status, PROJECT_STATUS_OPTIONS)
}

export function getTaskStatusLabel(status: string) {
  return getStatusLabel(status, TASK_STATUS_OPTIONS)
}

export function getTaskStatusType(status: string) {
  return getStatusType(status, TASK_STATUS_OPTIONS)
}

export function getTaskPriorityLabel(priority: string) {
  return getStatusLabel(priority, TASK_PRIORITY_OPTIONS)
}

export function getTaskPriorityType(priority: string) {
  return getStatusType(priority, TASK_PRIORITY_OPTIONS)
}

export function getAgentStatusLabel(status: string) {
  return getStatusLabel(status, AGENT_STATUS_OPTIONS)
}

export function getAgentStatusType(status: string) {
  return getStatusType(status, AGENT_STATUS_OPTIONS)
}

export function getSkillCallStatusLabel(status: string) {
  return getStatusLabel(status, SKILL_CALL_STATUS_OPTIONS)
}

export function getSkillCallStatusType(status: string) {
  return getStatusType(status, SKILL_CALL_STATUS_OPTIONS)
}

export function formatDateTime(dateStr: string | null | undefined): string {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

export function formatRelativeTime(dateStr: string | null | undefined): string {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 30) return `${days}天前`
  
  return formatDate(dateStr)
}

export function formatDuration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined) return '-'
  
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours}小时${minutes}分钟`
  }
  if (minutes > 0) {
    return `${minutes}分钟${secs}秒`
  }
  return `${secs}秒`
}

export function formatPercentage(value: number, total: number): number {
  if (total === 0) return 0
  return Math.round((value / total) * 100)
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
}
