<template>
  <div class="report-generator">
    <el-button type="primary" @click="openDialog" :loading="loading">
      <el-icon><Document /></el-icon>
      生成报告
    </el-button>

    <el-dialog 
      v-model="dialogVisible" 
      title="项目进度报告" 
      width="80%"
      :close-on-click-modal="false"
    >
      <div class="report-content" v-if="reportContent">
        <div class="report-header">
          <h3>{{ reportData.project_name }}</h3>
          <p class="generated-time">生成时间: {{ formatTime(reportData.generated_at) }}</p>
        </div>
        <el-divider />
        <div class="markdown-content" v-html="renderedMarkdown"></div>
      </div>
      <div v-else class="loading-container">
        <el-empty description="暂无报告内容" />
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">关闭</el-button>
          <el-button type="primary" @click="downloadReport" :disabled="!reportContent">
            <el-icon><Download /></el-icon>
            下载报告
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Document, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

interface ReportData {
  project_id: number
  project_name: string
  generated_at: string
  content: string
}

const props = defineProps<{
  projectId: number
}>()

const dialogVisible = ref(false)
const loading = ref(false)
const reportContent = ref('')
const reportData = ref<ReportData | null>(null)

const renderedMarkdown = computed(() => {
  if (!reportContent.value) return ''
  return renderMarkdown(reportContent.value)
})

const renderMarkdown = (markdown: string): string => {
  let html = markdown
  
  html = html.replace(/^### (.*$)/gim, '<h4>$1</h4>')
  html = html.replace(/^## (.*$)/gim, '<h3>$1</h3>')
  html = html.replace(/^# (.*$)/gim, '<h2>$1</h2>')
  
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>')
  
  html = html.replace(/^- (.*$)/gim, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
  
  html = html.replace(/^\d+\. (.*$)/gim, '<li>$1</li>')
  
  html = html.replace(/^---$/gim, '<hr />')
  
  html = html.replace(/\n/g, '<br>')
  
  return html
}

const formatTime = (time: string): string => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const formatDate = (date: string | null): string => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('zh-CN')
}

const getTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    progress: '进度报告',
    quality: '质量报告',
    risk: '风险报告',
    summary: '总结报告'
  }
  return labels[type] || type
}

const getTypeTag = (type: string): string => {
  const tags: Record<string, string> = {
    progress: 'primary',
    quality: 'success',
    risk: 'danger',
    summary: 'info'
  }
  return tags[type] || 'info'
}

const openDialog = async () => {
  dialogVisible.value = true
  loading.value = true
  
  try {
    const response = await api.get(`/reports/project/${props.projectId}`)
    reportData.value = response.data
    reportContent.value = response.data.content
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    ElMessage.error(err.response?.data?.detail || '生成报告失败')
    dialogVisible.value = false
  } finally {
    loading.value = false
  }
}

const downloadReport = () => {
  if (!reportData.value) return
  
  const blob = new Blob([reportContent.value], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${reportData.value.project_name}_报告_${new Date().toISOString().split('T')[0]}.md`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  
  ElMessage.success('报告下载成功')
}
</script>

<style scoped>
.report-generator {
  display: inline-block;
}

.report-content {
  max-height: 60vh;
  overflow-y: auto;
  padding: 20px;
}

.report-header {
  text-align: center;
  margin-bottom: 20px;
}

.report-header h3 {
  margin: 0 0 10px 0;
  font-size: 24px;
  color: #303133;
}

.generated-time {
  color: #909399;
  font-size: 14px;
  margin: 0;
}

.markdown-content {
  line-height: 1.8;
  color: #303133;
}

.markdown-content :deep(h2) {
  font-size: 20px;
  color: #303133;
  margin: 20px 0 15px 0;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}

.markdown-content :deep(h3) {
  font-size: 18px;
  color: #303133;
  margin: 15px 0 10px 0;
}

.markdown-content :deep(h4) {
  font-size: 16px;
  color: #606266;
  margin: 10px 0 8px 0;
}

.markdown-content :deep(strong) {
  color: #409eff;
}

.markdown-content :deep(ul) {
  padding-left: 20px;
  margin: 10px 0;
}

.markdown-content :deep(li) {
  margin: 5px 0;
}

.markdown-content :deep(hr) {
  border: none;
  border-top: 1px solid #ebeef5;
  margin: 20px 0;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
