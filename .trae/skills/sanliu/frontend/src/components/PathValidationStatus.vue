<template>
  <div class="path-validation-status">
    <el-card class="validation-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span class="title">路径验证状态面板</span>
            <el-tag :type="overallStatusType" effect="dark" size="small">
              {{ overallStatusLabel }}
            </el-tag>
          </div>
          <div class="header-actions">
            <el-button type="primary" size="small" :loading="validating" @click="validateAllPaths">
              <el-icon><Refresh /></el-icon>
              一键验证
            </el-button>
            <el-button size="small" @click="loadPaths">
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <div class="validation-content">
        <div class="summary-bar">
          <div class="summary-item" v-for="(count, status) in pathStats" :key="status">
            <span class="summary-icon">{{ getStatusEmoji(status) }}</span>
            <span class="summary-count" :class="`stat-${status}`">{{ count }}</span>
            <span class="summary-label">{{ getStatusLabel(status) }}</span>
          </div>
        </div>

        <el-divider />

        <el-table :data="paths" stripe style="width: 100%" v-loading="loading" row-class-name="path-table-row">
          <el-table-column prop="name" label="路径名称" min-width="220" show-overflow-tooltip>
            <template #default="{ row }">
              <div class="path-name-cell">
                <el-icon class="path-type-icon" :color="getPathTypeColor(row.path_type)">
                  <component :is="getPathTypeIcon(row.path_type)" />
                </el-icon>
                <span class="path-name-text">{{ row.name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="actual_value" label="实际值" width="140">
            <template #default="{ row }">
              <span class="actual-value" :class="getValueClass(row.status)">
                {{ row.actual_value ?? '-' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="expected_value" label="期望值" width="120">
            <template #default="{ row }">
              <span class="expected-value">{{ row.expected_value ?? '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <div class="status-cell">
                <span class="status-emoji">{{ getStatusEmoji(row.status) }}</span>
                <el-tag :type="getStatusTagType(row.status)" size="small" effect="dark">
                  {{ getStatusLabel(row.status) }}
                </el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="validated_at" label="验证时间" width="170">
            <template #default="{ row }">
              {{ formatTime(row.validated_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button type="primary" link size="small" :loading="row._validating" @click="revalidatePath(row)">
                  验证
                </el-button>
                <el-button
                  v-if="row.status !== 'normal'"
                  :type="row.status === 'abnormal' ? 'danger' : 'warning'"
                  link
                  size="small"
                  :loading="row._fixing"
                  @click="fixPath(row)"
                >
                  修复
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <el-divider />

        <div class="scan-results-section" v-if="scanResults.length > 0">
          <div class="section-header">
            <span class="section-title">硬编码路径扫描结果</span>
            <el-button type="danger" text size="small" @click="scanResults = []">
              清除
            </el-button>
          </div>
          <el-table :data="scanResults" size="small" style="width: 100%">
            <el-table-column prop="file_path" label="文件路径" min-width="250" show-overflow-tooltip />
            <el-table-column prop="line_number" label="行号" width="70" align="center" />
            <el-table-column prop="hardcoded_path" label="硬编码路径" min-width="200" show-overflow-tooltip>
              <template #default="{ row }">
                <code class="path-code">{{ row.hardcoded_path }}</code>
              </template>
            </el-table-column>
            <el-table-column prop="severity" label="严重程度" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.severity === 'high' ? 'danger' : row.severity === 'medium' ? 'warning' : 'info'" size="small">
                  {{ row.severity === 'high' ? '高' : row.severity === 'medium' ? '中' : '低' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="suggestion" label="建议" min-width="200" show-overflow-tooltip />
          </el-table>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh,
  FolderOpened,
  Document,
  Link,
  Setting,
  Warning,
  CircleClose,
  CircleCheck
} from '@element-plus/icons-vue'

interface PathItem {
  id: string
  name: string
  path_type: 'directory' | 'file' | 'url' | 'config'
  actual_value: string | number | null
  expected_value: string | number | null
  status: 'normal' | 'abnormal' | 'warning'
  validated_at: string
  description?: string
  _validating?: boolean
  _fixing?: boolean
}

interface ScanResult {
  file_path: string
  line_number: number
  hardcoded_path: string
  severity: 'high' | 'medium' | 'low'
  suggestion: string
}

const loading = ref(false)
const validating = ref(false)
const paths = ref<PathItem[]>([])
const scanResults = ref<ScanResult[]>([])

const mockPaths: PathItem[] = [
  { id: '1', name: 'src/components/', path_type: 'directory', actual_value: 'exists', expected_value: 'exists', status: 'normal', validated_at: new Date().toISOString(), description: '组件目录' },
  { id: '2', name: 'src/api/index.ts', path_type: 'file', actual_value: 'exists', expected_value: 'exists', status: 'normal', validated_at: new Date().toISOString(), description: 'API入口文件' },
  { id: '3', name: 'src/stores/dashboard.ts', path_type: 'file', actual_value: 'exists', expected_value: 'exists', status: 'normal', validated_at: new Date().toISOString(), description: 'Dashboard Store' },
  { id: '4', name: '/tmp/cache/', path_type: 'directory', actual_value: 'missing', expected_value: 'exists', status: 'abnormal', validated_at: new Date(Date.now() - 3600000).toISOString(), description: '缓存目录不存在' },
  { id: '5', name: 'http://localhost:3000/api', path_type: 'url', actual_value: 200, expected_value: 200, status: 'normal', validated_at: new Date().toISOString(), description: 'API端点可达' },
  { id: '6', name: '.env.production', path_type: 'config', actual_value: 'missing', expected_value: 'exists', status: 'warning', validated_at: new Date(Date.now() - 7200000).toISOString(), description: '生产环境配置缺失' },
  { id: '7', name: 'dist/build/', path_type: 'directory', actual_value: 'exists', expected_value: 'exists', status: 'normal', validated_at: new Date().toISOString(), description: '构建输出目录' },
  { id: '8', name: 'logs/app.log', path_type: 'file', actual_value: 'permission_denied', expected_value: 'writable', status: 'abnormal', validated_at: new Date(Date.now() - 1800000).toISOString(), description: '日志文件权限异常' },
  { id: '9', name: 'src/router/index.ts', path_type: 'file', actual_value: 'exists', expected_value: 'exists', status: 'normal', validated_at: new Date().toISOString(), description: '路由配置' },
  { id: '10', name: 'node_modules/.package-lock.json', path_type: 'file', actual_value: 'stale', expected_value: 'current', status: 'warning', validated_at: new Date(Date.now() - 86400000).toISOString(), description: '依赖锁文件可能过时' }
]

const mockScanResults: ScanResult[] = [
  { file_path: 'src/utils/config.ts', line_number: 42, hardcoded_path: '/usr/local/data', severity: 'high', suggestion: '使用环境变量或配置文件替代硬编码路径' },
  { file_path: 'src/services/file.ts', line_number: 118, hardcoded_path: 'C:\\Users\\admin\\data\\', severity: 'high', suggestion: '使用相对路径或配置项替代绝对路径' },
  { file_path: 'src/api/request.ts', line_number: 15, hardcoded_path: 'http://192.168.1.100:8080', severity: 'medium', suggestion: '将服务地址提取到环境变量中' },
  { file_path: 'src/components/Upload.vue', line_number: 89, hardcoded_path: '/var/uploads/', severity: 'medium', suggestion: '使用配置项管理上传目录' },
  { file_path: 'src/helpers/path.ts', line_number: 7, hardcoded_path: './../../static/', severity: 'low', suggestion: '考虑使用别名路径或路径常量' }
]

const pathStats = computed(() => {
  const stats: Record<string, number> = { normal: 0, abnormal: 0, warning: 0 }
  paths.value.forEach(p => { stats[p.status] = (stats[p.status] || 0) + 1 })
  return stats
})

const overallStatusType = computed(() => {
  const s = pathStats.value
  if (s.abnormal > 0) return 'danger'
  if (s.warning > 0) return 'warning'
  return 'success'
})

const overallStatusLabel = computed(() => {
  const s = pathStats.value
  if (s.abnormal > 0) return `存在 ${s.abnormal} 个异常`
  if (s.warning > 0) return `${s.warning} 个警告`
  return '全部正常'
})

function loadPaths() {
  loading.value = true
  setTimeout(() => {
    paths.value = mockPaths.map(p => ({ ...p }))
    loading.value = false
  }, 400)
}

async function validateAllPaths() {
  validating.value = true
  try {
    paths.value = paths.value.map(p => ({ ...p, _validating: true }))
    for (let i = 0; i < paths.value.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 200))
      const idx = paths.value.findIndex(p => p.id === mockPaths[i]?.id)
      if (idx >= 0) {
        paths.value[idx] = { ...paths.value[idx], _validating: false, validated_at: new Date().toISOString() }
      }
    }
    ElMessage.success('所有路径验证完成')
  } finally {
    validating.value = false
  }
}

async function revalidatePath(row: PathItem) {
  const idx = paths.value.findIndex(p => p.id === row.id)
  if (idx < 0) return
  paths.value[idx] = { ...paths.value[idx], _validating: true }
  await new Promise(resolve => setTimeout(resolve, 800))
  const statuses: ('normal' | 'abnormal' | 'warning')[] = ['normal', 'normal', 'normal', 'warning']
  const newStatus = statuses[Math.floor(Math.random() * statuses.length)]
  paths.value[idx] = { ...paths.value[idx], _validating: false, status: newStatus, validated_at: new Date().toISOString() }
  ElMessage.success(`"${row.name}" 验证完成`)
}

async function fixPath(row: PathItem) {
  const idx = paths.value.findIndex(p => p.id === row.id)
  if (idx < 0) return
  
  try {
    await ElMessageBox.confirm(
      `确定要修复路径 "${row.name}" 吗？`,
      '确认修复',
      { confirmButtonText: '确定修复', cancelButtonText: '取消', type: 'warning' }
    )
    paths.value[idx] = { ...paths.value[idx], _fixing: true }
    await new Promise(resolve => setTimeout(resolve, 1200))
    paths.value[idx] = { ...paths.value[idx], _fixing: false, status: 'normal', validated_at: new Date().toISOString() }
    ElMessage.success(`"${row.name}" 已修复`)
  } catch {
    // cancelled
  }
}

function runScan() {
  scanResults.value = [...mockScanResults]
  ElMessage.info(`扫描完成，发现 ${mockScanResults.length} 个硬编码路径`)
}

function getStatusEmoji(status: string): string {
  const emojis: Record<string, string> = { normal: '✅', abnormal: '❌', warning: '⚠️' }
  return emojis[status] || '❓'
}

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = { normal: '正常', abnormal: '异常', warning: '警告' }
  return labels[status] || status
}

function getStatusTagType(status: string): '' | 'success' | 'warning' | 'danger' | 'info' {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = { normal: 'success', abnormal: 'danger', warning: 'warning' }
  return types[status] || 'info'
}

function getValueClass(status: string): string {
  const classes: Record<string, string> = { normal: 'value-normal', abnormal: 'value-abnormal', valueWarning: 'value-warning' }
  return classes[`${status === 'warning' ? 'valueWarning' : status}`] || ''
}

function getPathTypeIcon(type: string) {
  const icons: Record<string, any> = { directory: FolderOpened, file: Document, url: Link, config: Setting }
  return icons[type] || Document
}

function getPathTypeColor(type: string): string {
  const colors: Record<string, string> = { directory: '#409eff', file: '#67c23a', url: '#e6a23c', config: '#909399' }
  return colors[type] || '#909399'
}

function formatTime(time: string): string {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  loadPaths()
  runScan()
})
</script>

<style scoped>
.path-validation-status {
  width: 100%;
}

.validation-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title {
  font-size: 18px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.validation-content {
  padding: 5px 0;
}

.summary-bar {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.summary-icon {
  font-size: 16px;
}

.summary-count {
  font-size: 20px;
  font-weight: 700;
}

.stat-normal { color: #67c23a; }
.stat-abnormal { color: #f56c6c; }
.stat-warning { color: #e6a23c; }

.summary-label {
  font-size: 13px;
  color: #606266;
}

.path-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.path-type-icon {
  flex-shrink: 0;
}

.path-name-text {
  font-family: monospace;
  font-size: 13px;
}

.actual-value {
  font-family: monospace;
  font-weight: 500;
  font-size: 13px;
}

.value-normal { color: #303133; }
.value-abnormal { color: #f56c6c; }
.value-warning { color: #e6a23c; }

.expected-value {
  font-family: monospace;
  font-size: 12px;
  color: #909399;
}

.status-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  justify-content: center;
}

.status-emoji {
  font-size: 14px;
}

.action-buttons {
  display: flex;
  gap: 4px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-title {
  font-weight: 600;
  font-size: 15px;
  color: #303133;
}

.scan-results-section {
  padding: 5px 0;
}

.path-code {
  font-family: monospace;
  font-size: 12px;
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  color: #f56c6c;
}

:deep(.path-table-row) {
  cursor: default;
}

@media (max-width: 768px) {
  .summary-bar { gap: 16px; }
  .action-buttons { flex-direction: column; }
}
</style>
