<template>
  <div class="operation-priority-indicator">
    <el-card shadow="hover" :class="`priority-${riskLevel.toLowerCase()}`">
      <template #header>
        <div class="indicator-header">
          <span class="title">操作优先级指示器</span>
          <div class="risk-badge" :class="`risk-${riskLevel.toLowerCase()}`">
            {{ riskEmoji }} {{ riskLevel }}
          </div>
        </div>
      </template>

      <div class="indicator-content">
        <div class="mode-section">
          <div class="section-label">当前操作模式</div>
          <div class="mode-display">
            <el-tag 
              :type="getModeTagType(currentMode)" 
              size="large" 
              effect="dark"
              class="mode-tag"
            >
              {{ currentMode }}
            </el-tag>
            <span class="mode-description">{{ modeDescriptions[currentMode] }}</span>
          </div>
        </div>

        <el-divider />

        <div class="priority-section">
          <div class="section-label">推荐优先级</div>
          <div class="priority-recommendation">
            <div class="priority-value">
              <el-tag 
                :type="getPriorityTagType(recommendedPriority)" 
                size="large" 
                effect="dark"
                class="priority-tag"
              >
                {{ recommendedPriority.toUpperCase() }}
              </el-tag>
            </div>
            
            <div class="reason-box">
              <div class="reason-label">推荐理由:</div>
              <ul class="reason-list">
                <li v-for="(reason, idx) in reasons" :key="idx">
                  <el-icon><InfoFilled /></el-icon>
                  <span>{{ reason }}</span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        <el-divider />

        <div class="distribution-section">
          <div class="section-label">任务分布</div>
          <div class="distribution-bars">
            <div 
              v-for="(count, priority) in distribution" 
              :key="priority"
              class="distribution-item"
            >
              <div class="dist-label">{{ getPriorityLabel(priority) }}</div>
              <el-progress 
                :percentage="getDistributionPercent(count)"
                :color="getProgressColor(priority)"
                :stroke-width="16"
              />
              <div class="dist-count">{{ count }}</div>
            </div>
          </div>
        </div>

        <el-divider />

        <div class="actions-section">
          <el-button 
            type="primary" 
            size="small" 
            @click="adjustPriority"
            :disabled="loading"
          >
            调整优先级
          </el-button>
          <el-button 
            size="small" 
            @click="switchMode"
            :disabled="loading"
          >
            切换模式
          </el-button>
        </div>
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" title="调整优先级" width="400px">
      <el-form label-width="100px">
        <el-form-item label="新优先级">
          <el-select v-model="newPriority" placeholder="选择优先级">
            <el-option label="高 (HIGH)" value="high" />
            <el-option label="中 (MEDIUM)" value="medium" />
            <el-option label="低 (LOW)" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="原因">
          <el-input v-model="adjustReason" type="textarea" :rows="3" placeholder="请输入调整原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmAdjustment" :loading="confirming">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { InfoFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

interface Props {
  initialMode?: string
  initialPriority?: string
}

const props = withDefaults(defineProps<Props>(), {
  initialMode: 'SCRIPT',
  initialPriority: 'medium'
})

const emit = defineEmits<{
  (e: 'modeChange', mode: string): void
  (e: 'priorityChange', priority: string): void
}>()

const currentMode = ref(props.initialMode)
const recommendedPriority = ref(props.initialPriority)
const riskLevel = ref('MEDIUM')
const riskEmoji = computed(() => {
  const emojis: Record<string, string> = {
    LOW: '🟢',
    MEDIUM: '🟡',
    HIGH: '🔴'
  }
  return emojis[riskLevel.value] || '⚪'
})

const reasons = ref<string[]>([])
const distribution = ref<Record<string, number>>({
  high: 5,
  medium: 15,
  low: 8
})

const loading = ref(false)
const dialogVisible = ref(false)
const newPriority = ref('')
const adjustReason = ref('')
const confirming = ref(false)

const modeDescriptions: Record<string, string> = {
  MANUAL: '人工手动操作模式，所有操作需用户确认',
  SCRIPT: '脚本自动化执行模式，按预定流程自动处理',
  COMMAND: '命令行指令模式，接收并执行命令序列'
}

const totalTasks = computed(() => {
  return Object.values(distribution.value).reduce((sum, count) => sum + count, 0)
})

const getModeTagType = (mode: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    MANUAL: '',
    SCRIPT: 'success',
    COMMAND: 'warning'
  }
  return types[mode] || ''
}

const getPriorityTagType = (priority: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    high: 'danger',
    medium: 'warning',
    low: 'success'
  }
  return types[priority] || ''
}

const getPriorityLabel = (priority: string): string => {
  const labels: Record<string, string> = {
    high: '高优先级',
    medium: '中优先级',
    low: '低优先级'
  }
  return labels[priority] || priority
}

const getDistributionPercent = (count: number): number => {
  if (totalTasks.value === 0) return 0
  return Math.round((count / totalTasks.value) * 100)
}

const getProgressColor = (priority: string): string => {
  const colors: Record<string, string> = {
    high: '#f56c6c',
    medium: '#e6a23c',
    low: '#67c23a'
  }
  return colors[priority] || '#409eff'
}

const fetchOperationPriority = async () => {
  loading.value = true
  try {
    const response = await api.get('/dashboard/extended-stats')
    const data = response.data.operation_priorities
    
    currentMode.value = data.current_mode || 'SCRIPT'
    recommendedPriority.value = data.recommended_priority || 'medium'
    
    if (data.distribution) {
      distribution.value = data.distribution
    }
    
    if (data.reason) {
      reasons.value = [data.reason]
      
      if (recommendedPriority.value === 'high') {
        riskLevel.value = 'HIGH'
        reasons.value.push('存在紧急任务需要立即处理')
      } else if (Object.keys(distribution.value).length > 20) {
        riskLevel.value = 'HIGH'
        reasons.value.push('任务积压较多，建议提高处理效率')
      } else if (distribution.value.high > distribution.value.medium * 0.5) {
        riskLevel.value = 'MEDIUM'
        reasons.value.push('高优先级任务占比较高')
      } else {
        riskLevel.value = 'LOW'
        reasons.value.push('系统运行正常，任务分布均衡')
      }
    }
  } catch (error) {
    console.error('获取操作优先级信息失败:', error)
    reasons.value = [
      '正常运行状态',
      '无异常风险因素'
    ]
    riskLevel.value = 'LOW'
  } finally {
    loading.value = false
  }
}

const adjustPriority = () => {
  newPriority.value = recommendedPriority.value
  dialogVisible.value = true
}

const switchMode = () => {
  const modes = ['MANUAL', 'SCRIPT', 'COMMAND']
  const currentIndex = modes.indexOf(currentMode.value)
  const nextIndex = (currentIndex + 1) % modes.length
  currentMode.value = modes[nextIndex]
  
  emit('modeChange', currentMode.value)
  ElMessage.success(`已切换到 ${currentMode.value} 模式`)
  
  fetchOperationPriority()
}

const confirmAdjustment = async () => {
  confirming.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 500))
    
    recommendedPriority.value = newPriority.value
    
    if (newPriority.value === 'high') {
      riskLevel.value = 'HIGH'
    } else if (newPriority.value === 'medium') {
      riskLevel.value = 'MEDIUM'
    } else {
      riskLevel.value = 'LOW'
    }
    
    emit('priorityChange', newPriority.value)
    ElMessage.success(`优先级已调整为 ${newPriority.value.toUpperCase()}`)
    dialogVisible.value = false
    
    fetchOperationPriority()
  } catch (error) {
    ElMessage.error('调整失败')
  } finally {
    confirming.value = false
  }
}

onMounted(() => {
  fetchOperationPriority()
})
</script>

<style scoped>
.operation-priority-indicator {
  max-width: 600px;
  margin: 0 auto;
}

.indicator-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.risk-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: bold;
}

.risk-low {
  background: #f0f9eb;
  color: #67c23a;
  border: 1px solid #c2e7b0;
}

.risk-medium {
  background: #fdf6ec;
  color: #e6a23c;
  border: 1px solid #f5dab1;
}

.risk-high {
  background: #fef0f0;
  color: #f56c6c;
  border: 1px solid #fbc4c4;
}

.priority-low {
  border-top: 3px solid #67c23a;
}

.priority-medium {
  border-top: 3px solid #e6a23c;
}

.priority-high {
  border-top: 3px solid #f56c6c;
}

.section-label {
  font-size: 13px;
  font-weight: 500;
  color: #606266;
  margin-bottom: 10px;
}

.mode-display {
  display: flex;
  align-items: center;
  gap: 15px;
}

.mode-tag {
  min-width: 120px;
  text-align: center;
}

.mode-description {
  font-size: 13px;
  color: #909399;
  flex: 1;
}

.priority-recommendation {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.priority-tag {
  text-align: center;
  min-width: 140px;
}

.reason-box {
  background: #f5f7fa;
  padding: 12px 15px;
  border-radius: 8px;
}

.reason-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.reason-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.reason-list li {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
}

.reason-list li .el-icon {
  margin-top: 2px;
  color: #409eff;
  flex-shrink: 0;
}

.distribution-section {
  margin: 10px 0;
}

.distribution-bars {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.distribution-item {
  display: grid;
  grid-template-columns: 80px 1fr 50px;
  align-items: center;
  gap: 10px;
}

.dist-label {
  font-size: 13px;
  color: #606266;
  font-weight: 500;
}

.dist-count {
  text-align: right;
  font-weight: bold;
  color: #303133;
}

.actions-section {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-top: 10px;
}
</style>
