<template>
  <div class="filter-bar">
    <el-input
      v-model="localSearchText"
      placeholder="搜索任务名称"
      style="width: 200px"
      clearable
      @clear="handleSearch"
      @keyup.enter="handleSearch"
    />
    <el-select 
      v-model="localFilterStatus" 
      placeholder="状态筛选" 
      clearable 
      style="width: 150px" 
      @change="handleSearch"
    >
      <el-option label="待分配" value="pending" />
      <el-option label="进行中" value="in_progress" />
      <el-option label="待审核" value="review" />
      <el-option label="已完成" value="completed" />
    </el-select>
    <el-select 
      v-model="localFilterPriority" 
      placeholder="优先级筛选" 
      clearable 
      style="width: 150px" 
      @change="handleSearch"
    >
      <el-option label="低" value="low" />
      <el-option label="中" value="medium" />
      <el-option label="高" value="high" />
      <el-option label="紧急" value="urgent" />
    </el-select>
    <el-button type="primary" @click="handleSearch">
      <el-icon><Search /></el-icon>
      查询
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { Search } from '@element-plus/icons-vue'

interface FilterParams {
  searchText: string
  filterStatus: string
  filterPriority: string
}

interface Props {
  searchText?: string
  filterStatus?: string
  filterPriority?: string
}

const props = withDefaults(defineProps<Props>(), {
  searchText: '',
  filterStatus: '',
  filterPriority: ''
})

const emit = defineEmits<{
  (e: 'search', params: FilterParams): void
  (e: 'update:searchText', value: string): void
  (e: 'update:filterStatus', value: string): void
  (e: 'update:filterPriority', value: string): void
}>()

const localSearchText = ref(props.searchText)
const localFilterStatus = ref(props.filterStatus)
const localFilterPriority = ref(props.filterPriority)

watch(() => props.searchText, (val) => {
  localSearchText.value = val
})

watch(() => props.filterStatus, (val) => {
  localFilterStatus.value = val
})

watch(() => props.filterPriority, (val) => {
  localFilterPriority.value = val
})

const handleSearch = () => {
  emit('update:searchText', localSearchText.value)
  emit('update:filterStatus', localFilterStatus.value)
  emit('update:filterPriority', localFilterPriority.value)
  emit('search', {
    searchText: localSearchText.value,
    filterStatus: localFilterStatus.value,
    filterPriority: localFilterPriority.value
  })
}
</script>

<style scoped>
.filter-bar {
  display: flex;
  gap: 15px;
  align-items: center;
}
</style>
