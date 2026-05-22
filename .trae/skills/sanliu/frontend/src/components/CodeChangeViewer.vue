<template>
  <el-card class="code-change-viewer" shadow="hover">
    <template #header>
      <div class="card-header">
        <span class="title">代码变更</span>
        <el-tag v-if="changes.length" type="info" size="small">
          {{ changes.length }} 个文件
        </el-tag>
      </div>
    </template>

    <div v-if="!changes || changes.length === 0" class="empty-container">
      <el-empty description="暂无代码变更" :image-size="80" />
    </div>

    <div v-else class="changes-container">
      <div class="changes-summary">
        <div class="summary-item added">
          <span class="count">{{ addedLines }}</span>
          <span class="label">新增行</span>
        </div>
        <div class="summary-item removed">
          <span class="count">{{ removedLines }}</span>
          <span class="label">删除行</span>
        </div>
        <div class="summary-item modified">
          <span class="count">{{ modifiedFiles }}</span>
          <span class="label">修改文件</span>
        </div>
      </div>

      <el-collapse v-model="activeFiles" class="changes-list">
        <el-collapse-item
          v-for="(change, index) in changes"
          :key="index"
          :name="index"
        >
          <template #title>
            <div class="change-title">
              <el-tag :type="getChangeTypeTag(change.type)" size="small">
                {{ getChangeTypeLabel(change.type) }}
              </el-tag>
              <span class="file-path">{{ change.filePath }}</span>
              <span class="line-info">
                <span class="added">+{{ change.addedLines || 0 }}</span>
                <span class="removed">-{{ change.removedLines || 0 }}</span>
              </span>
            </div>
          </template>

          <div class="diff-container">
            <div v-if="change.diff" class="diff-view">
              <div
                v-for="(line, lineIndex) in parseDiff(change.diff)"
                :key="lineIndex"
                class="diff-line"
                :class="getLineClass(line)"
              >
                <span class="line-number">{{ line.lineNumber || '' }}</span>
                <span class="line-prefix">{{ line.prefix }}</span>
                <span class="line-content">{{ line.content }}</span>
              </div>
            </div>
            <div v-else class="no-diff">
              <div v-if="change.newContent" class="full-content">
                <div class="content-label">完整内容：</div>
                <pre class="content-code">{{ change.newContent }}</pre>
              </div>
              <el-empty v-else description="暂无变更详情" :image-size="60" />
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed, defineProps } from 'vue'

interface CodeChange {
  filePath: string
  type: 'added' | 'modified' | 'deleted' | 'renamed'
  diff?: string
  newContent?: string
  addedLines?: number
  removedLines?: number
}

const props = defineProps<{
  changes: CodeChange[]
}>()

const activeFiles = ref<number[]>([])

const addedLines = computed(() => {
  return props.changes.reduce((sum, c) => sum + (c.addedLines || 0), 0)
})

const removedLines = computed(() => {
  return props.changes.reduce((sum, c) => sum + (c.removedLines || 0), 0)
})

const modifiedFiles = computed(() => {
  return props.changes.filter(c => c.type === 'modified').length
})

const changeTypeMap: Record<string, { label: string; type: string }> = {
  added: { label: '新增', type: 'success' },
  modified: { label: '修改', type: 'warning' },
  deleted: { label: '删除', type: 'danger' },
  renamed: { label: '重命名', type: 'info' }
}

const getChangeTypeTag = (type: string) => {
  return changeTypeMap[type]?.type || 'info'
}

const getChangeTypeLabel = (type: string) => {
  return changeTypeMap[type]?.label || type
}

interface DiffLine {
  lineNumber?: string
  prefix: string
  content: string
  type: 'add' | 'remove' | 'context' | 'header'
}

const parseDiff = (diff: string): DiffLine[] => {
  const lines = diff.split('\n')
  return lines.map(line => {
    if (line.startsWith('@@')) {
      return { prefix: '', content: line, type: 'header' }
    }
    if (line.startsWith('+')) {
      return { prefix: '+', content: line.substring(1), type: 'add' }
    }
    if (line.startsWith('-')) {
      return { prefix: '-', content: line.substring(1), type: 'remove' }
    }
    return { prefix: ' ', content: line, type: 'context' }
  })
}

const getLineClass = (line: DiffLine) => {
  return {
    'line-add': line.type === 'add',
    'line-remove': line.type === 'remove',
    'line-header': line.type === 'header'
  }
}
</script>

<style scoped>
.code-change-viewer {
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

.changes-container {
  padding: 10px 0;
}

.changes-summary {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.summary-item {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.summary-item .count {
  font-size: 20px;
  font-weight: bold;
}

.summary-item.added .count {
  color: #67c23a;
}

.summary-item.removed .count {
  color: #f56c6c;
}

.summary-item.modified .count {
  color: #e6a23c;
}

.summary-item .label {
  font-size: 13px;
  color: #909399;
}

.changes-list {
  border: none;
}

.change-title {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.file-path {
  flex: 1;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  color: #606266;
}

.line-info {
  display: flex;
  gap: 8px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
}

.line-info .added {
  color: #67c23a;
}

.line-info .removed {
  color: #f56c6c;
}

.diff-container {
  background: #fafafa;
  border-radius: 4px;
  overflow: hidden;
}

.diff-view {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.6;
  overflow-x: auto;
}

.diff-line {
  display: flex;
  padding: 0 10px;
  white-space: pre;
}

.diff-line.line-add {
  background: #f0f9eb;
}

.diff-line.line-remove {
  background: #fef0f0;
}

.diff-line.line-header {
  background: #ecf5ff;
  color: #409eff;
  padding: 5px 10px;
}

.line-number {
  min-width: 40px;
  color: #909399;
  text-align: right;
  padding-right: 10px;
  user-select: none;
}

.line-prefix {
  min-width: 15px;
  text-align: center;
}

.line-content {
  flex: 1;
}

.no-diff {
  padding: 10px;
}

.full-content {
  background: #fff;
  border-radius: 4px;
}

.content-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}

.content-code {
  margin: 0;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  line-height: 1.5;
  overflow-x: auto;
  white-space: pre-wrap;
}
</style>
