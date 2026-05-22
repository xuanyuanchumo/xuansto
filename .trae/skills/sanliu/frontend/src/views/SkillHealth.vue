<template>
  <div class="skill-health-view">
    <SkillHealthPanel :skill-id="skillId" @evaluation-complete="handleEvaluationComplete" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { SkillHealthPanel } from '@/components/evolution'

const route = useRoute()
const skillId = computed(() => route.query.skill_id as string || undefined)

const handleEvaluationComplete = (data: any) => {
  console.log('Evaluation complete:', data)
}
</script>

<style scoped>
.skill-health-view {
  padding: 20px;
}
</style>
