import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import type { RouteRecordRaw } from 'vue-router'

describe('Router Configuration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.resetModules()
  })

  describe('routes', () => {
    it('should have correct routes', async () => {
      const { routes } = await import('@/router/index')
      
      expect(routes).toBeDefined()
      expect(routes.length).toBeGreaterThan(0)
    })

    it('should have root redirect to dashboard', async () => {
      const { routes } = await import('@/router/index')
      const rootRoute = routes.find((r: RouteRecordRaw) => r.path === '/')
      
      expect(rootRoute).toBeDefined()
      expect(rootRoute!.redirect).toBe('/dashboard')
    })

    it('should have dashboard route', async () => {
      const { routes } = await import('@/router/index')
      const dashboardRoute = routes.find((r: RouteRecordRaw) => r.path === '/dashboard')
      
      expect(dashboardRoute).toBeDefined()
      expect(dashboardRoute!.name).toBe('Dashboard')
      expect(dashboardRoute!.meta).toEqual({ title: '仪表盘' })
    })

    it('should have tasks route', async () => {
      const { routes } = await import('@/router/index')
      const tasksRoute = routes.find((r: RouteRecordRaw) => r.path === '/tasks')
      
      expect(tasksRoute).toBeDefined()
      expect(tasksRoute!.name).toBe('TaskManagement')
      expect(tasksRoute!.meta).toEqual({ title: '任务管理' })
    })

    it('should have projects routes', async () => {
      const { routes } = await import('@/router/index')
      
      const projectListRoute = routes.find((r: RouteRecordRaw) => r.path === '/projects')
      expect(projectListRoute).toBeDefined()
      expect(projectListRoute!.name).toBe('ProjectList')
      
      const projectCreateRoute = routes.find((r: RouteRecordRaw) => r.path === '/projects/create')
      expect(projectCreateRoute).toBeDefined()
      expect(projectCreateRoute!.name).toBe('ProjectCreate')
      
      const projectDetailRoute = routes.find((r: RouteRecordRaw) => r.path === '/projects/:id')
      expect(projectDetailRoute).toBeDefined()
      expect(projectDetailRoute!.name).toBe('ProjectDetail')
    })

    it('should have agents route', async () => {
      const { routes } = await import('@/router/index')
      const agentsRoute = routes.find((r: RouteRecordRaw) => r.path === '/agents')
      
      expect(agentsRoute).toBeDefined()
      expect(agentsRoute!.name).toBe('Agents')
      expect(agentsRoute!.meta).toEqual({ title: 'Agent管理' })
    })

    it('should have skill calls route', async () => {
      const { routes } = await import('@/router/index')
      const skillCallsRoute = routes.find((r: RouteRecordRaw) => r.path === '/skill-calls')
      
      expect(skillCallsRoute).toBeDefined()
      expect(skillCallsRoute!.name).toBe('SkillCalls')
      expect(skillCallsRoute!.meta).toEqual({ title: '技能调用' })
    })

    it('should have statistics route', async () => {
      const { routes } = await import('@/router/index')
      const statsRoute = routes.find((r: RouteRecordRaw) => r.path === '/statistics')
      
      expect(statsRoute).toBeDefined()
      expect(statsRoute!.name).toBe('Statistics')
      expect(statsRoute!.meta).toEqual({ title: '系统统计' })
    })

    it('should have approvals route', async () => {
      const { routes } = await import('@/router/index')
      const approvalsRoute = routes.find((r: RouteRecordRaw) => r.path === '/approvals')
      
      expect(approvalsRoute).toBeDefined()
      expect(approvalsRoute!.name).toBe('ApprovalCenter')
      expect(approvalsRoute!.meta).toEqual({ title: '人工确认中心' })
    })

    it('should have transparency report route', async () => {
      const { routes } = await import('@/router/index')
      const transparencyRoute = routes.find((r: RouteRecordRaw) => r.path === '/transparency/:projectId')
      
      expect(transparencyRoute).toBeDefined()
      expect(transparencyRoute!.name).toBe('TransparencyReport')
    })

    it('should have pipeline monitor route', async () => {
      const { routes } = await import('@/router/index')
      const pipelineRoute = routes.find((r: RouteRecordRaw) => r.path === '/pipeline/:projectId')
      
      expect(pipelineRoute).toBeDefined()
      expect(pipelineRoute!.name).toBe('PipelineMonitor')
    })

    it('should have requirements route', async () => {
      const { routes } = await import('@/router/index')
      const requirementsRoute = routes.find((r: RouteRecordRaw) => r.path === '/requirements/:projectId')
      
      expect(requirementsRoute).toBeDefined()
      expect(requirementsRoute!.name).toBe('RequirementManagement')
    })
  })

  describe('beforeEach guard', () => {
    it('should set document title from route meta', async () => {
      const { beforeEach } = await import('@/router/index')
      
      const to = { meta: { title: '测试页面' } } as any
      const next = vi.fn()
      
      document.title = ''
      beforeEach(to, {} as any, next)
      
      expect(document.title).toBe('测试页面')
      expect(next).toHaveBeenCalled()
    })

    it('should use default title when no meta title', async () => {
      const { beforeEach } = await import('@/router/index')
      
      const to = { meta: {} } as any
      const next = vi.fn()
      
      document.title = ''
      beforeEach(to, {} as any, next)
      
      expect(document.title).toBe('三省六部协同开发系统')
      expect(next).toHaveBeenCalled()
    })
  })

  describe('history mode', () => {
    it('should use web history', async () => {
      const { history } = await import('@/router/index')
      
      expect(history).toBeDefined()
    })
  })
})
