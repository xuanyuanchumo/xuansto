<template>
  <div class="transparency-report-page">
    <div class="page-header">
      <el-button text @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        返回项目
      </el-button>
      <h2>透明度报告</h2>
      <div class="header-actions">
        <el-button type="primary" @click="exportFullReport">
          <el-icon><Download /></el-icon>
          导出完整报告
        </el-button>
        <el-button @click="refreshReport">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <div v-loading="loading" class="report-content">
      <template v-if="report">
        <el-row :gutter="20">
          <el-col :span="16">
            <el-card class="score-card">
              <div class="score-section">
                <div class="score-circle">
                  <el-progress
                    type="dashboard"
                    :percentage="report.overallScore"
                    :color="getScoreColor(report.overallScore)"
                    :width="160"
                  >
                    <template #default>
                      <span class="score-value">{{ report.overallScore }}</span>
                      <span class="score-label">透明度评分</span>
                    </template>
                  </el-progress>
                </div>
                <div class="score-description">
                  <div class="score-level" :class="getScoreLevel(report.overallScore)">
                    {{ getScoreLevelText(report.overallScore) }}
                  </div>
                  <div class="score-detail">
                    基于决策透明度、推理可追溯性、数据可见性等维度综合评估项目透明度
                  </div>
                  <div class="score-meta">
                    <span>生成时间：{{ formatTime(report.generatedAt) }}</span>
                    <span>项目：{{ report.projectName || '未知项目' }}</span>
                  </div>
                </div>
              </div>
            </el-card>

            <el-card class="dimensions-card">
              <template #header>
                <span>各维度评分详情</span>
              </template>
              <div class="dimensions-list">
                <div
                  v-for="dim in report.dimensions"
                  :key="dim.key"
                  class="dimension-item"
                >
                  <div class="dimension-header">
                    <span class="dimension-name">{{ dim.name }}</span>
                    <span class="dimension-score" :style="{ color: getScoreColor(dim.score) }">
                      {{ dim.score }}分
                    </span>
                  </div>
                  <el-progress
                    :percentage="dim.score"
                    :color="getScoreColor(dim.score)"
                    :stroke-width="12"
                  />
                  <div class="dimension-desc">{{ dim.description }}</div>
                </div>
              </div>
            </el-card>

            <el-card class="statistics-card">
              <template #header>
                <span>统计数据</span>
              </template>
              <div class="statistics-grid">
                <div class="stat-card">
                  <div class="stat-icon decisions">
                    <el-icon><Document /></el-icon>
                  </div>
                  <div class="stat-info">
                    <div class="stat-value">{{ report.statistics.decisionsCount || 0 }}</div>
                    <div class="stat-label">决策记录</div>
                  </div>
                </div>
                <div class="stat-card">
                  <div class="stat-icon reasoning">
                    <el-icon><Connection /></el-icon>
                  </div>
                  <div class="stat-info">
                    <div class="stat-value">{{ report.statistics.reasoningSteps || 0 }}</div>
                    <div class="stat-label">推理步骤</div>
                  </div>
                </div>
                <div class="stat-card">
                  <div class="stat-icon artifacts">
                    <el-icon><FolderOpened /></el-icon>
                  </div>
                  <div class="stat-info">
                    <div class="stat-value">{{ report.statistics.artifactsCount || 0 }}</div>
                    <div class="stat-label">中间产物</div>
                  </div>
                </div>
                <div class="stat-card">
                  <div class="stat-icon changes">
                    <el-icon><Edit /></el-icon>
                  </div>
                  <div class="stat-info">
                    <div class="stat-value">{{ report.statistics.codeChanges || 0 }}</div>
                    <div class="stat-label">代码变更</div>
                  </div>
                </div>
              </div>
            </el-card>

            <el-card class="timeline-card">
              <template #header>
                <span>时间线</span>
              </template>
              <div class="timeline-summary">
                <div class="timeline-item">
                  <span class="label">开始时间</span>
                  <span class="value">{{ formatTime(report.statistics.startTime) }}</span>
                </div>
                <div class="timeline-item">
                  <span class="label">结束时间</span>
                  <span class="value">{{ formatTime(report.statistics.endTime) }}</span>
                </div>
                <div class="timeline-item">
                  <span class="label">总耗时</span>
                  <span class="value">{{ formatDuration(report.statistics.duration) }}</span>
                </div>
              </div>
            </el-card>
          </el-col>

          <el-col :span="8">
            <el-card class="recommendations-card">
              <template #header>
                <div class="card-header">
                  <span>改进建议</span>
                  <el-tag v-if="recommendations.length" type="warning" size="small">
                    {{ recommendations.length }} 条建议
                  </el-tag>
                </div>
              </template>
              <div v-if="recommendations.length > 0" class="recommendations-list">
                <div
                  v-for="(rec, index) in recommendations"
                  :key="index"
                  class="recommendation-item"
                  :class="`level-${rec.level}`"
                >
                  <div class="rec-header">
                    <el-icon class="rec-icon" :class="rec.level">
                      <component :is="getRecommendationIcon(rec.level)" />
                    </el-icon>
                    <span class="rec-level">{{ getLevelText(rec.level) }}</span>
                  </div>
                  <div class="rec-content">
                    <div class="rec-title">{{ rec.title }}</div>
                    <div class="rec-desc">{{ rec.description }}</div>
                  </div>
                </div>
              </div>
              <el-empty v-else description="暂无改进建议，透明度表现优秀！" :image-size="80" />
            </el-card>

            <el-card class="export-card">
              <template #header>
                <span>导出选项</span>
              </template>
              <div class="export-options">
                <el-button class="export-btn" @click="exportAsJson">
                  <el-icon><Document /></el-icon>
                  导出 JSON
                </el-button>
                <el-button class="export-btn" @click="exportAsMarkdown">
                  <el-icon><Document /></el-icon>
                  导出 Markdown
                </el-button>
                <el-button class="export-btn" @click="exportAsHtml">
                  <el-icon><Document /></el-icon>
                  导出 HTML
                </el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </template>

      <el-empty v-else-if="!loading" description="暂无透明度报告数据" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Download, Refresh, Document, Connection, FolderOpened, Edit, Warning, InfoFilled, CircleCheck } from '@element-plus/icons-vue'
import { transparencyApi } from '@/api'

interface Dimension {
  key: string
  name: string
  score: number
  description: string
}

interface Statistics {
  decisionsCount?: number
  reasoningSteps?: number
  artifactsCount?: number
  codeChanges?: number
  startTime?: string
  endTime?: string
  duration?: number
}

interface Recommendation {
  level: 'high' | 'medium' | 'low'
  title: string
  description: string
}

interface TransparencyReportData {
  overallScore: number
  dimensions: Dimension[]
  statistics: Statistics
  recommendations?: Recommendation[]
  projectName?: string
  generatedAt?: string
}

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const report = ref<TransparencyReportData | null>(null)

const recommendations = computed(() => report.value?.recommendations || [])

const getScoreColor = (score: number) => {
  if (score >= 80) return '#67c23a'
  if (score >= 60) return '#e6a23c'
  if (score >= 40) return '#f56c6c'
  return '#909399'
}

const getScoreLevel = (score: number) => {
  if (score >= 80) return 'level-high'
  if (score >= 60) return 'level-medium'
  if (score >= 40) return 'level-low'
  return 'level-critical'
}

const getScoreLevelText = (score: number) => {
  if (score >= 80) return '优秀'
  if (score >= 60) return '良好'
  if (score >= 40) return '一般'
  return '需改进'
}

const getRecommendationIcon = (level: string) => {
  switch (level) {
    case 'high': return Warning
    case 'medium': return InfoFilled
    default: return CircleCheck
  }
}

const getLevelText = (level: string) => {
  switch (level) {
    case 'high': return '高优先级'
    case 'medium': return '中优先级'
    default: return '低优先级'
  }
}

const formatTime = (time?: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const formatDuration = (ms?: number) => {
  if (!ms) return '-'
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  if (ms < 3600000) return `${(ms / 60000).toFixed(1)}min`
  return `${(ms / 3600000).toFixed(1)}h`
}

const goBack = () => {
  const projectId = route.params.projectId
  if (projectId) {
    router.push(`/projects/${projectId}`)
  } else {
    router.back()
  }
}

const fetchReport = async () => {
  const projectId = Number(route.params.projectId)
  if (!projectId) {
    ElMessage.error('项目ID无效')
    return
  }

  loading.value = true
  try {
    const response = await transparencyApi.getReport(projectId)
    report.value = response || getDefaultReport()
  } catch (error) {
    console.error('Failed to fetch transparency report:', error)
    report.value = getDefaultReport()
  } finally {
    loading.value = false
  }
}

const getDefaultReport = (): TransparencyReportData => ({
  overallScore: 75,
  dimensions: [
    { key: 'decision', name: '决策透明度', score: 80, description: '决策过程的可追溯性和清晰度' },
    { key: 'reasoning', name: '推理可追溯性', score: 70, description: '推理步骤的完整性和可理解性' },
    { key: 'data', name: '数据可见性', score: 85, description: '输入输出数据的可见性和可访问性' },
    { key: 'code', name: '代码变更透明度', score: 65, description: '代码变更的可追溯性和可理解性' }
  ],
  statistics: {
    decisionsCount: 12,
    reasoningSteps: 45,
    artifactsCount: 8,
    codeChanges: 23,
    startTime: new Date(Date.now() - 3600000).toISOString(),
    endTime: new Date().toISOString(),
    duration: 3600000
  },
  recommendations: [
    { level: 'medium', title: '增加决策记录', description: '建议在关键决策点增加更多的决策记录，以提高透明度' },
    { level: 'low', title: '完善推理过程', description: '部分推理步骤缺少详细说明，建议补充推理依据' }
  ],
  projectName: '示例项目',
  generatedAt: new Date().toISOString()
})

const refreshReport = async () => {
  await fetchReport()
  ElMessage.success('报告已刷新')
}

const exportFullReport = () => {
  exportAsJson()
}

const exportAsJson = () => {
  if (!report.value) return
  
  const blob = new Blob([JSON.stringify(report.value, null, 2)], { type: 'application/json' })
  downloadBlob(blob, `transparency-report-${Date.now()}.json`)
  ElMessage.success('JSON 报告已导出')
}

const exportAsMarkdown = () => {
  if (!report.value) return
  
  let markdown = `# 透明度报告\n\n`
  markdown += `## 概览\n\n`
  markdown += `- **透明度评分**: ${report.value.overallScore}分 (${getScoreLevelText(report.value.overallScore)})\n`
  markdown += `- **生成时间**: ${formatTime(report.value.generatedAt)}\n\n`
  
  markdown += `## 各维度评分\n\n`
  report.value.dimensions.forEach(dim => {
    markdown += `### ${dim.name}\n\n`
    markdown += `- **评分**: ${dim.score}分\n`
    markdown += `- **说明**: ${dim.description}\n\n`
  })
  
  markdown += `## 统计数据\n\n`
  markdown += `| 指标 | 数值 |\n`
  markdown += `|------|------|\n`
  markdown += `| 决策记录 | ${report.value.statistics.decisionsCount || 0} |\n`
  markdown += `| 推理步骤 | ${report.value.statistics.reasoningSteps || 0} |\n`
  markdown += `| 中间产物 | ${report.value.statistics.artifactsCount || 0} |\n`
  markdown += `| 代码变更 | ${report.value.statistics.codeChanges || 0} |\n\n`
  
  if (recommendations.value.length > 0) {
    markdown += `## 改进建议\n\n`
    recommendations.value.forEach((rec, index) => {
      markdown += `${index + 1}. **${rec.title}** (${getLevelText(rec.level)})\n`
      markdown += `   ${rec.description}\n\n`
    })
  }
  
  const blob = new Blob([markdown], { type: 'text/markdown' })
  downloadBlob(blob, `transparency-report-${Date.now()}.md`)
  ElMessage.success('Markdown 报告已导出')
}

const getHtmlStyles = () => `
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
  h1 { color: #303133; border-bottom: 2px solid #409eff; padding-bottom: 10px; }
  h2 { color: #606266; margin-top: 30px; }
  .score { font-size: 48px; font-weight: bold; }
  table { width: 100%; border-collapse: collapse; margin: 20px 0; }
  th, td { border: 1px solid #ebeef5; padding: 10px; text-align: left; }
  th { background: #f5f7fa; }
  .recommendation { padding: 15px; margin: 10px 0; border-radius: 4px; background: #fafafa; }
  .high { border-left: 3px solid #f56c6c; }
  .medium { border-left: 3px solid #e6a23c; }
  .low { border-left: 3px solid #409eff; }
`

const getHtmlDimensionsTable = () => {
  if (!report.value) return ''
  return report.value.dimensions.map(dim => 
    `<tr><td>${dim.name}</td><td>${dim.score}</td><td>${dim.description}</td></tr>`
  ).join('')
}

const getHtmlStatisticsTable = () => {
  if (!report.value) return ''
  const stats = report.value.statistics
  return `
    <tr><td>决策记录</td><td>${stats.decisionsCount || 0}</td></tr>
    <tr><td>推理步骤</td><td>${stats.reasoningSteps || 0}</td></tr>
    <tr><td>中间产物</td><td>${stats.artifactsCount || 0}</td></tr>
    <tr><td>代码变更</td><td>${stats.codeChanges || 0}</td></tr>
  `
}

const getHtmlRecommendations = () => {
  if (!report.value || recommendations.value.length === 0) return ''
  return recommendations.value.map(rec => `
    <div class="recommendation ${rec.level}">
      <strong>${rec.title}</strong> (${getLevelText(rec.level)})<br>
      ${rec.description}
    </div>
  `).join('')
}

const exportAsHtml = () => {
  if (!report.value) return
  
  const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>透明度报告</title>
  <style>
    ${getHtmlStyles()}
    .score { color: ${getScoreColor(report.value.overallScore)}; }
  </style>
</head>
<body>
  <h1>透明度报告</h1>
  <p><strong>透明度评分</strong>: <span class="score">${report.value.overallScore}</span> (${getScoreLevelText(report.value.overallScore)})</p>
  <p><strong>生成时间</strong>: ${formatTime(report.value.generatedAt)}</p>
  
  <h2>各维度评分</h2>
  <table>
    <tr><th>维度</th><th>评分</th><th>说明</th></tr>
    ${getHtmlDimensionsTable()}
  </table>
  
  <h2>统计数据</h2>
  <table>
    <tr><th>指标</th><th>数值</th></tr>
    ${getHtmlStatisticsTable()}
  </table>
  
  ${recommendations.value.length > 0 ? `
  <h2>改进建议</h2>
  ${getHtmlRecommendations()}
  ` : ''}
</body>
</html>`
  
  const blob = new Blob([html], { type: 'text/html' })
  downloadBlob(blob, `transparency-report-${Date.now()}.html`)
  ElMessage.success('HTML 报告已导出')
}

const downloadBlob = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

onMounted(() => {
  fetchReport()
})
</script>

<style scoped>
.transparency-report-page {
  padding: 20px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  flex: 1;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.report-content {
  min-height: 400px;
}

.score-card, .dimensions-card, .statistics-card, .timeline-card, .recommendations-card, .export-card {
  margin-bottom: 20px;
}

.score-section {
  display: flex;
  align-items: center;
  gap: 40px;
  padding: 20px;
}

.score-circle {
  flex-shrink: 0;
}

.score-value {
  font-size: 36px;
  font-weight: bold;
  display: block;
}

.score-label {
  font-size: 14px;
  color: #909399;
}

.score-description {
  flex: 1;
}

.score-level {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 10px;
}

.score-level.level-high { color: #67c23a; }
.score-level.level-medium { color: #e6a23c; }
.score-level.level-low { color: #f56c6c; }
.score-level.level-critical { color: #909399; }

.score-detail {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  margin-bottom: 10px;
}

.score-meta {
  display: flex;
  gap: 20px;
  font-size: 12px;
  color: #909399;
}

.dimensions-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.dimension-item {
  padding: 15px;
  background: #fafafa;
  border-radius: 8px;
}

.dimension-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.dimension-name {
  font-weight: 500;
  font-size: 16px;
}

.dimension-score {
  font-size: 20px;
  font-weight: bold;
}

.dimension-desc {
  font-size: 13px;
  color: #909399;
  margin-top: 10px;
}

.statistics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
  background: #fafafa;
  border-radius: 8px;
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 50px;
  height: 50px;
  border-radius: 10px;
  color: #fff;
  font-size: 24px;
}

.stat-icon.decisions { background: #409eff; }
.stat-icon.reasoning { background: #67c23a; }
.stat-icon.artifacts { background: #e6a23c; }
.stat-icon.changes { background: #f56c6c; }

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 13px;
  color: #909399;
}

.timeline-summary {
  display: flex;
  justify-content: space-between;
  padding: 20px;
  background: #fafafa;
  border-radius: 8px;
}

.timeline-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.timeline-item .label {
  font-size: 12px;
  color: #909399;
}

.timeline-item .value {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.recommendations-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recommendation-item {
  padding: 15px;
  border-radius: 8px;
  background: #fafafa;
  border-left: 3px solid #909399;
}

.recommendation-item.level-high {
  border-left-color: #f56c6c;
  background: #fef0f0;
}

.recommendation-item.level-medium {
  border-left-color: #e6a23c;
  background: #fdf6ec;
}

.recommendation-item.level-low {
  border-left-color: #409eff;
  background: #ecf5ff;
}

.rec-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.rec-icon {
  font-size: 18px;
}

.rec-icon.high { color: #f56c6c; }
.rec-icon.medium { color: #e6a23c; }
.rec-icon.low { color: #409eff; }

.rec-level {
  font-size: 12px;
  font-weight: 500;
}

.rec-title {
  font-weight: 500;
  font-size: 14px;
  margin-bottom: 4px;
}

.rec-desc {
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
}

.export-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.export-btn {
  width: 100%;
  justify-content: flex-start;
}
</style>
