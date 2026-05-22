<template>
  <el-card class="clarification-dialog" shadow="hover">
    <template #header>
      <div class="card-header">
        <span class="title">澄清问题</span>
        <div class="header-stats">
          <el-tag type="warning" size="small" v-if="pendingCount > 0">
            {{ pendingCount }} 待回答
          </el-tag>
          <el-tag type="success" size="small" v-if="answeredCount > 0">
            {{ answeredCount }} 已回答
          </el-tag>
          <el-tag type="info" size="small" v-if="confirmedCount > 0">
            {{ confirmedCount }} 已确认
          </el-tag>
        </div>
      </div>
    </template>

    <div v-if="!questions || questions.length === 0" class="empty-container">
      <el-empty description="暂无澄清问题" :image-size="80" />
    </div>

    <div v-else class="questions-list">
      <div
        v-for="(question, index) in questions"
        :key="question.id || index"
        class="question-item"
        :class="getStatusClass(question.status)"
      >
        <div class="question-header">
          <div class="question-meta">
            <el-tag :type="getStatusTag(question.status)" size="small">
              {{ getStatusLabel(question.status) }}
            </el-tag>
            <span class="question-id">{{ question.id || `Q-${index + 1}` }}</span>
          </div>
          <div class="question-priority">
            <el-tag :type="getPriorityType(question.priority)" size="small" effect="plain">
              {{ getPriorityLabel(question.priority) }}优先级
            </el-tag>
          </div>
        </div>

        <div class="question-content">
          <div class="question-text">
            <el-icon class="q-icon"><QuestionFilled /></el-icon>
            {{ question.question }}
          </div>
          <div v-if="question.context" class="question-context">
            <span class="context-label">上下文：</span>
            {{ question.context }}
          </div>
        </div>

        <div class="answer-section">
          <div v-if="question.status === 'pending'" class="answer-input">
            <el-input
              v-model="answers[question.id || index]"
              type="textarea"
              :rows="3"
              placeholder="请输入您的回答..."
              @input="handleAnswerInput(question.id || index)"
            />
            <div class="answer-actions">
              <el-button
                type="primary"
                size="small"
                @click="submitAnswer(question, index)"
                :disabled="!answers[question.id || index]"
              >
                提交回答
              </el-button>
            </div>
          </div>

          <div v-else class="answer-display">
            <div class="answer-label">
              <el-icon><ChatDotRound /></el-icon>
              回答
            </div>
            <div class="answer-text">{{ question.answer }}</div>
            <div v-if="question.answeredAt" class="answer-time">
              回答时间：{{ formatTime(question.answeredAt) }}
            </div>
          </div>
        </div>

        <div v-if="question.status === 'answered'" class="confirm-section">
          <el-button
            type="success"
            size="small"
            @click="confirmAnswer(question, index)"
          >
            <el-icon><Check /></el-icon>
            确认答案
          </el-button>
          <el-button
            type="warning"
            size="small"
            @click="requestRevision(question, index)"
          >
            <el-icon><Edit /></el-icon>
            要求修改
          </el-button>
        </div>

        <div v-if="question.status === 'confirmed'" class="confirmed-badge">
          <el-icon><CircleCheck /></el-icon>
          已确认
        </div>
      </div>
    </div>

    <div class="summary-actions">
      <el-button
        type="primary"
        @click="confirmAll"
        :disabled="!canConfirmAll"
      >
        <el-icon><Finished /></el-icon>
        确认所有回答
      </el-button>
      <el-button @click="exportQuestions">
        <el-icon><Download /></el-icon>
        导出问答
      </el-button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed, defineProps, defineEmits } from 'vue'
import { ElMessage } from 'element-plus'
import {
  QuestionFilled,
  ChatDotRound,
  Check,
  Edit,
  CircleCheck,
  Finished,
  Download
} from '@element-plus/icons-vue'

interface Question {
  id?: string
  question: string
  context?: string
  priority: 'high' | 'medium' | 'low'
  status: 'pending' | 'answered' | 'confirmed'
  answer?: string
  answeredAt?: string
}

const props = defineProps<{
  questions: Question[]
}>()

const emit = defineEmits<{
  (e: 'answer', questionId: string | number, answer: string): void
  (e: 'confirm', questionId: string | number): void
  (e: 'revise', questionId: string | number): void
  (e: 'confirmAll'): void
}>()

const answers = ref<Record<string | number, string>>({})

const pendingCount = computed(() =>
  props.questions.filter(q => q.status === 'pending').length
)

const answeredCount = computed(() =>
  props.questions.filter(q => q.status === 'answered').length
)

const confirmedCount = computed(() =>
  props.questions.filter(q => q.status === 'confirmed').length
)

const canConfirmAll = computed(() =>
  props.questions.every(q => q.status === 'answered' || q.status === 'confirmed')
)

const statusMap: Record<string, { label: string; type: string }> = {
  pending: { label: '待回答', type: 'warning' },
  answered: { label: '已回答', type: 'primary' },
  confirmed: { label: '已确认', type: 'success' }
}

const priorityMap: Record<string, { label: string; type: string }> = {
  high: { label: '高', type: 'danger' },
  medium: { label: '中', type: 'warning' },
  low: { label: '低', type: 'info' }
}

const getStatusTag = (status: string) => statusMap[status]?.type || 'info'
const getStatusLabel = (status: string) => statusMap[status]?.label || status
const getStatusClass = (status: string) => `status-${status}`
const getPriorityType = (priority: string) => priorityMap[priority]?.type || 'info'
const getPriorityLabel = (priority: string) => priorityMap[priority]?.label || priority

const formatTime = (time?: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const handleAnswerInput = (id: string | number) => {
}

const submitAnswer = (question: Question, index: number) => {
  const answer = answers.value[question.id || index]
  if (!answer) return

  emit('answer', question.id || index, answer)
  ElMessage.success('回答已提交')
}

const confirmAnswer = (question: Question, index: number) => {
  emit('confirm', question.id || index)
  ElMessage.success('答案已确认')
}

const requestRevision = (question: Question, index: number) => {
  emit('revise', question.id || index)
  ElMessage.info('已要求修改回答')
}

const confirmAll = () => {
  emit('confirmAll')
  ElMessage.success('所有回答已确认')
}

const exportQuestions = () => {
  const data = props.questions.map(q => ({
    问题: q.question,
    上下文: q.context || '',
    回答: q.answer || '',
    状态: getStatusLabel(q.status)
  }))

  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `clarification-qa-${Date.now()}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)

  ElMessage.success('问答已导出')
}
</script>

<style scoped>
.clarification-dialog {
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

.header-stats {
  display: flex;
  gap: 8px;
}

.empty-container {
  padding: 20px 0;
}

.questions-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: 600px;
  overflow-y: auto;
}

.question-item {
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #fff;
  transition: all 0.3s;
}

.question-item.status-pending {
  border-left: 4px solid #e6a23c;
}

.question-item.status-answered {
  border-left: 4px solid #409eff;
}

.question-item.status-confirmed {
  border-left: 4px solid #67c23a;
  background: #f0f9eb;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.question-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.question-id {
  font-weight: 500;
  color: #606266;
}

.question-content {
  margin-bottom: 12px;
}

.question-text {
  font-size: 14px;
  color: #303133;
  line-height: 1.6;
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.q-icon {
  color: #409eff;
  margin-top: 2px;
}

.question-context {
  margin-top: 8px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 13px;
  color: #606266;
}

.context-label {
  color: #909399;
}

.answer-section {
  margin-top: 12px;
}

.answer-input {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.answer-actions {
  display: flex;
  justify-content: flex-end;
}

.answer-display {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.answer-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.answer-text {
  font-size: 14px;
  color: #303133;
  line-height: 1.6;
}

.answer-time {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

.confirm-section {
  display: flex;
  gap: 10px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #ebeef5;
}

.confirmed-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #ebeef5;
  color: #67c23a;
  font-weight: 500;
}

.summary-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}
</style>
