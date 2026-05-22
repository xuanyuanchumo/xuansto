<template>
  <div class="skill-call-tree">
    <div v-if="!treeData" class="empty">
      <el-empty description="暂无数据" />
    </div>
    
    <div v-else class="tree-container">
      <TreeNode :node="treeData" :level="0" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps } from 'vue'
import TreeNode from './TreeNode.vue'

export interface SkillCallTreeNode {
  id: string | number
  skill_name: string
  status: string
  start_time?: string
  children?: SkillCallTreeNode[]
}

defineProps<{
  treeData: SkillCallTreeNode | null
}>()
</script>

<style scoped>
.skill-call-tree {
  max-height: 500px;
  overflow-y: auto;
}

.tree-container {
  padding: 10px;
}
</style>
