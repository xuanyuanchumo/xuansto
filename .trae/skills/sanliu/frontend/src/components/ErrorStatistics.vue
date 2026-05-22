<template>
  <div class="error-statistics">
    <el-card class="stats-card">
      <template #header>
        <div class="card-header">
          <span class="title">错误统计</span>
          <div class="header-actions">
            <el-select v-model="timeRange" size="small" @change="fetchErrorStats" style="width: 150px;">
              <el-option label="最近1小时" :value="1" />
              <el-option label="最近6小时" :value="6" />
              <el-option label="最近12小时" :value="12" />
              <el-option label="最近24小时" :value="24" />
              <el-option label="最近3天" :value="72" />
              <el-option label="最近7天" :value="168" />
            </el-select>
            <el-button
              type="primary"
              size="small"
              :icon="Refresh"
              @click="fetchErrorStats"
              style="margin-left: 10px;"
            >
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <div class="stats-overview">
        <el-row :gutter="16">
          <el-col :span="6">
            <div class="overview-item">
              <div class="overview-icon error">
                <el-icon><CircleClose /></el-icon>
              </div>
              <div class="overview-content">
                <div class="overview-label">总错误数</div>
                <div class="overview-value">{{ errorStats?.total_errors || 0 }}</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="overview-item">
              <div class="overview-icon rate">
                <el-icon><TrendCharts /></el-icon>
              </div>
              <div class="overview-content">
                <div class="overview-label">错误率</div>
                <div class="overview-value" :class="errorRateClass">
                  {{ errorStats?.error_rate?.toFixed(2) || 0 }}%
                </div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="overview-item">
              <div class="overview-icon type">
                <el-icon><Warning /></el-icon>
              </div>
              <div class="overview-content">
                <div class="overview-label">错误类型</div>
                <div class="overview-value">{{ errorTypeCount }}</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="overview-item">
              <div class="overview-icon endpoint">
                <el-icon><Connection /></el-icon>
              </div>
              <div class="overview-content">
                <div class="overview-label">受影响端点</div>
                <div class="overview-value">{{ affectedEndpoints }}</div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>

      <el-divider />

      <div class="error-details">
        <el-row :gutter="16">
          <el-col :span="12">
            <div class="detail-section">
              <div class="section-title">错误类型分布</div>
              <div class="chart-container" ref="typeChartRef">
                <div v-if="loading" class="chart-loading">
                  <el-icon class="is-loading"><Loading /></el-icon>
                </div>
              </div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="detail-section">
              <div class="section-title">端点错误分布</div>
              <div class="endpoint-list">
                <div
                  v-for="(count, endpoint) in topEndpoints"
                  :key="endpoint"
                  class="endpoint-item"
                >
                  <div class="endpoint-name">{{ endpoint }}</div>
                  <div class="endpoint-count">
                    <el-tag type="danger" size="small">{{ count }}</el-tag>
                  </div>
                </div>
                <el-empty v-if="!Object.keys(topEndpoints).length" description="暂无数据" :image-size="60" />
              </div>
            </div>
          </el-col>
        </el-row>
      </div>

      <el-divider />

      <div class="error-trend">
        <div class="section-title">错误趋势</div>
        <div class="chart-container" ref="trendChartRef">
          <div v-if="loading" class="chart-loading">
            <el-icon class="is-loading"><Loading /></el-icon>
          </div>
        </div>
      </div>

      <el-divider />

      <div class="recent-errors">
        <div class="section-title">最近错误</div>
        <el-table
          :data="errorStats?.recent_errors || []"
          stripe
          max-height="300"
          v-loading="loading"
        >
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="skill_name" label="技能名称" width="150" />
          <el-table-column prop="error_message" label="错误信息" show-overflow-tooltip />
          <el-table-column prop="timestamp" label="时间" width="180">
            <template #default="{ row }">
              {{ formatTime(row.timestamp) }}
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { Refresh, CircleClose, TrendCharts, Warning, Connection, Loading } from '@element-plus/icons-vue'
import api from '@/api'

interface ErrorStats {
  total_errors: number
  error_rate: number
  errors_by_type: Record<string, number>
  errors_by_endpoint: Record<string, number>
  recent_errors: Array<{
    id: string
    skill_name: string
    error_message: string
    timestamp: string
  }>
  error_trend: Array<{
    hour: string
    error_count: number
  }>
}

const timeRange = ref(24)
const loading = ref(false)
const errorStats = ref<ErrorStats | null>(null)
const typeChartRef = ref<HTMLElement | null>(null)
const trendChartRef = ref<HTMLElement | null>(null)

let typeChartInstance: any = null
let trendChartInstance: any = null
let echarts: any = null

const errorRateClass = computed(() => {
  const rate = errorStats.value?.error_rate || 0
  if (rate <= 1) return 'rate-good'
  if (rate <= 5) return 'rate-warning'
  return 'rate-critical'
})

const errorTypeCount = computed(() => {
  return Object.keys(errorStats.value?.errors_by_type || {}).length
})

const affectedEndpoints = computed(() => {
  return Object.keys(errorStats.value?.errors_by_endpoint || {}).length
})

const topEndpoints = computed(() => {
  const endpoints = errorStats.value?.errors_by_endpoint || {}
  const sorted = Object.entries(endpoints)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
  return Object.fromEntries(sorted)
})

const formatTime = (time: string | undefined): string => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const fetchErrorStats = async () => {
  loading.value = true
  try {
    const response = await api.get('/quality/errors', {
      params: { hours: timeRange.value }
    })
    errorStats.value = response

    await nextTick()
    await initCharts()
    updateCharts()
  } catch (error) {
    console.error('Failed to fetch error stats:', error)
  } finally {
    loading.value = false
  }
}

const initCharts = async () => {
  if (!echarts) {
    echarts = await import('echarts')
  }

  if (typeChartRef.value) {
    if (typeChartInstance) {
      typeChartInstance.dispose()
    }
    typeChartInstance = echarts.init(typeChartRef.value)
  }

  if (trendChartRef.value) {
    if (trendChartInstance) {
      trendChartInstance.dispose()
    }
    trendChartInstance = echarts.init(trendChartRef.value)
  }
}

const updateCharts = () => {
  if (typeChartInstance && errorStats.value?.errors_by_type) {
    const data = Object.entries(errorStats.value.errors_by_type)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 10)

    const option = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} ({d}%)'
      },
      series: [
        {
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            show: false
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 14,
              fontWeight: 'bold'
            }
          },
          labelLine: {
            show: false
          },
          data: data
        }
      ]
    }
    typeChartInstance.setOption(option)
  }

  if (trendChartInstance && errorStats.value?.error_trend) {
    const times = errorStats.value.error_trend.map(d => d.hour)
    const values = errorStats.value.error_trend.map(d => d.error_count)

    const option = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          const point = params[0]
          return `${point.name}<br/>错误数: ${point.value}`
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '10%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: times,
        axisLine: { lineStyle: { color: '#ccc' } },
        axisLabel: {
          color: '#666',
          rotate: 45
        }
      },
      yAxis: {
        type: 'value',
        axisLine: { lineStyle: { color: '#ccc' } },
        axisLabel: { color: '#666' },
        splitLine: { lineStyle: { color: '#eee' } }
      },
      series: [
        {
          name: '错误数',
          type: 'bar',
          itemStyle: {
            color: '#f56c6c',
            borderRadius: [4, 4, 0, 0]
          },
          data: values
        }
      ]
    }
    trendChartInstance.setOption(option)
  }
}

const handleResize = () => {
  if (typeChartInstance) {
    typeChartInstance.resize()
  }
  if (trendChartInstance) {
    trendChartInstance.resize()
  }
}

onMounted(async () => {
  await fetchErrorStats()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (typeChartInstance) {
    typeChartInstance.dispose()
    typeChartInstance = null
  }
  if (trendChartInstance) {
    trendChartInstance.dispose()
    trendChartInstance = null
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.error-statistics {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 16px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  align-items: center;
}

.stats-overview {
  padding: 10px 0;
}

.overview-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.overview-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.overview-icon.error {
  background: #fef0f0;
  color: #f56c6c;
}

.overview-icon.rate {
  background: #fdf6ec;
  color: #e6a23c;
}

.overview-icon.type {
  background: #f0f9eb;
  color: #67c23a;
}

.overview-icon.endpoint {
  background: #ecf5ff;
  color: #409eff;
}

.overview-content {
  flex: 1;
}

.overview-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 5px;
}

.overview-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.rate-good { color: #67c23a; }
.rate-warning { color: #e6a23c; }
.rate-critical { color: #f56c6c; }

.error-details {
  padding: 10px 0;
}

.detail-section {
  height: 300px;
}

.section-title {
  font-weight: 500;
  margin-bottom: 15px;
  color: #303133;
  font-size: 14px;
}

.chart-container {
  height: 250px;
  position: relative;
}

.chart-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.endpoint-list {
  max-height: 250px;
  overflow-y: auto;
}

.endpoint-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  margin-bottom: 8px;
  background: #f5f7fa;
  border-radius: 6px;
  transition: all 0.3s;
}

.endpoint-item:hover {
  background: #ecf5ff;
}

.endpoint-name {
  font-size: 13px;
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  margin-right: 10px;
}

.error-trend {
  padding: 10px 0;
}

.recent-errors {
  padding: 10px 0;
}
</style>
