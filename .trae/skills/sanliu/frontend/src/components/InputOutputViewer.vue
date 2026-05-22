<template>
  <el-card class="input-output-viewer" shadow="hover">
    <template #header>
      <div class="card-header">
        <span class="title">输入输出</span>
        <div class="header-actions">
          <el-button-group size="small">
            <el-button :type="viewMode === 'formatted' ? 'primary' : 'default'" @click="viewMode = 'formatted'">
              格式化
            </el-button>
            <el-button :type="viewMode === 'raw' ? 'primary' : 'default'" @click="viewMode = 'raw'">
              原始
            </el-button>
          </el-button-group>
        </div>
      </div>
    </template>

    <div class="io-container">
      <div class="io-section">
        <div class="section-header">
          <span class="section-title">
            <el-icon><Upload /></el-icon>
            输入数据
          </span>
          <el-button
            v-if="inputData"
            type="primary"
            size="small"
            text
            @click="copyToClipboard(inputData, '输入')"
          >
            <el-icon><CopyDocument /></el-icon>
            复制
          </el-button>
        </div>
        <div class="section-content">
          <div v-if="!inputData" class="empty-data">
            <el-empty description="暂无输入数据" :image-size="60" />
          </div>
          <div v-else class="data-display">
            <pre v-if="viewMode === 'raw'" class="raw-data">{{ inputData }}</pre>
            <div v-else class="formatted-data">
              <vue-jsonViewer
                v-if="isJson(inputData)"
                :value="parseJson(inputData)"
                :expand-depth="3"
                copyable
                boxed
              />
              <pre v-else class="text-data">{{ formatText(inputData) }}</pre>
            </div>
          </div>
        </div>
      </div>

      <el-divider>
        <el-icon><Bottom /></el-icon>
      </el-divider>

      <div class="io-section">
        <div class="section-header">
          <span class="section-title">
            <el-icon><Download /></el-icon>
            输出数据
          </span>
          <el-button
            v-if="outputData"
            type="primary"
            size="small"
            text
            @click="copyToClipboard(outputData, '输出')"
          >
            <el-icon><CopyDocument /></el-icon>
            复制
          </el-button>
        </div>
        <div class="section-content">
          <div v-if="!outputData" class="empty-data">
            <el-empty description="暂无输出数据" :image-size="60" />
          </div>
          <div v-else class="data-display">
            <pre v-if="viewMode === 'raw'" class="raw-data">{{ outputData }}</pre>
            <div v-else class="formatted-data">
              <vueJsonViewer
                v-if="isJson(outputData)"
                :value="parseJson(outputData)"
                :expand-depth="3"
                copyable
                boxed
              />
              <pre v-else class="text-data">{{ formatText(outputData) }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, defineProps } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload, Download, CopyDocument, Bottom } from '@element-plus/icons-vue'

defineProps<{
  inputData?: string | object
  outputData?: string | object
}>()

const viewMode = ref<'formatted' | 'raw'>('formatted')

const isJson = (data: string | object): boolean => {
  if (typeof data === 'object') return true
  try {
    JSON.parse(data)
    return true
  } catch {
    return false
  }
}

const parseJson = (data: string | object): object => {
  if (typeof data === 'object') return data
  return JSON.parse(data)
}

const formatText = (data: string | object): string => {
  if (typeof data === 'object') return JSON.stringify(data, null, 2)
  return data
}

const copyToClipboard = async (data: string | object, label: string) => {
  const text = typeof data === 'object' ? JSON.stringify(data, null, 2) : data
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success(`${label}数据已复制到剪贴板`)
  } catch {
    ElMessage.error('复制失败')
  }
}
</script>

<style scoped>
.input-output-viewer {
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

.io-container {
  padding: 10px 0;
}

.io-section {
  margin-bottom: 10px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
  font-size: 14px;
  color: #303133;
}

.section-content {
  min-height: 100px;
  max-height: 400px;
  overflow: auto;
}

.empty-data {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100px;
  background: #fafafa;
  border-radius: 4px;
}

.data-display {
  background: #f5f7fa;
  border-radius: 4px;
  padding: 12px;
}

.raw-data,
.text-data {
  margin: 0;
  padding: 0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  color: #303133;
}

.formatted-data {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.el-divider {
  margin: 15px 0;
}
</style>
