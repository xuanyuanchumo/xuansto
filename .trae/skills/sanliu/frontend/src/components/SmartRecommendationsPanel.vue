<template>
  <div class="smart-recommendations-panel">
    <el-card class="panel-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon :size="20"><MagicStick /></el-icon>
            <span class="title">智能推荐</span>
          </div>
          <div class="header-actions">
            <el-select v-model="selectedContext" size="small" style="width: 150px" @change="fetchRecommendations">
              <el-option v-for="ctx in contextTypes" :key="ctx.value" :label="ctx.label" :value="ctx.value" />
            </el-select>
            <el-button size="small" @click="fetchRecommendations" :icon="Refresh">刷新</el-button>
          </div>
        </div>
      </template>

      <div class="recommendations-content">
        <div v-loading="loading" class="rec-cards-container">
          <transition-group name="rec-fade" tag="div" class="rec-cards-grid">
            <div
              v-for="rec in filteredRecommendations"
              :key="rec.recommendation_id"
              class="rec-card"
              :class="[`action-${rec.action_type}`, `priority-${rec.priority}`]"
            >
              <div class="rec-card-header">
                <div class="rec-action-icon" :class="rec.action_type">
                  <el-icon :size="20"><component :is="getActionIcon(rec.action_type)" /></el-icon>
                </div>
                <div class="rec-card-title-area">
                  <div class="rec-title">{{ rec.title }}</div>
                  <div class="rec-confidence-bar">
                    <div class="confidence-track">
                      <div class="confidence-fill" :style="{ width: `${rec.confidence_score * 100}%` }"></div>
                    </div>
                    <span class="confidence-text">{{ (rec.confidence_score * 100).toFixed(0) }}%</span>
                  </div>
                </div>
                <el-tag :type="getPriorityTagType(rec.priority)" size="small" effect="dark">
                  {{ getPriorityLabel(rec.priority) }}
                </el-tag>
              </div>

              <div class="rec-description">{{ rec.description }}</div>

              <div class="rec-impact" v-if="Object.keys(rec.impact_assessment).length > 0">
                <div class="impact-label">预期影响:</div>
                <div class="impact-tags">
                  <span v-for="(val, key) in rec.impact_assessment" :key="key" class="impact-tag" :class="Number(val) > 0 ? 'positive' : 'negative'">
                    {{ Number(val) > 0 ? '+' : '' }}{{ val }} {{ formatImpactKey(key) }}
                  </span>
                </div>
              </div>

              <div class="rec-actions-list" v-if="rec.suggested_actions.length > 0">
                <div class="actions-label">建议步骤:</div>
                <ol class="actions-steps">
                  <li v-for="(action, idx) in rec.suggested_actions" :key="idx">{{ action }}</li>
                </ol>
              </div>

              <div class="rec-card-footer">
                <div class="rec-meta-info">
                  <el-tag size="small" type="info">{{ rec.action_type }}</el-tag>
                  <span class="effort-label">工作量: {{ rec.effort_level }}</span>
                </div>
                <div class="rec-action-buttons">
                  <el-button type="primary" size="small" :icon="Check" @click="acceptRec(rec)">接受</el-button>
                  <el-button size="small" :icon="Close" @click="rejectRec(rec)">拒绝</el-button>
                  <el-button size="small" link @click="deferRec(rec)">稍后</el-button>
                </div>
              </div>
            </div>
          </transition-group>

          <div v-if="!loading && filteredRecommendations.length === 0" class="empty-state">
            <el-empty description="暂无推荐" :image-size="80">
              <el-button type="primary" @click="fetchRecommendations">刷新推荐</el-button>
            </el-empty>
          </div>
        </div>

        <el-divider />

        <div class="history-section">
          <div class="section-header">
            <span class="section-title">推荐历史</span>
            <el-button link type="primary" size="small" @click="showHistory = !showHistory">
              {{ showHistory ? '收起' : '展开' }}
            </el-button>
          </div>
          <div v-show="showHistory" class="history-table-wrapper">
            <el-table :data="historyItems" stripe size="small" max-height="280">
              <el-table-column prop="title" label="推荐标题" min-width="180" show-overflow-tooltip />
              <el-table-column prop="action" label="操作" width="90">
                <template #default="{ row }">
                  <el-tag :type="getActionTagType(row.action)" size="small">{{ row.action }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="rating" label="评分" width="80" align="center">
                <template #default="{ row }">
                  <span v-if="row.rating">{{ row.rating }} ⭐</span>
                  <span v-else class="text-muted">-</span>
                </template>
              </el-table-column>
              <el-table-column prop="timestamp" label="时间" width="160">
                <template #default="{ row }">{{ formatTime(row.timestamp) }}</template>
              </el-table-column>
            </el-table>
            <div class="history-stats">
              <span>接受率: <strong>{{ historyAcceptRate }}%</strong></span>
              <span>平均评分: <strong>{{ historyAvgRating }}</strong></span>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { MagicStick, Refresh, Check, Close, Setting, Brush, Warning, CirclePlus, Promotion } from '@element-plus/icons-vue'
import { recommendationsApi, type ContextRecommendation, type RecommendationHistoryItem } from '@/api'

const loading = ref(false)
const selectedContext = ref('code_editor')
const showHistory = ref(false)
const recommendations = ref<ContextRecommendation[]>([])
const historyItems = ref<RecommendationHistoryItem[]>([])

const contextTypes = [
  { value: 'code_editor', label: '代码编辑器' },
  { value: 'task_management', label: '任务管理' },
  { value: 'project_dashboard', label: '项目仪表盘' },
  { value: 'quality_monitor', label: '质量监控' },
  { value: 'evolution_panel', label: '演化面板' },
  { value: 'knowledge_base', label: '知识库' },
  { value: 'workflow_view', label: '工作流视图' },
]

const filteredRecommendations = computed(() => recommendations.value)

const historyAcceptance = computed(() => {
  if (!historyItems.value.length) return 0
  const accepted = historyItems.value.filter(h => h.action === 'accepted' || h.action === 'implemented').length
  return Math.round((accepted / historyItems.value.length) * 100)
})

const historyAvgRating = computed(() => {
  const rated = historyItems.value.filter(h => h.rating !== null && h.rating !== undefined)
  if (!rated.length) return '-'
  const sum = rated.reduce((acc, h) => acc + (h.rating || 0), 0)
  return (sum / rated.length).toFixed(1)
})

function getActionIcon(action: string): any {
  const icons: Record<string, any> = {
    optimize: Setting, refactor: Brush, fix: Warning,
    enhance: MagicStick, suggest: Promotion, automate: CirclePlus
  }
  return icons[action] || Setting
}

function getPriorityTagType(priority: string): '' | 'success' | 'warning' | 'danger' | 'info' {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    critical: 'danger', high: 'warning', medium: '', low: 'info'
  }
  return types[priority] || 'info'
}

function getPriorityLabel(priority: string): string {
  const labels: Record<string, string> = { critical: '紧急', high: '高', medium: '中', low: '低' }
  return labels[priority] || priority
}

function getActionTagType(action: string): '' | 'success' | 'warning' | 'danger' | 'info' {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    accepted: 'success', implemented: 'success', rejected: 'danger',
    dismissed: 'info', deferred: 'warning'
  }
  return types[action] || 'info'
}

function formatImpactKey(key: string): string {
  const keys: Record<string, string> = {
    code_reduction_pct: '代码减少%', maintainability_increase: '可维护性提升',
    type_safety_increase: '类型安全提升', ide_support_improvement: 'IDE支持改善',
    assignment_efficiency: '分配效率', cycle_time_reduction: '周期缩短',
    block_risk_reduction: '阻塞风险降低', coordination_improvement: '协调改善',
    utilization_increase: '利用率提升', delivery_speed_up: '交付加速',
    debt_reduction: '债务减少', quality_score_increase: '质量分提升',
    memory_reduction_pct: '内存减少%', stability_increase: '稳定性提升',
    sync_time_reduction: '同步时间缩短', bandwidth_saving_pct: '带宽节省%',
    knowledge_coverage: '知识覆盖', discovery_efficiency: '发现效率',
    performance_gain: '性能增益', automation_level: '自动化水平',
  }
  return keys[key] || key
}

function formatTime(time: string | undefined): string {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

async function fetchRecommendations() {
  loading.value = true
  try {
    recommendations.value = await recommendationsApi.getContextRecommendations(selectedContext.value)
  } catch (error) {
    console.error('获取推荐失败:', error)
  } finally {
    loading.value = false
  }
}

async function fetchHistory() {
  try {
    const data = await recommendationsApi.getHistory()
    historyItems.value = data.items
  } catch (error) {
    console.error('获取历史失败:', error)
  }
}

async function acceptRec(rec: ContextRecommendation) {
  try {
    await recommendationsApi.submitFeedback({
      recommendation_id: rec.recommendation_id,
      action: 'accepted',
      rating: 5,
    })
    ElMessage.success('已接受推荐')
    recommendations.value = recommendations.value.filter(r => r.recommendation_id !== rec.recommendation_id)
    fetchHistory()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

async function rejectRec(rec: ContextRecommendation) {
  try {
    await recommendationsApi.submitFeedback({
      recommendation_id: rec.recommendation_id,
      action: 'rejected',
    })
    ElMessage.info('已拒绝推荐')
    recommendations.value = recommendations.value.filter(r => r.recommendation_id !== rec.recommendation_id)
    fetchHistory()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

async function deferRec(rec: ContextRecommendation) {
  try {
    await recommendationsApi.submitFeedback({
      recommendation_id: rec.recommendation_id,
      action: 'deferred',
    })
    ElMessage.info('已推迟推荐')
    recommendations.value = recommendations.value.filter(r => r.recommendation_id !== rec.recommendation_id)
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

onMounted(() => {
  fetchRecommendations()
  fetchHistory()
})
</script>

<style scoped>
.smart-recommendations-panel { width: 100%; }
.panel-card { border-radius: 10px; }
.card-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
.header-left { display: flex; align-items: center; gap: 10px; }
.title { font-size: 17px; font-weight: 600; }
.header-actions { display: flex; gap: 8px; }

.recommendations-content { padding: 5px 0; }
.rec-cards-container { min-height: 200px; }
.rec-cards-grid { display: flex; flex-direction: column; gap: 14px; }

.rec-card {
  border-radius: 10px;
  padding: 18px;
  background: linear-gradient(135deg, #fafcff 0%, #f5f7fa 100%);
  border: 1px solid #e4e7ed;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}
.rec-card::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 4px;
}
.rec-card.priority-critical::before { background: linear-gradient(180deg, #f56c6c, #f78989); }
.rec-card.priority-high::before { background: linear-gradient(180deg, #e6a23c, #ebb563); }
.rec-card.priority-medium::before { background: linear-gradient(180deg, #409eff, #79bbff); }
.rec-card.priority-low::before { background: linear-gradient(180deg, #909399, #a6a9ad); }

.rec-card:hover { box-shadow: 0 6px 20px rgba(0,0,0,0.08); transform: translateY(-2px); }

.rec-card-header { display: flex; align-items: flex-start; gap: 12px; margin-bottom: 10px; }
.rec-action-icon {
  width: 40px; height: 40px; border-radius: 10px; display: flex;
  align-items: center; justify-content: center; flex-shrink: 0; color: #fff;
}
.rec-action-icon.optimize { background: linear-gradient(135deg, #409eff, #79bbff); }
.rec-action-icon.refactor { background: linear-gradient(135deg, #e6a23c, #ebb563); }
.rec-action-icon.fix { background: linear-gradient(135deg, #f56c6c, #f78989); }
.rec-action-icon.enhance { background: linear-gradient(135deg, #67c23a, #85ce61); }
.rec-action-icon.suggest { background: linear-gradient(135deg, #909399, #a6a9ad); }
.rec-action-icon.automate { background: linear-gradient(135deg, #722ed1, #9254de); }

.rec-card-title-area { flex: 1; min-width: 0; }
.rec-title { font-size: 15px; font-weight: 600; color: #303133; margin-bottom: 6px; line-height: 1.3; }
.rec-confidence-bar { display: flex; align-items: center; gap: 8px; }
.confidence-track { flex: 1; height: 6px; background: #ebeef5; border-radius: 3px; overflow: hidden; }
.confidence-fill { height: 100%; background: linear-gradient(90deg, #67c23a, #85ce61); border-radius: 3px; transition: width 0.5s ease; }
.confidence-text { font-size: 11px; color: #67c23a; font-weight: 600; min-width: 32px; text-align: right; }

.rec-description { font-size: 13px; color: #606266; line-height: 1.6; margin-bottom: 12px; }

.rec-impact { margin-bottom: 12px; }
.impact-label { font-size: 12px; color: #909399; margin-bottom: 6px; }
.impact-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.impact-tag {
  font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 500;
}
.impact-tag.positive { background: #f0f9eb; color: #67c23a; }
.impact-tag.negative { background: #fef0f0; color: #f56c6c; }

.rec-actions-list { margin-bottom: 14px; }
.actions-label { font-size: 12px; color: #909399; margin-bottom: 6px; }
.actions-steps { margin: 0; padding-left: 18px; font-size: 12px; color: #606266; }
.actions-steps li { margin-bottom: 3px; line-height: 1.5; }

.rec-card-footer { display: flex; justify-content: space-between; align-items: center; padding-top: 12px; border-top: 1px solid #ebeef5; flex-wrap: wrap; gap: 8px; }
.rec-meta-info { display: flex; align-items: center; gap: 8px; }
.effort-label { font-size: 11px; color: #909399; }
.rec-action-buttons { display: flex; gap: 6px; }

.empty-state { padding: 30px 0; }

.history-section { padding: 5px 0; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.section-title { font-weight: 600; font-size: 14px; color: #303133; }
.history-table-wrapper { overflow-x: auto; }
.history-stats { display: flex; gap: 24px; margin-top: 10px; font-size: 13px; color: #606266; }
.text-muted { color: #c0c4cc; }

.rec-fade-enter-active { transition: all 0.4s ease-out; }
.rec-fade-leave-active { transition: all 0.25s ease-in; }
.rec-fade-enter-from { opacity: 0; transform: translateY(15px); }
.rec-fade-leave-to { opacity: 0; transform: scale(0.96); }

@media (max-width: 600px) {
  .rec-card-footer { flex-direction: column; align-items: stretch; }
  .rec-action-buttons { justify-content: flex-end; }
}
</style>
