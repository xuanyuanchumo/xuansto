<template>
  <div class="stage-connector">
    <div class="connector-line" :class="{ active: isActive }"></div>
    <el-icon class="connector-arrow" :class="{ active: isActive }"><Right /></el-icon>
  </div>
</template>

<script setup lang="ts">
import { defineProps } from 'vue'
import { Right } from '@element-plus/icons-vue'

defineProps<{
  isActive: boolean
}>()
</script>

<style scoped>
.stage-connector {
  display: flex;
  align-items: center;
  padding: 0 8px;
}

.connector-line {
  width: 40px;
  height: 2px;
  background: #dcdfe6;
}

.connector-line.active {
  background: #67c23a;
}

.connector-arrow {
  color: #dcdfe6;
}

.connector-arrow.active {
  color: #67c23a;
}
</style>
