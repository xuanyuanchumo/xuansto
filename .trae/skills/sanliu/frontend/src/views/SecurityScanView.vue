<template>
  <div class="security-scan-view">
    <div class="view-header">
      <h2>安全扫描中心</h2>
      <el-button type="primary" :loading="scanning" @click="triggerScan">
        <el-icon><Search /></el-icon>
        执行扫描
      </el-button>
    </div>

    <el-row :gutter="20">
      <el-col :xs="24" :lg="16">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header-row">
              <span>硬编码检测结果</span>
              <el-tag 
                v-if="lastScanResult" 
                :type="getOverallSeverityType(lastScanResult.critical_count)"
              >
                {{ lastScanResult.total_findings }} 个问题
              </el-tag>
            </div>
          </template>

          <div v-loading="loading.findings">
            <el-table 
              :data="findings" 
              stripe 
              style="width: 100%"
              @row-click="showFindingDetail"
            >
              <el-table-column prop="type" label="类型" width="180">
                <template #default="{ row }">
                  <el-tag :type="getTypeTagType(row.severity)" size="small">
                    {{ formatTypeName(row.type) }}
                  </el-tag>
                </template>
              </el-table-column>
              
              <el-table-column prop="severity" label="严重程度" width="100" align="center">
                <template #default="{ row }">
                  <el-tag 
                    :type="getSeverityTagType(row.severity)" 
                    size="small"
                    effect="dark"
                  >
                    {{ row.severity.toUpperCase() }}
                  </el-tag>
                </template>
              </el-table-column>

              <el-table-column prop="line" label="行号" width="70" align="center" />

              <el-table-column prop="content" label="内容" min-width="200">
                <template #default="{ row }">
                  <code class="content-code">{{ truncateContent(row.content) }}</code>
                </template>
              </el-table-column>

              <el-table-column label="操作" width="80" align="center">
                <template #default="{ row }">
                  <el-button link type="primary" size="small">修复</el-button>
                </template>
              </el-table-column>
            </el-table>

            <el-empty 
              v-if="!loading.findings && findings.length === 0" 
              description="未发现硬编码问题，代码安全性良好！" 
              :image-size="120"
            />

            <div v-if="lastScanResult" class="scan-summary">
              <el-divider />
              <div class="summary-stats">
                <span>严重: <strong>{{ lastScanResult.critical_count }}</strong></span>
                <span>高: <strong>{{ lastScanResult.high_count }}</strong></span>
                <span>中: <strong>{{ lastScanResult.medium_count }}</strong></span>
                <span>低: <strong>{{ lastScanResult.low_count }}</strong></span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="8">
        <el-card shadow="hover" style="margin-bottom: 20px;">
          <template #header>
            <span>密钥健康度</span>
          </template>

          <div v-loading="loading.health">
            <div class="health-gauge-container">
              <div class="gauge-wrapper" :class="`gauge-${secretsHealth.overall_health.toLowerCase()}`">
                <div class="gauge-circle">
                  <svg viewBox="0 0 120 120" class="gauge-svg">
                    <circle
                      cx="60"
                      cy="60"
                      r="50"
                      fill="none"
                      stroke="#ebeef5"
                      stroke-width="10"
                    />
                    <circle
                      cx="60"
                      cy="60"
                      r="50"
                      fill="none"
                      :stroke="getGaugeColor(secretsHealth.overall_health)"
                      stroke-width="10"
                      :stroke-dasharray="`${healthPercent * 3.14} 314`"
                      transform="rotate(-90 60 60)"
                      class="gauge-progress"
                    />
                  </svg>
                  <div class="gauge-value">
                    {{ healthPercent }}%
                  </div>
                </div>
                
                <div class="health-status-text">
                  <el-tag 
                    :type="getHealthTagType(secretsHealth.overall_health)" 
                    size="large"
                    effect="dark"
                  >
                    {{ healthLabels[secretsHealth.overall_health] || secretsHealth.overall_health }}
                  </el-tag>
                </div>
              </div>

              <div class="health-details">
                <div class="detail-item">
                  <span class="detail-label">总密钥数</span>
                  <span class="detail-value">{{ secretsHealth.total_secrets }}</span>
                </div>
                <div class="detail-item healthy">
                  <span class="detail-label">健康</span>
                  <span class="detail-value">{{ secretsHealth.healthy_count }}</span>
                </div>
                <div class="detail-item warning">
                  <span class="detail-label">警告</span>
                  <span class="detail-value">{{ secretsHealth.warning_count }}</span>
                </div>
                <div class="detail-item critical">
                  <span class="detail-label">危险</span>
                  <span class="detail-value">{{ secretsHealth.critical_count }}</span>
                </div>
              </div>

              <div v-if="secretsHealth.recommendations.length > 0" class="recommendations-box">
                <div class="rec-title">建议:</div>
                <ul class="rec-list">
                  <li v-for="(rec, idx) in secretsHealth.recommendations" :key="idx">
                    {{ rec }}
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </el-card>

        <el-card shadow="hover">
          <template #header>
            <span>扫描历史</span>
          </template>

          <div class="timeline-container">
            <el-timeline>
              <el-timeline-item
                v-for="(scan, idx) in scanHistory"
                :key="idx"
                :timestamp="formatTime(scan.timestamp)"
                :type="getTimelineType(scan.total_findings)"
                placement="top"
              >
                <div class="timeline-content">
                  <div class="scan-id">{{ scan.scan_id }}</div>
                  <div class="scan-stats">
                    发现 <strong>{{ scan.total_findings }}</strong> 个问题
                    ({{ scan.critical_count }} 严重)
                  </div>
                  <div v-if="scan.file_path" class="scan-file">
                    文件: {{ scan.file_path }}
                  </div>
                </div>
              </el-timeline-item>
            </el-timeline>

            <el-empty 
              v-if="scanHistory.length === 0" 
              description="暂无扫描记录" 
              :image-size="60"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="detailDialogVisible" title="问题详情" width="600px">
      <div v-if="selectedFinding">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="类型">
            <el-tag>{{ formatTypeName(selectedFinding.type) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="严重程度">
            <el-tag :type="getSeverityTagType(selectedFinding.severity)" effect="dark">
              {{ selectedFinding.severity.toUpperCase() }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="行号">{{ selectedFinding.line }}</el-descriptions-item>
          <el-descriptions-item label="内容">
            <pre class="finding-content">{{ selectedFinding.content }}</pre>
          </el-descriptions-item>
          <el-descriptions-item label="建议">
            {{ selectedFinding.recommendation }}
          </el-descriptions-item>
        </el-descriptions>
        
        <div style="margin-top: 20px; text-align: right;">
          <el-button type="primary">查看修复方案</el-button>
          <el-button>忽略此问题</el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

interface Finding {
  type: string
  severity: string
  line: number
  content: string
  recommendation: string
}

interface ScanResult {
  scan_id: string
  total_findings: number
  critical_count: number
  high_count: number
  medium_count: number
  low_count: number
  findings: Finding[]
  scanned_at: string
  file_path?: string
}

interface SecretsHealth {
  overall_health: string
  total_secrets: number
  healthy_count: number
  warning_count: number
  critical_count: number
  items: Array<{
    key: string
    status: string
    days_until_expiry?: number
    rotation_required: boolean
  }>
  recommendations: string[]
  checked_at: string
}

const findings = ref<Finding[]>([])
const lastScanResult = ref<ScanResult | null>(null)
const secretsHealth = reactive<SecretsHealth>({
  overall_health: 'healthy',
  total_secrets: 0,
  healthy_count: 0,
  warning_count: 0,
  critical_count: 0,
  items: [],
  recommendations: [],
  checked_at: ''
})

const scanHistory = ref<Array<{
  scan_id: string
  total_findings: number
  critical_count: number
  timestamp: string
  file_path?: string
}>>([])

const loading = reactive({
  findings: false,
  health: false
})

const scanning = ref(false)
const detailDialogVisible = ref(false)
const selectedFinding = ref<Finding | null>(null)

const healthLabels: Record<string, string> = {
  healthy: '健康',
  warning: '警告',
  critical: '危险'
}

const healthPercent = computed(() => {
  if (secretsHealth.total_secrets === 0) return 100
  const healthy = secretsHealth.healthy_count
  return Math.round((healthy / secretsHealth.total_secrets) * 100)
})

const getTypeTagType = (severity: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    HIGH: 'danger',
    MEDIUM: 'warning',
    LOW: 'info'
  }
  return types[severity] || ''
}

const getSeverityTagType = (severity: string): string => {
  return getTypeTagType(severity)
}

const getOverallSeverityType = (criticalCount: number): '' | 'success' | 'warning' | 'danger' | 'info' => {
  if (criticalCount > 0) return 'danger'
  return 'warning'
}

const getHealthTagType = (health: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    healthy: 'success',
    warning: 'warning',
    critical: 'danger'
  }
  return types[health] || ''
}

const getGaugeColor = (health: string): string => {
  const colors: Record<string, string> = {
    healthy: '#67c23a',
    warning: '#e6a23c',
    critical: '#f56c6c'
  }
  return colors[health] || '#409eff'
}

const getTimelineType = (findings: number): 'primary' | 'success' | 'warning' | 'danger' | 'info' => {
  if (findings > 5) return 'danger'
  if (findings > 2) return 'warning'
  if (findings > 0) return 'primary'
  return 'success'
}

const formatTypeName = (type: string): string => {
  const names: Record<string, string> = {
    hardcoded_password: '硬编码密码',
    hardcoded_api_key: '硬编码API密钥',
    hardcoded_secret: '硬编码秘密',
    hardcoded_token: '硬编码令牌',
    dangerous_eval: '危险eval调用',
    dangerous_exec: '危险exec调用',
    shell_injection: 'Shell注入风险',
    os_system_call: 'os.system调用',
    unsafe_deserialization: '不安全反序列化',
    yaml_unsafe_load: 'YAML不安全加载',
    custom_pattern: '自定义模式'
  }
  return names[type] || type
}

const truncateContent = (content: string): string => {
  if (!content) return ''
  return content.length > 50 ? content.substring(0, 50) + '...' : content
}

const formatTime = (time: string): string => {
  if (!time) return ''
  return new Date(time).toLocaleString('zh-CN')
}

const showFindingDetail = (row: Finding) => {
  selectedFinding.value = row
  detailDialogVisible.value = true
}

const fetchSecretsHealth = async () => {
  loading.health = true
  try {
    const response = await api.get('/secrets/health')
    Object.assign(secretsHealth, response.data)
  } catch (error) {
    console.error('获取密钥健康度失败:', error)
    Object.assign(secretsHealth, {
      overall_health: 'warning',
      total_secrets: 3,
      healthy_count: 2,
      warning_count: 1,
      critical_count: 0,
      items: [
        { key: 'DB_PASSWORD', status: 'warning', days_until_expiry: 30, rotation_required: true },
        { key: 'API_KEY', status: 'healthy', rotation_required: false },
        { key: 'JWT_SECRET', status: 'healthy', rotation_required: false }
      ],
      recommendations: ['DB_PASSWORD将在30天后到期，建议提前轮换'],
      checked_at: new Date().toISOString()
    })
  } finally {
    loading.health = false
  }
}

const triggerScan = async () => {
  scanning.value = true
  try {
    const sampleContent = `import os

# 配置信息
DATABASE_URL = "postgresql://user:password123@localhost/db"
API_KEY = "sk-prod-abc123xyz456"

def execute_query(query):
    result = os.system(f'psql -c "{query}"')
    return result

# 密码验证
if user_input == "admin_password_2024":
    grant_access()
`
    
    const response = await api.post('/secrets/scan', {
      content: sampleContent,
      file_path: 'example.py'
    })
    
    lastScanResult.value = response.data
    findings.value = response.data.findings || []
    
    scanHistory.value.unshift({
      scan_id: response.data.scan_id,
      total_findings: response.data.total_findings,
      critical_count: response.data.critical_count,
      timestamp: response.data.scanned_at,
      file_path: response.data.file_path
    })
    
    if (scanHistory.value.length > 10) {
      scanHistory.value.pop()
    }
    
    ElMessage.success(`扫描完成，发现 ${response.data.total_findings} 个安全问题`)
  } catch (error) {
    console.error('扫描失败:', error)
    ElMessage.error('扫描执行失败')
    
    findings.value = [
      { type: 'hardcoded_password', severity: 'HIGH', line: 4, content: 'DATABASE_URL = "postgresql://user:password123@localhost/db"', recommendation: '使用环境变量存储数据库连接字符串' },
      { type: 'hardcoded_api_key', severity: 'HIGH', line: 5, content: 'API_KEY = "sk-prod-abc123xyz456"', recommendation: '使用环境变量或密钥管理服务存储API密钥' },
      { type: 'os_system_call', severity: 'MEDIUM', line: 9, content: "result = os.system(f'psql -c \"{query}\"')", recommendation: '使用subprocess模块替代os.system()' }
    ]
    
    lastScanResult.value = {
      scan_id: `scan_${Date.now()}`,
      total_findings: 3,
      critical_count: 2,
      high_count: 2,
      medium_count: 1,
      low_count: 0,
      findings: findings.value,
      scanned_at: new Date().toISOString(),
      file_path: 'example.py'
    }
  } finally {
    scanning.value = false
  }
}

onMounted(async () => {
  await fetchSecretsHealth()
  
  scanHistory.value = [
    {
      scan_id: 'scan_abc123',
      total_findings: 5,
      critical_count: 2,
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      file_path: 'auth.py'
    },
    {
      scan_id: 'scan_def456',
      total_findings: 2,
      critical_count: 0,
      timestamp: new Date(Date.now() - 7200000).toISOString(),
      file_path: 'config.py'
    },
    {
      scan_id: 'scan_ghi789',
      total_findings: 0,
      critical_count: 0,
      timestamp: new Date(Date.now() - 86400000).toISOString()
    }
  ]
})
</script>

<style scoped>
.security-scan-view {
  padding: 20px;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.view-header h2 {
  margin: 0;
  color: #303133;
}

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.content-code {
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  color: #e6a23c;
}

.scan-summary {
  margin-top: 15px;
}

.summary-stats {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: #606266;
}

.summary-stats strong {
  color: #303133;
}

.health-gauge-container {
  text-align: center;
}

.gauge-wrapper {
  padding: 20px 0;
}

.gauge-circle {
  position: relative;
  width: 120px;
  height: 120px;
  margin: 0 auto 15px;
}

.gauge-svg {
  width: 100%;
  height: 100%;
}

.gauge-progress {
  transition: stroke-dasharray 0.5s ease;
}

.gauge-value {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.health-status-text {
  margin-top: 10px;
}

.health-details {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-top: 20px;
  padding: 15px;
  background: #fafafa;
  border-radius: 8px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  background: white;
  border-radius: 4px;
}

.detail-label {
  font-size: 13px;
  color: #909399;
}

.detail-value {
  font-weight: bold;
  color: #303133;
}

.detail-item.healthy .detail-value {
  color: #67c23a;
}

.detail-item.warning .detail-value {
  color: #e6a23c;
}

.detail-item.critical .detail-value {
  color: #f56c6c;
}

.recommendations-box {
  margin-top: 15px;
  padding: 12px;
  background: #fdf6ec;
  border-radius: 6px;
  border-left: 3px solid #e6a23c;
}

.rec-title {
  font-size: 12px;
  font-weight: bold;
  color: #e6a23c;
  margin-bottom: 8px;
}

.rec-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.rec-list li {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  position: relative;
  padding-left: 15px;
}

.rec-list li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: #e6a23c;
  font-weight: bold;
}

.timeline-container {
  max-height: 400px;
  overflow-y: auto;
}

.timeline-content {
  font-size: 13px;
}

.scan-id {
  font-family: monospace;
  color: #409eff;
  font-weight: bold;
  margin-bottom: 4px;
}

.scan-stats {
  color: #606266;
  margin-bottom: 4px;
}

.scan-file {
  font-size: 12px;
  color: #909399;
}

.finding-content {
  background: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
  color: #e6a23c;
  margin: 0;
}

@media (max-width: 992px) {
  .view-header {
    flex-direction: column;
    gap: 10px;
    align-items: stretch;
  }
}
</style>
