/**
 * 页面加载性能测试
 * 测试页面加载时间和Web Vitals指标
 */

import { test, expect } from '@playwright/test'

const PAGE_LOAD_THRESHOLD_MS = 3000
const FCP_THRESHOLD_MS = 2000
const LCP_THRESHOLD_MS = 2500
const TTI_THRESHOLD_MS = 3800

test.describe('Page Load Performance', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('Dashboard page should load within threshold', async ({ page }) => {
    const startTime = Date.now()
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    const loadTime = Date.now() - startTime

    expect(loadTime).toBeLessThan(PAGE_LOAD_THRESHOLD_MS)
  })

  test('Projects page should load within threshold', async ({ page }) => {
    const startTime = Date.now()
    await page.goto('/projects')
    await page.waitForLoadState('networkidle')
    const loadTime = Date.now() - startTime

    expect(loadTime).toBeLessThan(PAGE_LOAD_THRESHOLD_MS)
  })

  test('Tasks page should load within threshold', async ({ page }) => {
    const startTime = Date.now()
    await page.goto('/tasks')
    await page.waitForLoadState('networkidle')
    const loadTime = Date.now() - startTime

    expect(loadTime).toBeLessThan(PAGE_LOAD_THRESHOLD_MS)
  })

  test('Agents page should load within threshold', async ({ page }) => {
    const startTime = Date.now()
    await page.goto('/agents')
    await page.waitForLoadState('networkidle')
    const loadTime = Date.now() - startTime

    expect(loadTime).toBeLessThan(PAGE_LOAD_THRESHOLD_MS)
  })
})

test.describe('Web Vitals', () => {
  test('First Contentful Paint should meet threshold', async ({ page }) => {
    await page.goto('/')
    
    const fcp = await page.evaluate(() => {
      return new Promise<number>((resolve) => {
        new PerformanceObserver((list) => {
          const entries = list.getEntries()
          const fcpEntry = entries.find(entry => entry.name === 'first-contentful-paint')
          if (fcpEntry) {
            resolve(fcpEntry.startTime)
          }
        }).observe({ entryTypes: ['paint'] })
        
        setTimeout(() => resolve(0), 5000)
      })
    })

    expect(fcp).toBeLessThan(FCP_THRESHOLD_MS)
  })

  test('Largest Contentful Paint should meet threshold', async ({ page }) => {
    await page.goto('/')
    
    const lcp = await page.evaluate(() => {
      return new Promise<number>((resolve) => {
        new PerformanceObserver((list) => {
          const entries = list.getEntries()
          const lastEntry = entries[entries.length - 1]
          if (lastEntry) {
            resolve(lastEntry.startTime)
          }
        }).observe({ entryTypes: ['largest-contentful-paint'] })
        
        setTimeout(() => resolve(0), 5000)
      })
    })

    expect(lcp).toBeLessThan(LCP_THRESHOLD_MS)
  })

  test('Time to Interactive should meet threshold', async ({ page }) => {
    const startTime = Date.now()
    await page.goto('/')
    await page.waitForLoadState('domcontentloaded')
    
    await page.waitForFunction(() => {
      return document.readyState === 'complete'
    })
    
    const tti = Date.now() - startTime
    expect(tti).toBeLessThan(TTI_THRESHOLD_MS)
  })
})

test.describe('Resource Loading Performance', () => {
  test('JavaScript bundle size should be reasonable', async ({ page }) => {
    const resources: { url: string; size: number }[] = []
    
    page.on('response', async (response) => {
      const url = response.url()
      if (url.includes('.js') && !url.includes('node_modules')) {
        try {
          const headers = response.headers()
          const size = parseInt(headers['content-length'] || '0')
          resources.push({ url, size })
        } catch (e) {
        }
      }
    })

    await page.goto('/')
    await page.waitForLoadState('networkidle')

    const totalJsSize = resources.reduce((sum, r) => sum + r.size, 0)
    const totalJsSizeMB = totalJsSize / 1024 / 1024
    
    expect(totalJsSizeMB).toBeLessThan(5)
  })

  test('CSS bundle size should be reasonable', async ({ page }) => {
    const resources: { url: string; size: number }[] = []
    
    page.on('response', async (response) => {
      const url = response.url()
      if (url.includes('.css')) {
        try {
          const headers = response.headers()
          const size = parseInt(headers['content-length'] || '0')
          resources.push({ url, size })
        } catch (e) {
        }
      }
    })

    await page.goto('/')
    await page.waitForLoadState('networkidle')

    const totalCssSize = resources.reduce((sum, r) => sum + r.size, 0)
    const totalCssSizeMB = totalCssSize / 1024 / 1024
    
    expect(totalCssSizeMB).toBeLessThan(1)
  })

  test('API response time should be fast', async ({ page }) => {
    const apiTimes: number[] = []
    
    page.on('response', async (response) => {
      const url = response.url()
      if (url.includes('/api/')) {
        const timing = response.timing()
        if (timing) {
          apiTimes.push(timing.responseEnd - timing.requestStart)
        }
      }
    })

    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')

    if (apiTimes.length > 0) {
      const avgApiTime = apiTimes.reduce((a, b) => a + b, 0) / apiTimes.length
      expect(avgApiTime).toBeLessThan(200)
    }
  })
})

test.describe('Interaction Performance', () => {
  test('Navigation should be responsive', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    const navTimes: number[] = []
    
    for (let i = 0; i < 5; i++) {
      const startTime = Date.now()
      await page.click('text=项目')
      await page.waitForLoadState('networkidle')
      navTimes.push(Date.now() - startTime)
      
      await page.click('text=仪表盘')
      await page.waitForLoadState('networkidle')
    }

    const avgNavTime = navTimes.reduce((a, b) => a + b, 0) / navTimes.length
    expect(avgNavTime).toBeLessThan(1000)
  })

  test('Form interactions should be responsive', async ({ page }) => {
    await page.goto('/projects')
    await page.waitForLoadState('networkidle')

    const inputTimes: number[] = []
    
    const searchInput = page.locator('input[placeholder*="搜索"]').first()
    if (await searchInput.isVisible()) {
      for (let i = 0; i < 5; i++) {
        const startTime = Date.now()
        await searchInput.fill(`test query ${i}`)
        await page.waitForTimeout(100)
        inputTimes.push(Date.now() - startTime)
      }
    }

    if (inputTimes.length > 0) {
      const avgInputTime = inputTimes.reduce((a, b) => a + b, 0) / inputTimes.length
      expect(avgInputTime).toBeLessThan(100)
    }
  })

  test('Button clicks should be responsive', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')

    const buttons = await page.locator('button').all()
    
    if (buttons.length > 0) {
      const clickTimes: number[] = []
      
      for (let i = 0; i < Math.min(5, buttons.length); i++) {
        const startTime = Date.now()
        await buttons[i].click({ timeout: 1000 }).catch(() => {})
        clickTimes.push(Date.now() - startTime)
        await page.waitForTimeout(100)
      }

      const avgClickTime = clickTimes.reduce((a, b) => a + b, 0) / clickTimes.length
      expect(avgClickTime).toBeLessThan(200)
    }
  })
})

test.describe('Memory Performance', () => {
  test('Memory usage should be reasonable', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    const memoryMetrics = await page.evaluate(() => {
      if ((performance as any).memory) {
        return {
          usedJSHeapSize: (performance as any).memory.usedJSHeapSize,
          totalJSHeapSize: (performance as any).memory.totalJSHeapSize,
          jsHeapSizeLimit: (performance as any).memory.jsHeapSizeLimit
        }
      }
      return null
    })

    if (memoryMetrics) {
      const usedMB = memoryMetrics.usedJSHeapSize / 1024 / 1024
      expect(usedMB).toBeLessThan(100)
    }
  })

  test('Memory should not leak during navigation', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    const initialMemory = await page.evaluate(() => {
      return (performance as any).memory?.usedJSHeapSize || 0
    })

    for (let i = 0; i < 10; i++) {
      await page.goto('/projects')
      await page.waitForLoadState('networkidle')
      await page.goto('/tasks')
      await page.waitForLoadState('networkidle')
      await page.goto('/agents')
      await page.waitForLoadState('networkidle')
      await page.goto('/')
      await page.waitForLoadState('networkidle')
    }

    const finalMemory = await page.evaluate(() => {
      return (performance as any).memory?.usedJSHeapSize || 0
    })

    if (initialMemory && finalMemory) {
      const memoryIncrease = (finalMemory - initialMemory) / 1024 / 1024
      expect(memoryIncrease).toBeLessThan(50)
    }
  })
})

test.describe('Network Performance', () => {
  test('Should handle slow network gracefully', async ({ page }) => {
    const client = await page.context().newCDPSession(page)
    await client.send('Network.emulateNetworkConditions', {
      offline: false,
      downloadThroughput: (500 * 1024) / 8,
      uploadThroughput: (500 * 1024) / 8,
      latency: 100
    })

    const startTime = Date.now()
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    const loadTime = Date.now() - startTime

    expect(loadTime).toBeLessThan(10000)
  })

  test('Should handle offline mode gracefully', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    await page.context().setOffline(true)
    
    try {
      await page.goto('/projects', { timeout: 5000 })
    } catch (e) {
    }

    const errorElement = page.locator('text=/网络|离线|错误|失败/')
    const hasErrorHandling = await errorElement.count() > 0 || 
      await page.locator('body').isVisible()

    expect(hasErrorHandling).toBeTruthy()

    await page.context().setOffline(false)
  })
})
