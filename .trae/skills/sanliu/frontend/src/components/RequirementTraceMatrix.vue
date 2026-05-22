<template>
  <el-card class="requirement-trace-matrix" shadow="hover">
    <template #header>
      <div class="card-header">
        <span class="title">需求追踪矩阵</span>
        <div class="header-actions">
          <el-tag type="success" size="small">
            覆盖率: {{ coverageRate }}%
          </el-tag>
          <el-button type="primary" size="small" @click="refreshMatrix">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </template>

    <div class="matrix-container">
      <div class="coverage-summary">
        <div class="summary-item">
          <div class="summary-value">{{ totalRequirements }}</div>
          <div class="summary-label">需求总数</div>
        </div>
        <div class="summary-item">
          <div class="summary-value covered">{{ coveredRequirements }}</div>
          <div class="summary-label">已覆盖</div>
        </div>
        <div class="summary-item">
          <div class="summary-value uncovered">{{ uncoveredRequirements }}</div>
          <div class="summary-label">未覆盖</div>
        </div>
        <div class="summary-item">
          <div class="summary-value">{{ totalTests }}</div>
          <div class="summary-label">测试用例</div>
        </div>
      </div>

      <el-divider />

      <div class="matrix-filter">
        <el-select v-model="filterStatus" placeholder="筛选状态" clearable size="small">
          <el-option label="全部" value="" />
          <el-option label="已覆盖" value="covered" />
          <el-option label="部分覆盖" value="partial" />
          <el-option label="未覆盖" value="uncovered" />
        </el-select>
        <el-input
          v-model="searchKeyword"
          placeholder="搜索需求..."
          clearable
          size="small"
          style="width: 200px"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <el-table
        :data="filteredMatrix"
        stripe
        border
        style="width: 100%"
        max-height="500"
      >
        <el-table-column prop="requirementId" label="需求ID" width="120" fixed />
        <el-table-column prop="requirementName" label="需求名称" min-width="180" />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTypeTag(row.type)" size="small">
              {{ getTypeLabel(row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="关联功能" min-width="150">
          <template #default="{ row }">
            <div v-if="row.features && row.features.length > 0" class="link-tags">
              <el-tag
                v-for="feature in row.features"
                :key="feature.id"
                size="small"
                type="info"
                class="link-tag"
              >
                {{ feature.name }}
              </el-tag>
            </div>
            <span v-else class="no-link">-</span>
          </template>
        </el-table-column>
        <el-table-column label="关联测试" min-width="150">
          <template #default="{ row }">
            <div v-if="row.tests && row.tests.length > 0" class="link-tags">
              <el-tag
                v-for="test in row.tests"
                :key="test.id"
                size="small"
                :type="test.status === 'passed' ? 'success' : test.status === 'failed' ? 'danger' : 'info'"
                class="link-tag"
              >
                {{ test.name }}
              </el-tag>
            </div>
            <span v-else class="no-link">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="覆盖状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getCoverageStatusTag(row.status)" size="small">
              {{ getCoverageStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="viewDetail(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="detailVisible" title="需求追踪详情" width="600px">
      <div v-if="currentDetail" class="detail-content">
        <div class="detail-section">
          <div class="section-title">需求信息</div>
          <div class="info-grid">
            <div class="info-item">
              <span class="label">ID：</span>
              <span>{{ currentDetail.requirementId }}</span>
            </div>
            <div class="info-item">
              <span class="label">名称：</span>
              <span>{{ currentDetail.requirementName }}</span>
            </div>
            <div class="info-item">
              <span class="label">类型：</span>
              <span>{{ getTypeLabel(currentDetail.type) }}</span>
            </div>
            <div class="info-item">
              <span class="label">状态：</span>
              <el-tag :type="getCoverageStatusTag(currentDetail.status)" size="small">
                {{ getCoverageStatusLabel(currentDetail.status) }}
              </el-tag>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <div class="section-title">关联功能点</div>
          <div v-if="currentDetail.features && currentDetail.features.length > 0" class="link-list">
            <div v-for="feature in currentDetail.features" :key="feature.id" class="link-item">
              <el-icon><Connection /></el-icon>
              <span>{{ feature.id }} - {{ feature.name }}</span>
            </div>
          </div>
          <div v-else class="no-data">暂无关联功能点</div>
        </div>

        <div class="detail-section">
          <div class="section-title">关联测试用例</div>
          <div v-if="currentDetail.tests && currentDetail.tests.length > 0" class="link-list">
            <div v-for="test in currentDetail.tests" :key="test.id" class="link-item">
              <el-icon><DocumentChecked /></el-icon>
              <span>{{ test.id }} - {{ test.name }}</span>
              <el-tag :type="test.status === 'passed' ? 'success' : test.status === 'failed' ? 'danger' : 'info'" size="small">
                {{ test.status === 'passed' ? '通过' : test.status === 'failed' ? '失败' : '未执行' }}
              </el-tag>
            </div>
          </div>
          <div v-else class="no-data">暂无关联测试用例</div>
        </div>
      </div>
    </el-dialog>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed, defineProps, defineEmits } from 'vue'
import { Refresh, Search, Connection, DocumentChecked } from '@element-plus/icons-vue'

interface Feature {
  id: string
  name: string
}

interface Test {
  id: string
  name: string
  status: 'passed' | 'failed' | 'pending'
}

interface TraceItem {
  requirementId: string
  requirementName: string
  type: 'functional' | 'non_functional' | 'business'
  features?: Feature[]
  tests?: Test[]
  status: 'covered' | 'partial' | 'uncovered'
}

const props = defineProps<{
  matrix: TraceItem[]
}>()

const emit = defineEmits<{
  (e: 'refresh'): void
}>()

const filterStatus = ref('')
const searchKeyword = ref('')
const detailVisible = ref(false)
const currentDetail = ref<TraceItem | null>(null)

const totalRequirements = computed(() => props.matrix.length)

const coveredRequirements = computed(() =>
  props.matrix.filter(item => item.status === 'covered').length
)

const uncoveredRequirements = computed(() =>
  props.matrix.filter(item => item.status === 'uncovered').length
)

const totalTests = computed(() =>
  props.matrix.reduce((sum, item) => sum + (item.tests?.length || 0), 0)
)

const coverageRate = computed(() => {
  if (totalRequirements.value === 0) return 0
  const covered = props.matrix.filter(item =>
    item.status === 'covered' || item.status === 'partial'
  ).length
  return Math.round((covered / totalRequirements.value) * 100)
})

const filteredMatrix = computed(() => {
  let result = props.matrix

  if (filterStatus.value) {
    result = result.filter(item => item.status === filterStatus.value)
  }

  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(item =>
      item.requirementId.toLowerCase().includes(keyword) ||
      item.requirementName.toLowerCase().includes(keyword)
    )
  }

  return result
})

const typeMap: Record<string, { label: string; type: string }> = {
  functional: { label: '功能性', type: 'primary' },
  non_functional: { label: '非功能性', type: 'warning' },
  business: { label: '业务性', type: 'success' }
}

const coverageStatusMap: Record<string, { label: string; type: string }> = {
  covered: { label: '已覆盖', type: 'success' },
  partial: { label: '部分覆盖', type: 'warning' },
  uncovered: { label: '未覆盖', type: 'danger' }
}

const getTypeTag = (type: string) => typeMap[type]?.type || 'info'
const getTypeLabel = (type: string) => typeMap[type]?.label || type
const getCoverageStatusTag = (status: string) => coverageStatusMap[status]?.type || 'info'
const getCoverageStatusLabel = (status: string) => coverageStatusMap[status]?.label || status

const refreshMatrix = () => {
  emit('refresh')
}

const viewDetail = (row: TraceItem) => {
  currentDetail.value = row
  detailVisible.value = true
}
</script>

<style scoped>
.requirement-trace-matrix {
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

.coverage-summary {
  display: flex;
  justify-content: space-around;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.summary-item {
  text-align: center;
}

.summary-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.summary-value.covered {
  color: #67c23a;
}

.summary-value.uncovered {
  color: #f56c6c;
}

.summary-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.matrix-filter {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.link-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.link-tag {
  margin: 2px 0;
}

.no-link {
  color: #c0c4cc;
}

.detail-content {
  padding: 10px 0;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.section-title {
  font-weight: 500;
  font-size: 14px;
  color: #303133;
  margin-bottom: 12px;
  padding-left: 10px;
  border-left: 3px solid #409eff;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.info-item {
  font-size: 14px;
}

.info-item .label {
  color: #909399;
}

.link-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.link-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 13px;
}

.no-data {
  color: #909399;
  font-size: 13px;
  text-align: center;
  padding: 20px;
}

.el-divider {
  margin: 20px 0;
}
</style>
