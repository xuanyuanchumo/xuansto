<template>
  <div class="realtime-quality-page">
    <RealtimeQualityMonitor />
  </div>
</template>

<script setup lang="ts">
import RealtimeQualityMonitor from '@/components/RealtimeQualityMonitor.vue'
</script>

<style scoped>
.realtime-quality-page {
  padding: 20px;
  min-height: 100vh;
  background: #f5f7fa;
}
</style>
