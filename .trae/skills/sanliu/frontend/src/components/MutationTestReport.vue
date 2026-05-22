<template>
  <el-card class="mutation-test-report" shadow="hover">
    <template #header>
      <div class="card-header">
        <span class="title">突变测试报告</span>
        <div class="header-actions">
          <el-tag :type="scoreStatus.type" size="small">
            突变得分: {{ mutationScore }}%
          </el-tag>
          <el-button type="primary" size="small" @click="refreshReport">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </template>

    <div class="score-dashboard">
      <div class="gauge-container">
        <el-progress
          type="dashboard"
          :percentage="mutationScore"
          :color="scoreColor"
          :width="150"
        >
          <template #default>
            <div class="gauge-content">
              <span class="gauge-value">{{ mutationScore }}</span>
              <span class="gauge-unit">%</span>
              <span class="gauge-label">突变得分</span>
            </div>
          </template>
        </el-progress>
      </div>
      <div class="score-breakdown">
        <div class="breakdown-item">
          <div class="breakdown-value killed">{{ killedMutants }}</div>
          <div class="breakdown-label">已杀死突变</div>
        </div>
        <div class="breakdown-item">
          <div class="breakdown-value survived">{{ survivedMutants }}</div>
          <div class="breakdown-label">存活突变</div>
        </div>
        <div class="breakdown-item">
          <div class="breakdown-value timeout">{{ timeoutMutants }}</div>
          <div class="breakdown-label">超时突变</div>
        </div>
        <div class="breakdown-item">
          <div class="breakdown-value total">{{ totalMutants }}</div>
          <div class="breakdown-label">总突变数</div>
        </div>
      </div>
    </div>

    <el-divider />

    <el-tabs v-model="activeTab">
      <el-tab-pane label="突变详情" name="details">
        <div v-if="!mutants || mutants.length === 0" class="empty-container">
          <el-empty description="暂无突变数据" :image-size="80" />
        </div>
        <el-table v-else :data="filteredMutants" stripe border style="width: 100%" max-height="400">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="file" label="文件" min-width="150" />
          <el-table-column prop="line" label="行号" width="80" />
          <el-table-column prop="type" label="突变类型" width="120">
            <template #default="{ row }">
              <el-tag :type="getMutantTypeTag(row.type)" size="small">
                {{ getMutantTypeLabel(row.type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="原始代码" min-width="150">
            <template #default="{ row }">
              <code class="code-snippet">{{ row.original }}</code>
            </template>
          </el-table-column>
          <el-table-column label="突变代码" min-width="150">
            <template #default="{ row }">
              <code class="code-snippet mutated">{{ row.mutated }}</code>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusTag(row.status)" size="small">
                {{ getStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="存活突变" name="survived">
        <div v-if="survivedList.length === 0" class="empty-container">
          <el-empty description="没有存活的突变，测试覆盖良好！" :image-size="80" />
        </div>
        <div v-else class="survived-list">
          <div
            v-for="mutant in survivedList"
            :key="mutant.id"
            class="survived-item"
          >
            <div class="survived-header">
              <el-tag type="danger" size="small">存活</el-tag>
              <span class="mutant-id">{{ mutant.id }}</span>
              <span class="mutant-location">{{ mutant.file }}:{{ mutant.line }}</span>
            </div>
            <div class="survived-code">
              <div class="code-diff">
                <div class="diff-line removed">
                  <span class="diff-marker">-</span>
                  <code>{{ mutant.original }}</code>
                </div>
                <div class="diff-line added">
                  <span class="diff-marker">+</span>
                  <code>{{ mutant.mutated }}</code>
                </div>
              </div>
            </div>
            <div class="survived-reason" v-if="mutant.reason">
              <span class="label">存活原因：</span>
              {{ mutant.reason }}
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="改进建议" name="suggestions">
        <div v-if="!suggestions || suggestions.length === 0" class="empty-container">
          <el-empty description="暂无改进建议" :image-size="80" />
        </div>
        <div v-else class="suggestions-list">
          <div
            v-for="(suggestion, index) in suggestions"
            :key="index"
            class="suggestion-item"
            :class="'priority-' + suggestion.priority"
          >
            <div class="suggestion-header">
              <el-tag :type="getPriorityTag(suggestion.priority)" size="small">
                {{ getPriorityLabel(suggestion.priority) }}优先级
              </el-tag>
              <span class="suggestion-title">{{ suggestion.title }}</span>
            </div>
            <div class="suggestion-content">
              <div class="suggestion-desc">{{ suggestion.description }}</div>
              <div v-if="suggestion.targetFile" class="suggestion-target">
                <span class="label">目标文件：</span>
                {{ suggestion.targetFile }}
              </div>
              <div v-if="suggestion.suggestedTest" class="suggestion-test">
                <span class="label">建议测试：</span>
                <pre>{{ suggestion.suggestedTest }}</pre>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <div class="filter-bar">
      <el-select v-model="statusFilter" placeholder="筛选状态" clearable size="small">
        <el-option label="全部" value="" />
        <el-option label="已杀死" value="killed" />
        <el-option label="存活" value="survived" />
        <el-option label="超时" value="timeout" />
      </el-select>
      <el-select v-model="typeFilter" placeholder="筛选类型" clearable size="small">
        <el-option label="全部" value="" />
        <el-option label="算术运算" value="arithmetic" />
        <el-option label="条件判断" value="conditional" />
        <el-option label="边界值" value="boundary" />
        <el-option label="返回值" value="return" />
      </el-select>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed, defineProps, defineEmits } from 'vue'
import { Refresh } from '@element-plus/icons-vue'

interface Mutant {
  id: string
  file: string
  line: number
  type: 'arithmetic' | 'conditional' | 'boundary' | 'return'
  original: string
  mutated: string
  status: 'killed' | 'survived' | 'timeout'
  reason?: string
}

interface Suggestion {
  priority: 'high' | 'medium' | 'low'
  title: string
  description: string
  targetFile?: string
  suggestedTest?: string
}

const props = defineProps<{
  mutationScore: number
  mutants: Mutant[]
  suggestions?: Suggestion[]
}>()

const emit = defineEmits<{
  (e: 'refresh'): void
}>()

const activeTab = ref('details')
const statusFilter = ref('')
const typeFilter = ref('')

const killedMutants = computed(() =>
  props.mutants.filter(m => m.status === 'killed').length
)

const survivedMutants = computed(() =>
  props.mutants.filter(m => m.status === 'survived').length
)

const timeoutMutants = computed(() =>
  props.mutants.filter(m => m.status === 'timeout').length
)

const totalMutants = computed(() => props.mutants.length)

const scoreColor = computed(() => {
  if (props.mutationScore >= 80) return '#67c23a'
  if (props.mutationScore >= 60) return '#e6a23c'
  if (props.mutationScore >= 40) return '#f56c6c'
  return '#909399'
})

const scoreStatus = computed(() => {
  if (props.mutationScore >= 80) return { type: 'success' }
  if (props.mutationScore >= 60) return { type: 'warning' }
  return { type: 'danger' }
})

const survivedList = computed(() =>
  props.mutants.filter(m => m.status === 'survived')
)

const filteredMutants = computed(() => {
  let result = props.mutants

  if (statusFilter.value) {
    result = result.filter(m => m.status === statusFilter.value)
  }

  if (typeFilter.value) {
    result = result.filter(m => m.type === typeFilter.value)
  }

  return result
})

const mutantTypeMap: Record<string, { label: string; type: string }> = {
  arithmetic: { label: '算术运算', type: 'primary' },
  conditional: { label: '条件判断', type: 'warning' },
  boundary: { label: '边界值', type: 'danger' },
  return: { label: '返回值', type: 'info' }
}

const statusMap: Record<string, { label: string; type: string }> = {
  killed: { label: '已杀死', type: 'success' },
  survived: { label: '存活', type: 'danger' },
  timeout: { label: '超时', type: 'warning' }
}

const priorityMap: Record<string, { label: string; type: string }> = {
  high: { label: '高', type: 'danger' },
  medium: { label: '中', type: 'warning' },
  low: { label: '低', type: 'info' }
}

const getMutantTypeTag = (type: string) => mutantTypeMap[type]?.type || 'info'
const getMutantTypeLabel = (type: string) => mutantTypeMap[type]?.label || type
const getStatusTag = (status: string) => statusMap[status]?.type || 'info'
const getStatusLabel = (status: string) => statusMap[status]?.label || status
const getPriorityTag = (priority: string) => priorityMap[priority]?.type || 'info'
const getPriorityLabel = (priority: string) => priorityMap[priority]?.label || priority

const refreshReport = () => {
  emit('refresh')
}
</script>

<style scoped>
.mutation-test-report {
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

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.score-dashboard {
  display: flex;
  align-items: center;
  gap: 40px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.gauge-container {
  flex-shrink: 0;
}

.gauge-content {
  text-align: center;
}

.gauge-value {
  font-size: 32px;
  font-weight: bold;
  display: block;
}

.gauge-unit {
  font-size: 16px;
  color: #909399;
}

.gauge-label {
  font-size: 12px;
  color: #909399;
  display: block;
  margin-top: 4px;
}

.score-breakdown {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.breakdown-item {
  text-align: center;
}

.breakdown-value {
  font-size: 24px;
  font-weight: bold;
}

.breakdown-value.killed {
  color: #67c23a;
}

.breakdown-value.survived {
  color: #f56c6c;
}

.breakdown-value.timeout {
  color: #e6a23c;
}

.breakdown-value.total {
  color: #409eff;
}

.breakdown-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.empty-container {
  padding: 20px 0;
}

.code-snippet {
  padding: 2px 6px;
  background: #f5f7fa;
  border-radius: 3px;
  font-size: 12px;
}

.code-snippet.mutated {
  background: #fef0f0;
  color: #f56c6c;
}

.survived-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.survived-item {
  padding: 16px;
  border: 1px solid #f56c6c;
  border-radius: 8px;
  background: #fef0f0;
}

.survived-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.mutant-id {
  font-weight: 500;
}

.mutant-location {
  color: #909399;
  font-size: 12px;
}

.survived-code {
  margin-bottom: 12px;
}

.code-diff {
  padding: 12px;
  background: #fff;
  border-radius: 6px;
  font-family: 'Consolas', monospace;
  font-size: 13px;
}

.diff-line {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 4px 0;
}

.diff-marker {
  width: 16px;
  font-weight: bold;
}

.diff-line.removed .diff-marker {
  color: #f56c6c;
}

.diff-line.removed code {
  color: #f56c6c;
  text-decoration: line-through;
}

.diff-line.added .diff-marker {
  color: #67c23a;
}

.diff-line.added code {
  color: #67c23a;
  background: #f0f9eb;
  padding: 0 4px;
  border-radius: 2px;
}

.survived-reason {
  font-size: 13px;
  color: #606266;
}

.survived-reason .label {
  color: #909399;
}

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.suggestion-item {
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #fff;
}

.suggestion-item.priority-high {
  border-left: 4px solid #f56c6c;
}

.suggestion-item.priority-medium {
  border-left: 4px solid #e6a23c;
}

.suggestion-item.priority-low {
  border-left: 4px solid #409eff;
}

.suggestion-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.suggestion-title {
  font-weight: 500;
  color: #303133;
}

.suggestion-content {
  font-size: 13px;
}

.suggestion-desc {
  color: #606266;
  line-height: 1.6;
  margin-bottom: 10px;
}

.suggestion-target,
.suggestion-test {
  margin-top: 8px;
}

.suggestion-target .label,
.suggestion-test .label {
  color: #909399;
}

.suggestion-test pre {
  margin: 8px 0 0 0;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
  font-size: 12px;
  white-space: pre-wrap;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

.el-divider {
  margin: 20px 0;
}
</style>
