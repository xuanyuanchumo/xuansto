<template>
  <div class="tree-node" :style="{ paddingLeft: level * 20 + 'px' }">
    <div class="node-content" @click="expanded = !expanded">
      <el-icon v-if="hasChildren">
        <ArrowRight v-if="!expanded" />
        <ArrowDown v-else />
      </el-icon>
      <span class="node-name">{{ node.skill_name }}</span>
      <el-tag :type="getStatusType(node.status)" size="small">
        {{ node.status }}
      </el-tag>
      <span class="node-time">{{ formatTime(node.start_time) }}</span>
    </div>
    
    <div v-if="expanded && hasChildren" class="children">
      <TreeNode 
        v-for="child in node.children" 
        :key="child.id" 
        :node="child" 
        :level="level + 1" 
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, defineProps } from 'vue'
import { ArrowRight, ArrowDown } from '@element-plus/icons-vue'
import type { SkillCallTreeNode } from './SkillCallTree.vue'

const props = defineProps<{
  node: SkillCallTreeNode
  level: number
}>()

const expanded = ref(false)

const hasChildren = computed(() => {
  return props.node.children && props.node.children.length > 0
})

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    started: 'primary',
    completed: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

const formatTime = (time: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleTimeString('zh-CN')
}
</script>

<style scoped>
.tree-node {
  margin-bottom: 5px;
}

.node-content {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.node-content:hover {
  background-color: #f5f7fa;
}

.node-name {
  font-weight: 500;
  flex: 1;
}

.node-time {
  color: #909399;
  font-size: 12px;
}

.children {
  border-left: 2px solid #dcdfe6;
  margin-left: 10px;
}
</style>
