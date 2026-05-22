<template>
  <div class="path-validation-detail-page">
    <PathValidationStatus />
  </div>
</template>

<script setup lang="ts">
import PathValidationStatus from '@/components/PathValidationStatus.vue'
</script>

<style scoped>
.path-validation-detail-page {
  padding: 20px;
  min-height: 100vh;
  background: #f5f7fa;
}
</style>
