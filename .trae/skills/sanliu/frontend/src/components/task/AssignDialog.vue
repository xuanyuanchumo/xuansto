<template>
  <el-dialog 
    v-model="dialogVisible" 
    title="任务分配" 
    width="500px"
    @close="handleClose"
  >
    <el-form :model="form" label-width="100px">
      <el-form-item label="任务名称">
        <el-input v-model="form.taskName" disabled />
      </el-form-item>
      <el-form-item label="选择 Agent" required>
        <el-select v-model="form.agentId" placeholder="请选择 Agent" style="width: 100%">
          <el-option
            v-for="agent in agents"
            :key="agent.id"
            :label="`${agent.name} (${agent.role || '未设置角色'}) - 负载: ${agent.current_load}/${agent.max_load}`"
            :value="agent.id"
            :disabled="agent.current_load >= agent.max_load"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="预估工时">
        <el-input-number v-model="form.estimatedHours" :min="0.5" :max="1000" :step="0.5" />
        <span style="margin-left: 10px">小时</span>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleConfirm" :loading="loading">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { Agent } from '@/stores/agents'

interface AssignForm {
  taskId: number
  taskName: string
  agentId: number | null
  estimatedHours: number
}

interface Props {
  modelValue: boolean
  form: AssignForm
  agents: Agent[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm', form: AssignForm): void
}>()

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const form = ref<AssignForm>({ ...props.form })

watch(() => props.form, (newForm) => {
  form.value = { ...newForm }
}, { deep: true })

const handleClose = () => {
  emit('update:modelValue', false)
}

const handleConfirm = () => {
  emit('confirm', form.value)
}
</script>
