<template>
  <div class="knowledge-graph-view">
    <el-card class="graph-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon :size="20"><Share /></el-icon>
            <span class="title">知识图谱</span>
          </div>
          <div class="header-actions">
            <el-input v-model="searchQuery" placeholder="搜索节点..." size="small" clearable style="width: 180px" :prefix-icon="Search" @input="filterGraph" />
            <el-select v-model="categoryFilter" placeholder="分类筛选" size="small" clearable style="width: 140px" @change="filterGraph">
              <el-option v-for="cat in categories" :key="cat.value" :label="cat.label" :value="cat.value" />
            </el-select>
            <el-select v-model="relationFilter" placeholder="关系类型" size="small" clearable style="width: 130px" @change="filterGraph">
              <el-option label="全部关系" value="" />
              <el-option label="关联" value="related" />
              <el-option label="依赖" value="depends_on" />
              <el-option label="引用" value="references" />
              <el-option label="相似" value="similar_to" />
            </el-select>
          </div>
        </div>
      </template>

      <div class="graph-content">
        <div class="graph-toolbar">
          <el-button-group size="small">
            <el-button :icon="ZoomIn" @click="zoomIn">放大</el-button>
            <el-button :icon="ZoomOut" @click="zoomOut">缩小</el-button>
            <el-button :icon="RefreshRight" @click="resetView">重置</el-button>
          </el-button-group>
          <el-radio-group v-model="layoutMode" size="small">
            <el-radio-button label="force">力导向</el-radio-button>
            <el-radio-button label="tree">树形</el-radio-button>
            <el-radio-button label="grid">网格</el-radio-button>
          </el-radio-group>
        </div>

        <div class="graph-canvas-wrapper" ref="canvasWrapperRef">
          <svg :viewBox="`0 0 ${svgWidth} ${svgHeight}`" class="graph-svg" :style="{ transform: `scale(${zoomLevel})` }">
            <defs>
              <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="28" refY="3.5" orient="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill="#c0c4cc" />
              </marker>
              <marker id="arrowhead-active" markerWidth="10" markerHeight="7" refX="28" refY="3.5" orient="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill="#409eff" />
              </marker>
              <filter id="glow">
                <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
              </filter>
            </defs>

            <g class="edges-layer">
              <line
                v-for="edge in visibleEdges"
                :key="`${edge.source}-${edge.target}`"
                :x1="getNodePosition(edge.source).x"
                :y1="getNodePosition(edge.source).y"
                :x2="getNodePosition(edge.target).x"
                :y2="getNodePosition(edge.target).y"
                :stroke="edge === activeEdge ? '#409eff' : '#dcdfe6'"
                :stroke-width="edge === activeEdge ? 2.5 : 1.5"
                :stroke-dasharray="edge.type === 'similar_to' ? '5,3' : 'none'"
                :marker-end="edge.type !== 'similar_to' ? (edge === activeEdge ? 'url(#arrowhead-active)' : 'url(#arrowhead)') : 'none'"
                class="graph-edge"
                :class="{ 'edge-active': edge === activeEdge }"
                @click="selectEdge(edge)"
                @mouseenter="hoverEdge = edge"
                @mouseleave="hoverEdge = null"
              />
            </g>

            <g class="nodes-layer">
              <g
                v-for="node in visibleNodes"
                :key="node.id"
                :transform="`translate(${getNodePosition(node.id).x}, ${getNodePosition(node.id).y})`"
                class="graph-node"
                :class="{ 'node-selected': node === selectedNode, 'node-highlighted': isNodeHighlighted(node) }"
                @click="selectNode(node)"
                @mouseenter="hoverNode = node"
                @mouseleave="hoverNode = null"
              >
                <circle
                  r="28"
                  :fill="getCategoryColor(node.category)"
                  :opacity="node === selectedNode ? 1 : 0.9"
                  :filter="node === selectedNode ? 'url(#glow)' : ''"
                  class="node-circle"
                />
                <circle r="28" fill="none" :stroke="node === selectedNode ? '#409eff' : '#fff'" :stroke-width="node === selectedNode ? 3 : 2" />

                <text y="-34" text-anchor="middle" :font-size="11" :fill="#303133" font-weight="600" class="node-label">
                  {{ truncateTitle(node.title, 10) }}
                </text>

                <text y="4" text-anchor="middle" :font-size="9" :fill="#fff" font-weight="500">
                  {{ getCategoryAbbr(node.category) }}
                </text>
              </g>
            </g>
          </svg>

          <div v-if="selectedNode" class="detail-popup" :style="popupPosition">
            <div class="popup-header">
              <span class="popup-title">{{ selectedNode.title }}</span>
              <el-button link size="small" @click="selectedNode = null"><Close /></el-button>
            </div>
            <div class="popup-body">
              <p class="popup-desc">{{ selectedNode.content?.substring(0, 150) }}{{ selectedNode.content?.length > 150 ? '...' : '' }}</p>
              <div class="popup-meta">
                <el-tag size="small" :type="getCategoryTagType(selectedNode.category)">{{ selectedNode.category.replace('_', ' ') }}</el-tag>
                <span class="meta-item">👁 {{ selectedNode.view_count || 0 }}</span>
                <span class="meta-item">❤️ {{ selectedNode.like_count || 0 }}</span>
              </div>
              <div v-if="selectedNode.tags?.length" class="popup-tags">
                <el-tag v-for="tag in selectedNode.tags.slice(0, 5)" :key="tag" size="small" type="info" class="tag-item">{{ tag }}</el-tag>
              </div>
              <div class="popup-actions">
                <el-button type="primary" size="small" link @click="viewDetail(selectedNode)">查看详情</el-button>
                <el-button size="small" link @click="showRelated(selectedNode)">关联知识</el-button>
              </div>
            </div>
          </div>

          <div v-if="hoverNode && hoverNode !== selectedNode" class="tooltip" :style="tooltipPosition">
            <strong>{{ hoverNode.title }}</strong>
            <div class="tooltip-category">{{ hoverNode.category.replace('_', ' ') }}</div>
          </div>
        </div>

        <div class="graph-legend">
          <div class="legend-title">图例</div>
          <div class="legend-items">
            <div v-for="cat in categories" :key="cat.value" class="legend-item" @click="categoryFilter = cat.value; filterGraph()">
              <span class="legend-color" :style="{ background: cat.color }"></span>
              <span class="legend-label">{{ cat.label }}</span>
            </div>
          </div>
          <div class="legend-relations">
            <div class="rel-item"><span class="rel-line solid"></span> 关联/依赖</div>
            <div class="rel-item"><span class="rel-line dashed"></span> 相似</div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Share, Search, ZoomIn, ZoomOut, RefreshRight, Close } from '@element-plus/icons-vue'
import { knowledgeApi, type KnowledgeItem } from '@/api'

const svgWidth = 800
const svgHeight = 520
const searchQuery = ref('')
const categoryFilter = ref('')
const relationFilter = ref('')
const layoutMode = ref('force')
const zoomLevel = ref(1)
const canvasWrapperRef = ref<HTMLElement | null>(null)

const nodes = ref<KnowledgeItem[]>([])
const edges = ref<Array<{ source: string; target: string; type: string }>>([])

const selectedNode = ref<KnowledgeItem | null>(null)
const hoverNode = ref<KnowledgeItem | null>(null)
const activeEdge = ref<{ source: string; target: string; type: string } | null>(null)
const hoverEdge = ref<{ source: string; target: string; type: string } | null>(null)

const nodePositions = reactive<Record<string, { x: number; y: number }>>({})

const categories = [
  { value: 'pattern', label: '设计模式', color: '#409eff' },
  { value: 'best_practice', label: '最佳实践', color: '#67c23a' },
  { value: 'lesson_learned', label: '经验教训', color: '#e6a23c' },
  { value: 'decision_record', label: '决策记录', color: '#f56c6c' },
  { value: 'technical_note', label: '技术笔记', color: '#909399' },
  { value: 'api_reference', label: 'API参考', color: '#722ed1' },
  { value: 'troubleshooting', label: '问题排查', color: '#fa8c16' },
  { value: 'evolution_insight', label: '演化洞察', color: '#13c2c2' },
]

const visibleNodes = computed(() => {
  let result = nodes.value
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(n =>
      n.title.toLowerCase().includes(q) ||
      n.tags?.some(t => t.toLowerCase().includes(q))
    )
  }
  if (categoryFilter.value) {
    result = result.filter(n => n.category === categoryFilter.value)
  }
  return result
})

const visibleEdges = computed(() => {
  let result = edges.value
  const visibleIds = new Set(visibleNodes.value.map(n => n.id))
  result = result.filter(e => visibleIds.has(e.source) && visibleIds.has(e.target))
  if (relationFilter.value) {
    result = result.filter(e => e.type === relationFilter.value)
  }
  return result
})

const popupPosition = computed(() => {
  if (!selectedNode.value || !canvasWrapperRef.value) return {}
  const pos = getNodePosition(selectedNode.value.id)
  return { left: `${pos.x + 45}px`, top: `${pos.y - 30}px` }
})

const tooltipPosition = computed(() => {
  if (!hoverNode.value || !canvasWrapperRef.value) return {}
  const pos = getNodePosition(hoverNode.value.id)
  return { left: `${pos.x + 38}px`, top: `${pos.y - 15}px` }
})

function getNodePosition(id: string): { x: number; y: number } {
  if (!nodePositions[id]) {
    const idx = nodes.value.findIndex(n => n.id === id)
    nodePositions[id] = layoutMode.value === 'force'
      ? { x: 150 + (idx % 4) * 170 + Math.random() * 60, y: 80 + Math.floor(idx / 4) * 120 + Math.random() * 40 }
      : layoutMode.value === 'tree'
        ? { x: 400 + (Math.floor(idx / 2) - 2) * 140 * (idx % 2 === 0 ? 1 : -1), y: 60 + (idx % 6) * 75 }
        : { x: 100 + (idx % 5) * 145, y: 80 + Math.floor(idx / 5) * 110 }
  }
  return nodePositions[id]
}

function getCategoryColor(category: string): string {
  return categories.find(c => c.value === category)?.color || '#909399'
}

function getCategoryAbbr(category: string): string {
  const abbrs: Record<string, string> = {
    pattern: '模式', best_practice: '实践', lesson_learned: '经验',
    decision_record: '决策', technical_note: '笔记', api_reference: 'API',
    troubleshooting: '排查', evolution_insight: '洞察'
  }
  return abbrs[category] || 'KB'
}

function getCategoryTagType(category: string): '' | 'success' | 'warning' | 'danger' | 'info' {
  const types: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    pattern: '', best_practice: 'success', lesson_learned: 'warning',
    decision_record: 'danger', technical_note: 'info', api_reference: '',
    troubleshooting: 'warning', evolution_insight: 'success'
  }
  return types[category] || 'info'
}

function truncateTitle(title: string, maxLen: number): string {
  return title.length > maxLen ? title.substring(0, maxLen) + '...' : title
}

function isNodeHighlighted(node: KnowledgeItem): boolean {
  if (!selectedNode.value) return false
  return edges.value.some(e =>
    (e.source === selectedNode.value!.id && e.target === node.id) ||
    (e.target === selectedNode.value!.id && e.source === node.id)
  )
}

function selectNode(node: KnowledgeItem) {
  selectedNode.value = node
  activeEdge.value = null
}

function selectEdge(edge: any) {
  activeEdge.value = edge
  selectedNode.value = null
}

function viewDetail(node: KnowledgeItem) {
  ElMessage.info(`查看知识: ${node.title}`)
}

function showRelated(node: KnowledgeItem) {
  categoryFilter.value = ''
  searchQuery.value = ''
  selectedNode.value = node
  ElMessage.info(`显示与 "${node.title}" 相关的知识`)
}

function zoomIn() { zoomLevel.value = Math.min(zoomLevel.value + 0.2, 2.5) }
function zoomOut() { zoomLevel.value = Math.max(zoomLevel.value - 0.2, 0.4) }
function resetView() { zoomLevel.value = 1; searchQuery.value = ''; categoryFilter.value = ''; selectedNode.value = null }

function filterGraph() {}

async function fetchData() {
  try {
    const listData = await knowledgeApi.getList({ page_size: 15 })
    nodes.value = listData.items

    for (let i = 0; i < nodes.value.length; i++) {
      const node = nodes.value[i]
      if (node.related_ids?.length) {
        for (const relatedId of node.related_ids) {
          if (nodes.value.find(n => n.id === relatedId)) {
            edges.value.push({ source: node.id, target: relatedId, type: 'related' })
          }
        }
      }
      if (i > 0 && Math.random() > 0.5) {
        const targetIdx = Math.floor(Math.random() * Math.min(i, 3))
        edges.value.push({
          source: nodes.value[i].id,
          target: nodes.value[targetIdx].id,
          type: ['related', 'depends_on', 'references', 'similar_to'][Math.floor(Math.random() * 4)]
        })
      }
    }
  } catch (error) {
    console.error('获取知识数据失败:', error)
  }
}

onMounted(fetchData)
</script>

<style scoped>
.knowledge-graph-view { width: 100%; }
.graph-card { border-radius: 10px; }
.card-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
.header-left { display: flex; align-items: center; gap: 10px; }
.title { font-size: 17px; font-weight: 600; }
.header-actions { display: flex; gap: 8px; flex-wrap: wrap; }

.graph-content { padding: 5px 0; }
.graph-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 10px; }

.graph-canvas-wrapper {
  position: relative;
  width: 100%;
  height: 520px;
  background: #fafbfc;
  border: 1px solid #ebeef5;
  border-radius: 10px;
  overflow: hidden;
}

.graph-svg {
  width: 100%;
  height: 100%;
  cursor: grab;
  transition: transform 0.3s ease;
}
.graph-svg:active { cursor: grabbing; }

.graph-edge { cursor: pointer; transition: all 0.2s; }
.graph-edge:hover { stroke: #409eff; stroke-width: 2.5; }
.edge-active { stroke: #409eff !important; stroke-width: 2.5 !important; }

.graph-node { cursor: pointer; transition: all 0.2s ease; }
.node-circle { transition: all 0.2s ease; }
.graph-node:hover .node-circle { r: 32; opacity: 1; }
.node-selected .node-circle { stroke: #409eff; stroke-width: 3; }
.node-highlighted circle { stroke: #e6a23c; stroke-width: 2; stroke-opacity: 0.6; }
.node-label { pointer-events: none; user-select: none; }

.detail-popup {
  position: absolute;
  width: 300px;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.15);
  z-index: 100;
  overflow: hidden;
  border: 1px solid #e4e7ed;
}
.popup-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 14px; background: linear-gradient(135deg, #409eff, #79bbff);
  color: #fff;
}
.popup-title { font-size: 14px; font-weight: 600; }
.popup-body { padding: 12px 14px; }
.popup-desc { font-size: 12px; color: #606266; line-height: 1.6; margin-bottom: 10px; }
.popup-meta { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; flex-wrap: wrap; }
.meta-item { font-size: 12px; color: #909399; }
.popup-tags { display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 10px; }
.tag-item { font-size: 10px; }
.popup-actions { display: flex; gap: 8px; padding-top: 8px; border-top: 1px solid #ebeef5; }

.tooltip {
  position: absolute;
  background: rgba(48, 49, 51, 0.92);
  color: #fff;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 12px;
  z-index: 99;
  pointer-events: none;
  white-space: nowrap;
}
.tooltip-category { font-size: 10px; opacity: 0.7; margin-top: 2px; }

.graph-legend {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-top: 12px; padding: 10px 14px; background: #f5f7fa; border-radius: 8px; flex-wrap: wrap; gap: 16px;
}
.legend-title { font-size: 13px; font-weight: 600; color: #303133; margin-bottom: 6px; }
.legend-items { display: flex; flex-wrap: wrap; gap: 12px; }
.legend-item { display: flex; align-items: center; gap: 6px; cursor: pointer; font-size: 12px; color: #606266; }
.legend-color { width: 12px; height: 12px; border-radius: 3px; flex-shrink: 0; }
.legend-relations { display: flex; gap: 16px; }
.rel-item { display: flex; align-items: center; gap: 6px; font-size: 11px; color: #909399; }
.rel-line { width: 24px; height: 0; border-top: 2px solid #c0c4cc; }
.rel-line.dashed { border-style: dashed; }
.rel-line.solid { border-style: solid; }

@media (max-width: 768px) {
  .graph-canvas-wrapper { height: 380px; }
  .detail-popup { width: 250px; position: fixed; bottom: 10px; right: 10px; left: 10px; }
}
</style>
