<template>
  <el-dialog 
    v-model="dialogVisible" 
    title="添加任务依赖" 
    width="500px"
    @close="handleClose"
  >
    <el-form :model="form" label-width="100px">
      <el-form-item label="当前任务">
        <el-input v-model="form.currentTaskName" disabled />
      </el-form-item>
      <el-form-item label="依赖任务" required>
        <el-select 
          v-model="form.dependsOnTaskId" 
          placeholder="请选择依赖任务" 
          style="width: 100%" 
          filterable
        >
          <el-option
            v-for="task in availableTasks"
            :key="task.id"
            :label="`#${task.id} - ${task.name}`"
            :value="task.id"
          />
        </el-select>
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
import type { Task } from '@/stores/tasks'

interface AddDependencyForm {
  currentTaskId: number
  currentTaskName: string
  dependsOnTaskId: number | null
}

interface Props {
  modelValue: boolean
  form: AddDependencyForm
  availableTasks: Task[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm', form: AddDependencyForm): void
}>()

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const form = ref<AddDependencyForm>({ ...props.form })

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
