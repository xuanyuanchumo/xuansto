<template>
  <div class="evolution-control-panel">
    <el-card class="control-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="control-icon"><Setting /></el-icon>
            <span class="title">演化控制面板</span>
          </div>
          <el-tag :type="statusTagType" size="small">
            {{ statusLabel }}
          </el-tag>
        </div>
      </template>

      <div class="control-content">
        <div class="control-section">
          <div class="section-title">演化操作</div>
          <div class="control-buttons">
            <el-tooltip content="手动触发一次演化" placement="top">
              <el-button
                type="primary"
                :loading="triggering"
                :disabled="isRunning || !canTrigger"
                @click="showTriggerDialog"
              >
                <el-icon><VideoPlay /></el-icon>
                触发演化
              </el-button>
            </el-tooltip>

            <el-tooltip :content="isPaused ? '恢复演化' : '暂停演化'" placement="top">
              <el-button
                :type="isPaused ? 'success' : 'warning'"
                :loading="pausing"
                :disabled="!isRunning && !isPaused"
                @click="handlePauseResume"
              >
                <el-icon>
                  <VideoPause v-if="!isPaused" />
                  <VideoPlay v-else />
                </el-icon>
                {{ isPaused ? '恢复' : '暂停' }}
              </el-button>
            </el-tooltip>

            <el-tooltip content="停止当前演化" placement="top">
              <el-button
                type="danger"
                :loading="stopping"
                :disabled="!isRunning && !isPaused"
                @click="showStopConfirm"
              >
                <el-icon><CircleClose /></el-icon>
                停止
              </el-button>
            </el-tooltip>
          </div>
        </div>

        <el-divider />

        <div class="control-section">
          <div class="section-title">回滚控制</div>
          <div class="rollback-control">
            <div class="rollback-info">
              <span class="info-label">当前版本:</span>
              <el-tag size="small">{{ currentVersion }}</el-tag>
              <span class="info-label" style="margin-left: 20px;">可回滚版本:</span>
              <span class="info-value">{{ availableRollbackSteps }} 步</span>
            </div>
            <div class="rollback-actions">
              <el-input-number
                v-model="rollbackSteps"
                :min="1"
                :max="availableRollbackSteps"
                :disabled="availableRollbackSteps === 0"
                size="small"
                style="width: 100px"
              />
              <el-button
                type="warning"
                :loading="rollingBack"
                :disabled="availableRollbackSteps === 0 || isRunning"
                @click="showRollbackConfirm"
              >
                <el-icon><RefreshLeft /></el-icon>
                回滚
              </el-button>
            </div>
          </div>
        </div>

        <el-divider />

        <div class="control-section">
          <div class="section-title">演化参数配置</div>
          <el-form
            ref="configFormRef"
            :model="evolutionConfig"
            :rules="configRules"
            label-width="120px"
            size="small"
          >
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="演化类型" prop="evolution_type">
                  <el-select v-model="evolutionConfig.evolution_type" placeholder="选择演化类型">
                    <el-option
                      v-for="type in evolutionTypes"
                      :key="type.value"
                      :label="type.label"
                      :value="type.value"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="演化模式" prop="mode">
                  <el-select v-model="evolutionConfig.mode" placeholder="选择演化模式">
                    <el-option label="自动" value="auto" />
                    <el-option label="手动" value="manual" />
                    <el-option label="半自动" value="semi_auto" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="最大迭代次数" prop="max_iterations">
                  <el-input-number
                    v-model="evolutionConfig.max_iterations"
                    :min="1"
                    :max="100"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="超时时间(秒)" prop="timeout_seconds">
                  <el-input-number
                    v-model="evolutionConfig.timeout_seconds"
                    :min="60"
                    :max="3600"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="安全模式">
                  <el-switch v-model="evolutionConfig.safe_mode" />
                  <el-tooltip content="启用安全模式将在异常时自动回滚" placement="top">
                    <el-icon class="info-icon"><InfoFilled /></el-icon>
                  </el-tooltip>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="自动验证">
                  <el-switch v-model="evolutionConfig.auto_validation" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="目标技能" prop="target_skills">
              <el-select
                v-model="evolutionConfig.target_skills"
                multiple
                placeholder="选择目标技能(可多选)"
                style="width: 100%"
              >
                <el-option
                  v-for="skill in availableSkills"
                  :key="skill.id"
                  :label="skill.name"
                  :value="skill.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveConfig" :loading="savingConfig">
                保存配置
              </el-button>
              <el-button @click="resetConfig">重置</el-button>
            </el-form-item>
          </el-form>
        </div>

        <el-divider />

        <div class="control-section">
          <div class="section-title">调度设置</div>
          <el-form label-width="120px" size="small">
            <el-form-item label="启用调度">
              <el-switch v-model="scheduleEnabled" @change="handleScheduleChange" />
            </el-form-item>
            <el-form-item v-if="scheduleEnabled" label="调度周期">
              <el-select v-model="scheduleInterval" style="width: 150px">
                <el-option label="每小时" value="hourly" />
                <el-option label="每天" value="daily" />
                <el-option label="每周" value="weekly" />
                <el-option label="自定义" value="custom" />
              </el-select>
              <el-time-picker
                v-if="scheduleInterval === 'daily' || scheduleInterval === 'weekly'"
                v-model="scheduleTime"
                placeholder="选择时间"
                style="margin-left: 10px; width: 120px"
              />
            </el-form-item>
            <el-form-item v-if="scheduleEnabled" label="下次执行">
              <span class="next-schedule">{{ nextScheduleTime }}</span>
            </el-form-item>
          </el-form>
        </div>
      </div>
    </el-card>

    <el-dialog
      v-model="triggerDialogVisible"
      title="触发演化"
      width="500px"
      destroy-on-close
    >
      <el-form :model="triggerParams" label-width="100px">
        <el-form-item label="演化类型">
          <el-select v-model="triggerParams.evolution_type" style="width: 100%">
            <el-option
              v-for="type in evolutionTypes"
              :key="type.value"
              :label="type.label"
              :value="type.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="演化原因">
          <el-input
            v-model="triggerParams.reason"
            type="textarea"
            :rows="3"
            placeholder="请输入触发演化的原因"
          />
        </el-form-item>
        <el-form-item label="优先级">
          <el-rate v-model="triggerParams.priority" :max="5" />
        </el-form-item>
        <el-form-item label="通知设置">
          <el-checkbox v-model="triggerParams.notify_on_start">开始时通知</el-checkbox>
          <el-checkbox v-model="triggerParams.notify_on_complete">完成时通知</el-checkbox>
          <el-checkbox v-model="triggerParams.notify_on_error">错误时通知</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="triggerDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="triggering" @click="confirmTrigger">
          确认触发
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="stopConfirmVisible"
      title="确认停止"
      width="400px"
    >
      <el-alert
        title="警告"
        type="warning"
        description="停止演化可能会导致未完成的变更丢失，确定要停止吗？"
        show-icon
        :closable="false"
      />
      <div style="margin-top: 15px;">
        <el-checkbox v-model="stopWithRollback">停止后自动回滚到上一个稳定版本</el-checkbox>
      </div>
      <template #footer>
        <el-button @click="stopConfirmVisible = false">取消</el-button>
        <el-button type="danger" :loading="stopping" @click="confirmStop">
          确认停止
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="rollbackConfirmVisible"
      title="确认回滚"
      width="450px"
    >
      <el-alert
        title="注意"
        type="warning"
        :description="`将回滚 ${rollbackSteps} 个版本，此操作不可撤销。`"
        show-icon
        :closable="false"
      />
      <div style="margin-top: 15px;">
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="当前版本">{{ currentVersion }}</el-descriptions-item>
          <el-descriptions-item label="目标版本">{{ targetRollbackVersion }}</el-descriptions-item>
          <el-descriptions-item label="回滚步数">{{ rollbackSteps }}</el-descriptions-item>
        </el-descriptions>
      </div>
      <div style="margin-top: 15px;">
        <el-input
          v-model="rollbackReason"
          type="textarea"
          :rows="2"
          placeholder="请输入回滚原因（必填）"
        />
      </div>
      <template #footer>
        <el-button @click="rollbackConfirmVisible = false">取消</el-button>
        <el-button
          type="warning"
          :loading="rollingBack"
          :disabled="!rollbackReason.trim()"
          @click="confirmRollback"
        >
          确认回滚
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus'
import {
  Setting,
  VideoPlay,
  VideoPause,
  CircleClose,
  RefreshLeft,
  InfoFilled
} from '@element-plus/icons-vue'
import api from '@/api'

interface EvolutionType {
  label: string
  value: string
}

interface Skill {
  id: string
  name: string
}

interface EvolutionStatus {
  status: 'running' | 'paused' | 'stopped' | 'idle'
  current_version: string
  available_rollback_steps: number
  can_trigger: boolean
  next_schedule: string | null
}

interface EvolutionConfig {
  evolution_type: string
  mode: string
  max_iterations: number
  timeout_seconds: number
  safe_mode: boolean
  auto_validation: boolean
  target_skills: string[]
}

interface Props {
  projectId?: number
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'trigger', params: any): void
  (e: 'pause'): void
  (e: 'resume'): void
  (e: 'stop', withRollback: boolean): void
  (e: 'rollback', steps: number, reason: string): void
  (e: 'config-change', config: EvolutionConfig): void
}>()

const configFormRef = ref<FormInstance>()

const triggering = ref(false)
const pausing = ref(false)
const stopping = ref(false)
const rollingBack = ref(false)
const savingConfig = ref(false)

const triggerDialogVisible = ref(false)
const stopConfirmVisible = ref(false)
const rollbackConfirmVisible = ref(false)

const stopWithRollback = ref(true)
const rollbackSteps = ref(1)
const rollbackReason = ref('')

const scheduleEnabled = ref(false)
const scheduleInterval = ref('daily')
const scheduleTime = ref(new Date())

const status = ref<EvolutionStatus>({
  status: 'idle',
  current_version: 'v1.0.0',
  available_rollback_steps: 5,
  can_trigger: true,
  next_schedule: null
})

const evolutionConfig = reactive<EvolutionConfig>({
  evolution_type: 'skill_optimization',
  mode: 'auto',
  max_iterations: 10,
  timeout_seconds: 300,
  safe_mode: true,
  auto_validation: true,
  target_skills: []
})

const triggerParams = reactive({
  evolution_type: 'skill_optimization',
  reason: '',
  priority: 3,
  notify_on_start: true,
  notify_on_complete: true,
  notify_on_error: true
})

const evolutionTypes: EvolutionType[] = [
  { label: '技能优化', value: 'skill_optimization' },
  { label: '工作流适配', value: 'workflow_adaptation' },
  { label: '资源重平衡', value: 'resource_rebalance' },
  { label: '知识更新', value: 'knowledge_update' },
  { label: '性能调优', value: 'performance_tuning' },
  { label: '安全加固', value: 'security_enhancement' }
]

const availableSkills = ref<Skill[]>([
  { id: 'skill_1', name: '代码生成' },
  { id: 'skill_2', name: '代码审查' },
  { id: 'skill_3', name: '测试生成' },
  { id: 'skill_4', name: '文档生成' },
  { id: 'skill_5', name: '需求分析' }
])

const configRules: FormRules = {
  evolution_type: [
    { required: true, message: '请选择演化类型', trigger: 'change' }
  ],
  mode: [
    { required: true, message: '请选择演化模式', trigger: 'change' }
  ],
  max_iterations: [
    { required: true, message: '请输入最大迭代次数', trigger: 'blur' }
  ],
  timeout_seconds: [
    { required: true, message: '请输入超时时间', trigger: 'blur' }
  ]
}

const isRunning = computed(() => status.value.status === 'running')
const isPaused = computed(() => status.value.status === 'paused')
const canTrigger = computed(() => status.value.can_trigger)
const currentVersion = computed(() => status.value.current_version)
const availableRollbackSteps = computed(() => status.value.available_rollback_steps)

const statusTagType = computed(() => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    running: 'success',
    paused: 'warning',
    stopped: 'danger',
    idle: 'info'
  }
  return types[status.value.status] || 'info'
})

const statusLabel = computed(() => {
  const labels: Record<string, string> = {
    running: '运行中',
    paused: '已暂停',
    stopped: '已停止',
    idle: '空闲'
  }
  return labels[status.value.status] || '未知'
})

const targetRollbackVersion = computed(() => {
  const current = status.value.current_version
  const match = current.match(/v(\d+)\.(\d+)\.(\d+)/)
  if (match) {
    const patch = Math.max(0, parseInt(match[3]) - rollbackSteps.value)
    return `v${match[1]}.${match[2]}.${patch}`
  }
  return current
})

const nextScheduleTime = computed(() => {
  if (!status.value.next_schedule) return '未设置'
  return new Date(status.value.next_schedule).toLocaleString('zh-CN')
})

const showTriggerDialog = () => {
  triggerParams.evolution_type = evolutionConfig.evolution_type
  triggerParams.reason = ''
  triggerParams.priority = 3
  triggerDialogVisible.value = true
}

const confirmTrigger = async () => {
  if (!triggerParams.reason.trim()) {
    ElMessage.warning('请输入触发演化的原因')
    return
  }

  triggering.value = true
  try {
    const params = {
      ...triggerParams,
      project_id: props.projectId
    }
    await api.post('/evolution-monitor/trigger', params)
    ElMessage.success('演化已触发')
    triggerDialogVisible.value = false
    emit('trigger', params)
    await fetchStatus()
  } catch (error) {
    console.error('Failed to trigger evolution:', error)
    ElMessage.error('触发演化失败')
  } finally {
    triggering.value = false
  }
}

const handlePauseResume = async () => {
  const action = isPaused.value ? '恢复' : '暂停'
  try {
    await ElMessageBox.confirm(
      `确定要${action}演化吗？`,
      '确认',
      { type: 'warning' }
    )

    pausing.value = true
    if (isPaused.value) {
      await api.post('/evolution-monitor/resume', { project_id: props.projectId })
      ElMessage.success('演化已恢复')
      emit('resume')
    } else {
      await api.post('/evolution-monitor/pause', { project_id: props.projectId })
      ElMessage.success('演化已暂停')
      emit('pause')
    }
    await fetchStatus()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to pause/resume:', error)
      ElMessage.error(`${action}失败`)
    }
  } finally {
    pausing.value = false
  }
}

const showStopConfirm = () => {
  stopWithRollback.value = true
  stopConfirmVisible.value = true
}

const confirmStop = async () => {
  stopping.value = true
  try {
    await api.post('/evolution-monitor/stop', {
      project_id: props.projectId,
      with_rollback: stopWithRollback.value
    })
    ElMessage.success('演化已停止')
    stopConfirmVisible.value = false
    emit('stop', stopWithRollback.value)
    await fetchStatus()
  } catch (error) {
    console.error('Failed to stop evolution:', error)
    ElMessage.error('停止演化失败')
  } finally {
    stopping.value = false
  }
}

const showRollbackConfirm = () => {
  rollbackReason.value = ''
  rollbackConfirmVisible.value = true
}

const confirmRollback = async () => {
  if (!rollbackReason.value.trim()) {
    ElMessage.warning('请输入回滚原因')
    return
  }

  rollingBack.value = true
  try {
    await api.post('/evolution-monitor/rollback', {
      project_id: props.projectId,
      steps: rollbackSteps.value,
      reason: rollbackReason.value
    })
    ElMessage.success('回滚成功')
    rollbackConfirmVisible.value = false
    emit('rollback', rollbackSteps.value, rollbackReason.value)
    await fetchStatus()
  } catch (error) {
    console.error('Failed to rollback:', error)
    ElMessage.error('回滚失败')
  } finally {
    rollingBack.value = false
  }
}

const saveConfig = async () => {
  if (!configFormRef.value) return

  await configFormRef.value.validate(async (valid) => {
    if (!valid) return

    savingConfig.value = true
    try {
      await api.post('/evolution-monitor/config', {
        project_id: props.projectId,
        config: evolutionConfig
      })
      ElMessage.success('配置已保存')
      emit('config-change', { ...evolutionConfig })
    } catch (error) {
      console.error('Failed to save config:', error)
      ElMessage.error('保存配置失败')
    } finally {
      savingConfig.value = false
    }
  })
}

const resetConfig = () => {
  evolutionConfig.evolution_type = 'skill_optimization'
  evolutionConfig.mode = 'auto'
  evolutionConfig.max_iterations = 10
  evolutionConfig.timeout_seconds = 300
  evolutionConfig.safe_mode = true
  evolutionConfig.auto_validation = true
  evolutionConfig.target_skills = []
}

const handleScheduleChange = async (enabled: boolean) => {
  try {
    await api.post('/evolution-monitor/schedule', {
      project_id: props.projectId,
      enabled,
      interval: scheduleInterval.value,
      time: scheduleTime.value
    })
    ElMessage.success(enabled ? '调度已启用' : '调度已禁用')
  } catch (error) {
    console.error('Failed to update schedule:', error)
    ElMessage.error('更新调度设置失败')
    scheduleEnabled.value = !enabled
  }
}

const fetchStatus = async () => {
  try {
    const url = props.projectId
      ? `/evolution-monitor/status?project_id=${props.projectId}`
      : '/evolution-monitor/status'
    const response = await api.get(url)
    status.value = response.data as EvolutionStatus
  } catch (error) {
    console.error('Failed to fetch status:', error)
  }
}

const fetchConfig = async () => {
  try {
    const url = props.projectId
      ? `/evolution-monitor/config?project_id=${props.projectId}`
      : '/evolution-monitor/config'
    const response = await api.get(url)
    Object.assign(evolutionConfig, response.data)
  } catch (error) {
    console.error('Failed to fetch config:', error)
  }
}

const fetchSkills = async () => {
  try {
    const response = await api.get('/skills')
    availableSkills.value = response.data as Skill[]
  } catch (error) {
    console.error('Failed to fetch skills:', error)
  }
}

onMounted(() => {
  fetchStatus()
  fetchConfig()
  fetchSkills()
})
</script>

<style scoped>
.evolution-control-panel {
  width: 100%;
}

.control-card {
  transition: all 0.3s ease;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.control-icon {
  font-size: 20px;
  color: #409eff;
}

.title {
  font-size: 16px;
  font-weight: 600;
}

.control-content {
  padding: 10px 0;
}

.control-section {
  margin-bottom: 10px;
}

.section-title {
  font-weight: 500;
  font-size: 14px;
  color: #303133;
  margin-bottom: 15px;
}

.control-buttons {
  display: flex;
  gap: 12px;
}

.rollback-control {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.rollback-info {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.info-label {
  font-size: 13px;
  color: #909399;
}

.info-value {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.rollback-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.info-icon {
  margin-left: 5px;
  color: #909399;
  cursor: help;
}

.next-schedule {
  font-size: 14px;
  color: #606266;
}

@media (max-width: 768px) {
  .control-buttons {
    flex-direction: column;
  }

  .rollback-info {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
