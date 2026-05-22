import { createApp } from 'vue'
import { createPinia } from 'pinia'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import { performanceMonitor } from './utils/performance'
import { setupRoutePrefetch, prefetchCriticalRoutes } from './utils/prefetch'

const app = createApp(App)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)

setupRoutePrefetch(router)

async function bootstrap() {
  performanceMonitor.markStart('app-bootstrap')
  
  const ElementPlus = await import('element-plus')
  await import('element-plus/dist/index.css')
  
  app.use(ElementPlus.default)
  app.mount('#app')
  
  prefetchCriticalRoutes()
  
  performanceMonitor.markEnd('app-bootstrap')
}

bootstrap()
