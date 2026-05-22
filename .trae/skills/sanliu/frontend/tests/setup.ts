import { config } from '@vue/test-utils'
import { vi } from 'vitest'
import ElementPlus from 'element-plus'

config.global.plugins = [ElementPlus]

config.global.mocks = {
  $router: {
    push: vi.fn(),
    replace: vi.fn(),
    go: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    currentRoute: {
      value: {
        path: '/',
        params: {},
        query: {}
      }
    }
  },
  $route: {
    path: '/',
    params: {},
    query: {}
  }
}

vi.mock('element-plus', () => ({
  default: {
    install: vi.fn()
  },
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn()
  }
}))

vi.mock('@element-plus/icons-vue', () => ({
  Document: { name: 'Document', template: '<svg />' },
  User: { name: 'User', template: '<svg />' },
  List: { name: 'List', template: '<svg />' },
  Connection: { name: 'Connection', template: '<svg />' },
  FullScreen: { name: 'FullScreen', template: '<svg />' },
  DataAnalysis: { name: 'DataAnalysis', template: '<svg />' },
  Setting: { name: 'Setting', template: '<svg />' },
  DocumentChecked: { name: 'DocumentChecked', template: '<svg />' },
  CircleCheck: { name: 'CircleCheck', template: '<svg />' },
  Plus: { name: 'Plus', template: '<svg />' },
  Search: { name: 'Search', template: '<svg />' },
  Edit: { name: 'Edit', template: '<svg />' },
  Delete: { name: 'Delete', template: '<svg />' },
  View: { name: 'View', template: '<svg />' },
  Refresh: { name: 'Refresh', template: '<svg />' },
  Download: { name: 'Download', template: '<svg />' },
  Upload: { name: 'Upload', template: '<svg />' },
  Close: { name: 'Close', template: '<svg />' },
  Check: { name: 'Check', template: '<svg />' },
  Warning: { name: 'Warning', template: '<svg />' },
  InfoFilled: { name: 'InfoFilled', template: '<svg />' },
  SuccessFilled: { name: 'SuccessFilled', template: '<svg />' },
  CircleClose: { name: 'CircleClose', template: '<svg />' }
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({
    path: '/',
    params: {},
    query: {}
  }),
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    go: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    currentRoute: {
      value: {
        path: '/',
        params: {},
        query: {}
      }
    }
  })
}))
