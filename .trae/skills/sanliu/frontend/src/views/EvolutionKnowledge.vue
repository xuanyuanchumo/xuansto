<template>
  <div class="evolution-knowledge-view">
    <EvolutionKnowledgeGraph :skill-id="skillId" @evolution-triggered="handleEvolutionTriggered" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { EvolutionKnowledgeGraph } from '@/components/evolution'

const route = useRoute()
const skillId = computed(() => route.query.skill_id as string || undefined)

const handleEvolutionTriggered = (data: any) => {
  console.log('Evolution triggered:', data)
}
</script>

<style scoped>
.evolution-knowledge-view {
  padding: 20px;
}
</style>
