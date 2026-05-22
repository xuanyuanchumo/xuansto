import { describe, it, expect } from 'vitest'
import {
  getStatusLabel,
  getStatusType,
  getProjectStatusLabel,
  getProjectStatusType,
  getTaskStatusLabel,
  getTaskStatusType,
  getTaskPriorityLabel,
  getTaskPriorityType,
  getAgentStatusLabel,
  getAgentStatusType,
  getSkillCallStatusLabel,
  getSkillCallStatusType,
  formatDateTime,
  formatDate,
  formatRelativeTime,
  formatDuration,
  formatPercentage,
  formatFileSize,
  PROJECT_STATUS_OPTIONS,
  TASK_STATUS_OPTIONS,
  TASK_PRIORITY_OPTIONS,
  AGENT_STATUS_OPTIONS,
  SKILL_CALL_STATUS_OPTIONS
} from '@/utils/formatters'

describe('formatters', () => {
  describe('constants', () => {
    it('should have correct project status options', () => {
      expect(PROJECT_STATUS_OPTIONS).toHaveLength(6)
      expect(PROJECT_STATUS_OPTIONS[0].value).toBe('REQUIREMENT')
    })

    it('should have correct task status options', () => {
      expect(TASK_STATUS_OPTIONS).toHaveLength(5)
      expect(TASK_STATUS_OPTIONS[0].value).toBe('PENDING')
    })

    it('should have correct task priority options', () => {
      expect(TASK_PRIORITY_OPTIONS).toHaveLength(3)
      expect(TASK_PRIORITY_OPTIONS[0].value).toBe('high')
    })

    it('should have correct agent status options', () => {
      expect(AGENT_STATUS_OPTIONS).toHaveLength(3)
      expect(AGENT_STATUS_OPTIONS[0].value).toBe('idle')
    })

    it('should have correct skill call status options', () => {
      expect(SKILL_CALL_STATUS_OPTIONS).toHaveLength(5)
      expect(SKILL_CALL_STATUS_OPTIONS[0].value).toBe('started')
    })
  })

  describe('getStatusLabel', () => {
    it('should return correct label for valid status', () => {
      const result = getStatusLabel('PENDING', TASK_STATUS_OPTIONS)
      expect(result).toBe('待处理')
    })

    it('should return status itself for unknown status', () => {
      const result = getStatusLabel('unknown', TASK_STATUS_OPTIONS)
      expect(result).toBe('unknown')
    })
  })

  describe('getStatusType', () => {
    it('should return correct type for valid status', () => {
      const result = getStatusType('PENDING', TASK_STATUS_OPTIONS)
      expect(result).toBe('info')
    })

    it('should return info for unknown status', () => {
      const result = getStatusType('unknown', TASK_STATUS_OPTIONS)
      expect(result).toBe('info')
    })
  })

  describe('project status helpers', () => {
    it('should return correct project status label', () => {
      expect(getProjectStatusLabel('REQUIREMENT')).toBe('需求分析')
      expect(getProjectStatusLabel('DESIGN')).toBe('设计阶段')
      expect(getProjectStatusLabel('DEVELOPMENT')).toBe('开发阶段')
      expect(getProjectStatusLabel('TESTING')).toBe('测试阶段')
      expect(getProjectStatusLabel('DEPLOYMENT')).toBe('部署阶段')
      expect(getProjectStatusLabel('COMPLETED')).toBe('已完成')
    })

    it('should return correct project status type', () => {
      expect(getProjectStatusType('REQUIREMENT')).toBe('info')
      expect(getProjectStatusType('DESIGN')).toBe('warning')
      expect(getProjectStatusType('DEVELOPMENT')).toBe('primary')
      expect(getProjectStatusType('COMPLETED')).toBe('success')
    })
  })

  describe('task status helpers', () => {
    it('should return correct task status label', () => {
      expect(getTaskStatusLabel('PENDING')).toBe('待处理')
      expect(getTaskStatusLabel('IN_PROGRESS')).toBe('进行中')
      expect(getTaskStatusLabel('REVIEW')).toBe('审核中')
      expect(getTaskStatusLabel('COMPLETED')).toBe('已完成')
      expect(getTaskStatusLabel('CANCELLED')).toBe('已取消')
    })

    it('should return correct task status type', () => {
      expect(getTaskStatusType('PENDING')).toBe('info')
      expect(getTaskStatusType('IN_PROGRESS')).toBe('primary')
      expect(getTaskStatusType('REVIEW')).toBe('warning')
      expect(getTaskStatusType('COMPLETED')).toBe('success')
      expect(getTaskStatusType('CANCELLED')).toBe('danger')
    })
  })

  describe('task priority helpers', () => {
    it('should return correct task priority label', () => {
      expect(getTaskPriorityLabel('high')).toBe('高')
      expect(getTaskPriorityLabel('medium')).toBe('中')
      expect(getTaskPriorityLabel('low')).toBe('低')
    })

    it('should return correct task priority type', () => {
      expect(getTaskPriorityType('high')).toBe('danger')
      expect(getTaskPriorityType('medium')).toBe('warning')
      expect(getTaskPriorityType('low')).toBe('info')
    })
  })

  describe('agent status helpers', () => {
    it('should return correct agent status label', () => {
      expect(getAgentStatusLabel('idle')).toBe('空闲')
      expect(getAgentStatusLabel('busy')).toBe('忙碌')
      expect(getAgentStatusLabel('offline')).toBe('离线')
    })

    it('should return correct agent status type', () => {
      expect(getAgentStatusType('idle')).toBe('success')
      expect(getAgentStatusType('busy')).toBe('warning')
      expect(getAgentStatusType('offline')).toBe('danger')
    })
  })

  describe('skill call status helpers', () => {
    it('should return correct skill call status label', () => {
      expect(getSkillCallStatusLabel('started')).toBe('已启动')
      expect(getSkillCallStatusLabel('running')).toBe('运行中')
      expect(getSkillCallStatusLabel('completed')).toBe('已完成')
      expect(getSkillCallStatusLabel('failed')).toBe('失败')
      expect(getSkillCallStatusLabel('cancelled')).toBe('已取消')
    })

    it('should return correct skill call status type', () => {
      expect(getSkillCallStatusType('started')).toBe('info')
      expect(getSkillCallStatusType('running')).toBe('primary')
      expect(getSkillCallStatusType('completed')).toBe('success')
      expect(getSkillCallStatusType('failed')).toBe('danger')
      expect(getSkillCallStatusType('cancelled')).toBe('warning')
    })
  })

  describe('formatDateTime', () => {
    it('should format date time correctly', () => {
      const result = formatDateTime('2024-01-15T10:30:00')
      expect(result).toContain('2024')
      expect(result).toContain('01')
      expect(result).toContain('15')
    })

    it('should return dash for null', () => {
      expect(formatDateTime(null)).toBe('-')
    })

    it('should return dash for undefined', () => {
      expect(formatDateTime(undefined)).toBe('-')
    })

    it('should return dash for empty string', () => {
      expect(formatDateTime('')).toBe('-')
    })
  })

  describe('formatDate', () => {
    it('should format date correctly', () => {
      const result = formatDate('2024-01-15')
      expect(result).toContain('2024')
    })

    it('should return dash for null', () => {
      expect(formatDate(null)).toBe('-')
    })

    it('should return dash for undefined', () => {
      expect(formatDate(undefined)).toBe('-')
    })
  })

  describe('formatRelativeTime', () => {
    it('should return 刚刚 for very recent time', () => {
      const now = new Date().toISOString()
      expect(formatRelativeTime(now)).toBe('刚刚')
    })

    it('should return minutes ago', () => {
      const date = new Date(Date.now() - 5 * 60000).toISOString()
      expect(formatRelativeTime(date)).toBe('5分钟前')
    })

    it('should return hours ago', () => {
      const date = new Date(Date.now() - 2 * 3600000).toISOString()
      expect(formatRelativeTime(date)).toBe('2小时前')
    })

    it('should return days ago', () => {
      const date = new Date(Date.now() - 3 * 86400000).toISOString()
      expect(formatRelativeTime(date)).toBe('3天前')
    })

    it('should return dash for null', () => {
      expect(formatRelativeTime(null)).toBe('-')
    })

    it('should return dash for undefined', () => {
      expect(formatRelativeTime(undefined)).toBe('-')
    })
  })

  describe('formatDuration', () => {
    it('should format seconds correctly', () => {
      expect(formatDuration(30)).toBe('30秒')
    })

    it('should format minutes and seconds correctly', () => {
      expect(formatDuration(90)).toBe('1分钟30秒')
    })

    it('should format hours and minutes correctly', () => {
      expect(formatDuration(3661)).toBe('1小时1分钟')
    })

    it('should return dash for null', () => {
      expect(formatDuration(null)).toBe('-')
    })

    it('should return dash for undefined', () => {
      expect(formatDuration(undefined)).toBe('-')
    })
  })

  describe('formatPercentage', () => {
    it('should calculate percentage correctly', () => {
      expect(formatPercentage(50, 100)).toBe(50)
      expect(formatPercentage(1, 3)).toBe(33)
      expect(formatPercentage(2, 3)).toBe(67)
    })

    it('should return 0 when total is 0', () => {
      expect(formatPercentage(50, 0)).toBe(0)
    })
  })

  describe('formatFileSize', () => {
    it('should format bytes correctly', () => {
      expect(formatFileSize(0)).toBe('0 B')
      expect(formatFileSize(512)).toBe('512 B')
    })

    it('should format kilobytes correctly', () => {
      expect(formatFileSize(1024)).toBe('1 KB')
      expect(formatFileSize(1536)).toBe('1.5 KB')
    })

    it('should format megabytes correctly', () => {
      expect(formatFileSize(1048576)).toBe('1 MB')
    })

    it('should format gigabytes correctly', () => {
      expect(formatFileSize(1073741824)).toBe('1 GB')
    })
  })
})
