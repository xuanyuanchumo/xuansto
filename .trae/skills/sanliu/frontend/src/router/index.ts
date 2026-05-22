import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '仪表盘' }
  },
  {
    path: '/skill-calls',
    name: 'SkillCalls',
    component: () => import('@/views/SkillCalls.vue'),
    meta: { title: '技能调用' }
  },
  {
    path: '/agents',
    name: 'Agents',
    component: () => import('@/views/Agents.vue'),
    meta: { title: 'Agent管理' }
  },
  {
    path: '/tasks',
    name: 'TaskManagement',
    component: () => import('@/views/TaskManagement.vue'),
    meta: { title: '任务管理' }
  },
  {
    path: '/projects',
    name: 'ProjectList',
    component: () => import('@/views/ProjectList.vue'),
    meta: { title: '项目列表' }
  },
  {
    path: '/projects/create',
    name: 'ProjectCreate',
    component: () => import('@/views/ProjectCreate.vue'),
    meta: { title: '创建项目' }
  },
  {
    path: '/projects/:id',
    name: 'ProjectDetail',
    component: () => import('@/views/ProjectDetail.vue'),
    meta: { title: '项目详情' }
  },
  {
    path: '/transparency/:projectId',
    name: 'TransparencyReport',
    component: () => import('@/views/TransparencyReport.vue'),
    meta: { title: '透明度报告' }
  },
  {
    path: '/requirements/:projectId',
    name: 'RequirementManagement',
    component: () => import('@/views/RequirementManagement.vue'),
    meta: { title: '需求管理' }
  },
  {
    path: '/approvals',
    name: 'ApprovalCenter',
    component: () => import('@/views/ApprovalCenter.vue'),
    meta: { title: '人工确认中心' }
  },
  {
    path: '/pipeline/:projectId',
    name: 'PipelineMonitor',
    component: () => import('@/views/PipelineMonitor.vue'),
    meta: { title: '流水线监控' }
  },
  {
    path: '/statistics',
    name: 'Statistics',
    component: () => import('@/views/Statistics.vue'),
    meta: { title: '系统统计' }
  },
  {
    path: '/skill-health',
    name: 'SkillHealth',
    component: () => import('@/views/SkillHealth.vue'),
    meta: { title: '技能健康度' }
  },
  {
    path: '/path-validation',
    name: 'PathValidation',
    component: () => import('@/views/PathValidation.vue'),
    meta: { title: '路径验证' }
  },
  {
    path: '/evolution-knowledge',
    name: 'EvolutionKnowledge',
    component: () => import('@/views/EvolutionKnowledge.vue'),
    meta: { title: '演化知识库' }
  },
  {
    path: '/realtime-evolution',
    name: 'RealtimeEvolution',
    component: () => import('@/views/RealtimeEvolution.vue'),
    meta: { title: '实时演化状态' }
  },
  {
    path: '/realtime-quality',
    name: 'RealtimeQuality',
    component: () => import('@/views/RealtimeQuality.vue'),
    meta: { title: '实时质量监控' }
  },
  {
    path: '/path-validation-detail',
    name: 'PathValidationDetail',
    component: () => import('@/views/PathValidationDetail.vue'),
    meta: { title: '路径验证详情' }
  },
  {
    path: '/four-d-defense',
    name: 'FourDDefense',
    component: () => import('@/views/FourDDefenseView.vue'),
    meta: { title: '四维防线' }
  },
  {
    path: '/security-scan',
    name: 'SecurityScan',
    component: () => import('@/views/SecurityScanView.vue'),
    meta: { title: '安全扫描' }
  }
]

export const history = createWebHistory()

const router = createRouter({
  history,
  routes
})

export const beforeEach = (to: any, _from: any, next: any) => {
  document.title = (to.meta.title as string) || '三省六部协同开发系统'
  next()
}

router.beforeEach(beforeEach)

export { routes }
export default router
