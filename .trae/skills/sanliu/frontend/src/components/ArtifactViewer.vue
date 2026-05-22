<template>
  <el-card class="artifact-viewer" shadow="hover">
    <template #header>
      <div class="card-header">
        <span class="title">中间产物</span>
        <el-tag v-if="artifacts.length" type="info" size="small">
          {{ artifacts.length }} 个产物
        </el-tag>
      </div>
    </template>

    <div v-if="!artifacts || artifacts.length === 0" class="empty-container">
      <el-empty description="暂无中间产物" :image-size="80" />
    </div>

    <div v-else class="artifacts-container">
      <div class="artifacts-list">
        <div
          v-for="(artifact, index) in artifacts"
          :key="artifact.id || index"
          class="artifact-item"
          @click="selectArtifact(artifact)"
        >
          <div class="artifact-icon">
            <el-icon :size="24">
              <component :is="getArtifactIcon(artifact.type)" />
            </el-icon>
          </div>
          <div class="artifact-info">
            <div class="artifact-name">{{ artifact.name }}</div>
            <div class="artifact-meta">
              <el-tag :type="getArtifactTypeTag(artifact.type)" size="small">
                {{ getArtifactTypeLabel(artifact.type) }}
              </el-tag>
              <span class="artifact-time">{{ formatTime(artifact.createdAt) }}</span>
            </div>
          </div>
          <div class="artifact-actions">
            <el-button
              type="primary"
              size="small"
              text
              @click.stop="previewArtifact(artifact)"
            >
              <el-icon><View /></el-icon>
            </el-button>
            <el-button
              type="primary"
              size="small"
              text
              @click.stop="downloadArtifact(artifact)"
            >
              <el-icon><Download /></el-icon>
            </el-button>
          </div>
        </div>
      </div>

      <el-dialog
        v-model="previewVisible"
        :title="selectedArtifact?.name || '预览'"
        width="800px"
        destroy-on-close
      >
        <div class="preview-container">
          <div v-if="previewLoading" class="preview-loading">
            <el-icon class="is-loading" :size="40"><Loading /></el-icon>
          </div>
          <div v-else-if="previewContent" class="preview-content">
            <vueJsonViewer
              v-if="isJsonContent"
              :value="previewContent"
              :expand-depth="3"
              copyable
              boxed
            />
            <pre v-else class="text-preview">{{ previewContent }}</pre>
          </div>
          <el-empty v-else description="无法预览此类型内容" :image-size="80" />
        </div>
        <template #footer>
          <el-button @click="previewVisible = false">关闭</el-button>
          <el-button type="primary" @click="downloadArtifact(selectedArtifact)">
            <el-icon><Download /></el-icon>
            下载
          </el-button>
        </template>
      </el-dialog>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed, defineProps } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Document,
  Picture,
  VideoPlay,
  Headset,
  FolderOpened,
  Download,
  View,
  Loading
} from '@element-plus/icons-vue'
import type { Component } from 'vue'

interface Artifact {
  id?: string | number
  name: string
  type: string
  createdAt?: string
  content?: string
  url?: string
  size?: number
}

type ParsedContent = string | number | boolean | object | null | undefined

defineProps<{
  artifacts: Artifact[]
}>()

const previewVisible = ref(false)
const previewLoading = ref(false)
const previewContent = ref<ParsedContent>(null)
const selectedArtifact = ref<Artifact | null>(null)

const isJsonContent = computed(() => {
  if (!previewContent.value) return false
  return typeof previewContent.value === 'object'
})

const artifactTypeMap: Record<string, { label: string; type: string; icon: Component }> = {
  document: { label: '文档', type: 'primary', icon: Document },
  image: { label: '图片', type: 'success', icon: Picture },
  video: { label: '视频', type: 'warning', icon: VideoPlay },
  audio: { label: '音频', type: 'info', icon: Headset },
  data: { label: '数据', type: '', icon: FolderOpened },
  code: { label: '代码', type: 'danger', icon: Document }
}

const getArtifactIcon = (type: string) => {
  return artifactTypeMap[type]?.icon || Document
}

const getArtifactTypeTag = (type: string) => {
  return artifactTypeMap[type]?.type || 'info'
}

const getArtifactTypeLabel = (type: string) => {
  return artifactTypeMap[type]?.label || type
}

const formatTime = (time?: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const selectArtifact = (artifact: Artifact) => {
  selectedArtifact.value = artifact
}

const parseContent = (content: string): ParsedContent => {
  try {
    return JSON.parse(content)
  } catch {
    return content
  }
}

const fetchUrlContent = async (url: string): Promise<ParsedContent> => {
  const response = await fetch(url)
  const text = await response.text()
  return parseContent(text)
}

const previewArtifact = async (artifact: Artifact) => {
  selectedArtifact.value = artifact
  previewVisible.value = true
  previewLoading.value = true
  previewContent.value = null

  try {
    if (!artifact.content && !artifact.url) {
      return
    }

    if (artifact.content) {
      previewContent.value = typeof artifact.content === 'string'
        ? parseContent(artifact.content)
        : artifact.content
      return
    }

    if (artifact.url) {
      previewContent.value = await fetchUrlContent(artifact.url)
    }
  } catch (error) {
    console.error('Preview failed:', error)
    ElMessage.error('预览失败')
  } finally {
    previewLoading.value = false
  }
}

const downloadArtifact = (artifact: Artifact | null) => {
  if (!artifact) return

  let blob: Blob
  let filename = artifact.name

  if (artifact.content) {
    const content = typeof artifact.content === 'string'
      ? artifact.content
      : JSON.stringify(artifact.content, null, 2)
    blob = new Blob([content], { type: 'text/plain' })
  } else if (artifact.url) {
    window.open(artifact.url, '_blank')
    return
  } else {
    ElMessage.warning('无可下载内容')
    return
  }

  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)

  ElMessage.success('下载已开始')
}
</script>

<style scoped>
.artifact-viewer {
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

.empty-container {
  padding: 20px 0;
}

.artifacts-container {
  padding: 10px 0;
}

.artifacts-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 400px;
  overflow-y: auto;
}

.artifact-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.artifact-item:hover {
  border-color: #409eff;
  background: #ecf5ff;
}

.artifact-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: #f5f7fa;
  color: #409eff;
}

.artifact-info {
  flex: 1;
  min-width: 0;
}

.artifact-name {
  font-weight: 500;
  font-size: 14px;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.artifact-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}

.artifact-time {
  font-size: 12px;
  color: #909399;
}

.artifact-actions {
  display: flex;
  gap: 4px;
}

.preview-container {
  min-height: 200px;
  max-height: 500px;
  overflow: auto;
}

.preview-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.preview-content {
  padding: 10px;
}

.text-preview {
  margin: 0;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
