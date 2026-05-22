<template>
  <el-card class="requirement-structurer" shadow="hover">
    <template #header>
      <div class="card-header">
        <span class="title">需求结构化</span>
        <div class="header-actions">
          <el-tag v-if="userStories.length" type="info" size="small">
            {{ userStories.length }} 个用户故事
          </el-tag>
          <el-button type="primary" size="small" @click="handleConfirm" :disabled="!canConfirm">
            <el-icon><Check /></el-icon>
            确认需求
          </el-button>
        </div>
      </div>
    </template>

    <el-tabs v-model="activeTab" class="structure-tabs">
      <el-tab-pane label="用户故事" name="stories">
        <div v-if="!userStories || userStories.length === 0" class="empty-container">
          <el-empty description="暂无用户故事" :image-size="80" />
        </div>
        <div v-else class="stories-list">
          <div
            v-for="(story, index) in userStories"
            :key="story.id || index"
            class="story-item"
          >
            <div class="story-header">
              <el-tag type="primary" size="small">{{ story.id || `US-${index + 1}` }}</el-tag>
              <span class="story-title">{{ story.title }}</span>
              <el-button
                v-if="editable"
                type="primary"
                link
                size="small"
                @click="editStory(story, index)"
              >
                编辑
              </el-button>
            </div>
            <div class="story-content">
              <div class="story-format">
                <span class="format-label">作为</span>
                <span class="format-value">{{ story.role }}</span>
                <span class="format-label">，我希望</span>
                <span class="format-value">{{ story.action }}</span>
                <span class="format-label">，以便</span>
                <span class="format-value">{{ story.benefit }}</span>
              </div>
            </div>
            <div v-if="story.acceptanceCriteria && story.acceptanceCriteria.length > 0" class="acceptance-criteria">
              <div class="criteria-title">验收标准 (Gherkin)</div>
              <div
                v-for="(criteria, cIndex) in story.acceptanceCriteria"
                :key="cIndex"
                class="criteria-item"
              >
                <div class="gherkin-scenario">
                  <div class="gherkin-line keyword">Scenario: {{ criteria.scenario }}</div>
                  <div class="gherkin-line">
                    <span class="keyword">Given</span>
                    <span>{{ criteria.given }}</span>
                  </div>
                  <div class="gherkin-line">
                    <span class="keyword">When</span>
                    <span>{{ criteria.when }}</span>
                  </div>
                  <div class="gherkin-line">
                    <span class="keyword">Then</span>
                    <span>{{ criteria.then }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="功能点列表" name="features">
        <div v-if="!features || features.length === 0" class="empty-container">
          <el-empty description="暂无功能点" :image-size="80" />
        </div>
        <el-table v-else :data="features" stripe border style="width: 100%">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="name" label="功能名称" min-width="150" />
          <el-table-column prop="description" label="描述" min-width="200" />
          <el-table-column prop="priority" label="优先级" width="100">
            <template #default="{ row }">
              <el-tag :type="getPriorityType(row.priority)" size="small">
                {{ getPriorityLabel(row.priority) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)" size="small">
                {{ getStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column v-if="editable" label="操作" width="100" fixed="right">
            <template #default="{ row, $index }">
              <el-button type="primary" link size="small" @click="editFeature(row, $index)">
                编辑
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="数据模型" name="models">
        <div v-if="!dataModels || dataModels.length === 0" class="empty-container">
          <el-empty description="暂无数据模型" :image-size="80" />
        </div>
        <div v-else class="models-container">
          <div
            v-for="(model, index) in dataModels"
            :key="model.name || index"
            class="model-card"
          >
            <div class="model-header">
              <el-icon><Document /></el-icon>
              <span class="model-name">{{ model.name }}</span>
              <el-tag size="small" type="info">{{ model.type || 'Entity' }}</el-tag>
            </div>
            <div class="model-fields">
              <div
                v-for="field in model.fields"
                :key="field.name"
                class="field-item"
              >
                <span class="field-name">{{ field.name }}</span>
                <span class="field-type">{{ field.type }}</span>
                <el-tag v-if="field.required" type="danger" size="small">必填</el-tag>
                <el-tag v-if="field.primaryKey" type="warning" size="small">主键</el-tag>
              </div>
            </div>
            <div v-if="model.stateTransitions && model.stateTransitions.length > 0" class="state-transitions">
              <div class="transitions-title">状态变更图</div>
              <div class="transitions-diagram">
                <div
                  v-for="(trans, tIndex) in model.stateTransitions"
                  :key="tIndex"
                  class="transition-item"
                >
                  <span class="state-node">{{ trans.from }}</span>
                  <el-icon class="arrow"><Right /></el-icon>
                  <span class="transition-label">{{ trans.action }}</span>
                  <el-icon class="arrow"><Right /></el-icon>
                  <span class="state-node">{{ trans.to }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="editDialogVisible" :title="editType === 'story' ? '编辑用户故事' : '编辑功能点'" width="600px">
      <div v-if="editType === 'story'" class="edit-form">
        <el-form :model="currentEditItem" label-width="80px">
          <el-form-item label="标题">
            <el-input v-model="currentEditItem.title" />
          </el-form-item>
          <el-form-item label="角色">
            <el-input v-model="currentEditItem.role" />
          </el-form-item>
          <el-form-item label="行为">
            <el-input v-model="currentEditItem.action" />
          </el-form-item>
          <el-form-item label="收益">
            <el-input v-model="currentEditItem.benefit" />
          </el-form-item>
        </el-form>
      </div>
      <div v-else class="edit-form">
        <el-form :model="currentEditItem" label-width="80px">
          <el-form-item label="名称">
            <el-input v-model="currentEditItem.name" />
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="currentEditItem.description" type="textarea" :rows="3" />
          </el-form-item>
          <el-form-item label="优先级">
            <el-select v-model="currentEditItem.priority">
              <el-option label="高" value="high" />
              <el-option label="中" value="medium" />
              <el-option label="低" value="low" />
            </el-select>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed, defineProps, defineEmits } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, Document, Right } from '@element-plus/icons-vue'

interface AcceptanceCriteria {
  scenario: string
  given: string
  when: string
  then: string
}

interface UserStory {
  id?: string
  title: string
  role: string
  action: string
  benefit: string
  acceptanceCriteria?: AcceptanceCriteria[]
}

interface Feature {
  id: string
  name: string
  description: string
  priority: 'high' | 'medium' | 'low'
  status: 'pending' | 'in_progress' | 'completed'
}

interface Field {
  name: string
  type: string
  required?: boolean
  primaryKey?: boolean
}

interface StateTransition {
  from: string
  to: string
  action: string
}

interface DataModel {
  name: string
  type?: string
  fields: Field[]
  stateTransitions?: StateTransition[]
}

const props = defineProps<{
  userStories: UserStory[]
  features: Feature[]
  dataModels: DataModel[]
  editable?: boolean
}>()

const emit = defineEmits<{
  (e: 'confirm', data: { userStories: UserStory[]; features: Feature[]; dataModels: DataModel[] }): void
  (e: 'update:userStories', value: UserStory[]): void
  (e: 'update:features', value: Feature[]): void
}>()

const activeTab = ref('stories')
const editDialogVisible = ref(false)
const editType = ref<'story' | 'feature'>('story')
const currentEditItem = ref<Record<string, any>>({})
const currentEditIndex = ref(-1)

const canConfirm = computed(() => {
  return props.userStories && props.userStories.length > 0
})

const priorityMap: Record<string, { label: string; type: string }> = {
  high: { label: '高', type: 'danger' },
  medium: { label: '中', type: 'warning' },
  low: { label: '低', type: 'info' }
}

const statusMap: Record<string, { label: string; type: string }> = {
  pending: { label: '待处理', type: 'info' },
  in_progress: { label: '进行中', type: 'warning' },
  completed: { label: '已完成', type: 'success' }
}

const getPriorityType = (priority: string) => priorityMap[priority]?.type || 'info'
const getPriorityLabel = (priority: string) => priorityMap[priority]?.label || priority
const getStatusType = (status: string) => statusMap[status]?.type || 'info'
const getStatusLabel = (status: string) => statusMap[status]?.label || status

const editStory = (story: UserStory, index: number) => {
  editType.value = 'story'
  currentEditItem.value = { ...story }
  currentEditIndex.value = index
  editDialogVisible.value = true
}

const editFeature = (feature: Feature, index: number) => {
  editType.value = 'feature'
  currentEditItem.value = { ...feature }
  currentEditIndex.value = index
  editDialogVisible.value = true
}

const saveEdit = () => {
  if (editType.value === 'story') {
    const updated = [...props.userStories]
    updated[currentEditIndex.value] = currentEditItem.value as UserStory
    emit('update:userStories', updated)
  } else {
    const updated = [...props.features]
    updated[currentEditIndex.value] = currentEditItem.value as Feature
    emit('update:features', updated)
  }
  editDialogVisible.value = false
  ElMessage.success('保存成功')
}

const handleConfirm = () => {
  emit('confirm', {
    userStories: props.userStories,
    features: props.features,
    dataModels: props.dataModels
  })
  ElMessage.success('需求已确认')
}
</script>

<style scoped>
.requirement-structurer {
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

.empty-container {
  padding: 20px 0;
}

.stories-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.story-item {
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #fafafa;
}

.story-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.story-title {
  font-weight: 500;
  flex: 1;
}

.story-content {
  margin-bottom: 12px;
}

.story-format {
  line-height: 1.8;
  font-size: 14px;
}

.format-label {
  color: #909399;
}

.format-value {
  color: #303133;
  font-weight: 500;
}

.acceptance-criteria {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #ebeef5;
}

.criteria-title {
  font-size: 13px;
  color: #606266;
  margin-bottom: 10px;
  font-weight: 500;
}

.criteria-item {
  margin-bottom: 10px;
}

.gherkin-scenario {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
  font-family: 'Consolas', monospace;
  font-size: 13px;
}

.gherkin-line {
  margin-bottom: 4px;
}

.gherkin-line:last-child {
  margin-bottom: 0;
}

.gherkin-line .keyword {
  color: #409eff;
  font-weight: bold;
  margin-right: 8px;
}

.models-container {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.model-card {
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #fff;
}

.model-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

.model-name {
  font-weight: 500;
  font-size: 15px;
  flex: 1;
}

.model-fields {
  margin-bottom: 12px;
}

.field-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px dashed #f0f0f0;
}

.field-item:last-child {
  border-bottom: none;
}

.field-name {
  font-weight: 500;
  color: #303133;
}

.field-type {
  color: #909399;
  font-size: 12px;
}

.state-transitions {
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
}

.transitions-title {
  font-size: 13px;
  color: #606266;
  margin-bottom: 10px;
  font-weight: 500;
}

.transitions-diagram {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.transition-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.state-node {
  padding: 4px 12px;
  background: #ecf5ff;
  border-radius: 4px;
  color: #409eff;
  font-weight: 500;
}

.arrow {
  color: #c0c4cc;
}

.transition-label {
  color: #67c23a;
  font-size: 12px;
}

.edit-form {
  padding: 10px 0;
}

.structure-tabs {
  min-height: 300px;
}
</style>
