<template>
  <div class="realtime-evolution-view">
    <RealtimeEvolutionStatus :evolution-id="evolutionId" @evolution-completed="handleEvolutionCompleted" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { RealtimeEvolutionStatus } from '@/components/evolution'

const route = useRoute()
const evolutionId = computed(() => route.query.evolution_id as string || undefined)

const handleEvolutionCompleted = (result: any) => {
  console.log('Evolution completed:', result)
}
</script>

<style scoped>
.realtime-evolution-view {
  padding: 20px;
}
</style>
