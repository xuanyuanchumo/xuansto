interface PerformanceMetrics {
  whiteScreenTime: number
  firstContentfulPaint: number
  largestContentfulPaint: number
  firstInputDelay: number
  cumulativeLayoutShift: number
  timeToInteractive: number
  domContentLoaded: number
  loadTime: number
}

const isDev = import.meta.env.DEV

class PerformanceMonitor {
  private metrics: Partial<PerformanceMetrics> = {}
  
  constructor() {
    this.init()
  }
  
  private init() {
    if (typeof window === 'undefined' || !window.performance) {
      return
    }
    
    this.measureWhiteScreenTime()
    this.measurePageLoad()
    this.measureWebVitals()
  }
  
  private measureWhiteScreenTime() {
    const timing = performance.timing
    this.metrics.whiteScreenTime = timing.domLoading - timing.navigationStart
  }
  
  private measurePageLoad() {
    window.addEventListener('load', () => {
      setTimeout(() => {
        const timing = performance.timing
        this.metrics.domContentLoaded = timing.domContentLoadedEventEnd - timing.navigationStart
        this.metrics.loadTime = timing.loadEventEnd - timing.navigationStart
        this.metrics.timeToInteractive = timing.domInteractive - timing.navigationStart
        
        if (isDev) {
          this.logMetrics()
        }
      }, 0)
    })
  }
  
  private measureWebVitals() {
    if ('PerformanceObserver' in window) {
      this.observeFCP()
      this.observeLCP()
      this.observeFID()
      this.observeCLS()
    }
  }
  
  private observeFCP() {
    try {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries()
        const fcpEntry = entries.find(entry => entry.name === 'first-contentful-paint')
        if (fcpEntry) {
          this.metrics.firstContentfulPaint = fcpEntry.startTime
        }
      })
      observer.observe({ entryTypes: ['paint'] })
    } catch (e) {
      console.warn('FCP observation failed:', e)
    }
  }
  
  private observeLCP() {
    try {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries()
        const lastEntry = entries[entries.length - 1]
        if (lastEntry) {
          this.metrics.largestContentfulPaint = lastEntry.startTime
        }
      })
      observer.observe({ entryTypes: ['largest-contentful-paint'] })
    } catch (e) {
      console.warn('LCP observation failed:', e)
    }
  }
  
  private observeFID() {
    try {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries()
        const firstEntry = entries[0]
        if (firstEntry) {
          this.metrics.firstInputDelay = (firstEntry as PerformanceEventTiming).processingStart - firstEntry.startTime
        }
      })
      observer.observe({ entryTypes: ['first-input'] })
    } catch (e) {
      console.warn('FID observation failed:', e)
    }
  }
  
  private observeCLS() {
    try {
      let clsValue = 0
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (!(entry as any).hadRecentInput) {
            clsValue += (entry as any).value
          }
        }
        this.metrics.cumulativeLayoutShift = clsValue
      })
      observer.observe({ entryTypes: ['layout-shift'] })
    } catch (e) {
      console.warn('CLS observation failed:', e)
    }
  }
  
  private logMetrics() {
    if (!isDev) return
    
    console.group('🚀 性能指标')
    console.log('白屏时间:', this.metrics.whiteScreenTime, 'ms')
    console.log('首次内容绘制 (FCP):', this.metrics.firstContentfulPaint, 'ms')
    console.log('最大内容绘制 (LCP):', this.metrics.largestContentfulPaint, 'ms')
    console.log('首次输入延迟 (FID):', this.metrics.firstInputDelay, 'ms')
    console.log('累积布局偏移 (CLS):', this.metrics.cumulativeLayoutShift)
    console.log('DOM内容加载时间:', this.metrics.domContentLoaded, 'ms')
    console.log('页面完全加载时间:', this.metrics.loadTime, 'ms')
    console.log('可交互时间:', this.metrics.timeToInteractive, 'ms')
    console.groupEnd()
    
    this.checkPerformanceTargets()
  }
  
  private checkPerformanceTargets() {
    if (!isDev) return
    
    const targets = {
      whiteScreenTime: { target: 500, unit: 'ms' },
      firstContentfulPaint: { target: 2000, unit: 'ms' },
      timeToInteractive: { target: 3000, unit: 'ms' }
    }
    
    console.group('🎯 性能目标检查')
    for (const [key, config] of Object.entries(targets)) {
      const value = this.metrics[key as keyof PerformanceMetrics]
      if (value !== undefined) {
        const passed = value <= config.target
        const status = passed ? '✅ 达标' : '❌ 未达标'
        console.log(`${key}: ${value}${config.unit} (目标: ≤${config.target}${config.unit}) ${status}`)
      }
    }
    console.groupEnd()
  }
  
  getMetrics(): Partial<PerformanceMetrics> {
    return { ...this.metrics }
  }
  
  markStart(name: string) {
    performance.mark(`${name}-start`)
  }
  
  markEnd(name: string) {
    performance.mark(`${name}-end`)
    performance.measure(name, `${name}-start`, `${name}-end`)
    const measure = performance.getEntriesByName(name)[0]
    if (isDev) {
      console.log(`⏱️ ${name}: ${measure.duration.toFixed(2)}ms`)
    }
  }
}

export const performanceMonitor = new PerformanceMonitor()

export function markComponentLoad(componentName: string) {
  return {
    start: () => performanceMonitor.markStart(`component-${componentName}`),
    end: () => performanceMonitor.markEnd(`component-${componentName}`)
  }
}

interface PerformanceEventTiming extends PerformanceEntry {
  processingStart: number
}
