<template>
  <div class="project-selector">
    <el-select
      v-if="!multiple"
      v-model="selectedProject"
      :placeholder="placeholder"
      :loading="loading"
      :filterable="filterable"
      :clearable="clearable"
      :disabled="disabled"
      :size="size"
      style="width: 100%"
      @change="handleSingleChange"
    >
      <template #prefix>
        <el-icon><Folder /></el-icon>
      </template>
      <el-option
        v-for="project in filteredProjects"
        :key="project.id"
        :label="project.name"
        :value="project.id"
      >
        <div class="project-option">
          <div class="project-info">
            <span class="project-name">{{ project.name }}</span>
            <el-tag
              v-if="showStatus"
              :type="getStatusType(project.status)"
              size="small"
            >
              {{ getStatusLabel(project.status) }}
            </el-tag>
          </div>
          <div v-if="project.description" class="project-description">
            {{ project.description }}
          </div>
        </div>
      </el-option>
    </el-select>

    <el-select
      v-else
      v-model="selectedProjects"
      :placeholder="placeholder"
      :loading="loading"
      :filterable="filterable"
      :clearable="clearable"
      :disabled="disabled"
      :size="size"
      multiple
      collapse-tags
      collapse-tags-tooltip
      style="width: 100%"
      @change="handleMultipleChange"
    >
      <template #prefix>
        <el-icon><Folder /></el-icon>
      </template>
      <template #header>
        <div class="select-header">
          <el-checkbox
            v-model="selectAll"
            :indeterminate="isIndeterminate"
            @change="handleSelectAll"
          >
            全选
          </el-checkbox>
          <el-button
            type="primary"
            link
            size="small"
            @click="invertSelection"
          >
            反选
          </el-button>
        </div>
      </template>
      <el-option
        v-for="project in filteredProjects"
        :key="project.id"
        :label="project.name"
        :value="project.id"
      >
        <div class="project-option">
          <div class="project-info">
            <span class="project-name">{{ project.name }}</span>
            <el-tag
              v-if="showStatus"
              :type="getStatusType(project.status)"
              size="small"
            >
              {{ getStatusLabel(project.status) }}
            </el-tag>
          </div>
          <div v-if="project.description" class="project-description">
            {{ project.description }}
          </div>
        </div>
      </el-option>
    </el-select>

    <el-card v-if="showSelectedList && multiple && selectedProjectDetails.length > 0" class="selected-list-card">
      <template #header>
        <div class="card-header">
          <span>已选项目 ({{ selectedProjectDetails.length }})</span>
          <el-button type="primary" link @click="clearSelection">
            清空
          </el-button>
        </div>
      </template>
      <div class="selected-list">
        <el-tag
          v-for="project in selectedProjectDetails"
          :key="project.id"
          closable
          size="large"
          @close="removeProject(project.id)"
        >
          {{ project.name }}
        </el-tag>
      </div>
    </el-card>

    <el-card v-if="showProjectList" class="project-list-card">
      <template #header>
        <div class="card-header">
          <span>项目列表</span>
          <div class="header-actions">
            <el-input
              v-model="searchQuery"
              placeholder="搜索项目"
              :prefix-icon="Search"
              clearable
              size="small"
              style="width: 200px"
            />
            <el-select
              v-model="statusFilter"
              placeholder="状态筛选"
              clearable
              size="small"
              style="width: 120px"
            >
              <el-option label="全部" value="" />
              <el-option label="进行中" value="in_progress" />
              <el-option label="已完成" value="completed" />
              <el-option label="暂停" value="paused" />
              <el-option label="归档" value="archived" />
            </el-select>
            <el-button
              type="primary"
              size="small"
              @click="refreshProjects"
              :loading="loading"
            >
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        :data="paginatedProjects"
        stripe
        @selection-change="handleTableSelectionChange"
        @row-click="handleRowClick"
      >
        <el-table-column v-if="multiple" type="selection" width="55" />
        <el-table-column prop="name" label="项目名称" min-width="150">
          <template #default="{ row }">
            <div class="table-project-name">
              {{ row.name }}
            </div>
          </template>
        </el-table-column>
        <el-table-column v-if="showDescription" prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column v-if="showStatus" prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column v-if="showTechStack" prop="tech_stack" label="技术栈" width="200">
          <template #default="{ row }">
            <div class="tech-stack">
              <el-tag
                v-for="tech in (row.tech_stack || []).slice(0, 3)"
                :key="tech"
                size="small"
                type="info"
              >
                {{ tech }}
              </el-tag>
              <el-tag v-if="row.tech_stack && row.tech_stack.length > 3" size="small" type="info">
                +{{ row.tech_stack.length - 3 }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column v-if="showProgress" label="进度" width="150">
          <template #default="{ row }">
            <el-progress
              :percentage="row.progress || 0"
              :stroke-width="10"
            />
          </template>
        </el-table-column>
        <el-table-column v-if="showActions" label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              size="small"
              @click.stop="selectProject(row)"
            >
              选择
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="filteredProjects.length"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Folder, Search, Refresh } from '@element-plus/icons-vue'
import { useProjectsStore, Project } from '@/stores/projects'

interface Props {
  modelValue?: number | number[] | null
  multiple?: boolean
  placeholder?: string
  filterable?: boolean
  clearable?: boolean
  disabled?: boolean
  size?: 'large' | 'default' | 'small'
  showStatus?: boolean
  showDescription?: boolean
  showTechStack?: boolean
  showProgress?: boolean
  showActions?: boolean
  showProjectList?: boolean
  showSelectedList?: boolean
  excludeIds?: number[]
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '请选择项目',
  filterable: true,
  clearable: true,
  disabled: false,
  size: 'default',
  showStatus: true,
  showDescription: false,
  showTechStack: false,
  showProgress: false,
  showActions: false,
  showProjectList: false,
  showSelectedList: false,
  excludeIds: () => []
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: number | number[] | null): void
  (e: 'change', value: number | number[] | null): void
  (e: 'select', project: Project): void
  (e: 'error', error: Error): void
}>()

const projectsStore = useProjectsStore()

const loading = ref(false)
const searchQuery = ref('')
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(10)

const selectedProject = ref<number | null>(null)
const selectedProjects = ref<number[]>([])

const projects = computed(() => projectsStore.projects)

const filteredProjects = computed(() => {
  let result = projects.value

  if (props.excludeIds.length > 0) {
    result = result.filter(p => !props.excludeIds.includes(p.id))
  }

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(p =>
      p.name.toLowerCase().includes(query) ||
      (p.description && p.description.toLowerCase().includes(query))
    )
  }

  if (statusFilter.value) {
    result = result.filter(p => p.status === statusFilter.value)
  }

  return result
})

const paginatedProjects = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredProjects.value.slice(start, end)
})

const selectedProjectDetails = computed(() => {
  if (!props.multiple) return []
  return projects.value.filter(p => selectedProjects.value.includes(p.id))
})

const selectAll = computed({
  get: () => {
    return filteredProjects.value.length > 0 &&
      filteredProjects.value.every(p => selectedProjects.value.includes(p.id))
  },
  set: () => {}
})

const isIndeterminate = computed(() => {
  const selected = selectedProjects.value.filter(id =>
    filteredProjects.value.some(p => p.id === id)
  )
  return selected.length > 0 && selected.length < filteredProjects.value.length
})

const getStatusType = (status: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    in_progress: 'primary',
    completed: 'success',
    paused: 'warning',
    archived: 'info',
    planning: 'info'
  }
  return types[status] || 'info'
}

const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    in_progress: '进行中',
    completed: '已完成',
    paused: '暂停',
    archived: '归档',
    planning: '规划中'
  }
  return labels[status] || status
}

const handleSingleChange = (value: number | null) => {
  emit('update:modelValue', value)
  emit('change', value)

  if (value) {
    const project = projects.value.find(p => p.id === value)
    if (project) {
      emit('select', project)
    }
  }
}

const handleMultipleChange = (value: number[]) => {
  emit('update:modelValue', value)
  emit('change', value)
}

const handleSelectAll = (checked: boolean) => {
  if (checked) {
    selectedProjects.value = [
      ...new Set([
        ...selectedProjects.value,
        ...filteredProjects.value.map(p => p.id)
      ])
    ]
  } else {
    const filteredIds = new Set(filteredProjects.value.map(p => p.id))
    selectedProjects.value = selectedProjects.value.filter(id => !filteredIds.has(id))
  }
  handleMultipleChange(selectedProjects.value)
}

const invertSelection = () => {
  const filteredIds = filteredProjects.value.map(p => p.id)
  const newSelected = selectedProjects.value.filter(id => !filteredIds.includes(id))
  const unselected = filteredIds.filter(id => !selectedProjects.value.includes(id))
  selectedProjects.value = [...newSelected, ...unselected]
  handleMultipleChange(selectedProjects.value)
}

const removeProject = (projectId: number) => {
  selectedProjects.value = selectedProjects.value.filter(id => id !== projectId)
  handleMultipleChange(selectedProjects.value)
}

const clearSelection = () => {
  if (props.multiple) {
    selectedProjects.value = []
    handleMultipleChange([])
  } else {
    selectedProject.value = null
    handleSingleChange(null)
  }
}

const handleTableSelectionChange = (selection: Project[]) => {
  selectedProjects.value = selection.map(p => p.id)
  handleMultipleChange(selectedProjects.value)
}

const handleRowClick = (row: Project) => {
  if (props.multiple) {
    const index = selectedProjects.value.indexOf(row.id)
    if (index > -1) {
      selectedProjects.value.splice(index, 1)
    } else {
      selectedProjects.value.push(row.id)
    }
    handleMultipleChange(selectedProjects.value)
  } else {
    selectedProject.value = row.id
    handleSingleChange(row.id)
  }
}

const selectProject = (project: Project) => {
  if (props.multiple) {
    if (!selectedProjects.value.includes(project.id)) {
      selectedProjects.value.push(project.id)
      handleMultipleChange(selectedProjects.value)
    }
  } else {
    selectedProject.value = project.id
    handleSingleChange(project.id)
  }
  emit('select', project)
}

const refreshProjects = async () => {
  loading.value = true
  try {
    await projectsStore.fetchProjects()
    ElMessage.success('项目列表已刷新')
  } catch (error) {
    console.error('Failed to refresh projects:', error)
    emit('error', error as Error)
  } finally {
    loading.value = false
  }
}

watch(() => props.modelValue, (newValue) => {
  if (props.multiple) {
    selectedProjects.value = Array.isArray(newValue) ? newValue : []
  } else {
    selectedProject.value = typeof newValue === 'number' ? newValue : null
  }
}, { immediate: true })

onMounted(() => {
  if (projects.value.length === 0) {
    refreshProjects()
  }
})
</script>

<style scoped>
.project-selector {
  width: 100%;
}

.project-option {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.project-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.project-name {
  font-weight: 500;
}

.project-description {
  font-size: 12px;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.select-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 20px;
  border-bottom: 1px solid #ebeef5;
}

.selected-list-card,
.project-list-card {
  margin-top: 15px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.selected-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.table-project-name {
  font-weight: 500;
}

.tech-stack {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

:deep(.el-select-dropdown__item) {
  height: auto;
  padding: 10px 20px;
}

@media (max-width: 768px) {
  .header-actions {
    flex-wrap: wrap;
  }
}
</style>
