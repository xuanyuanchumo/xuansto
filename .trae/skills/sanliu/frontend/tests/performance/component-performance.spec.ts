/**
 * 组件渲染性能测试
 * 测试组件渲染时间和页面加载时间
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick, ref, computed, defineComponent } from 'vue'

const RENDER_TIME_THRESHOLD_MS = 100
const MOUNT_TIME_THRESHOLD_MS = 50
const UPDATE_TIME_THRESHOLD_MS = 30

interface PerformanceMetrics {
  mountTime: number
  renderTime: number
  updateTime: number
  memoryUsage?: number
}

class PerformanceTimer {
  private startTime: number = 0
  private metrics: PerformanceMetrics = {
    mountTime: 0,
    renderTime: 0,
    updateTime: 0
  }

  start(): void {
    this.startTime = performance.now()
  }

  stop(): number {
    return performance.now() - this.startTime
  }

  measureMount<T>(fn: () => T): { result: T; time: number } {
    const start = performance.now()
    const result = fn()
    const time = performance.now() - start
    this.metrics.mountTime = time
    return { result, time }
  }

  async measureAsyncMount<T>(fn: () => Promise<T>): Promise<{ result: T; time: number }> {
    const start = performance.now()
    const result = await fn()
    const time = performance.now() - start
    this.metrics.mountTime = time
    return { result, time }
  }

  getMetrics(): PerformanceMetrics {
    return { ...this.metrics }
  }
}

describe('Component Rendering Performance', () => {
  let timer: PerformanceTimer
  let pinia: ReturnType<typeof createPinia>

  beforeEach(() => {
    timer = new PerformanceTimer()
    pinia = createPinia()
    setActivePinia(pinia)
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Basic Component Performance', () => {
    it('should mount simple component within threshold', async () => {
      const SimpleComponent = defineComponent({
        template: '<div class="simple">{{ message }}</div>',
        setup() {
          const message = ref('Hello World')
          return { message }
        }
      })
      
      const { time } = timer.measureMount(() => {
        return mount(SimpleComponent, {
          global: {
            plugins: [pinia]
          }
        })
      })

      expect(time).toBeLessThan(MOUNT_TIME_THRESHOLD_MS)
    })

    it('should handle reactive updates efficiently', async () => {
      const ReactiveComponent = defineComponent({
        template: '<div>{{ count }}</div>',
        setup() {
          const count = ref(0)
          return { count }
        }
      })
      
      const wrapper = mount(ReactiveComponent, {
        global: {
          plugins: [pinia]
        }
      })

      const updateTimes: number[] = []
      
      for (let i = 0; i < 10; i++) {
        const start = performance.now()
        await wrapper.vm.$forceUpdate()
        await nextTick()
        updateTimes.push(performance.now() - start)
      }

      const avgUpdateTime = updateTimes.reduce((a, b) => a + b, 0) / updateTimes.length
      expect(avgUpdateTime).toBeLessThan(UPDATE_TIME_THRESHOLD_MS)
      
      wrapper.unmount()
    })

    it('should render list efficiently', async () => {
      const ListComponent = defineComponent({
        template: `
          <ul>
            <li v-for="item in items" :key="item.id">{{ item.name }}</li>
          </ul>
        `,
        setup() {
          const items = ref(Array.from({ length: 100 }, (_, i) => ({
            id: i + 1,
            name: `Item ${i + 1}`
          })))
          return { items }
        }
      })
      
      const { time } = timer.measureMount(() => {
        return mount(ListComponent, {
          global: {
            plugins: [pinia]
          }
        })
      })

      expect(time).toBeLessThan(RENDER_TIME_THRESHOLD_MS * 2)
    })

    it('should handle computed properties efficiently', async () => {
      const ComputedComponent = defineComponent({
        template: '<div>{{ doubledCount }}</div>',
        setup() {
          const count = ref(100)
          const doubledCount = computed(() => count.value * 2)
          return { doubledCount }
        }
      })
      
      const { time } = timer.measureMount(() => {
        return mount(ComputedComponent, {
          global: {
            plugins: [pinia]
          }
        })
      })

      expect(time).toBeLessThan(MOUNT_TIME_THRESHOLD_MS)
    })
  })

  describe('Complex Component Performance', () => {
    it('should handle nested components efficiently', async () => {
      const ChildComponent = defineComponent({
        template: '<span>{{ value }}</span>',
        props: ['value']
      })

      const ParentComponent = defineComponent({
        template: `
          <div>
            <ChildComponent v-for="i in 50" :key="i" :value="i" />
          </div>
        `,
        components: { ChildComponent }
      })
      
      const { time } = timer.measureMount(() => {
        return mount(ParentComponent, {
          global: {
            plugins: [pinia]
          }
        })
      })

      expect(time).toBeLessThan(RENDER_TIME_THRESHOLD_MS * 3)
    })

    it('should handle conditional rendering efficiently', async () => {
      const ConditionalComponent = defineComponent({
        template: `
          <div>
            <div v-if="show">Visible Content</div>
            <div v-else>Hidden Content</div>
          </div>
        `,
        setup() {
          const show = ref(true)
          return { show }
        }
      })
      
      const wrapper = mount(ConditionalComponent, {
        global: {
          plugins: [pinia]
        }
      })

      const toggleTimes: number[] = []
      
      for (let i = 0; i < 10; i++) {
        const start = performance.now()
        wrapper.vm.show = !wrapper.vm.show
        await nextTick()
        toggleTimes.push(performance.now() - start)
      }

      const avgToggleTime = toggleTimes.reduce((a, b) => a + b, 0) / toggleTimes.length
      expect(avgToggleTime).toBeLessThan(UPDATE_TIME_THRESHOLD_MS)
      
      wrapper.unmount()
    })
  })
})

describe('Memory Performance', () => {
  it('should not have memory leaks after multiple mounts', async () => {
    const TestComponent = defineComponent({
      template: '<div>Test Component</div>'
    })
    
    const initialMemory = (performance as any).memory?.usedJSHeapSize || 0
    
    for (let i = 0; i < 20; i++) {
      const wrapper = mount(TestComponent, {
        global: {
          plugins: [createPinia()]
        }
      })
      wrapper.unmount()
    }

    if ((performance as any).memory) {
      const finalMemory = (performance as any).memory.usedJSHeapSize
      const memoryIncrease = (finalMemory - initialMemory) / 1024 / 1024
      expect(memoryIncrease).toBeLessThan(10)
    }
  })
})

describe('Reactivity Performance', () => {
  let pinia: ReturnType<typeof createPinia>

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
  })

  it('should handle rapid state changes efficiently', async () => {
    const state = ref<number[]>([])
    
    const updateTimes: number[] = []
    
    for (let i = 0; i < 100; i++) {
      const start = performance.now()
      state.value = [...state.value, i]
      await nextTick()
      updateTimes.push(performance.now() - start)
    }

    const avgUpdateTime = updateTimes.reduce((a, b) => a + b, 0) / updateTimes.length
    expect(avgUpdateTime).toBeLessThan(5)
  })

  it('should handle computed property updates efficiently', async () => {
    const items = ref(Array.from({ length: 100 }, (_, i) => ({
      id: i + 1,
      name: `Item ${i + 1}`,
      status: i % 2 === 0 ? 'active' : 'inactive'
    })))
    
    const activeItems = computed(() => items.value.filter(item => item.status === 'active'))
    
    const computedTimes: number[] = []
    
    for (let i = 0; i < 10; i++) {
      const start = performance.now()
      const _ = activeItems.value
      computedTimes.push(performance.now() - start)
    }

    const avgComputedTime = computedTimes.reduce((a, b) => a + b, 0) / computedTimes.length
    expect(avgComputedTime).toBeLessThan(1)
  })
})

describe('Component Lifecycle Performance', () => {
  it('should mount and unmount components quickly', async () => {
    const TestComponent = defineComponent({
      template: '<div>Test</div>',
      setup() {
        const data = ref('test')
        return { data }
      }
    })
    
    const lifecycleTimes: number[] = []
    
    for (let i = 0; i < 10; i++) {
      const mountStart = performance.now()
      const wrapper = mount(TestComponent, {
        global: {
          plugins: [createPinia()]
        }
      })
      const mountTime = performance.now() - mountStart
      
      const unmountStart = performance.now()
      wrapper.unmount()
      const unmountTime = performance.now() - unmountStart
      
      lifecycleTimes.push(mountTime + unmountTime)
    }

    const avgLifecycleTime = lifecycleTimes.reduce((a, b) => a + b, 0) / lifecycleTimes.length
    expect(avgLifecycleTime).toBeLessThan(50)
  })
})
