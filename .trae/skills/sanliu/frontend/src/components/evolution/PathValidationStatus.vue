<template>
  <div class="path-validation-status">
    <el-card class="validation-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span class="title">路径验证状态</span>
            <el-tag :type="statusType" effect="dark">
              {{ statusLabel }}
            </el-tag>
          </div>
          <div class="header-actions">
            <el-button type="primary" :loading="validating" @click="runValidation">
              <el-icon><Search /></el-icon>
              验证路径
            </el-button>
            <el-button
              type="warning"
              :disabled="!hasErrors"
              :loading="fixing"
              @click="fixAllErrors"
            >
              <el-icon><Tools /></el-icon>
              一键修复
            </el-button>
          </div>
        </div>
      </template>

      <div class="validation-content">
        <div class="summary-section">
          <el-row :gutter="20">
            <el-col :span="6">
              <div class="summary-item">
                <div class="summary-value">{{ validationData?.total_paths || 0 }}</div>
                <div class="summary-label">总路径数</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="summary-item success">
                <div class="summary-value">{{ validationData?.valid_paths || 0 }}</div>
                <div class="summary-label">有效路径</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="summary-item error">
                <div class="summary-value">{{ validationData?.invalid_paths || 0 }}</div>
                <div class="summary-label">无效路径</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="summary-item warning">
                <div class="summary-value">{{ validationData?.warning_paths || 0 }}</div>
                <div class="summary-label">警告路径</div>
              </div>
            </el-col>
          </el-row>
        </div>

        <el-divider />

        <div class="errors-section" v-if="errorPaths.length > 0">
          <div class="section-header">
            <span class="section-title">错误路径列表</span>
            <el-input
              v-model="searchKeyword"
              placeholder="搜索路径..."
              prefix-icon="Search"
              clearable
              style="width: 250px"
            />
          </div>
          <el-table
            :data="filteredErrorPaths"
            style="width: 100%"
            max-height="400"
            stripe
          >
            <el-table-column prop="path" label="路径" min-width="250">
              <template #default="{ row }">
                <div class="path-cell">
                  <el-icon :color="getPathIconColor(row.status)"><FolderOpened /></el-icon>
                  <span class="path-text">{{ row.path }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="error_type" label="错误类型" width="150">
              <template #default="{ row }">
                <el-tag :type="getErrorTypeTag(row.error_type)" size="small">
                  {{ getErrorTypeLabel(row.error_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="error_message" label="错误信息" min-width="200">
              <template #default="{ row }">
                <el-tooltip :content="row.error_message" placement="top">
                  <span class="error-message">{{ row.error_message }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="can_fix" label="可修复" width="80" align="center">
              <template #default="{ row }">
                <el-icon v-if="row.can_fix" color="#67c23a"><CircleCheck /></el-icon>
                <el-icon v-else color="#909399"><CircleClose /></el-icon>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button
                  v-if="row.can_fix"
                  type="primary"
                  size="small"
                  link
                  @click="fixSinglePath(row)"
                >
                  修复
                </el-button>
                <el-button
                  type="info"
                  size="small"
                  link
                  @click="ignorePath(row)"
                >
                  忽略
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <el-empty v-else description="所有路径验证通过" :image-size="100" />

        <div class="history-section" v-if="repairHistory.length > 0">
          <el-divider />
          <div class="section-header">
            <span class="section-title">修复历史</span>
            <el-button type="primary" link @click="clearHistory">
              清空历史
            </el-button>
          </div>
          <el-timeline>
            <el-timeline-item
              v-for="(item, index) in repairHistory"
              :key="index"
              :type="item.success ? 'success' : 'danger'"
              :timestamp="formatTime(item.timestamp)"
              placement="top"
            >
              <div class="history-item">
                <div class="history-header">
                  <el-tag :type="item.success ? 'success' : 'danger'" size="small">
                    {{ item.success ? '修复成功' : '修复失败' }}
                  </el-tag>
                  <span class="history-action">{{ item.action }}</span>
                </div>
                <div class="history-path">{{ item.path }}</div>
                <div v-if="item.message" class="history-message">{{ item.message }}</div>
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>
      </div>
    </el-card>

    <el-dialog
      v-model="fixDialogVisible"
      title="路径修复预览"
      width="600px"
    >
      <div class="fix-preview">
        <div class="preview-item">
          <span class="preview-label">原路径:</span>
          <span class="preview-value error">{{ currentFixPath?.path }}</span>
        </div>
        <div class="preview-item">
          <span class="preview-label">修复方案:</span>
          <span class="preview-value success">{{ currentFixPath?.suggested_fix }}</span>
        </div>
        <div class="preview-item">
          <span class="preview-label">修复类型:</span>
          <el-tag size="small">{{ getFixTypeLabel(currentFixPath?.fix_type) }}</el-tag>
        </div>
        <div class="preview-item" v-if="currentFixPath?.description">
          <span class="preview-label">说明:</span>
          <span class="preview-value">{{ currentFixPath?.description }}</span>
        </div>
      </div>
      <template #footer>
        <el-button @click="fixDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="fixing" @click="confirmFix">
          确认修复
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Tools,
  FolderOpened,
  CircleCheck,
  CircleClose
} from '@element-plus/icons-vue'
import api from '@/api'

interface ErrorPath {
  id: string
  path: string
  error_type: 'missing' | 'invalid' | 'permission' | 'broken_link' | 'circular'
  error_message: string
  status: 'error' | 'warning'
  can_fix: boolean
  suggested_fix?: string
  fix_type?: 'create' | 'delete' | 'move' | 'update' | 'repair'
  description?: string
}

interface ValidationData {
  total_paths: number
  valid_paths: number
  invalid_paths: number
  warning_paths: number
  last_validated: string
  status: 'valid' | 'invalid' | 'warning'
}

interface RepairHistoryItem {
  timestamp: string
  path: string
  action: string
  success: boolean
  message?: string
}

interface Props {
  skillId?: string
  autoValidate?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  autoValidate: true
})

const emit = defineEmits<{
  (e: 'validation-complete', data: ValidationData): void
  (e: 'path-fixed', path: string): void
  (e: 'error', error: Error): void
}>()

const loading = ref(false)
const validating = ref(false)
const fixing = ref(false)
const searchKeyword = ref('')
const fixDialogVisible = ref(false)
const currentFixPath = ref<ErrorPath | null>(null)

const validationData = ref<ValidationData | null>(null)
const errorPaths = ref<ErrorPath[]>([])
const repairHistory = ref<RepairHistoryItem[]>([])

const hasErrors = computed(() => errorPaths.value.length > 0)

const statusType = computed(() => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    valid: 'success',
    invalid: 'danger',
    warning: 'warning'
  }
  return types[validationData.value?.status || 'valid'] || 'info'
})

const statusLabel = computed(() => {
  const labels: Record<string, string> = {
    valid: '验证通过',
    invalid: '存在错误',
    warning: '存在警告'
  }
  return labels[validationData.value?.status || 'valid'] || '未知'
})

const filteredErrorPaths = computed(() => {
  if (!searchKeyword.value) return errorPaths.value
  const keyword = searchKeyword.value.toLowerCase()
  return errorPaths.value.filter(p =>
    p.path.toLowerCase().includes(keyword) ||
    p.error_message.toLowerCase().includes(keyword)
  )
})

const formatTime = (time: string): string => {
  return new Date(time).toLocaleString('zh-CN')
}

const getPathIconColor = (status: string): string => {
  return status === 'error' ? '#f56c6c' : '#e6a23c'
}

const getErrorTypeTag = (type: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    missing: 'danger',
    invalid: 'danger',
    permission: 'warning',
    broken_link: 'warning',
    circular: 'danger'
  }
  return types[type] || 'info'
}

const getErrorTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    missing: '路径缺失',
    invalid: '无效路径',
    permission: '权限问题',
    broken_link: '断链',
    circular: '循环引用'
  }
  return labels[type] || type
}

const getFixTypeLabel = (type: string | undefined): string => {
  const labels: Record<string, string> = {
    create: '创建路径',
    delete: '删除路径',
    move: '移动路径',
    update: '更新路径',
    repair: '修复路径'
  }
  return labels[type || ''] || '修复'
}

const fetchValidationData = async () => {
  loading.value = true
  try {
    const url = props.skillId
      ? `/path-validation/${props.skillId}`
      : '/path-validation/current'
    const response = await api.get(url)
    validationData.value = (response as any).validation
    errorPaths.value = (response as any).errors || []
  } catch (error) {
    console.error('Failed to fetch validation data:', error)
    emit('error', error as Error)
  } finally {
    loading.value = false
  }
}

const runValidation = async () => {
  validating.value = true
  try {
    const url = props.skillId
      ? `/path-validation/${props.skillId}/validate`
      : '/path-validation/validate'
    const response = await api.post(url)
    validationData.value = (response as any).validation
    errorPaths.value = (response as any).errors || []
    ElMessage.success('路径验证完成')
    emit('validation-complete', validationData.value)
  } catch (error) {
    console.error('Failed to run validation:', error)
    ElMessage.error('路径验证失败')
    emit('error', error as Error)
  } finally {
    validating.value = false
  }
}

const fixSinglePath = (path: ErrorPath) => {
  currentFixPath.value = path
  fixDialogVisible.value = true
}

const confirmFix = async () => {
  if (!currentFixPath.value) return

  fixing.value = true
  try {
    const url = props.skillId
      ? `/path-validation/${props.skillId}/fix`
      : '/path-validation/fix'
    await api.post(url, { path_id: currentFixPath.value.id })

    repairHistory.value.unshift({
      timestamp: new Date().toISOString(),
      path: currentFixPath.value.path,
      action: getFixTypeLabel(currentFixPath.value.fix_type),
      success: true,
      message: '路径已成功修复'
    })

    errorPaths.value = errorPaths.value.filter(p => p.id !== currentFixPath.value!.id)
    if (validationData.value) {
      validationData.value.invalid_paths--
      validationData.value.valid_paths++
    }

    ElMessage.success('路径修复成功')
    emit('path-fixed', currentFixPath.value.path)
    fixDialogVisible.value = false
    currentFixPath.value = null
  } catch (error) {
    console.error('Failed to fix path:', error)

    if (currentFixPath.value) {
      repairHistory.value.unshift({
        timestamp: new Date().toISOString(),
        path: currentFixPath.value.path,
        action: getFixTypeLabel(currentFixPath.value.fix_type),
        success: false,
        message: '修复失败'
      })
    }

    ElMessage.error('路径修复失败')
  } finally {
    fixing.value = false
  }
}

const fixAllErrors = async () => {
  const fixablePaths = errorPaths.value.filter(p => p.can_fix)
  if (fixablePaths.length === 0) {
    ElMessage.warning('没有可自动修复的路径')
    return
  }

  try {
    await ElMessageBox.confirm(
      `将自动修复 ${fixablePaths.length} 个路径，是否继续？`,
      '批量修复确认',
      { type: 'warning' }
    )

    fixing.value = true
    const url = props.skillId
      ? `/path-validation/${props.skillId}/fix-all`
      : '/path-validation/fix-all'
    const response = await api.post(url)

    const results = (response as any).results || []
    let successCount = 0
    let failCount = 0

    results.forEach((r: any) => {
      repairHistory.value.unshift({
        timestamp: new Date().toISOString(),
        path: r.path,
        action: '批量修复',
        success: r.success,
        message: r.message
      })
      if (r.success) successCount++
      else failCount++
    })

    errorPaths.value = errorPaths.value.filter(p => !p.can_fix || !results.find((r: any) => r.path_id === p.id && r.success))
    if (validationData.value) {
      validationData.value.invalid_paths -= successCount
      validationData.value.valid_paths += successCount
    }

    ElMessage.success(`批量修复完成：成功 ${successCount} 个，失败 ${failCount} 个`)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to fix all paths:', error)
      ElMessage.error('批量修复失败')
    }
  } finally {
    fixing.value = false
  }
}

const ignorePath = async (path: ErrorPath) => {
  try {
    await ElMessageBox.confirm(
      `确定要忽略此路径错误吗？路径：${path.path}`,
      '忽略确认',
      { type: 'warning' }
    )

    const url = props.skillId
      ? `/path-validation/${props.skillId}/ignore`
      : '/path-validation/ignore'
    await api.post(url, { path_id: path.id })

    errorPaths.value = errorPaths.value.filter(p => p.id !== path.id)
    ElMessage.success('已忽略此路径错误')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to ignore path:', error)
    }
  }
}

const clearHistory = () => {
  repairHistory.value = []
  ElMessage.success('修复历史已清空')
}

onMounted(() => {
  fetchValidationData()
  if (props.autoValidate) {
    runValidation()
  }
})
</script>

<style scoped>
.path-validation-status {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.title {
  font-size: 16px;
  font-weight: 600;
}

.validation-content {
  padding: 10px 0;
}

.summary-section {
  padding: 10px 0;
}

.summary-item {
  text-align: center;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.summary-item.success { background: #f0f9eb; }
.summary-item.error { background: #fef0f0; }
.summary-item.warning { background: #fdf6ec; }

.summary-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
}

.summary-item.success .summary-value { color: #67c23a; }
.summary-item.error .summary-value { color: #f56c6c; }
.summary-item.warning .summary-value { color: #e6a23c; }

.summary-label {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.section-title {
  font-weight: 500;
  color: #303133;
}

.path-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.path-text {
  font-family: monospace;
  font-size: 13px;
}

.error-message {
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
  max-width: 200px;
}

.history-item {
  padding: 5px 0;
}

.history-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 5px;
}

.history-action {
  font-weight: 500;
}

.history-path {
  font-family: monospace;
  font-size: 13px;
  color: #606266;
  margin-bottom: 5px;
}

.history-message {
  font-size: 12px;
  color: #909399;
}

.fix-preview {
  padding: 10px 0;
}

.preview-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 15px;
}

.preview-label {
  width: 80px;
  color: #909399;
  flex-shrink: 0;
}

.preview-value {
  flex: 1;
  font-family: monospace;
  word-break: break-all;
}

.preview-value.error { color: #f56c6c; }
.preview-value.success { color: #67c23a; }
</style>
