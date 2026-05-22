<template>
  <div class="quality-alerts">
    <el-card class="alerts-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span class="title">质量告警</span>
            <el-badge :value="activeAlertsCount" :hidden="activeAlertsCount === 0" type="danger">
              <el-icon><Bell /></el-icon>
            </el-badge>
          </div>
          <div class="header-actions">
            <el-button
              type="primary"
              size="small"
              :icon="Setting"
              @click="showRulesDialog = true"
            >
              告警规则
            </el-button>
            <el-button
              type="success"
              size="small"
              :icon="Check"
              :disabled="activeAlertsCount === 0"
              @click="acknowledgeAllAlerts"
            >
              全部确认
            </el-button>
          </div>
        </div>
      </template>

      <div class="alerts-filter">
        <el-row :gutter="16">
          <el-col :span="8">
            <el-select v-model="filterSeverity" placeholder="按严重程度筛选" clearable @change="filterAlerts">
              <el-option label="信息" value="info" />
              <el-option label="警告" value="warning" />
              <el-option label="错误" value="error" />
              <el-option label="严重" value="critical" />
            </el-select>
          </el-col>
          <el-col :span="8">
            <el-select v-model="filterMetricType" placeholder="按指标类型筛选" clearable @change="filterAlerts">
              <el-option label="性能" value="performance" />
              <el-option label="错误率" value="error_rate" />
              <el-option label="代码质量" value="code_quality" />
              <el-option label="测试覆盖率" value="test_coverage" />
            </el-select>
          </el-col>
          <el-col :span="8">
            <el-switch
              v-model="showAcknowledged"
              active-text="显示已确认"
              inactive-text="仅未确认"
              @change="filterAlerts"
            />
          </el-col>
        </el-row>
      </div>

      <el-divider />

      <div class="alerts-list" v-loading="loading">
        <div v-if="filteredAlerts.length === 0" class="empty-alerts">
          <el-empty description="暂无告警">
            <el-button type="primary" @click="triggerQualityCheck">
              触发质量检查
            </el-button>
          </el-empty>
        </div>
        <div v-else>
          <transition-group name="alert-list">
            <div
              v-for="alert in filteredAlerts"
              :key="alert.alert_id"
              class="alert-item"
              :class="[`alert-${alert.severity}`, { 'alert-acknowledged': alert.acknowledged }]"
            >
              <div class="alert-indicator">
                <div class="indicator-dot" :class="`severity-${alert.severity}`"></div>
              </div>

              <div class="alert-icon">
                <el-icon :size="24">
                  <component :is="getAlertIcon(alert.severity)" />
                </el-icon>
              </div>

              <div class="alert-content">
                <div class="alert-header">
                  <span class="alert-title">{{ alert.title }}</span>
                  <el-tag :type="getSeverityType(alert.severity)" size="small" effect="dark">
                    {{ getSeverityLabel(alert.severity) }}
                  </el-tag>
                </div>
                <div class="alert-message">{{ alert.message }}</div>
                <div class="alert-details">
                  <div class="detail-item">
                    <el-icon><DataLine /></el-icon>
                    <span>{{ getMetricTypeLabel(alert.metric_type) }}</span>
                  </div>
                  <div class="detail-item">
                    <el-icon><Position /></el-icon>
                    <span>当前值: {{ alert.current_value.toFixed(2) }}</span>
                  </div>
                  <div class="detail-item">
                    <el-icon><Aim /></el-icon>
                    <span>阈值: {{ alert.threshold.toFixed(2) }}</span>
                  </div>
                  <div class="detail-item">
                    <el-icon><Clock /></el-icon>
                    <span>{{ formatTime(alert.timestamp) }}</span>
                  </div>
                </div>
              </div>

              <div class="alert-actions">
                <el-button
                  v-if="!alert.acknowledged"
                  type="primary"
                  size="small"
                  :icon="Check"
                  @click="acknowledgeAlert(alert.alert_id)"
                >
                  确认
                </el-button>
                <el-button
                  type="success"
                  size="small"
                  :icon="CircleCheck"
                  @click="resolveAlert(alert.alert_id)"
                >
                  解决
                </el-button>
              </div>
            </div>
          </transition-group>
        </div>
      </div>
    </el-card>

    <el-card class="history-card" style="margin-top: 16px;">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span class="title">告警历史查询</span>
            <el-badge :value="alertHistory.length" :hidden="alertHistory.length === 0" type="primary">
              <el-icon><Clock /></el-icon>
            </el-badge>
          </div>
          <div class="header-actions">
            <el-select v-model="historySeverityFilter" placeholder="级别筛选" size="small" clearable style="width: 120px">
              <el-option label="紧急" value="emergency" />
              <el-option label="严重" value="critical" />
              <el-option label="错误" value="error" />
              <el-option label="警告" value="warning" />
              <el-option label="信息" value="info" />
            </el-select>
            <el-button size="small" :icon="Refresh" @click="fetchAlertHistory">刷新</el-button>
          </div>
        </div>
      </template>

      <el-table :data="filteredHistory" stripe size="small" max-height="300" v-loading="historyLoading">
        <el-table-column prop="alert_id" label="ID" width="140" show-overflow-tooltip>
          <template #default="{ row }"><code style="font-size:11px">{{ row.alert_id }}</code></template>
        </el-table-column>
        <el-table-column prop="severity" label="级别" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="getSeverityType(row.severity)" size="small" effect="dark">{{ getSeverityLabel(row.severity) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="metric_type" label="指标类型" width="110" />
        <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
        <el-table-column prop="current_value" label="当前值" width="85" align="right">
          <template #default="{ row }">{{ row.current_value?.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="timestamp" label="时间" width="155">
          <template #default="{ row }">{{ formatTime(row.timestamp) }}</template>
        </el-table-column>
        <el-table-column prop="acknowledged" label="状态" width="75" align="center">
          <template #default="{ row }">
            <el-tag :type="row.resolved ? 'success' : row.acknowledged ? 'warning' : 'danger'" size="small">
              {{ row.resolved ? '已解决' : row.acknowledged ? '已确认' : '待处理' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="filteredHistory.length === 0 && !historyLoading" style="padding: 20px; text-align: center; color: #909399;">暂无历史记录</div>
    </el-card>

    <el-dialog
      v-model="showRulesDialog"
      title="告警规则配置"
      width="80%"
      :close-on-click-modal="false"
    >
      <div class="rules-content">
        <div class="rules-header">
          <el-button type="primary" :icon="Plus" @click="createNewRule">
            新建规则
          </el-button>
        </div>

        <el-table :data="alertRules" stripe>
          <el-table-column prop="name" label="规则名称" width="180" />
          <el-table-column prop="metric_type" label="指标类型" width="120">
            <template #default="{ row }">
              {{ getMetricTypeLabel(row.metric_type) }}
            </template>
          </el-table-column>
          <el-table-column prop="condition" label="条件" width="150" />
          <el-table-column prop="threshold" label="阈值" width="100" />
          <el-table-column prop="severity" label="严重程度" width="100">
            <template #default="{ row }">
              <el-tag :type="getSeverityType(row.severity)" size="small">
                {{ getSeverityLabel(row.severity) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="cooldown_minutes" label="冷却时间(分钟)" width="120" />
          <el-table-column prop="enabled" label="状态" width="80">
            <template #default="{ row }">
              <el-switch v-model="row.enabled" @change="updateRule(row)" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click="editRule(row)">
                编辑
              </el-button>
              <el-button type="danger" link size="small" @click="deleteRule(row.rule_id)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>

    <el-dialog
      v-model="showEditRuleDialog"
      :title="editingRule ? '编辑规则' : '新建规则'"
      width="500px"
    >
      <el-form :model="ruleForm" label-width="120px">
        <el-form-item label="规则名称">
          <el-input v-model="ruleForm.name" placeholder="请输入规则名称" />
        </el-form-item>
        <el-form-item label="指标类型">
          <el-select v-model="ruleForm.metric_type" placeholder="请选择指标类型">
            <el-option label="性能" value="performance" />
            <el-option label="错误率" value="error_rate" />
            <el-option label="代码质量" value="code_quality" />
            <el-option label="测试覆盖率" value="test_coverage" />
          </el-select>
        </el-form-item>
        <el-form-item label="条件">
          <el-select v-model="ruleForm.condition" placeholder="请选择条件">
            <el-option label="大于阈值" value="> threshold" />
            <el-option label="小于阈值" value="< threshold" />
            <el-option label="等于阈值" value="== threshold" />
          </el-select>
        </el-form-item>
        <el-form-item label="阈值">
          <el-input-number v-model="ruleForm.threshold" :precision="2" :step="0.1" />
        </el-form-item>
        <el-form-item label="严重程度">
          <el-select v-model="ruleForm.severity" placeholder="请选择严重程度">
            <el-option label="信息" value="info" />
            <el-option label="警告" value="warning" />
            <el-option label="错误" value="error" />
            <el-option label="严重" value="critical" />
          </el-select>
        </el-form-item>
        <el-form-item label="冷却时间">
          <el-input-number v-model="ruleForm.cooldown_minutes" :min="1" :max="1440" />
          <span style="margin-left: 10px; color: #909399;">分钟</span>
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="ruleForm.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditRuleDialog = false">取消</el-button>
        <el-button type="primary" @click="saveRule">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Bell,
  Setting,
  Check,
  CircleCheck,
  CircleClose,
  Warning,
  InfoFilled,
  DataLine,
  Position,
  Aim,
  Clock,
  Plus,
  Refresh
} from '@element-plus/icons-vue'
import api from '@/api'

interface QualityAlert {
  alert_id: string
  metric_type: string
  severity: 'info' | 'warning' | 'error' | 'critical' | 'emergency'
  title: string
  message: string
  current_value: number
  threshold: number
  source: string
  timestamp: string
  acknowledged: boolean
  resolved: boolean
}

interface AlertRule {
  rule_id: string
  name: string
  metric_type: string
  condition: string
  threshold: number
  severity: 'info' | 'warning' | 'error' | 'critical'
  enabled: boolean
  cooldown_minutes: number
}

const loading = ref(false)
const alerts = ref<QualityAlert[]>([])
const alertRules = ref<AlertRule[]>([])
const filterSeverity = ref('')
const filterMetricType = ref('')
const showAcknowledged = ref(false)
const showRulesDialog = ref(false)
const showEditRuleDialog = ref(false)
const historySeverityFilter = ref('')
const historyLoading = ref(false)
const alertHistory = ref<QualityAlert[]>([])

const filteredHistory = computed(() => {
  if (!historySeverityFilter.value) return alertHistory.value
  return alertHistory.value.filter(a => a.severity === historySeverityFilter.value)
})
const editingRule = ref<AlertRule | null>(null)

const ruleForm = ref<Partial<AlertRule>>({
  name: '',
  metric_type: 'performance',
  condition: '> threshold',
  threshold: 0,
  severity: 'warning',
  enabled: true,
  cooldown_minutes: 5
})

let refreshTimer: ReturnType<typeof setInterval> | null = null

const activeAlertsCount = computed(() => {
  return alerts.value.filter(a => !a.acknowledged).length
})

const filteredAlerts = computed(() => {
  let result = alerts.value

  if (filterSeverity.value) {
    result = result.filter(a => a.severity === filterSeverity.value)
  }

  if (filterMetricType.value) {
    result = result.filter(a => a.metric_type === filterMetricType.value)
  }

  if (!showAcknowledged.value) {
    result = result.filter(a => !a.acknowledged)
  }

  return result
})

const getAlertIcon = (severity: string) => {
  const icons: Record<string, any> = {
    info: InfoFilled, warning: Warning, error: CircleClose,
    critical: CircleClose, emergency: Warning
  }
  return icons[severity] || Warning
}

const getSeverityType = (severity: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    info: 'info', warning: 'warning', error: 'danger', critical: 'danger', emergency: 'danger'
  }
  return types[severity] || 'info'
}

const getSeverityLabel = (severity: string): string => {
  const labels: Record<string, string> = {
    info: '信息', warning: '警告', error: '错误', critical: '严重', emergency: '紧急'
  }
  return labels[severity] || severity
}

const getMetricTypeLabel = (metricType: string): string => {
  const labels: Record<string, string> = {
    performance: '性能',
    error_rate: '错误率',
    code_quality: '代码质量',
    test_coverage: '测试覆盖率'
  }
  return labels[metricType] || metricType
}

const formatTime = (time: string | undefined): string => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const fetchAlerts = async () => {
  loading.value = true
  try {
    const response = await api.get('/quality/alerts')
    alerts.value = response || []
  } catch (error) {
    console.error('Failed to fetch alerts:', error)
  } finally {
    loading.value = false
  }
}

const fetchRules = async () => {
  try {
    const response = await api.get('/quality/alerts/rules')
    alertRules.value = response || []
  } catch (error) {
    console.error('Failed to fetch rules:', error)
  }
}

const acknowledgeAlert = async (alertId: string) => {
  try {
    await api.post(`/quality/alerts/${alertId}/acknowledge`)
    ElMessage.success('告警已确认')
    await fetchAlerts()
  } catch (error) {
    console.error('Failed to acknowledge alert:', error)
    ElMessage.error('确认失败')
  }
}

const resolveAlert = async (alertId: string) => {
  try {
    await api.post(`/quality/alerts/${alertId}/resolve`)
    ElMessage.success('告警已解决')
    await fetchAlerts()
  } catch (error) {
    console.error('Failed to resolve alert:', error)
    ElMessage.error('解决失败')
  }
}

const acknowledgeAllAlerts = async () => {
  try {
    const unacknowledged = alerts.value.filter(a => !a.acknowledged)
    await Promise.all(
      unacknowledged.map(a => api.post(`/quality/alerts/${a.alert_id}/acknowledge`))
    )
    ElMessage.success('所有告警已确认')
    await fetchAlerts()
  } catch (error) {
    console.error('Failed to acknowledge all alerts:', error)
    ElMessage.error('批量确认失败')
  }
}

const triggerQualityCheck = async () => {
  try {
    await api.post('/quality/check')
    ElMessage.success('质量检查已触发')
    setTimeout(fetchAlerts, 2000)
  } catch (error) {
    console.error('Failed to trigger quality check:', error)
    ElMessage.error('触发失败')
  }
}

const filterAlerts = () => {
}

const createNewRule = () => {
  editingRule.value = null
  ruleForm.value = {
    name: '',
    metric_type: 'performance',
    condition: '> threshold',
    threshold: 0,
    severity: 'warning',
    enabled: true,
    cooldown_minutes: 5
  }
  showEditRuleDialog.value = true
}

const editRule = (rule: AlertRule) => {
  editingRule.value = rule
  ruleForm.value = { ...rule }
  showEditRuleDialog.value = true
}

const saveRule = async () => {
  try {
    if (editingRule.value) {
      await api.put(`/quality/alerts/rules/${editingRule.value.rule_id}`, ruleForm.value)
      ElMessage.success('规则已更新')
    } else {
      await api.post('/quality/alerts/rules', {
        ...ruleForm.value,
        rule_id: `rule_${Date.now()}`
      })
      ElMessage.success('规则已创建')
    }
    showEditRuleDialog.value = false
    await fetchRules()
  } catch (error) {
    console.error('Failed to save rule:', error)
    ElMessage.error('保存失败')
  }
}

const deleteRule = async (ruleId: string) => {
  try {
    await ElMessageBox.confirm('确定要删除此规则吗？', '确认删除', {
      type: 'warning'
    })
    await api.delete(`/quality/alerts/rules/${ruleId}`)
    ElMessage.success('规则已删除')
    await fetchRules()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete rule:', error)
      ElMessage.error('删除失败')
    }
  }
}

const updateRule = async (rule: AlertRule) => {
  try {
    await api.put(`/quality/alerts/rules/${rule.rule_id}`, rule)
    ElMessage.success('规则已更新')
  } catch (error) {
    console.error('Failed to update rule:', error)
    ElMessage.error('更新失败')
  }
}

const startAutoRefresh = () => {
  if (!refreshTimer) {
    refreshTimer = setInterval(fetchAlerts, 30000)
  }
}

async function fetchAlertHistory() {
  historyLoading.value = true
  try {
    const response = await api.get('/quality/alerts?limit=20')
    const data: QualityAlert[] = response || []
    alertHistory.value = data.map((a, i) => ({
      ...a,
      severity: i === 0 ? 'emergency' : i === 1 ? 'critical' : a.severity
    }))
  } catch (error) {
    console.error('Failed to fetch alert history:', error)
  } finally {
    historyLoading.value = false
  }
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

onMounted(async () => {
  await fetchAlerts()
  await fetchRules()
  await fetchAlertHistory()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.quality-alerts {
  width: 100%;
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

.title {
  font-size: 16px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.alerts-filter {
  padding: 10px 0;
}

.alerts-list {
  min-height: 300px;
}

.empty-alerts {
  padding: 40px 0;
}

.alert-list-enter-active,
.alert-list-leave-active {
  transition: all 0.5s ease;
}

.alert-list-enter-from,
.alert-list-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

.alert-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 15px;
  margin-bottom: 12px;
  border-radius: 8px;
  background: #f5f7fa;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.alert-item.alert-info {
  background: #f4f4f5;
  border-left: 4px solid #909399;
}

.alert-item.alert-warning {
  background: #fdf6ec;
  border-left: 4px solid #e6a23c;
}

.alert-item.alert-error {
  background: #fef0f0;
  border-left: 4px solid #f56c6c;
}

.alert-item.alert-critical {
  background: #fef0f0;
  border-left: 4px solid #f56c6c;
  animation: pulse 2s infinite;
}

.alert-item.alert-emergency {
  background: linear-gradient(135deg, #fef0f0, #fde2e2);
  border-left: 4px solid #cf1322;
  animation: emergency-pulse 1s infinite;
  box-shadow: 0 0 12px rgba(207, 19, 34, 0.3);
}

.alert-item.alert-acknowledged {
  opacity: 0.6;
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(245, 108, 108, 0.4);
  }
  50% {
    box-shadow: 0 0 0 10px rgba(245, 108, 108, 0);
  }
}

.alert-indicator {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
}

.indicator-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  position: absolute;
  left: -2px;
  top: 50%;
  transform: translateY(-50%);
}

.indicator-dot.severity-info { background: #909399; }
.indicator-dot.severity-warning { background: #e6a23c; }
.indicator-dot.severity-error { background: #f56c6c; }
.indicator-dot.severity-critical { 
  background: #f56c6c; 
  animation: blink 1s infinite; 
}
.indicator-dot.severity-emergency { 
  background: #cf1322; 
  animation: emergency-blink 0.5s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

@keyframes emergency-pulse {
  0%, 100% { box-shadow: 0 0 12px rgba(207, 19, 34, 0.3); }
  50% { box-shadow: 0 0 24px rgba(207, 19, 34, 0.6); }
}

@keyframes emergency-blink {
  0%, 100% { opacity: 1; background: #cf1322; }
  50% { opacity: 0.4; background: #ff4d4f; }
}

.alert-icon {
  font-size: 24px;
  padding-top: 5px;
}

.alert-item.alert-info .alert-icon { color: #909399; }
.alert-item.alert-warning .alert-icon { color: #e6a23c; }
.alert-item.alert-error .alert-icon { color: #f56c6c; }
.alert-item.alert-critical .alert-icon { color: #f56c6c; }

.alert-content {
  flex: 1;
  min-width: 0;
}

.alert-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.alert-title {
  font-weight: 600;
  font-size: 15px;
  color: #303133;
}

.alert-message {
  font-size: 13px;
  color: #606266;
  margin-bottom: 10px;
  line-height: 1.5;
}

.alert-details {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: #909399;
}

.alert-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rules-content {
  padding: 20px 0;
}

.rules-header {
  margin-bottom: 15px;
}
</style>
