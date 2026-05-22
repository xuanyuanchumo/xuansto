<template>
  <div class="skill-evolution-timeline">
    <el-card class="timeline-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span class="title">技能演化时间线</span>
            <el-tag :type="evolutionRunning ? 'primary' : 'info'" effect="dark" size="small">
              {{ evolutionRunning ? '运行中' : '空闲' }}
            </el-tag>
          </div>
          <div class="header-actions">
            <el-radio-group v-model="timeFilter" size="small" @change="fetchCycles">
              <el-radio-button label="7d">最近7天</el-radio-button>
              <el-radio-button label="30d">最近30天</el-radio-button>
              <el-radio-button label="all">全部</el-radio-button>
            </el-radio-group>
            <el-button type="primary" size="small" :loading="loading" @click="fetchCycles">
              <el-icon><Refresh /></el-icon> 刷新
            </el-button>
          </div>
        </div>
      </template>

      <div class="timeline-content">
        <div v-if="loading && cycles.length === 0" class="loading-state">
          <el-icon class="is-loading" :size="32"><Loading /></el-icon>
          <span>加载演化历史...</span>
        </div>

        <div v-else-if="cycles.length === 0" class="empty-state">
          <el-empty description="暂无演化记录" :image-size="80" />
        </div>

        <div v-else class="timeline-wrapper">
          <div class="timeline-track">
            <div class="timeline-line"></div>
            <div
              v-for="(cycle, index) in cycles"
              :key="cycle.cycle_id"
              class="timeline-node"
              :class="{ 'node-active': isCurrentCycle(cycle), `phase-${cycle.phase}` }"
              :style="{ '--delay': `${index * 0.08}s` }"
            >
              <div class="node-marker" :class="{ 'marker-active': isCurrentCycle(cycle) }">
                <div class="marker-inner" :class="getPhaseColor(cycle.phase)">
                  <span class="phase-letter">{{ getPhaseLetter(cycle.phase) }}</span>
                </div>
                <div v-if="isCurrentCycle(cycle)" class="pulse-ring"></div>
              </div>

              <div class="node-card" @click="toggleExpand(cycle.cycle_id)">
                <div class="node-header">
                  <div class="node-id">
                    <span class="cycle-label">循环</span>
                    <span class="cycle-num">#{{ index + 1 }}</span>
                    <el-tag size="small" :type="getStatusType(cycle.status)" effect="plain">
                      {{ getStatusLabel(cycle.status) }}
                    </el-tag>
                  </div>
                  <div class="node-phase">
                    <el-tag :type="getPhaseTagType(cycle.phase)" effect="dark" size="small">
                      {{ getPhaseLabel(cycle.phase) }}
                    </el-tag>
                  </div>
                </div>

                <div class="node-meta">
                  <div class="meta-row">
                    <span class="meta-item">
                      <el-icon><Timer /></el-icon>
                      耗时: {{ formatDuration(cycle.duration_seconds) }}
                    </span>
                    <span class="meta-item" :class="cycle.improvement_score >= 0 ? 'score-positive' : 'score-negative'">
                      <el-icon><TrendCharts /></el-icon>
                      改进: {{ cycle.improvement_score >= 0 ? '+' : '' }}{{ cycle.improvement_score.toFixed(1) }}%
                    </span>
                  </div>
                  <div class="meta-row">
                    <span class="meta-item">
                      <el-icon><Clock /></el-icon>
                      {{ formatTime(cycle.start_time) }}
                    </span>
                  </div>
                </div>

                <transition name="expand">
                  <div v-if="expandedCycles.has(cycle.cycle_id)" class="node-detail">
                    <el-divider />
                    <div class="detail-grid">
                      <div class="detail-item">
                        <span class="detail-label">循环ID</span>
                        <span class="detail-value mono">{{ cycle.cycle_id }}</span>
                      </div>
                      <div class="detail-item">
                        <span class="detail-label">阶段</span>
                        <span class="detail-value">{{ getPhaseLabel(cycle.phase) }}</span>
                      </div>
                      <div class="detail-item">
                        <span class="detail-label">状态</span>
                        <span class="detail-value">{{ getStatusLabel(cycle.status) }}</span>
                      </div>
                      <div class="detail-item">
                        <span class="detail-label">耗时</span>
                        <span class="detail-value">{{ formatDuration(cycle.duration_seconds) }}</span>
                      </div>
                      <div class="detail-item">
                        <span class="detail-label">改进效果</span>
                        <span class="detail-value" :class="cycle.improvement_score >= 0 ? 'text-success' : 'text-danger'">
                          {{ cycle.improvement_score >= 0 ? '+' : '' }}{{ cycle.improvement_score.toFixed(1) }}%
                        </span>
                      </div>
                      <div class="detail-item">
                        <span class="detail-label">开始时间</span>
                        <span class="detail-value">{{ formatTime(cycle.start_time) }}</span>
                      </div>
                      <div class="detail-item">
                        <span class="detail-label">结束时间</span>
                        <span class="detail-value">{{ cycle.end_time ? formatTime(cycle.end_time) : '进行中' }}</span>
                      </div>
                    </div>

                    <div class="capabilities-panel" v-if="capabilities">
                      <el-divider content-position="left">四大能力状态</el-divider>
                      <div class="cap-grid">
                        <div class="cap-item" v-for="(cap, key) in capabilities" :key="key">
                          <div class="cap-icon" :class="cap.enabled ? 'cap-on' : 'cap-off'">
                            <el-icon :size="20"><component :is="getCapIcon(key)" /></el-icon>
                          </div>
                          <div class="cap-info">
                            <span class="cap-name">{{ getCapName(key) }}</span>
                            <el-tag :type="cap.enabled ? 'success' : 'info'" size="small">
                              {{ cap.enabled ? cap.status : '未启用' }}
                            </el-tag>
                            <span class="cap-last-run">{{ cap.last_run ? formatTime(cap.last_run) : '-' }}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </transition>

                <div class="expand-hint" v-if="!expandedCycles.has(cycle.cycle_id)">
                  <el-icon><ArrowDown /></el-icon>
                  <span>展开详情</span>
                </div>
              </div>
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
import {
  Refresh,
  Loading,
  Timer,
  TrendCharts,
  Clock,
  ArrowDown,
  Cpu,
  MagicStick,
  SetUp,
  CircleCheck
} from '@element-plus/icons-vue'
import { evolutionStatusApi, type EvolutionCycleSummary, type EvolutionStatusOverview } from '@/api'

const loading = ref(false)
const timeFilter = ref('7d')
const cycles = ref<EvolutionCycleSummary[]>([])
const expandedCycles = ref(new Set<string>())
const evolutionOverview = ref<EvolutionStatusOverview | null>(null)

const capabilities = computed(() => evolutionOverview.value?.capabilities)

const evolutionRunning = computed(() => {
  return evolutionOverview.value?.status === 'running'
})

async function fetchCycles() {
  loading.value = true
  try {
    const periodMap: Record<string, string> = { '7d': '7d', '30d': '30d', 'all': 'all' }
    const [cyclesData, overviewData] = await Promise.all([
      evolutionStatusApi.getCycles(periodMap[timeFilter.value]),
      evolutionStatusApi.getStatus()
    ])
    cycles.value = Array.isArray(cyclesData) ? cyclesData : []
    evolutionOverview.value = overviewData
  } catch (error) {
    console.error('获取演化数据失败:', error)
    ElMessage.error('加载演化历史失败')
  } finally {
    loading.value = false
  }
}

function isCurrentCycle(cycle: EvolutionCycleSummary): boolean {
  return evolutionOverview.value?.current_cycle_id === cycle.cycle_id
}

function toggleExpand(cycleId: string) {
  if (expandedCycles.value.has(cycleId)) {
    expandedCycles.value.delete(cycleId)
  } else {
    expandedCycles.value.add(cycleId)
  }
  expandedCycles.value = new Set(expandedCycles.value)
}

function getPhaseColor(phase: string): string {
  const colors: Record<string, string> = {
    analysis: 'phase-red',
    planning: 'phase-green',
    execution: 'phase-blue',
    validation: 'phase-yellow',
    review: 'phase-purple'
  }
  return colors[phase] || 'phase-gray'
}

function getPhaseLetter(phase: string): string {
  const letters: Record<string, string> = {
    analysis: '析', planning: '规', execution: '执', validation: '验', review: '审'
  }
  return letters[phase] || '?'
}

function getPhaseLabel(phase: string): string {
  const labels: Record<string, string> = {
    analysis: '分析阶段',
    planning: '规划阶段',
    execution: '执行阶段',
    validation: '验证阶段',
    review: '评审阶段'
  }
  return labels[phase] || phase
}

function getPhaseTagType(phase: string): '' | 'success' | 'warning' | 'danger' | 'info' | 'primary' {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info' | 'primary'> = {
    analysis: 'danger',
    planning: 'primary',
    execution: 'success',
    warning: 'warning',
    review: 'info'
  }
  return types[phase] || 'info'
}

function getStatusType(status: string): '' | 'success' | 'warning' | 'danger' | 'info' {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    completed: 'success',
    running: 'primary',
    failed: 'danger',
    paused: 'warning',
    idle: 'info'
  }
  return types[status] || 'info'
}

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    completed: '已完成', running: '运行中', failed: '失败', paused: '已暂停', idle: '空闲'
  }
  return labels[status] || status
}

function getCapIcon(key: string) {
  const icons: Record<string, any> = {
    self_iteration: Cpu,
    self_optimization: MagicStick,
    self_repair: SetUp,
    self_improvement: CircleCheck
  }
  return icons[key] || Cpu
}

function getCapName(key: string): string {
  const names: Record<string, string> = {
    self_iteration: '自迭代',
    self_optimization: '自优化',
    self_repair: '自修复',
    self_improvement: '自完善'
  }
  return names[key] || key
}

function formatTime(time: string): string {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

function formatDuration(seconds: number): string {
  if (!seconds || seconds <= 0) return '-'
  if (seconds < 60) return `${seconds.toFixed(0)}秒`
  if (seconds < 3600) return `${(seconds / 60).toFixed(1)}分钟`
  return `${(seconds / 3600).toFixed(1)}小时`
}

onMounted(() => {
  fetchCycles()
})
</script>

<style scoped>
.skill-evolution-timeline {
  width: 100%;
}

.timeline-card {
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
  gap: 10px;
}

.timeline-content {
  padding: 5px 0;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 60px 0;
  color: #909399;
}

.timeline-wrapper {
  padding: 10px 0;
}

.timeline-track {
  position: relative;
  padding-left: 40px;
}

.timeline-line {
  position: absolute;
  left: 19px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: linear-gradient(to bottom, #409eff, #67c23a);
  border-radius: 1px;
}

.timeline-node {
  position: relative;
  margin-bottom: 24px;
  animation: node-fade-in 0.4s ease both;
  animation-delay: var(--delay, 0s);
  opacity: 0;
}

@keyframes node-fade-in {
  from { opacity: 0; transform: translateX(-10px); }
  to { opacity: 1; transform: translateX(0); }
}

.node-marker {
  position: absolute;
  left: -31px;
  top: 12px;
  z-index: 2;
}

.marker-inner {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 700;
  font-size: 13px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transition: transform 0.2s;
}

.phase-red { background: linear-gradient(135deg, #f56c6c, #f78989); }
.phase-green { background: linear-gradient(135deg, #67c23a, #85ce61); }
.phase-blue { background: linear-gradient(135deg, #409eff, #66b1ff); }
.phase-yellow { background: linear-gradient(135deg, #e6a23c, #ebb563); }
.phase-purple { background: linear-gradient(135deg, #909399, #b1b3b8); }
.phase-gray { background: linear-gradient(135deg, #c0c4cc, #dcdfe6); }

.marker-active .marker-inner {
  transform: scale(1.15);
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.25);
}

.pulse-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  border: 2px solid #409eff;
  animation: pulse-expand 2s infinite;
}

@keyframes pulse-expand {
  0% { transform: translate(-50%, -50%) scale(1); opacity: 0.6; }
  100% { transform: translate(-50%, -50%) scale(2.2); opacity: 0; }
}

.node-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 10px;
  padding: 16px 18px;
  cursor: pointer;
  transition: all 0.25s ease;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.node-card:hover {
  border-color: #c6e2ff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.1);
  transform: translateY(-1px);
}

.node-active > .node-card {
  border-color: #409eff;
  background: linear-gradient(135deg, #ecf5ff, #fff);
}

.node-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  flex-wrap: wrap;
  gap: 8px;
}

.node-id {
  display: flex;
  align-items: center;
  gap: 8px;
}

.cycle-label {
  font-size: 12px;
  color: #909399;
}

.cycle-num {
  font-weight: 700;
  font-size: 15px;
  color: #303133;
}

.node-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.meta-row {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #606266;
}

.score-positive { color: #67c23a; }
.score-negative { color: #f56c6c; }
.text-success { color: #67c23a !important; }
.text-danger { color: #f56c6c !important; }

.node-detail {
  overflow: hidden;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.detail-label {
  font-size: 11px;
  color: #909399;
}

.detail-value {
  font-size: 13px;
  color: #303133;
  font-weight: 500;
}

.detail-value.mono {
  font-family: monospace;
  font-size: 12px;
  word-break: break-all;
}

.capabilities-panel {
  margin-top: 4px;
}

.cap-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.cap-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.cap-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.cap-on { background: #e1f3d8; color: #67c23a; }
.cap-off { background: #f4f4f5; color: #909399; }

.cap-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.cap-name {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
}

.cap-last-run {
  font-size: 11px;
  color: #909399;
}

.expand-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}
.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
  margin-top: 0;
  padding-top: 0;
  padding-bottom: 0;
}

@media (max-width: 768px) {
  .timeline-track { padding-left: 30px; }
  .node-marker { left: -25px; }
  .marker-inner { width: 32px; height: 32px; font-size: 11px; }
  .pulse-ring { width: 32px; height: 32px; }
  .timeline-line { left: 15px; }
  .detail-grid { grid-template-columns: 1fr; }
  .cap-grid { grid-template-columns: 1fr; }
  .meta-row { flex-direction: column; gap: 4px; }
}
</style>
