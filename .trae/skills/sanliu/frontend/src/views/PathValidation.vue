<template>
  <div class="path-validation-view">
    <PathValidationStatus :skill-id="skillId" @path-fixed="handlePathFixed" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { PathValidationStatus } from '@/components/evolution'

const route = useRoute()
const skillId = computed(() => route.query.skill_id as string || undefined)

const handlePathFixed = (path: string) => {
  console.log('Path fixed:', path)
}
</script>

<style scoped>
.path-validation-view {
  padding: 20px;
}
</style>
