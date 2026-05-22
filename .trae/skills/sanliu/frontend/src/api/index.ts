import axios, { AxiosRequestConfig, AxiosError } from 'axios'

export interface ApiError {
  code: string
  message: string
  details?: unknown
}

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  (response) => {
    return response
  },
  (error: AxiosError) => {
    const apiError: ApiError = {
      code: 'UNKNOWN_ERROR',
      message: '请求失败，请稍后重试',
      details: error.response?.data
    }

    if (error.response) {
      switch (error.response.status) {
        case 400:
          apiError.code = 'BAD_REQUEST'
          apiError.message = '请求参数错误'
          break
        case 401:
          apiError.code = 'UNAUTHORIZED'
          apiError.message = '未授权，请先登录'
          break
        case 403:
          apiError.code = 'FORBIDDEN'
          apiError.message = '没有权限访问该资源'
          break
        case 404:
          apiError.code = 'NOT_FOUND'
          apiError.message = '请求的资源不存在'
          break
        case 500:
          apiError.code = 'SERVER_ERROR'
          apiError.message = '服务器内部错误'
          break
        case 502:
          apiError.code = 'BAD_GATEWAY'
          apiError.message = '网关错误'
          break
        case 503:
          apiError.code = 'SERVICE_UNAVAILABLE'
          apiError.message = '服务暂时不可用'
          break
        default:
          apiError.code = `HTTP_${error.response.status}`
          apiError.message = `请求失败 (${error.response.status})`
      }
    } else if (error.code === 'ECONNABORTED') {
      apiError.code = 'TIMEOUT'
      apiError.message = '请求超时，请检查网络连接'
    } else if (!navigator.onLine) {
      apiError.code = 'OFFLINE'
      apiError.message = '网络连接已断开'
    }

    console.error('API Error:', apiError)
    return Promise.reject(apiError)
  }
)

const request = {
  get: <T = unknown>(url: string, config?: AxiosRequestConfig) => api.get<T>(url, config).then(res => res.data),
  post: <T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig) => api.post<T>(url, data, config).then(res => res.data),
  put: <T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig) => api.put<T>(url, data, config).then(res => res.data),
  delete: <T = unknown>(url: string, config?: AxiosRequestConfig) => api.delete<T>(url, config).then(res => res.data)
}

export interface DecisionLog {
  id: number
  skill_call_id: number
  decision_type: string
  reasoning: string | null
  alternatives: string[] | null
  created_at: string
}

export interface IOTrace {
  id: number
  skill_call_id: number
  trace_type: string
  input_data: unknown
  output_data: unknown
  created_at: string
}

export interface CodeChange {
  id: number
  skill_call_id: number
  file_path: string
  change_type: string
  diff: string | null
  description: string | null
  created_at: string
}

export interface Artifact {
  id: number
  project_id: number
  artifact_type: string
  name: string
  content: string | null
  file_path: string | null
  created_at: string
}

export interface TransparencyReport {
  project_id: number
  total_skill_calls: number
  total_decisions: number
  total_artifacts: number
  decision_breakdown: Record<string, number>
  generated_at: string
}

export interface RequirementTrace {
  id: number
  project_id: number
  requirement_id: string
  source_type: string
  source_id: number
  status: string
  created_at: string
}

export interface ClarificationQuestion {
  id: number
  project_id: number
  question: string
  context: string | null
  status: string
  answer: string | null
  answered_by: string | null
  answered_at: string | null
  confirmed_by: string | null
  created_at: string
}

export interface HumanApproval {
  id: number
  project_id: number
  approval_type: string
  description: string
  status: string
  requested_by: string
  decided_by: string | null
  decided_at: string | null
  decision_reason: string | null
  created_at: string
}

export interface AcceptanceTest {
  id: number
  project_id: number
  requirement_id: string | null
  scenario_name: string
  given: string | null
  when: string | null
  then: string | null
  test_code: string | null
  execution_result: string | null
  execution_log: string | null
  executed_at: string | null
  is_shadow_test: boolean
  created_at: string
}

export interface MutationTest {
  id: number
  project_id: number
  test_file: string
  target_file: string
  mutation_type: string
  status: string
  killed_by: string | null
  created_at: string
}

export interface NonFunctionalCheck {
  id: number
  project_id: number
  check_type: string
  description: string
  status: string
  result: string | null
  executed_at: string | null
  created_at: string
}

export interface PipelineStatus {
  project_id: number
  current_stage: string | null
  stages: PipelineStage[]
  created_at: string
}

export interface PipelineStage {
  name: string
  status: string
  started_at: string | null
  completed_at: string | null
  output_artifacts: string[] | null
}

export const decisionLogsApi = {
  getBySkillCall: (skillCallId: number) => 
    request.get<DecisionLog[]>(`/decision_logs/skill_call/${skillCallId}`),
  getById: (id: number) => 
    request.get<DecisionLog>(`/decision_logs/${id}`),
  create: (data: Partial<DecisionLog>) => 
    request.post<DecisionLog>('/decision_logs/', data),
}

export const ioTracesApi = {
  getBySkillCall: (skillCallId: number, traceType?: string) => 
    request.get<IOTrace[]>(`/io_traces/skill_call/${skillCallId}`, { params: { trace_type: traceType } }),
  getById: (id: number) => 
    request.get<IOTrace>(`/io_traces/${id}`),
  create: (data: Partial<IOTrace>) => 
    request.post<IOTrace>('/io_traces/', data),
}

export const codeChangesApi = {
  getBySkillCall: (skillCallId: number) => 
    request.get<CodeChange[]>(`/code_changes/skill_call/${skillCallId}`),
  getById: (id: number) => 
    request.get<CodeChange>(`/code_changes/${id}`),
  create: (data: Partial<CodeChange>) => 
    request.post<CodeChange>('/code_changes/', data),
}

export const artifactsApi = {
  getByProject: (projectId: number, artifactType?: string) => 
    request.get<Artifact[]>(`/artifacts/project/${projectId}`, { params: { artifact_type: artifactType } }),
  getById: (id: number) => 
    request.get<Artifact>(`/artifacts/${id}`),
  create: (data: Partial<Artifact>) => 
    request.post<Artifact>('/artifacts/', data),
}

export const transparencyApi = {
  getReport: (projectId: number) => 
    request.get<TransparencyReport>(`/transparency/report/project/${projectId}`),
}

export const requirementTracesApi = {
  getByProject: (projectId: number, status?: string) => 
    request.get<RequirementTrace[]>(`/requirement_traces/project/${projectId}`, { params: { status } }),
  create: (data: Partial<RequirementTrace>) => 
    request.post<RequirementTrace>('/requirement_traces/', data),
  getCoverage: (projectId: number) => 
    request.get<{ coverage: number }>(`/requirement_traces/coverage/${projectId}`),
  updateStatus: (traceId: number, status: string) => 
    request.put<RequirementTrace>(`/requirement_traces/${traceId}/status`, null, { params: { status } }),
}

export const clarificationQuestionsApi = {
  getByProject: (projectId: number, status?: string) => 
    request.get<ClarificationQuestion[]>(`/clarification_questions/project/${projectId}`, { params: { status } }),
  create: (data: Partial<ClarificationQuestion>) => 
    request.post<ClarificationQuestion>('/clarification_questions/', data),
  answer: (questionId: number, data: { answer: string; answered_by: string }) => 
    request.put<ClarificationQuestion>(`/clarification_questions/${questionId}/answer`, data),
  confirm: (questionId: number, confirmedBy: string) => 
    request.put<ClarificationQuestion>(`/clarification_questions/${questionId}/confirm`, null, { params: { confirmed_by: confirmedBy } }),
}

export const humanApprovalsApi = {
  getByProject: (projectId: number, status?: string) => 
    request.get<HumanApproval[]>(`/human_approvals/project/${projectId}`, { params: { status } }),
  getPending: () => 
    request.get<HumanApproval[]>('/human_approvals/pending'),
  create: (data: Partial<HumanApproval>) => 
    request.post<HumanApproval>('/human_approvals/', data),
  decide: (approvalId: number, data: { decision: string; decided_by: string; reason?: string }) => 
    request.put<HumanApproval>(`/human_approvals/${approvalId}/decide`, data),
}

export const acceptanceTestsApi = {
  getByProject: (projectId: number, isShadow?: boolean) => 
    request.get<AcceptanceTest[]>(`/acceptance_tests/project/${projectId}`, { params: { is_shadow: isShadow } }),
  create: (data: Partial<AcceptanceTest>) => 
    request.post<AcceptanceTest>('/acceptance_tests/', data),
  execute: (testId: number) => 
    request.post<{ test_id: number; result: string }>(`/acceptance_tests/${testId}/execute`),
  compareShadow: (projectId: number) => 
    request.get<{
      project_id: number
      main_tests_count: number
      shadow_tests_count: number
      divergences: Array<{ requirement_id: string; main_result: string; shadow_result: string }>
      needs_human_intervention: boolean
    }>(`/acceptance_tests/shadow-comparison/${projectId}`),
}

export const mutationTestsApi = {
  getByProject: (projectId: number) => 
    request.get<MutationTest[]>(`/mutation_tests/project/${projectId}`),
  create: (data: Partial<MutationTest>) => 
    request.post<MutationTest>('/mutation_tests/', data),
  run: (testId: number) => 
    request.post<{ test_id: number; status: string }>(`/mutation_tests/${testId}/run`),
}

export const nonFunctionalChecksApi = {
  getByProject: (projectId: number, checkType?: string) => 
    request.get<NonFunctionalCheck[]>(`/non_functional_checks/project/${projectId}`, { params: { check_type: checkType } }),
  create: (data: Partial<NonFunctionalCheck>) => 
    request.post<NonFunctionalCheck>('/non_functional_checks/', data),
  execute: (checkId: number) => 
    request.post<{ check_id: number; status: string }>(`/non_functional_checks/${checkId}/execute`),
}

export const pipelineApi = {
  initialize: (projectId: number) => 
    request.post<PipelineStatus>(`/pipeline/project/${projectId}/initialize`),
  getStatus: (projectId: number) => 
    request.get<PipelineStatus>(`/pipeline/project/${projectId}`),
  startStage: (projectId: number, stageName: string) => 
    request.post<PipelineStage>(`/pipeline/project/${projectId}/stage/${stageName}/start`),
  completeStage: (projectId: number, stageName: string, artifacts?: string[]) => 
    request.post<PipelineStage>(`/pipeline/project/${projectId}/stage/${stageName}/complete`, { output_artifacts: artifacts }),
}

export interface RealtimeQualityData {
  timestamp: string
  coverage_percent: number
  complexity_score: number
  technical_debt_hours: number
  pass_rate: number
  code_quality_score: number
  test_success_rate: number
  defect_density: number
}

export interface QualityTrendPoint {
  timestamp: string
  coverage: number
  complexity: number
  technical_debt: number
  pass_rate: number
}

export interface QualityGateResult {
  gate_id: string
  gate_name: string
  status: 'passed' | 'warning' | 'failed' | 'skipped'
  criteria: Record<string, { actual: number; threshold: number; passed: boolean }>
  checked_at: string
  overall_status: 'passed' | 'warning' | 'failed'
}

export interface QualityAlertItem {
  alert_id: string
  metric_type: string
  severity: 'info' | 'warning' | 'error' | 'critical'
  title: string
  message: string
  timestamp: string
  acknowledged: boolean
  resolved: boolean
}

export interface TrendAnalysisResult {
  metric_type: string
  period: string
  trend_direction: 'improving' | 'stable' | 'declining'
  change_percentage: number
  data_points: Array<{ timestamp: string; value: number }>
  prediction?: number
  confidence?: number
}

export interface RealtimeSummary {
  timestamp: string
  overall_health: 'excellent' | 'good' | 'fair' | 'poor'
  active_alerts_count: number
  quality_gate_status: string
  key_metrics: {
    coverage: number
    complexity: number
    pass_rate: number
    technical_debt: number
  }
  last_check_time: string
}

export interface EvolutionStatusOverview {
  current_cycle_id: string
  status: 'idle' | 'running' | 'paused' | 'completed' | 'failed'
  current_phase: 'analysis' | 'planning' | 'execution' | 'validation' | 'review'
  progress: number
  total_cycles_completed: number
  current_cycle_start_time: string
  estimated_completion: string
  capabilities: {
    self_iteration: { enabled: boolean; status: string; last_run: string }
    self_optimization: { enabled: boolean; status: string; last_run: string }
    self_repair: { enabled: boolean; status: string; last_run: string }
    self_improvement: { enabled: boolean; status: string; last_run: string }
  }
  recent_cycles: EvolutionCycleSummary[]
}

export interface EvolutionCycleSummary {
  cycle_id: string
  phase: string
  status: string
  duration_seconds: number
  improvement_score: number
  start_time: string
  end_time: string | null
}

export interface ComprehensiveHealthCheck {
  timestamp: string
  overall_status: 'healthy' | 'degraded' | 'critical' | 'unknown'
  components: Array<{
    name: string
    status: 'healthy' | 'degraded' | 'critical' | 'unknown'
    message: string
    response_time_ms: number
    last_check: string
  }>
  recommendations: string[]
}

export interface ReportGenerateRequest {
  report_type: 'daily' | 'weekly' | 'monthly' | 'custom'
  start_date: string | null
  end_date: string | null
  include_charts: boolean
  include_recommendations: boolean
}

export interface ReportGenerateResponse {
  report_id: string
  report_url: string
  generated_at: string
  expires_at: string
  summary: {
    overall_score: number
    issues_found: Array<{ type: string; severity: string; description: string }>
    recommendations: string[]
  }
}

export const realtimeQualityApi = {
  getRealtimeSummary: () => 
    request.get<RealtimeSummary>('/quality/realtime/summary'),
  getTrendAnalysis: (metricType?: string, hours?: number) => 
    request.get<TrendAnalysisResult>('/quality/trend/analysis', { params: { metric_type: metricType, hours } }),
  checkQualityGate: () => 
    request.get<QualityGateResult>('/quality/gate/check'),
  runAlertEngine: () => 
    request.post<QualityAlertItem[]>('/quality/alerts/engine/run'),
  getAlerts: (severity?: string) => 
    request.get<QualityAlertItem[]>('/quality/alerts', { params: { severity } })
}

export const evolutionStatusApi = {
  getStatus: () => 
    request.get<EvolutionStatusOverview>('/skill-evolution/evolution/status'),
  getCycles: (period?: string) => 
    request.get<EvolutionCycleSummary[]>('/skill-evolution/cycles', { params: { period } })
}

export const healthComprehensiveApi = {
  check: () => 
    request.get<ComprehensiveHealthCheck>('/health/comprehensive')
}

export const reportGenerateApi = {
  generate: (data: ReportGenerateRequest) => 
    request.post<ReportGenerateResponse>('/reports/generate', data),
  download: (reportId: string) => 
    request.get<Blob>(`/reports/${reportId}/download`)
}

export const qualityGateApi = {
  check: () => 
    request.get<QualityGateResult>('/quality/gate/check'),
  forceRecheck: () => 
    request.post<QualityGateResult>('/quality/gate/recheck')
}

export interface InsightMetricType {
  performance: string
  efficiency: string
  success_rate: string
  response_time: string
  resource_usage: string
  error_rate: string
  coverage: string
  technical_debt: string
}

export interface TrendDirection {
  upward: string
  downward: string
  stable: string
  volatile: string
}

export interface TrendDataPoint {
  timestamp: string
  value: number
  predicted: boolean
  confidence?: number
}

export interface TrendPrediction {
  metric_type: string
  period: string
  direction: string
  change_percentage: number
  current_value: number
  predicted_value?: number
  confidence_score: number
  data_points: TrendDataPoint[]
  prediction_horizon: string
}

export interface ImprovementRecommendation {
  recommendation_id: string
  title: string
  description: string
  priority: string
  category: string
  impact_assessment: Record<string, number>
  effort_level: string
  risk_level: string
  status: string
  created_at: string
  implemented_at?: string
}

export interface EvolutionStatusInsight {
  current_phase: string
  progress_percentage: number
  active_cycle_id?: string
  last_cycle_result?: Record<string, any>
  next_scheduled?: string
  total_cycles_completed: number
  success_rate: number
  average_cycle_duration_seconds: number
  capabilities_status: Record<string, Record<string, any>>
  system_health_score: number
}

export interface EvolutionTriggerResponse {
  trigger_id: string
  status: string
  message: string
  estimated_duration?: number
  cycle_id?: string
}

export const evolutionInsightsApi = {
  getTrends: (metric?: string, period?: string) =>
    request.get<TrendPrediction>(`/evolution/insights/trends?metric=${metric || 'performance'}&period=${period || '7d'}`),
  getAllTrends: (period?: string) =>
    request.get<TrendPrediction[]>(`/evolution/insights/trends/all?period=${period || '7d'}`),
  getRecommendations: (priority?: string, category?: string, limit?: number) => {
    const params: string[] = []
    if (priority) params.push(`priority=${priority}`)
    if (category) params.push(`category=${category}`)
    if (limit) params.push(`limit=${limit}`)
    return request.get<ImprovementRecommendation[]>(`/evolution/insights/recommendations?${params.join('&')}`)
  },
  getStatus: () =>
    request.get<EvolutionStatusInsight>('/evolution/insights/status'),
  trigger: (data?: { evolution_type?: string; force?: boolean; dry_run?: boolean }) =>
    request.post<EvolutionTriggerResponse>('/evolution/insights/trigger', data || {}),
  getSummary: () =>
    request.get<Record<string, any>>('/evolution/insights/summary'),
}

export interface ContextRecommendation {
  recommendation_id: string
  context_type: string
  action_type: string
  title: string
  description: string
  confidence_score: number
  priority: string
  impact_assessment: Record<string, any>
  suggested_actions: string[]
  related_items: string[]
  metadata: Record<string, any>
  created_at: string
  expires_at?: string
  is_actionable: boolean
}

export interface RecommendationFeedback {
  recommendation_id: string
  action: string
  rating?: number
  comment?: string
  context_snapshot?: Record<string, any>
  timestamp: string
}

export interface RecommendationHistoryItem {
  feedback_id: string
  recommendation_id: string
  title: string
  action: string
  rating?: number
  comment?: string
  timestamp: string
  context_type?: string
}

export interface RecommendationHistoryResponse {
  total: number
  items: RecommendationHistoryItem[]
  page: number
  page_size: number
  total_pages: number
  acceptance_rate: number
  average_rating: number
}

export const recommendationsApi = {
  getContextRecommendations: (contextType: string, limit?: number) =>
    request.get<ContextRecommendation[]>(`/recommendations/context/${contextType}?limit=${limit || 10}`),
  submitFeedback: (feedback: RecommendationFeedback) =>
    request.post('/recommendations/feedback', feedback),
  getHistory: (action?: string, contextType?: string, limit?: number) => {
    const params: string[] = []
    if (action) params.push(`action=${action}`)
    if (contextType) params.push(`context_type=${contextType}`)
    if (limit) params.push(`limit=${limit || 20}`)
    return request.get<RecommendationHistoryResponse>(`/recommendations/history?${params.join('&')}`)
  },
  getStats: () =>
    request.get<Record<string, any>>('/recommendations/stats'),
}

export interface KnowledgeCategory {
  pattern: string
  best_practice: string
  lesson_learned: string
  decision_record: string
  technical_note: string
  api_reference: string
  troubleshooting: string
  evolution_insight: string
}

export interface KnowledgeStatus {
  draft: string
  review: string
  published: string
  archived: string
  deprecated: string
}

export interface KnowledgeItem {
  id: string
  title: string
  content: string
  category: string
  tags: string[]
  source?: string
  author?: string
  status: string
  priority: number
  related_ids: string[]
  metadata: Record<string, any>
  created_at: string
  updated_at: string
  version: number
  view_count: number
  like_count: number
}

export interface KnowledgeListResponse {
  total: number
  items: KnowledgeItem[]
  page: number
  page_size: number
  total_pages: number
}

export interface SearchResultItem {
  id: string
  title: string
  content_preview: string
  category: string
  score: number
  highlights: string[]
  matched_tags: string[]
}

export interface SearchResponse {
  query: string
  total_results: number
  results: SearchResultItem[]
  search_time_ms: number
  suggestions: string[]
}

export interface RecommendResponse {
  knowledge_id: string
  title: string
  reason: string
  relevance_score: number
  category: string
}

export const knowledgeApi = {
  getList: (params?: { page?: number; page_size?: number; category?: string; status?: string; tag?: string; search?: string }) =>
    request.get<KnowledgeListResponse>(`/knowledge?${new URLSearchParams(params as Record<string, string>).toString()}`),
  create: (data: Partial<KnowledgeItem>) =>
    request.post<KnowledgeItem>('/knowledge', data),
  getById: (id: string) =>
    request.get<KnowledgeItem>(`/knowledge/${id}`),
  update: (id: string, data: Partial<KnowledgeItem>) =>
    request.put<KnowledgeItem>(`/knowledge/${id}`, data),
  delete: (id: string, hardDelete?: boolean) =>
    request.delete(`/knowledge/${id}?hard_delete=${hardDelete || false}`),
  search: (query: string, category?: string, limit?: number) => {
    const params = `q=${encodeURIComponent(query)}`
    return request.get<SearchResponse>(`/knowledge/search?${params}${category ? `&category=${category}` : ''}${limit ? `&limit=${limit}` : ''}`)
  },
  recommend: (currentItemId?: string, category?: string, limit?: number) => {
    let url = '/knowledge/recommend'
    const qs: string[] = []
    if (currentItemId) qs.push(`current_item_id=${currentItemId}`)
    if (category) qs.push(`category=${category}`)
    if (limit) qs.push(`limit=${limit}`)
    if (qs.length) url += `?${qs.join('&')}`
    return request.get<RecommendResponse[]>(url)
  },
  getCategories: () =>
    request.get<Record<string, any>>('/knowledge/categories'),
  getTags: (limit?: number) =>
    request.get<Array<{ tag: string; count: number }>>(`/knowledge/tags?limit=${limit || 30}`),
  like: (id: string) =>
    request.post(`/knowledge/${id}/like`),
}

export interface UXMetricCard {
  metric_name: string
  display_name: string
  value: number
  unit: string
  level: string
  trend: string
  change_percentage: number
  threshold_good: number
  threshold_fair: number
  target_value?: number
}

export interface UXMetricsResponse {
  timestamp: string
  metrics: UXMetricCard[]
  overall_score: number
  overall_level: string
}

export interface UserEvent {
  event_id: string
  event_type: string
  page_url: string
  user_id?: string
  session_id: string
  device_type: string
  timestamp: string
  data: Record<string, any>
  duration_ms?: number
  metadata: Record<string, any>
}

export interface BehaviorPathAnalysis {
  session_id: string
  user_id?: string
  path: Array<{ page: string; timestamp: string; duration_seconds: number; event_count: number }>
  total_duration_seconds: number
  page_count: number
  bounce_rate: number
  exit_page: string
  conversion_funnel: Array<Record<string, any>>
}

export interface DashboardData {
  period: string
  generated_at: string
  summary: Record<string, any>
  metrics_cards: UXMetricCard[]
  top_pages: Array<Record<string, any>>
  error_distribution: Array<Record<string, any>>
  device_breakdown: Record<string, any>
  trend_data: Record<string, any[]>
  user_flow_funnel: Array<Record<string, any>>
}

export const uxMonitorApi = {
  getMetrics: () =>
    request.get<UXMetricsResponse>('/ux/metrics'),
  reportEvents: (events: { events: UserEvent[] }) =>
    request.post('/ux/events', events),
  getBehaviorAnalysis: (sessionId?: string, userId?: string) => {
    let url = '/ux/analysis'
    const qs: string[] = []
    if (sessionId) qs.push(`session_id=${sessionId}`)
    if (userId) qs.push(`user_id=${userId}`)
    if (qs.length) url += `?${qs.join('&')}`
    return request.get<BehaviorPathAnalysis>(url)
  },
  getDashboard: (period?: string) =>
    request.get<DashboardData>(`/ux/dashboard?period=${period || '24h'}`),
  getPagePerformance: (sortBy?: string, limit?: number) =>
    request.get(`/ux/pages?sort_by=${sortBy || 'avg_duration'}&limit=${limit || 20}`),
  getErrorStats: (hours?: number) =>
    request.get(`/ux/errors?hours=${hours || 24}`),
}

export default api
