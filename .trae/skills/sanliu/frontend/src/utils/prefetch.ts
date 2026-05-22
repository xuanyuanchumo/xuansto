import { RouteLocationNormalized, Router } from 'vue-router'

const prefetchMap: Record<string, string[]> = {
  '/dashboard': ['/skill-calls', '/agents', '/tasks'],
  '/projects': ['/projects/create'],
  '/agents': ['/tasks', '/skill-calls'],
  '/tasks': ['/approvals'],
  '/approvals': ['/tasks']
}

const prefetchedRoutes = new Set<string>()
const isDev = import.meta.env.DEV

export function setupRoutePrefetch(router: Router) {
  router.afterEach((to: RouteLocationNormalized) => {
    const path = to.path
    const routesToPrefetch = prefetchMap[path]
    
    if (routesToPrefetch) {
      setTimeout(() => {
        routesToPrefetch.forEach(routePath => {
          if (!prefetchedRoutes.has(routePath)) {
            prefetchRoute(routePath, router)
            prefetchedRoutes.add(routePath)
          }
        })
      }, 1000)
    }
  })
}

function prefetchRoute(path: string, router: Router) {
  const route = router.resolve(path)
  if (route?.matched?.length > 0) {
    const component = route.matched[0].components?.default
    if (component && typeof component === 'function') {
      (component as Function)()
        .then(() => {
          if (isDev) {
            console.log(`✅ 预加载路由: ${path}`)
          }
        })
        .catch((err: Error) => {
          if (isDev) {
            console.warn(`⚠️ 预加载路由失败: ${path}`, err)
          }
        })
    }
  }
}

export function prefetchCriticalRoutes() {
  const criticalRoutes = ['/dashboard', '/projects', '/tasks']
  
  setTimeout(() => {
    criticalRoutes.forEach(path => {
      if (!prefetchedRoutes.has(path)) {
        import('@/views/Dashboard.vue').catch(() => {})
        import('@/views/ProjectList.vue').catch(() => {})
        import('@/views/TaskManagement.vue').catch(() => {})
        prefetchedRoutes.add(path)
      }
    })
    if (isDev) {
      console.log('✅ 关键路由预加载完成')
    }
  }, 2000)
}
