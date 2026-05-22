<template>
  <div class="knowledge-base-visualization">
    <el-card class="visualization-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span class="title">知识库可视化</span>
            <el-tag type="primary" effect="dark" size="small">
              {{ totalKnowledge }} 条知识
            </el-tag>
          </div>
          <div class="header-actions">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索知识..."
              prefix-icon="Search"
              clearable
              style="width: 250px"
              @input="handleSearch"
            />
            <el-button type="primary" @click="refreshData">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <div class="visualization-content">
        <div class="stats-section">
          <el-row :gutter="16">
            <el-col :span="6" v-for="stat in statistics" :key="stat.key">
              <div class="stat-card" :class="stat.class">
                <div class="stat-icon">
                  <el-icon :size="28">
                    <component :is="stat.icon" />
                  </el-icon>
                </div>
                <div class="stat-content">
                  <div class="stat-value">{{ stat.value }}</div>
                  <div class="stat-label">{{ stat.label }}</div>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>

        <el-divider />

        <div class="main-content">
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="category-section">
                <div class="section-title">知识分类</div>
                <el-input
                  v-model="categoryFilter"
                  placeholder="过滤分类..."
                  prefix-icon="Filter"
                  clearable
                  size="small"
                  style="margin-bottom: 12px"
                />
                <el-tree
                  ref="treeRef"
                  :data="filteredCategories"
                  :props="treeProps"
                  node-key="id"
                  highlight-current
                  :expand-on-click-node="false"
                  :default-expand-all="true"
                  @node-click="handleCategoryClick"
                >
                  <template #default="{ node, data }">
                    <div class="tree-node">
                      <span class="node-label">
                        <el-icon v-if="data.icon" style="margin-right: 5px">
                          <component :is="data.icon" />
                        </el-icon>
                        {{ node.label }}
                      </span>
                      <el-badge :value="data.count || 0" :max="99" class="node-badge" />
                    </div>
                  </template>
                </el-tree>
              </div>
            </el-col>

            <el-col :span="16">
              <div class="knowledge-list-section">
                <div class="section-header">
                  <span class="section-title">知识列表</span>
                  <el-select v-model="sortBy" size="small" style="width: 150px" @change="handleSort">
                    <el-option label="按更新时间" value="updated_at" />
                    <el-option label="按创建时间" value="created_at" />
                    <el-option label="按使用次数" value="usage_count" />
                    <el-option label="按评分" value="rating" />
                  </el-select>
                </div>
                <div class="knowledge-list" v-loading="loading">
                  <div
                    v-for="item in knowledgeList"
                    :key="item.id"
                    class="knowledge-item"
                    @click="showKnowledgeDetail(item)"
                  >
                    <div class="knowledge-header">
                      <div class="knowledge-title">
                        <el-icon class="knowledge-icon">
                          <component :is="getKnowledgeIcon(item.type)" />
                        </el-icon>
                        <span>{{ item.title }}</span>
                      </div>
                      <el-tag :type="getKnowledgeTypeTag(item.type)" size="small">
                        {{ getKnowledgeTypeLabel(item.type) }}
                      </el-tag>
                    </div>
                    <div class="knowledge-content">{{ item.summary || item.content?.slice(0, 100) }}</div>
                    <div class="knowledge-footer">
                      <div class="knowledge-meta">
                        <span class="meta-item">
                          <el-icon><Clock /></el-icon>
                          {{ formatTime(item.updated_at) }}
                        </span>
                        <span class="meta-item">
                          <el-icon><View /></el-icon>
                          {{ item.usage_count || 0 }} 次使用
                        </span>
                        <span class="meta-item">
                          <el-icon><Star /></el-icon>
                          {{ item.rating?.toFixed(1) || '-' }}
                        </span>
                      </div>
                      <div class="knowledge-tags">
                        <el-tag
                          v-for="tag in item.tags?.slice(0, 3)"
                          :key="tag"
                          size="small"
                          type="info"
                          effect="plain"
                        >
                          {{ tag }}
                        </el-tag>
                      </div>
                    </div>
                  </div>
                  <el-empty v-if="knowledgeList.length === 0 && !loading" description="暂无知识数据" />
                </div>
                <div class="pagination-section" v-if="totalKnowledge > pageSize">
                  <el-pagination
                    v-model:current-page="currentPage"
                    :page-size="pageSize"
                    :total="totalKnowledge"
                    layout="prev, pager, next"
                    @current-change="handlePageChange"
                  />
                </div>
              </div>
            </el-col>
          </el-row>
        </div>

        <div v-if="notifications.length > 0" class="notifications-section">
          <el-divider />
          <div class="section-title">知识更新通知</div>
          <div class="notifications-list">
            <div
              v-for="notification in notifications"
              :key="notification.id"
              class="notification-item"
              :class="`notification-${notification.type}`"
            >
              <div class="notification-icon">
                <el-icon>
                  <component :is="getNotificationIcon(notification.type)" />
                </el-icon>
              </div>
              <div class="notification-content">
                <div class="notification-title">{{ notification.title }}</div>
                <div class="notification-desc">{{ notification.description }}</div>
              </div>
              <div class="notification-time">{{ formatTime(notification.created_at) }}</div>
              <el-button
                type="primary"
                link
                size="small"
                @click="dismissNotification(notification.id)"
              >
                忽略
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <el-drawer
      v-model="detailDrawerVisible"
      :title="selectedKnowledge?.title"
      size="50%"
      direction="rtl"
    >
      <div class="knowledge-detail" v-if="selectedKnowledge">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="类型">
            <el-tag :type="getKnowledgeTypeTag(selectedKnowledge.type)">
              {{ getKnowledgeTypeLabel(selectedKnowledge.type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="分类">{{ selectedKnowledge.category }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatTime(selectedKnowledge.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ formatTime(selectedKnowledge.updated_at) }}</el-descriptions-item>
          <el-descriptions-item label="使用次数">{{ selectedKnowledge.usage_count || 0 }}</el-descriptions-item>
          <el-descriptions-item label="评分">{{ selectedKnowledge.rating?.toFixed(1) || '-' }}</el-descriptions-item>
        </el-descriptions>
        <el-divider />
        <div class="detail-section">
          <div class="detail-title">内容</div>
          <div class="detail-content">{{ selectedKnowledge.content }}</div>
        </div>
        <div class="detail-section" v-if="selectedKnowledge.tags?.length">
          <div class="detail-title">标签</div>
          <div class="detail-tags">
            <el-tag v-for="tag in selectedKnowledge.tags" :key="tag" style="margin-right: 8px">
              {{ tag }}
            </el-tag>
          </div>
        </div>
        <div class="detail-section" v-if="selectedKnowledge.references?.length">
          <div class="detail-title">参考链接</div>
          <el-link
            v-for="ref in selectedKnowledge.references"
            :key="ref"
            :href="ref"
            target="_blank"
            type="primary"
            style="margin-right: 12px"
          >
            {{ ref }}
          </el-link>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Refresh,
  Search,
  Filter,
  Clock,
  View,
  Star,
  Document,
  Folder,
  Collection,
  ChatDotRound,
  Cpu,
  Connection,
  CircleCheck,
  Warning,
  Bell,
  Plus,
  Edit
} from '@element-plus/icons-vue'
import { useWebSocket, ConnectionState } from '@/composables/useWebSocket'
import api from '@/api'

interface KnowledgeItem {
  id: number
  title: string
  type: string
  category: string
  content: string
  summary?: string
  tags?: string[]
  references?: string[]
  usage_count?: number
  rating?: number
  created_at: string
  updated_at: string
}

interface CategoryNode {
  id: string
  label: string
  icon?: any
  count?: number
  children?: CategoryNode[]
}

interface KnowledgeNotification {
  id: number
  type: 'new' | 'update' | 'delete' | 'warning'
  title: string
  description: string
  created_at: string
}

interface Props {
  autoRefresh?: boolean
  refreshInterval?: number
}

const props = withDefaults(defineProps<Props>(), {
  autoRefresh: true,
  refreshInterval: 60000
})

const emit = defineEmits<{
  (e: 'knowledge-selected', knowledge: KnowledgeItem): void
  (e: 'category-selected', category: string): void
  (e: 'error', error: Error): void
}>()

const loading = ref(false)
const searchKeyword = ref('')
const categoryFilter = ref('')
const sortBy = ref('updated_at')
const currentPage = ref(1)
const pageSize = 10
const totalKnowledge = ref(0)
const knowledgeList = ref<KnowledgeItem[]>([])
const categories = ref<CategoryNode[]>([])
const notifications = ref<KnowledgeNotification[]>([])
const selectedKnowledge = ref<KnowledgeItem | null>(null)
const detailDrawerVisible = ref(false)
const treeRef = ref()

let refreshTimer: ReturnType<typeof setInterval> | null = null

const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
const wsHost = window.location.host
const wsUrl = `${wsProtocol}//${wsHost}/api/knowledge-base/ws`

const {
  connectionState,
  isConnected,
  connect: wsConnect,
  disconnect: wsDisconnect
} = useWebSocket({
  url: wsUrl,
  heartbeatInterval: 30000,
  onMessage: handleWebSocketMessage
})

const statistics = computed(() => [
  {
    key: 'total',
    label: '总知识数',
    value: totalKnowledge.value,
    icon: Collection,
    class: 'stat-primary'
  },
  {
    key: 'categories',
    label: '分类数',
    value: categories.value.length,
    icon: Folder,
    class: 'stat-success'
  },
  {
    key: 'usage',
    label: '总使用次数',
    value: knowledgeList.value.reduce((sum, k) => sum + (k.usage_count || 0), 0),
    icon: View,
    class: 'stat-warning'
  },
  {
    key: 'avg_rating',
    label: '平均评分',
    value: calculateAverageRating(),
    icon: Star,
    class: 'stat-info'
  }
])

const filteredCategories = computed(() => {
  if (!categoryFilter.value) return categories.value
  return filterTree(categories.value, categoryFilter.value.toLowerCase())
})

const treeProps = {
  children: 'children',
  label: 'label'
}

const calculateAverageRating = (): string => {
  const ratedItems = knowledgeList.value.filter(k => k.rating !== undefined)
  if (ratedItems.length === 0) return '-'
  const avg = ratedItems.reduce((sum, k) => sum + (k.rating || 0), 0) / ratedItems.length
  return avg.toFixed(1)
}

const filterTree = (nodes: CategoryNode[], keyword: string): CategoryNode[] => {
  return nodes.reduce((acc: CategoryNode[], node) => {
    if (node.label.toLowerCase().includes(keyword)) {
      acc.push(node)
    } else if (node.children) {
      const filteredChildren = filterTree(node.children, keyword)
      if (filteredChildren.length > 0) {
        acc.push({ ...node, children: filteredChildren })
      }
    }
    return acc
  }, [])
}

const formatTime = (time: string): string => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const getKnowledgeIcon = (type: string) => {
  const icons: Record<string, any> = {
    document: Document,
    code: Cpu,
    workflow: Connection,
    faq: ChatDotRound,
    default: Document
  }
  return icons[type] || icons.default
}

const getKnowledgeTypeTag = (type: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const tags: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    document: 'primary',
    code: 'success',
    workflow: 'warning',
    faq: 'info'
  }
  return tags[type] || 'info'
}

const getKnowledgeTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    document: '文档',
    code: '代码',
    workflow: '工作流',
    faq: 'FAQ'
  }
  return labels[type] || type
}

const getNotificationIcon = (type: string) => {
  const icons: Record<string, any> = {
    new: Plus,
    update: Edit,
    delete: Warning,
    warning: Bell
  }
  return icons[type] || Bell
}

const fetchKnowledgeList = async () => {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: currentPage.value,
      page_size: pageSize,
      sort_by: sortBy.value
    }
    if (searchKeyword.value) {
      params.keyword = searchKeyword.value
    }
    const response = await api.get('/knowledge-base/list', { params })
    knowledgeList.value = response.items || []
    totalKnowledge.value = response.total || 0
  } catch (error) {
    console.error('Failed to fetch knowledge list:', error)
    emit('error', error as Error)
  } finally {
    loading.value = false
  }
}

const fetchCategories = async () => {
  try {
    const response = await api.get('/knowledge-base/categories')
    categories.value = response || []
  } catch (error) {
    console.error('Failed to fetch categories:', error)
  }
}

const fetchNotifications = async () => {
  try {
    const response = await api.get('/knowledge-base/notifications')
    notifications.value = response || []
  } catch (error) {
    console.error('Failed to fetch notifications:', error)
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchKnowledgeList()
}

const searchKnowledge = async () => {
  if (!searchKeyword.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }
  
  loading.value = true
  try {
    const response = await api.post('/evolution-knowledge/search', null, {
      params: {
        query: searchKeyword.value,
        category: selectedCategory.value,
        skip: 0,
        limit: 20
      }
    })
    
    knowledgeList.value = (response as any).results || []
    totalKnowledge.value = (response as any).total_results || 0
    ElMessage.success(`找到 ${(response as any).total_results} 个结果`)
  } catch (error) {
    console.error('搜索失败:', error)
    ElMessage.error('搜索失败')
  } finally {
    loading.value = false
  }
}

const loadAnalytics = async () => {
  try {
    const response = await api.get('/evolution-knowledge/analytics', {
      params: {
        period: '7d'
      }
    })
    
    analyticsData.value = response
  } catch (error) {
    console.error('加载分析数据失败:', error)
    ElMessage.error('加载分析数据失败')
  }
}

const importKnowledge = async () => {
  if (!importConfig.value.sourceData) {
    ElMessage.warning('请输入来源数据')
    return
  }
  
  try {
    const response = await api.post('/evolution-knowledge/import', importConfig.value)
    
    ElMessage.success('导入任务已创建')
    importDialogVisible.value = false
    
    setTimeout(() => {
      fetchKnowledgeList()
    }, 2000)
  } catch (error) {
    console.error('导入失败:', error)
    ElMessage.error('导入失败')
  }
}

const exportKnowledge = async () => {
  try {
    const response = await api.post('/evolution-knowledge/export', {
      export_type: exportConfig.value.exportType,
      category: selectedCategory.value,
      include_metadata: exportConfig.value.includeMetadata
    })
    
    ElMessage.success('导出任务已创建')
    
    if ((response as any).download_url) {
      window.open((response as any).download_url, '_blank')
    }
    
    exportDialogVisible.value = false
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

const rateKnowledge = async (knowledgeId: string, rating: number, feedback?: string) => {
  try {
    await api.post(`/evolution-knowledge/knowledge/${knowledgeId}/rate`, null, {
      params: {
        rating: rating,
        feedback: feedback
      }
    })
    
    ElMessage.success('评分已提交')
    fetchKnowledgeList()
  } catch (error) {
    console.error('评分失败:', error)
    ElMessage.error('评分失败')
  }
}

const relateKnowledge = async (knowledgeId: string, relatedIds: string[], relationType: string) => {
  try {
    await api.post(`/evolution-knowledge/knowledge/${knowledgeId}/relate`, null, {
      params: {
        related_ids: relatedIds,
        relation_type: relationType
      }
    })
    
    ElMessage.success('关联关系已建立')
  } catch (error) {
    console.error('关联失败:', error)
    ElMessage.error('关联失败')
  }
}

const showImportDialog = () => {
  importDialogVisible.value = true
}

const showExportDialog = () => {
  exportDialogVisible.value = true
}

const showAnalyticsDialog = () => {
  analyticsDialogVisible.value = true
  loadAnalytics()
}

const getTrendIcon = (trend: string): string => {
  const icons: Record<string, string> = {
    'up': '↑',
    'stable': '→',
    'down': '↓'
  }
  return icons[trend] || '→'
}

const getTrendColor = (trend: string): string => {
  const colors: Record<string, string> = {
    'up': '#67C23A',
    'stable': '#909399',
    'down': '#F56C6C'
  }
  return colors[trend] || '#909399'
}

const handleSort = () => {
  fetchKnowledgeList()
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchKnowledgeList()
}

const handleCategoryClick = (data: CategoryNode) => {
  emit('category-selected', data.id)
  searchKeyword.value = ''
  fetchKnowledgeByCategory(data.id)
}

const fetchKnowledgeByCategory = async (categoryId: string) => {
  loading.value = true
  try {
    const response = await api.get(`/knowledge-base/category/${categoryId}`)
    knowledgeList.value = response.items || []
    totalKnowledge.value = response.total || 0
  } catch (error) {
    console.error('Failed to fetch knowledge by category:', error)
    emit('error', error as Error)
  } finally {
    loading.value = false
  }
}

const showKnowledgeDetail = (item: KnowledgeItem) => {
  selectedKnowledge.value = item
  detailDrawerVisible.value = true
  emit('knowledge-selected', item)
}

const dismissNotification = async (id: number) => {
  try {
    await api.post(`/knowledge-base/notifications/${id}/dismiss`)
    notifications.value = notifications.value.filter(n => n.id !== id)
    ElMessage.success('通知已忽略')
  } catch (error) {
    console.error('Failed to dismiss notification:', error)
  }
}

const refreshData = () => {
  fetchKnowledgeList()
  fetchCategories()
  fetchNotifications()
}

const handleWebSocketMessage = (data: any) => {
  switch (data.type) {
    case 'knowledge_created':
      notifications.value.unshift({
        id: Date.now(),
        type: 'new',
        title: '新知识添加',
        description: `知识 "${data.data.title}" 已添加到知识库`,
        created_at: new Date().toISOString()
      })
      totalKnowledge.value++
      break
    case 'knowledge_updated':
      notifications.value.unshift({
        id: Date.now(),
        type: 'update',
        title: '知识更新',
        description: `知识 "${data.data.title}" 已更新`,
        created_at: new Date().toISOString()
      })
      const index = knowledgeList.value.findIndex(k => k.id === data.data.id)
      if (index >= 0) {
        knowledgeList.value[index] = data.data
      }
      break
    case 'knowledge_deleted':
      notifications.value.unshift({
        id: Date.now(),
        type: 'delete',
        title: '知识删除',
        description: `知识 "${data.data.title}" 已从知识库删除`,
        created_at: new Date().toISOString()
      })
      knowledgeList.value = knowledgeList.value.filter(k => k.id !== data.data.id)
      totalKnowledge.value--
      break
  }
}

const startAutoRefresh = () => {
  if (props.autoRefresh && !refreshTimer && !isConnected.value) {
    refreshTimer = setInterval(refreshData, props.refreshInterval)
  }
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

onMounted(() => {
  refreshData()
  wsConnect()
  startAutoRefresh()
})

onUnmounted(() => {
  wsDisconnect()
  stopAutoRefresh()
})
</script>

<style scoped>
.knowledge-base-visualization {
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
  font-size: 18px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.visualization-content {
  padding: 10px 0;
}

.stats-section {
  padding: 10px 0;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.stat-card.stat-primary {
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: #fff;
}

.stat-card.stat-success {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
  color: #fff;
}

.stat-card.stat-warning {
  background: linear-gradient(135deg, #e6a23c 0%, #ebb563 100%);
  color: #fff;
}

.stat-card.stat-info {
  background: linear-gradient(135deg, #909399 0%, #c0c4cc 100%);
  color: #fff;
}

.stat-icon {
  opacity: 0.9;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
}

.stat-label {
  font-size: 13px;
  opacity: 0.9;
}

.section-title {
  font-weight: 500;
  margin-bottom: 15px;
  color: #303133;
  font-size: 15px;
}

.category-section {
  background: #fafafa;
  border-radius: 8px;
  padding: 15px;
  max-height: 500px;
  overflow-y: auto;
}

.tree-node {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding-right: 10px;
}

.node-label {
  display: flex;
  align-items: center;
}

.node-badge {
  margin-left: 10px;
}

.knowledge-list-section {
  background: #fff;
  border-radius: 8px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.knowledge-list {
  max-height: 450px;
  overflow-y: auto;
}

.knowledge-item {
  padding: 15px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.knowledge-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.1);
}

.knowledge-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.knowledge-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  font-size: 15px;
}

.knowledge-icon {
  color: #409eff;
}

.knowledge-content {
  font-size: 13px;
  color: #606266;
  margin-bottom: 10px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.knowledge-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.knowledge-meta {
  display: flex;
  gap: 15px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
}

.knowledge-tags {
  display: flex;
  gap: 5px;
}

.pagination-section {
  display: flex;
  justify-content: center;
  margin-top: 15px;
}

.notifications-section {
  margin-top: 15px;
}

.notifications-list {
  max-height: 200px;
  overflow-y: auto;
}

.notification-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 10px;
  background: #f5f7fa;
}

.notification-item.notification-new {
  background: #ecf5ff;
  border-left: 3px solid #409eff;
}

.notification-item.notification-update {
  background: #f0f9eb;
  border-left: 3px solid #67c23a;
}

.notification-item.notification-delete {
  background: #fef0f0;
  border-left: 3px solid #f56c6c;
}

.notification-item.notification-warning {
  background: #fdf6ec;
  border-left: 3px solid #e6a23c;
}

.notification-icon {
  color: #409eff;
}

.notification-content {
  flex: 1;
}

.notification-title {
  font-weight: 500;
  margin-bottom: 4px;
}

.notification-desc {
  font-size: 12px;
  color: #909399;
}

.notification-time {
  font-size: 12px;
  color: #909399;
}

.knowledge-detail {
  padding: 10px;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-title {
  font-weight: 500;
  margin-bottom: 10px;
  color: #303133;
}

.detail-content {
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.detail-tags {
  display: flex;
  flex-wrap: wrap;
}
</style>
