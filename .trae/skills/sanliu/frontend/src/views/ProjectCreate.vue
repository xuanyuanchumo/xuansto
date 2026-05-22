<template>
  <div class="project-create">
    <h2>创建新项目</h2>

    <el-steps :active="currentStep" finish-status="success" simple class="steps">
      <el-step title="选择模板" />
      <el-step title="基本信息" />
      <el-step title="技术栈配置" />
    </el-steps>

    <div class="step-content">
      <template v-if="currentStep === 0">
        <el-card class="template-card">
          <template #header>
            <span>选择项目模板</span>
          </template>
          <el-row :gutter="20">
            <el-col :span="8" v-for="template in templates" :key="template.id">
              <div
                class="template-item"
                :class="{ active: selectedTemplate === template.id }"
                @click="selectTemplate(template.id)"
              >
                <div class="template-icon">
                  <el-icon :size="48">
                    <component :is="template.icon" />
                  </el-icon>
                </div>
                <div class="template-info">
                  <h3>{{ template.name }}</h3>
                  <p>{{ template.description }}</p>
                </div>
                <div class="template-check" v-if="selectedTemplate === template.id">
                  <el-icon><Check /></el-icon>
                </div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </template>

      <template v-if="currentStep === 1">
        <el-card class="form-card">
          <template #header>
            <span>基本信息</span>
          </template>
          <el-form
            ref="basicFormRef"
            :model="basicForm"
            :rules="basicRules"
            label-width="100px"
          >
            <el-form-item label="项目名称" prop="name">
              <el-input
                v-model="basicForm.name"
                placeholder="请输入项目名称"
                maxlength="50"
                show-word-limit
              />
            </el-form-item>
            <el-form-item label="项目描述" prop="description">
              <el-input
                v-model="basicForm.description"
                type="textarea"
                :rows="4"
                placeholder="请输入项目描述"
                maxlength="500"
                show-word-limit
              />
            </el-form-item>
            <el-form-item label="项目类型" prop="type">
              <el-select v-model="basicForm.type" placeholder="请选择项目类型">
                <el-option
                  v-for="type in projectTypes"
                  :key="type.value"
                  :label="type.label"
                  :value="type.value"
                />
              </el-select>
            </el-form-item>
          </el-form>
        </el-card>
      </template>

      <template v-if="currentStep === 2">
        <el-card class="form-card">
          <template #header>
            <span>技术栈配置</span>
          </template>
          <el-form
            ref="techFormRef"
            :model="techForm"
            :rules="techRules"
            label-width="120px"
          >
            <el-form-item label="前端框架" prop="frontend">
              <el-radio-group v-model="techForm.frontend">
                <el-radio-button
                  v-for="framework in frontendFrameworks"
                  :key="framework.value"
                  :value="framework.value"
                >
                  <div class="radio-content">
                    <span class="radio-label">{{ framework.label }}</span>
                    <span class="radio-desc">{{ framework.desc }}</span>
                  </div>
                </el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="后端框架" prop="backend">
              <el-radio-group v-model="techForm.backend">
                <el-radio-button
                  v-for="framework in backendFrameworks"
                  :key="framework.value"
                  :value="framework.value"
                >
                  <div class="radio-content">
                    <span class="radio-label">{{ framework.label }}</span>
                    <span class="radio-desc">{{ framework.desc }}</span>
                  </div>
                </el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="数据库" prop="database">
              <el-radio-group v-model="techForm.database">
                <el-radio-button
                  v-for="db in databases"
                  :key="db.value"
                  :value="db.value"
                >
                  <div class="radio-content">
                    <span class="radio-label">{{ db.label }}</span>
                    <span class="radio-desc">{{ db.desc }}</span>
                  </div>
                </el-radio-button>
              </el-radio-group>
            </el-form-item>
          </el-form>
        </el-card>
      </template>
    </div>

    <div class="action-bar">
      <el-button @click="saveDraft" :loading="savingDraft">
        <el-icon><DocumentCopy /></el-icon>
        保存草稿
      </el-button>
      <el-button
        v-if="currentStep > 0"
        @click="prevStep"
      >
        上一步
      </el-button>
      <el-button
        v-if="currentStep < 2"
        type="primary"
        @click="nextStep"
      >
        下一步
      </el-button>
      <el-button
        v-if="currentStep === 2"
        type="success"
        @click="submitProject"
        :loading="submitting"
      >
        <el-icon><Check /></el-icon>
        提交创建
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Monitor,
  Connection,
  Cpu,
  Check,
  DocumentCopy
} from '@element-plus/icons-vue'
import { useProjectsStore } from '@/stores/projects'

const router = useRouter()
const projectsStore = useProjectsStore()

const currentStep = ref(0)
const selectedTemplate = ref<string | null>(null)

const basicFormRef = ref()
const techFormRef = ref()

const savingDraft = ref(false)
const submitting = ref(false)

const templates = [
  {
    id: 'web',
    name: 'Web项目',
    description: '适用于构建现代化的Web应用程序，包含前后端完整架构',
    icon: Monitor
  },
  {
    id: 'mcp',
    name: 'MCP服务器',
    description: '用于构建Model Context Protocol服务器，支持AI模型集成',
    icon: Connection
  },
  {
    id: 'ai',
    name: 'AI项目',
    description: '用于构建AI应用项目，集成机器学习和深度学习能力',
    icon: Cpu
  }
]

const projectTypes = [
  { label: '企业级应用', value: 'enterprise' },
  { label: '中小型项目', value: 'small' },
  { label: '原型验证', value: 'prototype' },
  { label: '个人项目', value: 'personal' }
]

const frontendFrameworks = [
  { label: 'Vue', value: 'vue', desc: '渐进式JavaScript框架' },
  { label: 'React', value: 'react', desc: '用于构建用户界面的JavaScript库' }
]

const backendFrameworks = [
  { label: 'FastAPI', value: 'fastapi', desc: '高性能Python Web框架' },
  { label: 'Express', value: 'express', desc: 'Node.js Web应用框架' }
]

const databases = [
  { label: 'PostgreSQL', value: 'postgresql', desc: '强大的开源关系型数据库' },
  { label: 'MongoDB', value: 'mongodb', desc: '面向文档的NoSQL数据库' }
]

const basicForm = reactive({
  name: '',
  description: '',
  type: ''
})

const techForm = reactive({
  frontend: '',
  backend: '',
  database: ''
})

const basicRules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择项目类型', trigger: 'change' }
  ]
}

const techRules = {
  frontend: [
    { required: true, message: '请选择前端框架', trigger: 'change' }
  ],
  backend: [
    { required: true, message: '请选择后端框架', trigger: 'change' }
  ],
  database: [
    { required: true, message: '请选择数据库', trigger: 'change' }
  ]
}

const selectTemplate = (id: string) => {
  selectedTemplate.value = id
}

const nextStep = async () => {
  if (currentStep.value === 0) {
    if (!selectedTemplate.value) {
      ElMessage.warning('请选择一个项目模板')
      return
    }
    currentStep.value++
  } else if (currentStep.value === 1) {
    const valid = await basicFormRef.value?.validate().catch(() => false)
    if (valid) {
      currentStep.value++
    }
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const saveDraft = async () => {
  savingDraft.value = true
  try {
    const draftData = {
      name: basicForm.name || '未命名项目',
      description: basicForm.description,
      tech_stack: [techForm.frontend, techForm.backend, techForm.database].filter(Boolean),
      status: 'draft'
    }
    await projectsStore.createProject(draftData)
    ElMessage.success('草稿保存成功')
    router.push('/projects')
  } catch (error) {
    ElMessage.error('保存草稿失败')
  } finally {
    savingDraft.value = false
  }
}

const submitProject = async () => {
  const valid = await techFormRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const projectData = {
      name: basicForm.name,
      description: basicForm.description,
      tech_stack: [techForm.frontend, techForm.backend, techForm.database],
      status: 'pending'
    }
    const result = await projectsStore.createProject(projectData)
    if (result) {
      ElMessage.success('项目创建成功')
      router.push('/projects')
    }
  } catch (error) {
    ElMessage.error('创建项目失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.project-create {
  padding: 20px;
}

.steps {
  margin-bottom: 30px;
}

.step-content {
  margin-bottom: 20px;
}

.template-card {
  margin-bottom: 20px;
}

.template-item {
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
  height: 180px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.template-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.2);
}

.template-item.active {
  border-color: #409eff;
  background-color: #ecf5ff;
}

.template-icon {
  margin-bottom: 15px;
  color: #409eff;
}

.template-info {
  text-align: center;
}

.template-info h3 {
  margin: 0 0 10px 0;
  font-size: 16px;
  color: #303133;
}

.template-info p {
  margin: 0;
  font-size: 13px;
  color: #909399;
  line-height: 1.5;
}

.template-check {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 24px;
  height: 24px;
  background-color: #409eff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.form-card {
  margin-bottom: 20px;
}

.radio-content {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 5px 0;
}

.radio-label {
  font-weight: 500;
}

.radio-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.action-bar {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}
</style>
