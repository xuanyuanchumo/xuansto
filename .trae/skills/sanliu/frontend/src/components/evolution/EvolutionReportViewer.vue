<template>
  <div class="evolution-report-viewer" :class="{ 'dark-theme': isDarkTheme }">
    <el-card class="report-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="report-icon"><Document /></el-icon>
            <span class="title">演化报告</span>
            <el-tag v-if="report" :type="reportStatusType" size="small">
              {{ reportStatusLabel }}
            </el-tag>
          </div>
          <div class="header-actions">
            <el-select
              v-model="selectedReportId"
              placeholder="选择报告"
              size="small"
              filterable
              @change="loadReport"
              style="width: 200px"
            >
              <el-option
                v-for="r in reportList"
                :key="r.id"
                :label="`${r.id} - ${formatTime(r.created_at)}`"
                :value="r.id"
              >
                <div class="report-option">
                  <span>{{ r.id }}</span>
                  <el-tag size="small" :type="r.success ? 'success' : 'danger'">
                    {{ r.success ? '成功' : '失败' }}
                  </el-tag>
                </div>
              </el-option>
            </el-select>
            <el-button-group>
              <el-button size="small" @click="showCompareDialog" :disabled="!report">
                <el-icon><Sort /></el-icon>
                对比
              </el-button>
              <el-button size="small" @click="exportReport('json')" :disabled="!report">
                <el-icon><Download /></el-icon>
                导出JSON
              </el-button>
              <el-button size="small" @click="exportReport('pdf')" :disabled="!report">
                <el-icon><Document /></el-icon>
                导出PDF
              </el-button>
            </el-button-group>
          </div>
        </div>
      </template>

      <div v-if="loading" class="loading-container">
        <el-icon class="is-loading" :size="40"><Loading /></el-icon>
        <span>加载中...</span>
      </div>

      <div v-else-if="!report" class="empty-container">
        <el-empty description="请选择一个演化报告查看" :image-size="100" />
      </div>

      <div v-else class="report-content">
        <div class="report-summary">
          <el-descriptions :column="4" border>
            <el-descriptions-item label="报告ID">{{ report.id }}</el-descriptions-item>
            <el-descriptions-item label="演化类型">
              <el-tag size="small">{{ getEvolutionTypeLabel(report.evolution_type) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="执行状态">
              <el-tag :type="report.success ? 'success' : 'danger'" size="small">
                {{ report.success ? '成功' : '失败' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="执行时间">{{ formatDuration(report.duration) }}</el-descriptions-item>
            <el-descriptions-item label="开始时间">{{ formatTime(report.started_at) }}</el-descriptions-item>
            <el-descriptions-item label="结束时间">{{ formatTime(report.completed_at) }}</el-descriptions-item>
            <el-descriptions-item label="触发方式">
              <el-tag size="small" type="info">{{ getTriggerLabel(report.trigger_type) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="触发人">{{ report.triggered_by || '系统' }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <el-divider />

        <div class="report-section">
          <div class="section-header">
            <span class="section-title">演化摘要</span>
          </div>
          <div class="summary-content">
            <el-row :gutter="20">
              <el-col :span="6">
                <div class="summary-item">
                  <div class="summary-label">变更数量</div>
                  <div class="summary-value">{{ report.changes_count }}</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="summary-item">
                  <div class="summary-label">成功变更</div>
                  <div class="summary-value success">{{ report.successful_changes }}</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="summary-item">
                  <div class="summary-label">失败变更</div>
                  <div class="summary-value danger">{{ report.failed_changes }}</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="summary-item">
                  <div class="summary-label">影响技能</div>
                  <div class="summary-value">{{ report.affected_skills.length }}</div>
                </div>
              </el-col>
            </el-row>
          </div>
        </div>

        <el-divider />

        <div class="report-section">
          <div class="section-header">
            <span class="section-title">变更详情</span>
            <el-radio-group v-model="changeViewMode" size="small">
              <el-radio-button label="list">列表</el-radio-button>
              <el-radio-button label="timeline">时间线</el-radio-button>
            </el-radio-group>
          </div>

          <div v-if="changeViewMode === 'list'" class="changes-list">
            <el-table :data="report.changes" border stripe max-height="400">
              <el-table-column prop="type" label="变更类型" width="120">
                <template #default="{ row }">
                  <el-tag size="small">{{ getChangeTypeLabel(row.type) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="target" label="目标" width="150" show-overflow-tooltip />
              <el-table-column prop="description" label="描述" show-overflow-tooltip />
              <el-table-column prop="status" label="状态" width="80">
                <template #default="{ row }">
                  <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
                    {{ row.status === 'success' ? '成功' : '失败' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="duration" label="耗时" width="100">
                <template #default="{ row }">
                  {{ formatDuration(row.duration) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100" fixed="right">
                <template #default="{ row }">
                  <el-button type="primary" link size="small" @click="viewChangeDetail(row)">
                    详情
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <div v-else class="changes-timeline">
            <el-timeline>
              <el-timeline-item
                v-for="(change, index) in report.changes"
                :key="index"
                :type="change.status === 'success' ? 'success' : 'danger'"
                :timestamp="formatTime(change.timestamp)"
                placement="top"
              >
                <el-card class="timeline-card">
                  <div class="timeline-header">
                    <el-tag size="small">{{ getChangeTypeLabel(change.type) }}</el-tag>
                    <el-tag :type="change.status === 'success' ? 'success' : 'danger'" size="small">
                      {{ change.status === 'success' ? '成功' : '失败' }}
                    </el-tag>
                  </div>
                  <div class="timeline-target">{{ change.target }}</div>
                  <div class="timeline-description">{{ change.description }}</div>
                  <div v-if="change.error_message" class="timeline-error">
                    <el-alert type="error" :closable="false" show-icon>
                      {{ change.error_message }}
                    </el-alert>
                  </div>
                </el-card>
              </el-timeline-item>
            </el-timeline>
          </div>
        </div>

        <el-divider />

        <div class="report-section">
          <div class="section-header">
            <span class="section-title">调用链</span>
            <el-button type="primary" link size="small" @click="expandCallChain">
              展开全部
            </el-button>
          </div>
          <div class="call-chain-container" ref="callChainContainer">
            <div v-if="callChainLoading" class="chart-loading">
              <el-icon class="is-loading"><Loading /></el-icon>
            </div>
          </div>
        </div>

        <el-divider />

        <div class="report-section">
          <div class="section-header">
            <span class="section-title">性能指标</span>
          </div>
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="metric-card">
                <div class="metric-header">
                  <span class="metric-title">执行前</span>
                </div>
                <div class="metric-values">
                  <div class="metric-item">
                    <span class="metric-label">成功率</span>
                    <span class="metric-value">{{ report.metrics.before.success_rate.toFixed(1) }}%</span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-label">平均响应</span>
                    <span class="metric-value">{{ report.metrics.before.avg_response_time }}ms</span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-label">吞吐量</span>
                    <span class="metric-value">{{ report.metrics.before.throughput }}/s</span>
                  </div>
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="metric-card highlight">
                <div class="metric-header">
                  <span class="metric-title">变化</span>
                </div>
                <div class="metric-values">
                  <div class="metric-item">
                    <span class="metric-label">成功率</span>
                    <span class="metric-value" :class="getMetricChangeClass(report.metrics.change.success_rate)">
                      {{ formatChange(report.metrics.change.success_rate) }}
                    </span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-label">平均响应</span>
                    <span class="metric-value" :class="getMetricChangeClass(-report.metrics.change.avg_response_time)">
                      {{ formatChange(report.metrics.change.avg_response_time) }}
                    </span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-label">吞吐量</span>
                    <span class="metric-value" :class="getMetricChangeClass(report.metrics.change.throughput)">
                      {{ formatChange(report.metrics.change.throughput) }}
                    </span>
                  </div>
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="metric-card">
                <div class="metric-header">
                  <span class="metric-title">执行后</span>
                </div>
                <div class="metric-values">
                  <div class="metric-item">
                    <span class="metric-label">成功率</span>
                    <span class="metric-value">{{ report.metrics.after.success_rate.toFixed(1) }}%</span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-label">平均响应</span>
                    <span class="metric-value">{{ report.metrics.after.avg_response_time }}ms</span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-label">吞吐量</span>
                    <span class="metric-value">{{ report.metrics.after.throughput }}/s</span>
                  </div>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
      </div>
    </el-card>

    <el-dialog
      v-model="compareDialogVisible"
      title="报告对比"
      width="90%"
      top="5vh"
      destroy-on-close
    >
      <div class="compare-container">
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="compare-panel">
              <div class="compare-header">
                <span class="compare-title">基准报告</span>
                <el-select v-model="compareBaseId" size="small" @change="loadCompareBase">
                  <el-option
                    v-for="r in reportList"
                    :key="r.id"
                    :label="r.id"
                    :value="r.id"
                  />
                </el-select>
              </div>
              <div v-if="compareBase" class="compare-content">
                <ReportCompareView :report="compareBase" />
              </div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="compare-panel">
              <div class="compare-header">
                <span class="compare-title">对比报告</span>
                <el-select v-model="compareTargetId" size="small" @change="loadCompareTarget">
                  <el-option
                    v-for="r in reportList"
                    :key="r.id"
                    :label="r.id"
                    :value="r.id"
                  />
                </el-select>
              </div>
              <div v-if="compareTarget" class="compare-content">
                <ReportCompareView :report="compareTarget" />
              </div>
            </div>
          </el-col>
        </el-row>
        <div v-if="compareBase && compareTarget" class="compare-diff">
          <el-divider>差异对比</el-divider>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="成功率变化">
              <span :class="getMetricChangeClass(compareTarget.metrics.after.success_rate - compareBase.metrics.after.success_rate)">
                {{ formatChange(compareTarget.metrics.after.success_rate - compareBase.metrics.after.success_rate) }}
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="响应时间变化">
              <span :class="getMetricChangeClass(-(compareTarget.metrics.after.avg_response_time - compareBase.metrics.after.avg_response_time))">
                {{ formatChange(compareTarget.metrics.after.avg_response_time - compareBase.metrics.after.avg_response_time) }}ms
              </span>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </el-dialog>

    <el-dialog
      v-model="changeDetailVisible"
      title="变更详情"
      width="600px"
      destroy-on-close
    >
      <div v-if="selectedChange" class="change-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="变更类型">{{ getChangeTypeLabel(selectedChange.type) }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="selectedChange.status === 'success' ? 'success' : 'danger'" size="small">
              {{ selectedChange.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="目标" :span="2">{{ selectedChange.target }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ selectedChange.description }}</el-descriptions-item>
          <el-descriptions-item label="耗时">{{ formatDuration(selectedChange.duration) }}</el-descriptions-item>
          <el-descriptions-item label="时间">{{ formatTime(selectedChange.timestamp) }}</el-descriptions-item>
        </el-descriptions>
        <div v-if="selectedChange.before_after" class="before-after">
          <div class="ba-title">变更前后对比</div>
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="ba-panel">
                <div class="ba-label">变更前</div>
                <pre class="ba-code">{{ selectedChange.before_after.before }}</pre>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="ba-panel">
                <div class="ba-label">变更后</div>
                <pre class="ba-code">{{ selectedChange.before_after.after }}</pre>
              </div>
            </el-col>
          </el-row>
        </div>
        <div v-if="selectedChange.error_message" class="error-section">
          <el-alert type="error" :closable="false" show-icon>
            <template #title>错误信息</template>
            {{ selectedChange.error_message }}
          </el-alert>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, defineComponent, h } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Document,
  Download,
  Sort,
  Loading
} from '@element-plus/icons-vue'
import api from '@/api'

interface ReportListItem {
  id: string
  created_at: string
  success: boolean
}

interface Change {
  type: string
  target: string
  description: string
  status: 'success' | 'failed'
  duration: number
  timestamp: string
  error_message?: string
  before_after?: {
    before: string
    after: string
  }
}

interface Metrics {
  success_rate: number
  avg_response_time: number
  throughput: number
}

interface EvolutionReport {
  id: string
  evolution_type: string
  trigger_type: string
  triggered_by: string | null
  started_at: string
  completed_at: string
  duration: number
  success: boolean
  changes_count: number
  successful_changes: number
  failed_changes: number
  affected_skills: string[]
  changes: Change[]
  metrics: {
    before: Metrics
    after: Metrics
    change: {
      success_rate: number
      avg_response_time: number
      throughput: number
    }
  }
  call_chain: any
}

const ReportCompareView = defineComponent({
  name: 'ReportCompareView',
  props: {
    report: {
      type: Object as () => EvolutionReport,
      required: true
    }
  },
  setup(props) {
    return () => h('div', { class: 'report-compare-view' }, [
      h('el-descriptions', { column: 1, border: true, size: 'small' }, () => [
        h('el-descriptions-item', { label: '演化类型' }, () => props.report.evolution_type),
        h('el-descriptions-item', { label: '执行状态' }, () =>
          h('el-tag', {
            type: props.report.success ? 'success' : 'danger',
            size: 'small'
          }, props.report.success ? '成功' : '失败')
        ),
        h('el-descriptions-item', { label: '变更数量' }, () => `${props.report.changes_count} 次`),
        h('el-descriptions-item', { label: '成功率' }, () =>
          `${props.report.metrics.after.success_rate.toFixed(1)}%`
        ),
        h('el-descriptions-item', { label: '平均响应' }, () =>
          `${props.report.metrics.after.avg_response_time}ms`
        )
      ])
    ])
  }
})

interface Props {
  projectId?: number
  reportId?: string
  isDarkTheme?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isDarkTheme: false
})

const emit = defineEmits<{
  (e: 'report-loaded', report: EvolutionReport): void
  (e: 'export', format: string, report: EvolutionReport): void
}>()

const loading = ref(false)
const callChainLoading = ref(false)
const selectedReportId = ref(props.reportId || '')
const changeViewMode = ref<'list' | 'timeline'>('list')
const changeDetailVisible = ref(false)
const selectedChange = ref<Change | null>(null)
const compareDialogVisible = ref(false)
const compareBaseId = ref('')
const compareTargetId = ref('')
const compareBase = ref<EvolutionReport | null>(null)
const compareTarget = ref<EvolutionReport | null>(null)

const reportList = ref<ReportListItem[]>([])
const report = ref<EvolutionReport | null>(null)
const callChainContainer = ref<HTMLElement | null>(null)

let callChainEchartsInstance: any = null
let echarts: any = null

const reportStatusType = computed(() => {
  if (!report.value) return 'info'
  return report.value.success ? 'success' : 'danger'
})

const reportStatusLabel = computed(() => {
  if (!report.value) return ''
  return report.value.success ? '成功' : '失败'
})

const getEvolutionTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    skill_optimization: '技能优化',
    workflow_adaptation: '工作流适配',
    resource_rebalance: '资源重平衡',
    knowledge_update: '知识更新',
    performance_tuning: '性能调优',
    security_enhancement: '安全加固'
  }
  return labels[type] || type
}

const getTriggerLabel = (type: string): string => {
  const labels: Record<string, string> = {
    auto: '自动触发',
    manual: '手动触发',
    scheduled: '定时触发',
    api: 'API调用'
  }
  return labels[type] || type
}

const getChangeTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    code_update: '代码更新',
    config_change: '配置变更',
    skill_modify: '技能修改',
    workflow_update: '工作流更新',
    resource_adjust: '资源调整'
  }
  return labels[type] || type
}

const formatTime = (time: string): string => {
  return new Date(time).toLocaleString('zh-CN')
}

const formatDuration = (ms: number): string => {
  if (!ms) return '-'
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${(ms / 60000).toFixed(1)}min`
}

const formatChange = (value: number): string => {
  const prefix = value > 0 ? '+' : ''
  return `${prefix}${value.toFixed(1)}`
}

const getMetricChangeClass = (value: number): string => {
  if (value > 0) return 'metric-up'
  if (value < 0) return 'metric-down'
  return 'metric-stable'
}

const loadReport = async () => {
  if (!selectedReportId.value) return

  loading.value = true
  try {
    const params: Record<string, any> = {}
    if (props.projectId) {
      params.project_id = props.projectId
    }

    const response = await api.get(`/evolution-monitor/reports/${selectedReportId.value}`, { params })
    report.value = response.data as EvolutionReport
    emit('report-loaded', report.value)

    await nextTick()
    await renderCallChain()
  } catch (error) {
    console.error('Failed to load report:', error)
    ElMessage.error('加载报告失败')
  } finally {
    loading.value = false
  }
}

const fetchReportList = async () => {
  try {
    const params: Record<string, any> = {}
    if (props.projectId) {
      params.project_id = props.projectId
    }

    const response = await api.get('/evolution-monitor/reports', { params })
    reportList.value = response.data as ReportListItem[]

    if (reportList.value.length > 0 && !selectedReportId.value) {
      selectedReportId.value = reportList.value[0].id
      await loadReport()
    }
  } catch (error) {
    console.error('Failed to fetch report list:', error)
  }
}

const renderCallChain = async () => {
  if (!callChainContainer.value || !report.value?.call_chain) return

  callChainLoading.value = true
  try {
    if (!echarts) {
      echarts = await import('echarts')
    }

    if (callChainEchartsInstance) {
      callChainEchartsInstance.dispose()
    }

    callChainEchartsInstance = echarts.init(
      callChainContainer.value,
      props.isDarkTheme ? 'dark' : undefined
    )

    const data = report.value.call_chain
    const option = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        backgroundColor: props.isDarkTheme ? '#1f1f1f' : '#fff',
        borderColor: props.isDarkTheme ? '#333' : '#ddd',
        textStyle: {
          color: props.isDarkTheme ? '#fff' : '#333'
        }
      },
      series: [
        {
          type: 'tree',
          data: [data],
          left: '10%',
          right: '10%',
          top: '10%',
          bottom: '10%',
          symbol: 'rect',
          symbolSize: [120, 30],
          orient: 'vertical',
          expandAndCollapse: true,
          label: {
            position: 'inside',
            verticalAlign: 'middle',
            align: 'center',
            fontSize: 12,
            color: props.isDarkTheme ? '#fff' : '#333'
          },
          leaves: {
            label: {
              position: 'inside'
            }
          },
          animationDuration: 550,
          animationDurationUpdate: 750
        }
      ]
    }

    callChainEchartsInstance.setOption(option)
  } catch (error) {
    console.error('Failed to render call chain:', error)
  } finally {
    callChainLoading.value = false
  }
}

const expandCallChain = () => {
  if (callChainEchartsInstance) {
    callChainEchartsInstance.dispatchAction({
      type: 'treeExpandAndCollapse',
      seriesIndex: 0,
      dataIndex: 0
    })
  }
}

const viewChangeDetail = (change: Change) => {
  selectedChange.value = change
  changeDetailVisible.value = true
}

const showCompareDialog = () => {
  if (reportList.value.length < 2) {
    ElMessage.warning('至少需要两个报告才能进行对比')
    return
  }
  compareBaseId.value = selectedReportId.value
  compareTargetId.value = reportList.value.find(r => r.id !== selectedReportId.value)?.id || ''
  loadCompareBase()
  loadCompareTarget()
  compareDialogVisible.value = true
}

const loadCompareBase = async () => {
  if (!compareBaseId.value) return
  try {
    const response = await api.get(`/evolution-monitor/reports/${compareBaseId.value}`)
    compareBase.value = response.data as EvolutionReport
  } catch (error) {
    console.error('Failed to load compare base:', error)
  }
}

const loadCompareTarget = async () => {
  if (!compareTargetId.value) return
  try {
    const response = await api.get(`/evolution-monitor/reports/${compareTargetId.value}`)
    compareTarget.value = response.data as EvolutionReport
  } catch (error) {
    console.error('Failed to load compare target:', error)
  }
}

const exportReport = async (format: 'json' | 'pdf') => {
  if (!report.value) return

  try {
    if (format === 'json') {
      const blob = new Blob([JSON.stringify(report.value, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `evolution-report-${report.value.id}.json`
      a.click()
      URL.revokeObjectURL(url)
      ElMessage.success('JSON导出成功')
    } else {
      const response = await api.get(`/evolution-monitor/reports/${report.value.id}/export/pdf`, {
        responseType: 'blob'
      })
      const blob = new Blob([response as any], { type: 'application/pdf' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `evolution-report-${report.value.id}.pdf`
      a.click()
      URL.revokeObjectURL(url)
      ElMessage.success('PDF导出成功')
    }
    emit('export', format, report.value)
  } catch (error) {
    console.error('Failed to export report:', error)
    ElMessage.error('导出失败')
  }
}

const handleResize = () => {
  if (callChainEchartsInstance) {
    callChainEchartsInstance.resize()
  }
}

onMounted(() => {
  fetchReportList()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (callChainEchartsInstance) {
    callChainEchartsInstance.dispose()
    callChainEchartsInstance = null
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.evolution-report-viewer {
  width: 100%;
}

.report-card {
  transition: all 0.3s ease;
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

.report-icon {
  font-size: 20px;
  color: #409eff;
}

.title {
  font-size: 16px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.report-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.loading-container,
.empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  gap: 15px;
  color: #909399;
}

.report-content {
  padding: 10px 0;
}

.report-summary {
  margin-bottom: 10px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.section-title {
  font-weight: 500;
  font-size: 14px;
  color: #303133;
}

.summary-content {
  margin-bottom: 10px;
}

.summary-item {
  text-align: center;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.dark-theme .summary-item {
  background: #2d2d2d;
}

.summary-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.summary-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.dark-theme .summary-value {
  color: #e0e0e0;
}

.summary-value.success {
  color: #67c23a;
}

.summary-value.danger {
  color: #f56c6c;
}

.changes-list {
  margin-top: 10px;
}

.changes-timeline {
  max-height: 500px;
  overflow-y: auto;
}

.timeline-card {
  margin-bottom: 0;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.timeline-target {
  font-weight: 500;
  margin-bottom: 5px;
}

.timeline-description {
  font-size: 13px;
  color: #606266;
}

.timeline-error {
  margin-top: 10px;
}

.call-chain-container {
  height: 300px;
  position: relative;
  border: 1px solid #ebeef5;
  border-radius: 8px;
}

.dark-theme .call-chain-container {
  border-color: #3d3d3d;
}

.chart-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #909399;
}

.metric-card {
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.dark-theme .metric-card {
  background: #2d2d2d;
}

.metric-card.highlight {
  background: #ecf5ff;
  border: 1px solid #b3d8ff;
}

.dark-theme .metric-card.highlight {
  background: #1a3a5c;
  border-color: #2d5a8c;
}

.metric-header {
  margin-bottom: 10px;
}

.metric-title {
  font-weight: 500;
  font-size: 14px;
}

.metric-values {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.metric-label {
  font-size: 12px;
  color: #909399;
}

.metric-value {
  font-size: 14px;
  font-weight: 500;
}

.metric-up {
  color: #67c23a;
}

.metric-down {
  color: #f56c6c;
}

.metric-stable {
  color: #909399;
}

.compare-container {
  min-height: 400px;
}

.compare-panel {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 15px;
}

.dark-theme .compare-panel {
  border-color: #3d3d3d;
}

.compare-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.compare-title {
  font-weight: 500;
}

.compare-content {
  max-height: 300px;
  overflow-y: auto;
}

.compare-diff {
  margin-top: 20px;
}

.change-detail {
  padding: 10px 0;
}

.before-after {
  margin-top: 20px;
}

.ba-title {
  font-weight: 500;
  margin-bottom: 10px;
}

.ba-panel {
  background: #f5f7fa;
  border-radius: 8px;
  overflow: hidden;
}

.dark-theme .ba-panel {
  background: #2d2d2d;
}

.ba-label {
  padding: 8px 12px;
  background: #e4e7ed;
  font-size: 12px;
  font-weight: 500;
}

.dark-theme .ba-label {
  background: #3d3d3d;
}

.ba-code {
  margin: 0;
  padding: 12px;
  font-size: 12px;
  font-family: monospace;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
}

.error-section {
  margin-top: 15px;
}

@media (max-width: 1200px) {
  .header-actions {
    flex-wrap: wrap;
  }
}

@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    gap: 15px;
  }

  .header-actions {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
