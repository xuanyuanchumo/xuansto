<template>
  <el-card class="transparency-report" shadow="hover">
    <template #header>
      <div class="card-header">
        <span class="title">透明度报告</span>
        <el-button type="primary" size="small" @click="exportReport">
          <el-icon><Download /></el-icon>
          导出报告
        </el-button>
      </div>
    </template>

    <div class="report-container">
      <div class="score-section">
        <div class="score-circle">
          <el-progress
            type="dashboard"
            :percentage="overallScore"
            :color="getScoreColor(overallScore)"
            :width="120"
          >
            <template #default>
              <span class="score-value">{{ overallScore }}</span>
              <span class="score-label">透明度评分</span>
            </template>
          </el-progress>
        </div>
        <div class="score-description">
          <div class="score-level" :class="getScoreLevel(overallScore)">
            {{ getScoreLevelText(overallScore) }}
          </div>
          <div class="score-detail">
            基于决策透明度、推理可追溯性、数据可见性等维度综合评估
          </div>
        </div>
      </div>

      <el-divider />

      <div class="dimensions-section">
        <div class="section-title">各维度评分</div>
        <div class="dimensions-grid">
          <div
            v-for="dim in dimensions"
            :key="dim.key"
            class="dimension-item"
          >
            <div class="dimension-header">
              <span class="dimension-name">{{ dim.name }}</span>
              <span class="dimension-score" :style="{ color: getScoreColor(dim.score) }">
                {{ dim.score }}
              </span>
            </div>
            <el-progress
              :percentage="dim.score"
              :color="getScoreColor(dim.score)"
              :stroke-width="8"
              :show-text="false"
            />
            <div class="dimension-desc">{{ dim.description }}</div>
          </div>
        </div>
      </div>

      <el-divider />

      <div class="statistics-section">
        <div class="section-title">统计数据</div>
        <div class="statistics-grid">
          <div class="stat-card">
            <div class="stat-icon decisions">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.decisionsCount || 0 }}</div>
              <div class="stat-label">决策记录</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon reasoning">
              <el-icon><Connection /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.reasoningSteps || 0 }}</div>
              <div class="stat-label">推理步骤</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon artifacts">
              <el-icon><FolderOpened /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.artifactsCount || 0 }}</div>
              <div class="stat-label">中间产物</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon changes">
              <el-icon><Edit /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.codeChanges || 0 }}</div>
              <div class="stat-label">代码变更</div>
            </div>
          </div>
        </div>
      </div>

      <el-divider />

      <div class="timeline-section">
        <div class="section-title">时间线</div>
        <div class="timeline-summary">
          <div class="timeline-item">
            <span class="label">开始时间</span>
            <span class="value">{{ formatTime(statistics.startTime) }}</span>
          </div>
          <div class="timeline-item">
            <span class="label">结束时间</span>
            <span class="value">{{ formatTime(statistics.endTime) }}</span>
          </div>
          <div class="timeline-item">
            <span class="label">总耗时</span>
            <span class="value">{{ formatDuration(statistics.duration) }}</span>
          </div>
        </div>
      </div>

      <el-divider />

      <div class="recommendations-section">
        <div class="section-title">改进建议</div>
        <div v-if="recommendations.length > 0" class="recommendations-list">
          <div
            v-for="(rec, index) in recommendations"
            :key="index"
            class="recommendation-item"
          >
            <el-icon class="rec-icon" :class="rec.level"><Warning /></el-icon>
            <div class="rec-content">
              <div class="rec-title">{{ rec.title }}</div>
              <div class="rec-desc">{{ rec.description }}</div>
            </div>
          </div>
        </div>
        <el-empty v-else description="暂无改进建议" :image-size="60" />
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed, defineProps } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Document, Connection, FolderOpened, Edit, Warning } from '@element-plus/icons-vue'

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

const props = defineProps<{
  overallScore: number
  dimensions: Dimension[]
  statistics: Statistics
  recommendations?: Recommendation[]
}>()

const recommendations = computed(() => props.recommendations || [])

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

const exportReport = () => {
  const report = {
    overallScore: props.overallScore,
    dimensions: props.dimensions,
    statistics: props.statistics,
    recommendations: recommendations.value,
    exportedAt: new Date().toISOString()
  }

  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `transparency-report-${Date.now()}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)

  ElMessage.success('报告已导出')
}
</script>

<style scoped>
.transparency-report {
  margin-bottom: 15px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-weight: bold;
  font-size: 16px;
}

.report-container {
  padding: 10px 0;
}

.score-section {
  display: flex;
  align-items: center;
  gap: 30px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 10px;
}

.score-circle {
  flex-shrink: 0;
}

.score-value {
  font-size: 28px;
  font-weight: bold;
  display: block;
}

.score-label {
  font-size: 12px;
  color: #909399;
}

.score-description {
  flex: 1;
}

.score-level {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 8px;
}

.score-level.level-high {
  color: #67c23a;
}

.score-level.level-medium {
  color: #e6a23c;
}

.score-level.level-low {
  color: #f56c6c;
}

.score-level.level-critical {
  color: #909399;
}

.score-detail {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}

.section-title {
  font-weight: 500;
  font-size: 14px;
  color: #303133;
  margin-bottom: 15px;
  padding-left: 10px;
  border-left: 3px solid #409eff;
}

.dimensions-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
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
  margin-bottom: 8px;
}

.dimension-name {
  font-weight: 500;
  font-size: 14px;
}

.dimension-score {
  font-size: 18px;
  font-weight: bold;
}

.dimension-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}

.statistics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px;
  background: #fafafa;
  border-radius: 8px;
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  color: #fff;
}

.stat-icon.decisions {
  background: #409eff;
}

.stat-icon.reasoning {
  background: #67c23a;
}

.stat-icon.artifacts {
  background: #e6a23c;
}

.stat-icon.changes {
  background: #f56c6c;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

.timeline-summary {
  display: flex;
  gap: 40px;
  padding: 15px;
  background: #fafafa;
  border-radius: 8px;
}

.timeline-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
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

.recommendations-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.recommendation-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
  border-left: 3px solid #909399;
}

.rec-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.rec-icon.high {
  color: #f56c6c;
}

.rec-icon.medium {
  color: #e6a23c;
}

.rec-icon.low {
  color: #409eff;
}

.rec-content {
  flex: 1;
}

.rec-title {
  font-weight: 500;
  font-size: 14px;
  margin-bottom: 4px;
}

.rec-desc {
  font-size: 13px;
  color: #606266;
}

.el-divider {
  margin: 20px 0;
}
</style>
