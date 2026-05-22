<template>
  <div class="project-list">
    <div class="header">
      <h2>项目列表</h2>
      <el-button type="primary" @click="goToCreate">
        <el-icon><Plus /></el-icon>
        创建项目
      </el-button>
    </div>

    <div class="filters">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-input
            v-model="searchQuery"
            placeholder="搜索项目名称..."
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select v-model="statusFilter" placeholder="状态筛选" clearable @change="handleFilter">
            <el-option
              v-for="status in statusOptions"
              :key="status.value"
              :label="status.label"
              :value="status.value"
            />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="sortBy" placeholder="排序方式" @change="handleSort">
            <el-option label="创建时间（最新）" value="created_at_desc" />
            <el-option label="创建时间（最早）" value="created_at_asc" />
            <el-option label="更新时间（最新）" value="updated_at_desc" />
            <el-option label="更新时间（最早）" value="updated_at_asc" />
            <el-option label="名称（A-Z）" value="name_asc" />
            <el-option label="名称（Z-A）" value="name_desc" />
          </el-select>
        </el-col>
      </el-row>
    </div>

    <div v-loading="loading" class="project-cards">
      <el-row :gutter="20">
        <el-col v-for="project in filteredProjects" :key="project.id" :span="8">
          <el-card shadow="hover" class="project-card" @click="goToDetail(project.id)">
            <template #header>
              <div class="card-header">
                <span class="project-name">{{ project.name }}</span>
                <el-tag :type="getStatusType(project.status)" size="small">
                  {{ getStatusLabel(project.status) }}
                </el-tag>
              </div>
            </template>
            <div class="project-info">
              <p class="description">{{ project.description || '暂无描述' }}</p>
              <div v-if="project.tech_stack && project.tech_stack.length" class="tech-stack">
                <el-tag
                  v-for="tech in project.tech_stack.slice(0, 3)"
                  :key="tech"
                  size="small"
                  type="info"
                  class="tech-tag"
                >
                  {{ tech }}
                </el-tag>
                <el-tag v-if="project.tech_stack.length > 3" size="small" type="info">
                  +{{ project.tech_stack.length - 3 }}
                </el-tag>
              </div>
              <div class="progress-section">
                <span class="progress-label">项目进度</span>
                <el-progress
                  :percentage="getProjectProgress(project)"
                  :stroke-width="10"
                  :status="getProgressStatus(project)"
                />
              </div>
              <div class="task-info">
                <span>
                  <el-icon><Document /></el-icon>
                  任务: {{ project.task_stats?.total || 0 }}
                </span>
                <span>
                  <el-icon><CircleCheck /></el-icon>
                  完成: {{ project.task_stats?.completed || 0 }}
                </span>
              </div>
              <div class="time-info">
                <span>创建: {{ formatTime(project.created_at) }}</span>
                <span v-if="project.updated_at">更新: {{ formatTime(project.updated_at) }}</span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      <el-empty v-if="!loading && filteredProjects.length === 0" description="暂无项目数据" />
    </div>

    <div v-if="total > pageSize" class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Search, Document, CircleCheck } from '@element-plus/icons-vue'
import { useProjectsStore, type Project } from '@/stores/projects'

const router = useRouter()
const projectsStore = useProjectsStore()

const searchQuery = ref('')
const statusFilter = ref('')
const sortBy = ref('created_at_desc')
const currentPage = ref(1)
const pageSize = ref(12)
const total = ref(0)
const loading = computed(() => projectsStore.loading)

const statusOptions = [
  { value: 'REQUIREMENT', label: '需求分析' },
  { value: 'DESIGN', label: '设计阶段' },
  { value: 'DEVELOPMENT', label: '开发阶段' },
  { value: 'TESTING', label: '测试阶段' },
  { value: 'DEPLOYMENT', label: '部署阶段' },
  { value: 'COMPLETED', label: '已完成' }
]

const filteredProjects = computed(() => {
  let result = [...projectsStore.projects]

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(p => p.name.toLowerCase().includes(query))
  }

  if (statusFilter.value) {
    result = result.filter(p => p.status === statusFilter.value)
  }

  switch (sortBy.value) {
    case 'created_at_desc':
      result.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      break
    case 'created_at_asc':
      result.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
      break
    case 'updated_at_desc':
      result.sort((a, b) => {
        if (!a.updated_at) return 1
        if (!b.updated_at) return -1
        return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
      })
      break
    case 'updated_at_asc':
      result.sort((a, b) => {
        if (!a.updated_at) return 1
        if (!b.updated_at) return -1
        return new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime()
      })
      break
    case 'name_asc':
      result.sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'))
      break
    case 'name_desc':
      result.sort((a, b) => b.name.localeCompare(a.name, 'zh-CN'))
      break
  }

  total.value = result.length

  const start = (currentPage.value - 1) * pageSize.value
  return result.slice(start, start + pageSize.value)
})

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    REQUIREMENT: 'info',
    DESIGN: 'warning',
    DEVELOPMENT: 'primary',
    TESTING: '',
    DEPLOYMENT: 'success',
    COMPLETED: 'success'
  }
  return types[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const option = statusOptions.find(o => o.value === status)
  return option ? option.label : status
}

const getProjectProgress = (project: Project) => {
  if (!project.task_stats || project.task_stats.total === 0) return 0
  return Math.round((project.task_stats.completed / project.task_stats.total) * 100)
}

const getProgressStatus = (project: Project) => {
  const progress = getProjectProgress(project)
  if (progress === 100) return 'success'
  if (progress >= 80) return ''
  return ''
}

const formatTime = (time: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleDateString('zh-CN')
}

const handleSearch = () => {
  currentPage.value = 1
}

const handleFilter = () => {
  currentPage.value = 1
}

const handleSort = () => {
  currentPage.value = 1
}

const handlePageChange = (page: number) => {
  currentPage.value = page
}

const goToCreate = () => {
  router.push('/projects/create')
}

const goToDetail = (id: number) => {
  router.push(`/projects/${id}`)
}

onMounted(async () => {
  await projectsStore.fetchProjects()
})
</script>

<style scoped>
.project-list {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
}

.filters {
  margin-bottom: 20px;
}

.project-cards {
  min-height: 400px;
}

.project-card {
  cursor: pointer;
  transition: transform 0.2s;
  margin-bottom: 20px;
}

.project-card:hover {
  transform: translateY(-5px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.project-name {
  font-weight: 600;
  font-size: 16px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}

.project-info {
  min-height: 150px;
}

.description {
  color: #666;
  font-size: 14px;
  margin: 0 0 10px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.tech-stack {
  margin-bottom: 15px;
}

.tech-tag {
  margin-right: 5px;
  margin-bottom: 5px;
}

.progress-section {
  margin-bottom: 15px;
}

.progress-label {
  font-size: 12px;
  color: #666;
  display: block;
  margin-bottom: 5px;
}

.task-info {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: #666;
  margin-bottom: 10px;
}

.task-info span {
  display: flex;
  align-items: center;
  gap: 5px;
}

.time-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #999;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>
