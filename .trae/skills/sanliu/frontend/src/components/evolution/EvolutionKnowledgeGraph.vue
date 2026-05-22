<template>
  <div class="evolution-knowledge-graph">
    <el-row :gutter="20">
      <el-col :span="16">
        <el-card class="graph-card">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <span class="title">演化模式网络图</span>
                <el-tag type="info" size="small">
                  {{ graphData?.nodes?.length || 0 }} 节点 / {{ graphData?.edges?.length || 0 }} 连接
                </el-tag>
              </div>
              <div class="header-actions">
                <el-select v-model="selectedCategory" placeholder="筛选类别" clearable size="small" style="width: 120px">
                  <el-option label="全部" value="" />
                  <el-option label="优化" value="optimization" />
                  <el-option label="适配" value="adaptation" />
                  <el-option label="修复" value="repair" />
                  <el-option label="增强" value="enhancement" />
                </el-select>
                <el-button-group>
                  <el-button size="small" @click="zoomIn">
                    <el-icon><ZoomIn /></el-icon>
                  </el-button>
                  <el-button size="small" @click="zoomOut">
                    <el-icon><ZoomOut /></el-icon>
                  </el-button>
                  <el-button size="small" @click="resetZoom">
                    <el-icon><RefreshRight /></el-icon>
                  </el-button>
                </el-button-group>
              </div>
            </div>
          </template>

          <div class="graph-container" ref="graphContainer">
            <div v-if="loading" class="graph-loading">
              <el-icon class="is-loading"><Loading /></el-icon>
              <span>加载中...</span>
            </div>
          </div>

          <div class="graph-legend">
            <div class="legend-item">
              <span class="legend-dot optimization"></span>
              <span>优化模式</span>
            </div>
            <div class="legend-item">
              <span class="legend-dot adaptation"></span>
              <span>适配模式</span>
            </div>
            <div class="legend-item">
              <span class="legend-dot repair"></span>
              <span>修复模式</span>
            </div>
            <div class="legend-item">
              <span class="legend-dot enhancement"></span>
              <span>增强模式</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="recommendations-card">
          <template #header>
            <div class="card-header">
              <span class="title">演化推荐</span>
              <el-button type="primary" size="small" @click="refreshRecommendations">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>

          <div class="recommendations-list">
            <div
              v-for="(rec, index) in recommendations"
              :key="index"
              class="recommendation-item"
              @click="selectRecommendation(rec)"
            >
              <div class="rec-header">
                <el-tag :type="getCategoryType(rec.category)" size="small">
                  {{ getCategoryLabel(rec.category) }}
                </el-tag>
                <span class="rec-confidence">置信度: {{ (rec.confidence * 100).toFixed(0) }}%</span>
              </div>
              <div class="rec-title">{{ rec.title }}</div>
              <div class="rec-desc">{{ rec.description }}</div>
              <div class="rec-impact">
                <span class="impact-label">预期影响:</span>
                <el-progress
                  :percentage="rec.impact_score"
                  :stroke-width="6"
                  :color="getImpactColor(rec.impact_score)"
                />
              </div>
            </div>
            <el-empty v-if="recommendations.length === 0" description="暂无推荐" :image-size="60" />
          </div>
        </el-card>

        <el-card class="prediction-card" style="margin-top: 20px">
          <template #header>
            <span class="title">演化效果预测</span>
          </template>

          <div v-if="selectedPrediction" class="prediction-content">
            <div class="prediction-item">
              <span class="pred-label">预测成功率</span>
              <el-progress
                :percentage="selectedPrediction.success_rate * 100"
                :stroke-width="15"
                :color="getSuccessColor(selectedPrediction.success_rate)"
              >
                <span>{{ (selectedPrediction.success_rate * 100).toFixed(1) }}%</span>
              </el-progress>
            </div>
            <div class="prediction-metrics">
              <div class="metric-row">
                <span class="metric-label">性能提升</span>
                <span class="metric-value" :class="{ positive: selectedPrediction.performance_gain > 0 }">
                  {{ selectedPrediction.performance_gain > 0 ? '+' : '' }}{{ selectedPrediction.performance_gain.toFixed(1) }}%
                </span>
              </div>
              <div class="metric-row">
                <span class="metric-label">稳定性变化</span>
                <span class="metric-value" :class="{ positive: selectedPrediction.stability_change > 0 }">
                  {{ selectedPrediction.stability_change > 0 ? '+' : '' }}{{ selectedPrediction.stability_change.toFixed(1) }}%
                </span>
              </div>
              <div class="metric-row">
                <span class="metric-label">风险等级</span>
                <el-tag :type="getRiskType(selectedPrediction.risk_level)" size="small">
                  {{ getRiskLabel(selectedPrediction.risk_level) }}
                </el-tag>
              </div>
              <div class="metric-row">
                <span class="metric-label">预计耗时</span>
                <span class="metric-value">{{ formatDuration(selectedPrediction.estimated_duration) }}</span>
              </div>
            </div>
            <el-button
              type="primary"
              :loading="triggering"
              :disabled="!selectedPrediction.can_execute"
              @click="triggerEvolution"
              style="width: 100%; margin-top: 15px"
            >
              <el-icon><VideoPlay /></el-icon>
              触发演化
            </el-button>
          </div>
          <el-empty v-else description="选择推荐查看预测" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>

    <el-dialog
      v-model="nodeDetailVisible"
      :title="selectedNode?.name"
      width="500px"
    >
      <div class="node-detail" v-if="selectedNode">
        <div class="detail-row">
          <span class="detail-label">类型</span>
          <el-tag :type="getCategoryType(selectedNode.category)">
            {{ getCategoryLabel(selectedNode.category) }}
          </el-tag>
        </div>
        <div class="detail-row">
          <span class="detail-label">描述</span>
          <span class="detail-value">{{ selectedNode.description }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">应用次数</span>
          <span class="detail-value">{{ selectedNode.apply_count }} 次</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">成功率</span>
          <el-progress
            :percentage="selectedNode.success_rate * 100"
            :stroke-width="10"
            :color="getSuccessColor(selectedNode.success_rate)"
          />
        </div>
        <div class="detail-row">
          <span class="detail-label">相关模式</span>
          <div class="related-patterns">
            <el-tag
              v-for="p in selectedNode.related_patterns"
              :key="p"
              size="small"
              style="margin-right: 5px"
            >
              {{ p }}
            </el-tag>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  ZoomIn,
  ZoomOut,
  RefreshRight,
  Refresh,
  VideoPlay,
  Loading
} from '@element-plus/icons-vue'
import api from '@/api'

interface GraphNode {
  id: string
  name: string
  category: 'optimization' | 'adaptation' | 'repair' | 'enhancement'
  description: string
  apply_count: number
  success_rate: number
  related_patterns: string[]
  x?: number
  y?: number
}

interface GraphEdge {
  source: string
  target: string
  weight: number
  type: string
}

interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

interface Recommendation {
  id: string
  title: string
  description: string
  category: string
  confidence: number
  impact_score: number
  pattern_ids: string[]
}

interface Prediction {
  success_rate: number
  performance_gain: number
  stability_change: number
  risk_level: 'low' | 'medium' | 'high'
  estimated_duration: number
  can_execute: boolean
}

interface Props {
  skillId?: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'evolution-triggered', data: any): void
  (e: 'error', error: Error): void
}>()

const loading = ref(false)
const triggering = ref(false)
const selectedCategory = ref('')
const graphContainer = ref<HTMLElement | null>(null)
const nodeDetailVisible = ref(false)

const graphData = ref<GraphData | null>(null)
const recommendations = ref<Recommendation[]>([])
const selectedRecommendation = ref<Recommendation | null>(null)
const selectedPrediction = ref<Prediction | null>(null)
const selectedNode = ref<GraphNode | null>(null)

let echartsInstance: any = null
let echarts: any = null

const getCategoryType = (category: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    optimization: 'success',
    adaptation: 'primary',
    repair: 'warning',
    enhancement: 'info'
  }
  return types[category] || 'info'
}

const getCategoryLabel = (category: string): string => {
  const labels: Record<string, string> = {
    optimization: '优化',
    adaptation: '适配',
    repair: '修复',
    enhancement: '增强'
  }
  return labels[category] || category
}

const getImpactColor = (score: number): string => {
  if (score >= 70) return '#67c23a'
  if (score >= 40) return '#e6a23c'
  return '#f56c6c'
}

const getSuccessColor = (rate: number): string => {
  if (rate >= 0.8) return '#67c23a'
  if (rate >= 0.5) return '#e6a23c'
  return '#f56c6c'
}

const getRiskType = (level: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    low: 'success',
    medium: 'warning',
    high: 'danger'
  }
  return types[level] || 'info'
}

const getRiskLabel = (level: string): string => {
  const labels: Record<string, string> = {
    low: '低风险',
    medium: '中风险',
    high: '高风险'
  }
  return labels[level] || level
}

const formatDuration = (seconds: number): string => {
  if (seconds < 60) return `${seconds}秒`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟`
  return `${Math.floor(seconds / 3600)}小时`
}

const fetchGraphData = async () => {
  loading.value = true
  try {
    const params: Record<string, any> = {}
    if (props.skillId) params.skill_id = props.skillId
    if (selectedCategory.value) params.category = selectedCategory.value

    const response = await api.get('/evolution-knowledge/graph', { params })
    graphData.value = response as GraphData

    await nextTick()
    if (!echartsInstance) {
      await initChart()
    }
    updateChart()
  } catch (error) {
    console.error('Failed to fetch graph data:', error)
    emit('error', error as Error)
  } finally {
    loading.value = false
  }
}

const fetchRecommendations = async () => {
  try {
    const params: Record<string, any> = {}
    if (props.skillId) params.skill_id = props.skillId

    const response = await api.get('/evolution-knowledge/recommendations', { params })
    recommendations.value = response as Recommendation[]
  } catch (error) {
    console.error('Failed to fetch recommendations:', error)
  }
}

const selectRecommendation = async (rec: Recommendation) => {
  selectedRecommendation.value = rec
  try {
    const response = await api.post('/evolution-knowledge/predict', {
      recommendation_id: rec.id,
      skill_id: props.skillId
    })
    selectedPrediction.value = response as Prediction
  } catch (error) {
    console.error('Failed to fetch prediction:', error)
    selectedPrediction.value = null
  }
}

const refreshRecommendations = () => {
  fetchRecommendations()
  selectedRecommendation.value = null
  selectedPrediction.value = null
}

const triggerEvolution = async () => {
  if (!selectedRecommendation.value || !selectedPrediction.value) return

  triggering.value = true
  try {
    const response = await api.post('/evolution-knowledge/trigger', {
      recommendation_id: selectedRecommendation.value.id,
      skill_id: props.skillId
    })
    ElMessage.success('演化已触发')
    emit('evolution-triggered', response)
  } catch (error) {
    console.error('Failed to trigger evolution:', error)
    ElMessage.error('演化触发失败')
    emit('error', error as Error)
  } finally {
    triggering.value = false
  }
}

const initChart = async () => {
  if (!graphContainer.value) return
  try {
    if (!echarts) {
      echarts = await import('echarts')
    }
    if (echartsInstance) {
      echartsInstance.dispose()
    }
    echartsInstance = echarts.init(graphContainer.value)

    echartsInstance.on('click', (params: any) => {
      if (params.dataType === 'node') {
        selectedNode.value = params.data
        nodeDetailVisible.value = true
      }
    })
  } catch (error) {
    console.error('Failed to initialize chart:', error)
  }
}

const updateChart = () => {
  if (!echartsInstance || !graphData.value) return

  const categoryColors: Record<string, string> = {
    optimization: '#67c23a',
    adaptation: '#409eff',
    repair: '#e6a23c',
    enhancement: '#909399'
  }

  const nodes = graphData.value.nodes.map(node => ({
    id: node.id,
    name: node.name,
    category: node.category,
    description: node.description,
    apply_count: node.apply_count,
    success_rate: node.success_rate,
    related_patterns: node.related_patterns,
    symbolSize: Math.max(20, Math.min(50, node.apply_count * 2)),
    itemStyle: {
      color: categoryColors[node.category] || '#909399'
    },
    label: {
      show: true,
      fontSize: 12
    }
  }))

  const edges = graphData.value.edges.map(edge => ({
    source: edge.source,
    target: edge.target,
    value: edge.weight,
    lineStyle: {
      width: Math.max(1, edge.weight * 2),
      curveness: 0.2
    }
  }))

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        if (params.dataType === 'node') {
          return `<strong>${params.data.name}</strong><br/>
                  类型: ${getCategoryLabel(params.data.category)}<br/>
                  应用次数: ${params.data.apply_count}<br/>
                  成功率: ${(params.data.success_rate * 100).toFixed(1)}%`
        }
        return ''
      }
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        data: nodes,
        links: edges,
        roam: true,
        draggable: true,
        force: {
          repulsion: 200,
          edgeLength: 120,
          gravity: 0.1
        },
        emphasis: {
          focus: 'adjacency',
          lineStyle: {
            width: 3
          }
        },
        label: {
          position: 'right',
          formatter: '{b}'
        },
        lineStyle: {
          color: '#aaa',
          curveness: 0.2
        }
      }
    ]
  }

  echartsInstance.setOption(option)
}

const zoomIn = () => {
  if (echartsInstance) {
    const option = echartsInstance.getOption()
    const zoom = (option.series[0].zoom || 1) * 1.2
    echartsInstance.setOption({ series: [{ zoom }] })
  }
}

const zoomOut = () => {
  if (echartsInstance) {
    const option = echartsInstance.getOption()
    const zoom = (option.series[0].zoom || 1) / 1.2
    echartsInstance.setOption({ series: [{ zoom: Math.max(0.3, zoom) }] })
  }
}

const resetZoom = () => {
  if (echartsInstance) {
    echartsInstance.setOption({ series: [{ zoom: 1, center: undefined }] })
  }
}

const handleResize = () => {
  if (echartsInstance) {
    echartsInstance.resize()
  }
}

watch(selectedCategory, () => {
  fetchGraphData()
})

onMounted(async () => {
  await fetchGraphData()
  await fetchRecommendations()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (echartsInstance) {
    echartsInstance.dispose()
    echartsInstance = null
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.evolution-knowledge-graph {
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

.graph-container {
  height: 500px;
  position: relative;
}

.graph-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  color: #909399;
}

.graph-legend {
  display: flex;
  justify-content: center;
  gap: 20px;
  padding-top: 15px;
  border-top: 1px solid #ebeef5;
  margin-top: 15px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #606266;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.legend-dot.optimization { background: #67c23a; }
.legend-dot.adaptation { background: #409eff; }
.legend-dot.repair { background: #e6a23c; }
.legend-dot.enhancement { background: #909399; }

.recommendations-card {
  height: 350px;
  overflow: hidden;
}

.recommendations-list {
  max-height: 280px;
  overflow-y: auto;
}

.recommendation-item {
  padding: 12px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.recommendation-item:hover {
  border-color: #409eff;
  background: #f5f7fa;
}

.rec-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.rec-confidence {
  font-size: 12px;
  color: #909399;
}

.rec-title {
  font-weight: 500;
  margin-bottom: 5px;
}

.rec-desc {
  font-size: 13px;
  color: #606266;
  margin-bottom: 10px;
}

.rec-impact {
  display: flex;
  align-items: center;
  gap: 10px;
}

.impact-label {
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
}

.prediction-content {
  padding: 10px 0;
}

.prediction-item {
  margin-bottom: 20px;
}

.pred-label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
}

.prediction-metrics {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 15px;
}

.metric-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #ebeef5;
}

.metric-row:last-child {
  border-bottom: none;
}

.metric-label {
  color: #909399;
}

.metric-value {
  font-weight: 500;
}

.metric-value.positive {
  color: #67c23a;
}

.node-detail {
  padding: 10px 0;
}

.detail-row {
  display: flex;
  margin-bottom: 15px;
}

.detail-label {
  width: 80px;
  color: #909399;
  flex-shrink: 0;
}

.detail-value {
  flex: 1;
}

.related-patterns {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}
</style>
