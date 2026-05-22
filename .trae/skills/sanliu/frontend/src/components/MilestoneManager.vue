<template>
  <div class="milestone-manager">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>里程碑管理</span>
          <el-button type="primary" @click="openCreateDialog">
            <el-icon><Plus /></el-icon>
            新建里程碑
          </el-button>
        </div>
      </template>

      <div class="filter-bar">
        <el-select v-model="selectedProjectId" placeholder="选择项目筛选" clearable @change="fetchMilestones" style="width: 200px">
          <el-option
            v-for="project in projects"
            :key="project.id"
            :label="project.name"
            :value="project.id"
          />
        </el-select>
      </div>

      <el-table :data="milestones" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="里程碑名称" min-width="150" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="planned_date" label="计划完成日期" width="150">
          <template #default="scope">
            {{ formatDate(scope.row.planned_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="completed_date" label="实际完成日期" width="150">
          <template #default="scope">
            {{ formatDate(scope.row.completed_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusLabel(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="150">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button size="small" @click="openEditDialog(scope.row)">编辑</el-button>
            <el-button
              size="small"
              type="success"
              :disabled="scope.row.status === 'completed'"
              @click="handleComplete(scope.row)"
            >
              完成
            </el-button>
            <el-button size="small" type="danger" @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑里程碑' : '新建里程碑'"
      width="500px"
      :close-on-click-modal="false"
      @close="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="所属项目" prop="project_id">
          <el-select v-model="form.project_id" placeholder="选择项目" style="width: 100%" :disabled="isEdit">
            <el-option
              v-for="project in projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="里程碑名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入里程碑名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="计划完成日期" prop="planned_date">
          <el-date-picker
            v-model="form.planned_date"
            type="datetime"
            placeholder="选择计划完成日期"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus'
import axios from 'axios'

interface Milestone {
  id: number
  project_id: number
  name: string
  description: string | null
  planned_date: string | null
  completed_date: string | null
  status: string
  created_at: string
  updated_at: string | null
}

interface Project {
  id: number
  name: string
}

const loading = ref(false)
const submitting = ref(false)
const milestones = ref<Milestone[]>([])
const projects = ref<Project[]>([])
const selectedProjectId = ref<number | null>(null)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance>()

const form = ref({
  project_id: null as number | null,
  name: '',
  description: '',
  planned_date: null as Date | null
})

const rules: FormRules = {
  project_id: [{ required: true, message: '请选择项目', trigger: 'change' }],
  name: [{ required: true, message: '请输入里程碑名称', trigger: 'blur' }]
}

const statusMap: Record<string, { label: string; type: string }> = {
  pending: { label: '待处理', type: 'info' },
  in_progress: { label: '进行中', type: 'primary' },
  completed: { label: '已完成', type: 'success' }
}

const getStatusType = (status: string) => statusMap[status]?.type || 'info'
const getStatusLabel = (status: string) => statusMap[status]?.label || status

const formatDate = (date: string | null) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('zh-CN')
}

const fetchProjects = async () => {
  try {
    const response = await axios.get('/api/projects/')
    projects.value = response.data
  } catch (error) {
    console.error('Failed to fetch projects:', error)
  }
}

const fetchMilestones = async () => {
  loading.value = true
  try {
    let url = '/api/milestones/'
    if (selectedProjectId.value) {
      url = `/api/milestones/project/${selectedProjectId.value}`
    }
    const response = await axios.get(url)
    milestones.value = response.data
  } catch (error) {
    console.error('Failed to fetch milestones:', error)
    ElMessage.error('获取里程碑列表失败')
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  isEdit.value = false
  editingId.value = null
  dialogVisible.value = true
}

const openEditDialog = (milestone: Milestone) => {
  isEdit.value = true
  editingId.value = milestone.id
  form.value = {
    project_id: milestone.project_id,
    name: milestone.name,
    description: milestone.description || '',
    planned_date: milestone.planned_date ? new Date(milestone.planned_date) : null
  }
  dialogVisible.value = true
}

const resetForm = () => {
  form.value = {
    project_id: null,
    name: '',
    description: '',
    planned_date: null
  }
  formRef.value?.resetFields()
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      const data = {
        ...form.value,
        planned_date: form.value.planned_date?.toISOString()
      }
      
      if (isEdit.value && editingId.value) {
        await axios.put(`/api/milestones/${editingId.value}`, data)
        ElMessage.success('更新成功')
      } else {
        await axios.post('/api/milestones/', data)
        ElMessage.success('创建成功')
      }
      
      dialogVisible.value = false
      fetchMilestones()
    } catch (error) {
      console.error('Failed to save milestone:', error)
      ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
    } finally {
      submitting.value = false
    }
  })
}

const handleComplete = async (milestone: Milestone) => {
  try {
    await ElMessageBox.confirm('确定要标记此里程碑为已完成吗？', '确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await axios.put(`/api/milestones/${milestone.id}/complete`)
    ElMessage.success('已标记为完成')
    fetchMilestones()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to complete milestone:', error)
      ElMessage.error('操作失败')
    }
  }
}

const handleDelete = async (milestone: Milestone) => {
  try {
    await ElMessageBox.confirm('确定要删除此里程碑吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await axios.delete(`/api/milestones/${milestone.id}`)
    ElMessage.success('删除成功')
    fetchMilestones()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete milestone:', error)
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  fetchProjects()
  fetchMilestones()
})
</script>

<style scoped>
.milestone-manager {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-bar {
  margin-bottom: 15px;
}
</style>
