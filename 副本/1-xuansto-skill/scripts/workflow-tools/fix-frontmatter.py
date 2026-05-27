import yaml, re, os, sys

base = r'd:\Projects\TraeProjects\skiller\.trae\skills\xuansto-skill\workflows'
yaml_base = os.path.join(base, '_yaml')
ref_base = r'd:\Projects\TraeProjects\skiller\.trae\skills\xuansto-skill\references'

files = [
    'sdd-tdd-full','sdd-tdd-medium','sdd-tdd-fast','ui-ux-workflow',
    'desktop-build-workflow','security-audit','ai-pentest','acceptance',
    'bug-fix','cross-platform-workflow','flutter-desktop-workflow',
    'performance-test','brainstorming-workflow','subagent-driven-workflow',
    'webapp-testing-workflow'
]

GATE_MAP = {
    'design_review': 'DESIGN-REVIEW',
    'design_tokens_sync': 'DESIGN-TOKENS',
    'visual_regression_check': 'DESIGN-VISUAL-REGRESSION',
    'accessibility_check': 'DESIGN-ACCESSIBILITY',
    'design_system_complete': 'DESIGN-SYSTEM-COMPLETE',
    'anti_pattern_check': 'ANTI-PATTERN-CHECK',
    'req_completeness': 'GATE-001',
    'spec_consistency': 'GATE-002',
    'arch_review': 'GATE-003',
    'contract_defined': 'GATE-004',
    'api_contract_defined': 'GATE-004',
    'ipc_contract_defined': 'IPC-CONTRACT',
    'coverage_80': 'GATE-005',
    'shared_coverage_80': 'GATE-005',
    'test_data_ready': 'GATE-006',
    'lint_pass': 'GATE-007',
    'unit_test_pass': 'TEST-PASS',
    'test_pass': 'TEST-PASS',
    'bug_fixed': 'TEST-PASS',
    'regression_pass': 'TEST-PASS',
    'code_review_pass': 'GATE-009',
    'flutter_code_review': 'GATE-009',
    'review_confidence': 'REVIEW-CONFIDENCE',
    'multi_perspective_coverage': 'MULTI-PERSPECTIVE-COVERAGE',
    'file_encoding': 'FILE-ENCODING',
    'comment_language': 'COMMENT-LANGUAGE',
    'script_security': 'SCRIPT-SECURITY',
    'script_cleanup': 'SCRIPT-CLEANUP',
    'token_budget': 'TOKEN-BUDGET',
    'e2e_test_pass': 'GATE-011',
    'smoke_tests_pass': 'GATE-011',
    'security_scan': 'GATE-012',
    'no_high_risk_vuln': 'GATE-012',
    'no_p0_p1': 'GATE-012',
    'no_p0_p1_defects': 'GATE-012',
    'security_verified': 'GATE-012',
    'agentic_security': 'AGENTIC-SECURITY',
    'ai_pentest_pass': 'AI-PENTEST',
    'visual_regression_pass': 'VISUAL-REGRESSION-PASS',
    'accessibility_pass': 'ACCESSIBILITY',
    'performance_met': 'PERFORMANCE',
    'performance_baseline': 'PERFORMANCE',
    'spec_consistency_check': 'SPEC-CONSISTENCY',
    'spec_drift_check': 'SPEC-CONSISTENCY',
    'deploy_ready': 'GATE-013',
    'prod_verify': 'GATE-014',
    'infra_health': 'INFRA-HEALTH',
    'ux_acceptance': 'UX-ACCEPTANCE',
    'satisfaction_80': 'UX-ACCEPTANCE',
    'satisfaction_4': 'UX-ACCEPTANCE',
    'iteration_close': 'GATE-015',
    'doc_completeness': 'DOC-COMPLETENESS',
    'docs_complete': 'DOC-COMPLETENESS',
    'release_docs_complete': 'DOC-COMPLETENESS',
    'simplification_behavior': 'SIMPLIFICATION-BEHAVIOR',
    'chesterton_fence': 'CHESTERTON-FENCE',
    'desktop_build_pass': 'DESKTOP-BUILD',
    'desktop_build': 'DESKTOP-BUILD',
    'build_env_ready': 'DESKTOP-BUILD',
    'signing_verified': 'DESKTOP-SIGN',
    'desktop_sign': 'DESKTOP-SIGN',
    'signing_cert_available': 'DESKTOP-SIGN',
    'desktop_update': 'DESKTOP-UPDATE',
    'auto_update_verified': 'DESKTOP-UPDATE',
    'update_manifest_valid': 'DESKTOP-UPDATE',
    'desktop_cross': 'DESKTOP-CROSS',
    'cross_platform_consistency': 'DESKTOP-CROSS',
    'ipc_contract': 'IPC-CONTRACT',
    'platform_channel_tested': 'IPC-CONTRACT',
    'brainstorm_complete': 'BRAINSTORM-COMPLETE',
    'plan_atomic': 'PLAN-ATOMIC',
    'subagent_review': 'SUBAGENT-REVIEW',
    'playwright_e2e_pass': 'PLAYWRIGHT-E2E-PASS',
    'console_error_free': 'CONSOLE-ERROR-FREE',
    'loop_completion': 'LOOP-COMPLETION',
    'iteration_budget': 'ITERATION-BUDGET',
    'plan_persistence': 'PLAN-PERSISTENCE',
    'session_recovery': 'SESSION-RECOVERY',
    'all_code_scanned': 'GATE-012',
    'high_risk_identified': 'GATE-012',
    'vulns_classified': 'GATE-012',
    'critical_vulns_verified': 'GATE-012',
    'compliance_checked': 'GATE-012',
    'report_complete': 'DOC-COMPLETENESS',
    'risk_rated': 'GATE-012',
    'remediation_assigned': 'GATE-012',
    'scope_confirmed': 'GATE-001',
    'assets_identified': 'GATE-001',
    'scan_complete': 'GATE-012',
    'vulns_verified': 'GATE-012',
    'false_positives_removed': 'GATE-012',
    'critical_exploited': 'AI-PENTEST',
    'acceptance_criteria_confirmed': 'GATE-001',
    'test_coverage_complete': 'GATE-005',
    'plan_approved': 'GATE-003',
    'core_function_pass': 'TEST-PASS',
    'uat_pass': 'UX-ACCEPTANCE',
    'all_items_evaluated': 'GATE-013',
    'decision_made': 'GATE-013',
    'deliverables_ready': 'GATE-013',
    'bug_reproducible': 'GATE-005',
    'root_cause_found': 'GATE-005',
    'fix_complete': 'TEST-PASS',
    'no_security_issue': 'GATE-012',
    'no_new_defects': 'TEST-PASS',
    'deploy_success': 'GATE-013',
    'production_verified': 'GATE-014',
    'platform_requirements_clear': 'GATE-001',
    'tech_stack_confirmed': 'GATE-003',
    'platform_diffs_identified': 'GATE-001',
    'shared_layer_boundary_clear': 'GATE-003',
    'no_platform_coupling': 'GATE-003',
    'web_core_done': 'TEST-PASS',
    'desktop_core_done': 'TEST-PASS',
    'feature_alignment': 'TEST-PASS',
    'core_consistency_100': 'DESKTOP-CROSS',
    'web_acceptance_pass': 'UX-ACCEPTANCE',
    'desktop_acceptance_pass': 'UX-ACCEPTANCE',
    'no_blockers': 'GATE-013',
    'flutter_design_approved': 'DESIGN-REVIEW',
    'platform_matrix_defined': 'GATE-001',
    'plugin_compat_verified': 'TEST-PASS',
    'install_uninstall_pass': 'DESKTOP-BUILD',
    'distribution_available': 'GATE-013',
    'version_compliant': 'GATE-003',
    'changelog_updated': 'DOC-COMPLETENESS',
    'restoration_95': 'VISUAL-REGRESSION',
    'responsive_done': 'DESIGN-REVIEW',
    'animation_smooth': 'DESIGN-REVIEW',
    'task_completion_80': 'UX-ACCEPTANCE',
    'key_issues_fixed': 'TEST-PASS',
    'metrics_quantified': 'GATE-001',
    'scenarios_covered': 'GATE-005',
    'acceptance_confirmed': 'GATE-001',
    'env_ready': 'GATE-005',
    'scripts_valid': 'GATE-005',
    'execution_complete': 'TEST-PASS',
    'bottleneck_located': 'PERFORMANCE',
    'optimization_feasible': 'PERFORMANCE',
    'discovery_gaps_answered': 'BRAINSTORM-COMPLETE',
    'option_analysis_complete': 'BRAINSTORM-COMPLETE',
    'design_document_created': 'BRAINSTORM-COMPLETE',
    'design_reflected': 'BRAINSTORM-COMPLETE',
    'design_committed': 'BRAINSTORM-COMPLETE',
    'transition_complete': 'BRAINSTORM-COMPLETE',
    'dag_no_cycle': 'PLAN-ATOMIC',
    'agents_dispatched': 'SUBAGENT-REVIEW',
    'review_summary_complete': 'GATE-009',
    'rework_complete': 'TEST-PASS',
    'target_classified': 'GATE-001',
    'page_loaded': 'GATE-011',
    'elements_discovered': 'GATE-011',
    'actions_executed': 'TEST-PASS',
    'invest_check': 'GATE-001',
    'acceptance_criteria_defined': 'GATE-001',
    'solid_check': 'GATE-003',
    'interface_defined': 'GATE-004',
    'coverage_all_stories': 'GATE-005',
    'automation_ready': 'GATE-006',
    'all_tests_pass': 'TEST-PASS',
    'no_p0_p1_security': 'GATE-012',
    'coverage_met': 'GATE-005',
    'acceptance_criteria_pass': 'UX-ACCEPTANCE',
    'fixes_verified': 'TEST-PASS',
    'rca_completed': 'GATE-015',
    'build_success': 'DESKTOP-BUILD',
    'signing_pass': 'DESKTOP-SIGN',
    'update_verified': 'DESKTOP-UPDATE',
    'gate_001': 'GATE-001',
    'gate_002': 'GATE-002',
    'gate_003': 'GATE-003',
    'gate_004': 'GATE-004',
    'gate_005': 'GATE-005',
    'gate_006': 'GATE-006',
    'gate_007': 'GATE-007',
    'gate_009': 'GATE-009',
    'gate_011': 'GATE-011',
    'gate_012': 'GATE-012',
    'gate_013': 'GATE-013',
    'gate_014': 'GATE-014',
    'gate_015': 'GATE-015',
}

SECURITY_AUDIT_PHASES = [
    {'id': 'phase-1', 'name': '审计规划', 'order': 1, 'optional': False,
     'trigger_condition': '用户请求安全审计或定期安全检查',
     'agents': {'primary': ['security-auditor'], 'supporting': []},
     'inputs': [{'name': '审计范围定义', 'type': 'document', 'required': True},
                {'name': '系统架构文档', 'type': 'document', 'required': True}],
     'outputs': [{'name': '审计计划书', 'type': 'document', 'validation': '审计范围和重点明确'}],
     'quality_gates': [{'gate_id': 'GATE-001', 'blocking': True, 'pass_criteria': '审计范围和重点明确'}],
     'timeout_minutes': 60, 'retry': {'max_attempts': 2, 'backoff': 'fixed'}},
    {'id': 'phase-2', 'name': '代码安全审查', 'order': 2, 'optional': False,
     'trigger_condition': '审计规划完成',
     'agents': {'primary': ['security-auditor', 'code-reviewer'], 'supporting': []},
     'inputs': [{'name': '审计计划书', 'type': 'document', 'required': True, 'source_phase': 'phase-1'}],
     'outputs': [{'name': '代码安全审查报告', 'type': 'document', 'validation': '高风险代码已识别'}],
     'quality_gates': [{'gate_id': 'GATE-012', 'blocking': True, 'pass_criteria': '代码安全审查完成'}],
     'timeout_minutes': 120, 'retry': {'max_attempts': 2, 'backoff': 'fixed'}},
    {'id': 'phase-3', 'name': '漏洞扫描', 'order': 3, 'optional': False,
     'trigger_condition': '代码安全审查完成',
     'agents': {'primary': ['security-auditor'], 'supporting': []},
     'inputs': [{'name': '代码安全审查报告', 'type': 'document', 'required': True, 'source_phase': 'phase-2'}],
     'outputs': [{'name': '漏洞扫描报告', 'type': 'document', 'validation': '漏洞已分类和评级'}],
     'quality_gates': [{'gate_id': 'GATE-012', 'blocking': True, 'pass_criteria': '漏洞扫描完成且已分类'}],
     'timeout_minutes': 90, 'retry': {'max_attempts': 2, 'backoff': 'fixed'}},
    {'id': 'phase-4', 'name': '渗透测试', 'order': 4, 'optional': False,
     'trigger_condition': '漏洞扫描完成',
     'agents': {'primary': ['penetration-tester', 'security-auditor'], 'supporting': []},
     'inputs': [{'name': '漏洞扫描报告', 'type': 'document', 'required': True, 'source_phase': 'phase-3'}],
     'outputs': [{'name': '渗透测试报告', 'type': 'document', 'validation': '关键漏洞已验证'}],
     'quality_gates': [{'gate_id': 'AI-PENTEST', 'blocking': True, 'pass_criteria': '渗透测试完成'}],
     'timeout_minutes': 120, 'retry': {'max_attempts': 2, 'backoff': 'fixed'}},
    {'id': 'phase-5', 'name': '合规检查', 'order': 5, 'optional': False,
     'trigger_condition': '渗透测试完成',
     'agents': {'primary': ['compliance-officer', 'security-auditor'], 'supporting': []},
     'inputs': [{'name': '渗透测试报告', 'type': 'document', 'required': True, 'source_phase': 'phase-4'}],
     'outputs': [{'name': '合规检查报告', 'type': 'document', 'validation': '合规状态已评估'}],
     'quality_gates': [{'gate_id': 'GATE-012', 'blocking': True, 'pass_criteria': '合规检查完成'}],
     'timeout_minutes': 90, 'retry': {'max_attempts': 2, 'backoff': 'fixed'}},
    {'id': 'phase-6', 'name': '报告与整改', 'order': 6, 'optional': False,
     'trigger_condition': '合规检查完成',
     'agents': {'primary': ['security-auditor', 'compliance-officer'], 'supporting': []},
     'inputs': [{'name': '合规检查报告', 'type': 'document', 'required': True, 'source_phase': 'phase-5'}],
     'outputs': [{'name': '安全审计总报告', 'type': 'document', 'validation': '报告完整且整改建议明确'},
                 {'name': '整改跟踪清单', 'type': 'document', 'validation': '整改项已分配责任人'}],
     'quality_gates': [{'gate_id': 'DOC-COMPLETENESS', 'blocking': True, 'pass_criteria': '审计报告完整'},
                       {'gate_id': 'GATE-012', 'blocking': True, 'pass_criteria': '无P0/P1安全问题'}],
     'timeout_minutes': 60, 'retry': {'max_attempts': 2, 'backoff': 'fixed'}},
]

ACCEPTANCE_PHASES = [
    {'id': 'phase-1', 'name': '验收准备', 'order': 1, 'optional': False,
     'trigger_condition': '开发完成且通过验证阶段',
     'agents': {'primary': ['product-manager', 'test-architect'], 'supporting': ['e2e-tester', 'security-auditor', 'performance-tester', 'documentation-engineer', 'desktop-developer', 'build-release-engineer']},
     'inputs': [{'name': '验证通过的产物', 'type': 'document', 'required': True},
                {'name': '用户故事和验收标准', 'type': 'document', 'required': True}],
     'outputs': [{'name': '验收计划', 'type': 'document', 'validation': '验收范围和标准明确'}],
     'quality_gates': [{'gate_id': 'GATE-001', 'blocking': True, 'pass_criteria': '验收标准确认'},
                       {'gate_id': 'GATE-005', 'blocking': True, 'pass_criteria': '测试覆盖完整'}],
     'timeout_minutes': 60, 'retry': {'max_attempts': 2, 'backoff': 'fixed'}},
    {'id': 'phase-2', 'name': '功能验收', 'order': 2, 'optional': False,
     'trigger_condition': '验收准备完成',
     'agents': {'primary': ['e2e-tester', 'product-manager'], 'supporting': []},
     'inputs': [{'name': '验收计划', 'type': 'document', 'required': True, 'source_phase': 'phase-1'}],
     'outputs': [{'name': '功能验收报告', 'type': 'document', 'validation': '核心功能通过'}],
     'quality_gates': [{'gate_id': 'TEST-PASS', 'blocking': True, 'pass_criteria': '核心功能验收通过'},
                       {'gate_id': 'GATE-012', 'blocking': True, 'pass_criteria': '无P0/P1缺陷'}],
     'timeout_minutes': 120, 'retry': {'max_attempts': 2, 'backoff': 'fixed'}},
    {'id': 'phase-3', 'name': '非功能验收', 'order': 3, 'optional': False,
     'trigger_condition': '功能验收完成',
     'agents': {'primary': ['performance-tester', 'security-auditor'], 'supporting': []},
     'inputs': [{'name': '功能验收报告', 'type': 'document', 'required': True, 'source_phase': 'phase-2'}],
     'outputs': [{'name': '性能验收报告', 'type': 'document'}, {'name': '安全验收报告', 'type': 'document'}],
     'quality_gates': [{'gate_id': 'PERFORMANCE', 'blocking': True, 'pass_criteria': '性能达标'},
                       {'gate_id': 'GATE-012', 'blocking': True, 'pass_criteria': '无高危漏洞'}],
     'timeout_minutes': 120, 'retry': {'max_attempts': 2, 'backoff': 'fixed'}},
    {'id': 'phase-3-5', 'name': '桌面安装验证', 'order': 4, 'optional': False,
     'trigger_condition': '非功能验收完成且项目包含桌面端',
     'agents': {'primary': ['desktop-developer', 'build-release-engineer'], 'supporting': []},
     'inputs': [{'name': '非功能验收报告', 'type': 'document', 'required': True, 'source_phase': 'phase-3'}],
     'outputs': [{'name': '桌面安装验证报告', 'type': 'document', 'validation': '安装卸载正常'}],
     'quality_gates': [{'gate_id': 'DESKTOP-BUILD', 'blocking': True, 'pass_criteria': '安装包构建成功'}],
     'timeout_minutes': 90, 'retry': {'max_attempts': 2, 'backoff': 'fixed'}},
    {'id': 'phase-3-6', 'name': '自动更新验证', 'order': 5, 'optional': False,
     'trigger_condition': '桌面安装验证完成',
     'agents': {'primary': ['build-release-engineer', 'desktop-developer'], 'supporting': []},
     'inputs': [{'name': '桌面安装验证报告', 'type': 'document', 'required': True, 'source_phase': 'phase-3-5'}],
     'outputs': [{'name': '自动更新验证报告', 'type': 'document', 'validation': '自动更新功能正常'}],
     'quality_gates': [{'gate_id': 'DESKTOP-UPDATE', 'blocking': True, 'pass_criteria': '自动更新验证通过'}],
     'timeout_minutes': 60, 'retry': {'max_attempts': 2, 'backoff': 'fixed'}},
    {'id': 'phase-3-7', 'name': '跨平台兼容性验证', 'order': 6, 'optional': False,
     'trigger_condition': '自动更新验证完成',
     'agents': {'primary': ['desktop-developer', 'e2e-tester'], 'supporting': []},
     'inputs': [{'name': '自动更新验证报告', 'type': 'document', 'required': True, 'source_phase': 'phase-3-6'}],
     'outputs': [{'name': '跨平台兼容性报告', 'type': 'document', 'validation': '三平台功能一致性>95%'}],
     'quality_gates': [{'gate_id': 'DESKTOP-CROSS', 'blocking': True, 'pass_criteria': '跨平台一致性达标'}],
     'timeout_minutes': 90, 'retry': {'max_attempts': 2, 'backoff': 'fixed'}},
    {'id': 'phase-4', 'name': '文档验收', 'order': 7, 'optional': False,
     'trigger_condition': '跨平台兼容性验证完成或跳过桌面端验证',
     'agents': {'primary': ['documentation-engineer', 'technical-writer'], 'supporting': []},
     'inputs': [{'name': '全部验收报告', 'type': 'document', 'required': True}],
     'outputs': [{'name': '文档验收报告', 'type': 'document', 'validation': '文档覆盖完整'}],
     'quality_gates': [{'gate_id': 'DOC-COMPLETENESS', 'blocking': True, 'pass_criteria': '文档覆盖完整'}],
     'timeout_minutes': 60, 'retry': {'max_attempts': 2, 'backoff': 'fixed'}},
    {'id': 'phase-5', 'name': '用户验收测试', 'order': 8, 'optional': False,
     'trigger_condition': '文档验收完成',
     'agents': {'primary': ['product-manager'], 'supporting': []},
     'inputs': [{'name': '文档验收报告', 'type': 'document', 'required': True, 'source_phase': 'phase-4'}],
     'outputs': [{'name': 'UAT报告', 'type': 'document', 'validation': '用户验收通过'}],
     'quality_gates': [{'gate_id': 'UX-ACCEPTANCE', 'blocking': True, 'pass_criteria': '用户验收测试通过'}],
     'timeout_minutes': 120, 'retry': {'max_attempts': 2, 'backoff': 'fixed'}},
    {'id': 'phase-6', 'name': '验收决策与交付', 'order': 9, 'optional': False,
     'trigger_condition': '用户验收测试完成',
     'agents': {'primary': ['product-manager', 'e2e-tester'], 'supporting': []},
     'inputs': [{'name': 'UAT报告', 'type': 'document', 'required': True, 'source_phase': 'phase-5'}],
     'outputs': [{'name': '验收决策报告', 'type': 'document', 'validation': '验收决策已做出'},
                 {'name': '交付清单', 'type': 'document', 'validation': '交付物完整'}],
     'quality_gates': [{'gate_id': 'GATE-013', 'blocking': True, 'pass_criteria': '验收决策已做出且交付物就绪'}],
     'timeout_minutes': 60, 'retry': {'max_attempts': 2, 'backoff': 'fixed'}},
]

PERFORMANCE_TEST_PHASES = [
    {'id': 'phase-1', 'name': '性能需求分析', 'order': 1, 'optional': False,
     'trigger_condition': '用户请求性能测试或开发阶段完成',
     'agents': {'primary': ['performance-tester', 'system-architect'], 'supporting': []},
     'inputs': [{'name': '系统架构文档', 'type': 'document', 'required': True},
                {'name': '性能需求', 'type': 'document', 'required': True}],
     'outputs': [{'name': '性能测试计划', 'type': 'document', 'validation': '性能指标和场景明确'}],
     'quality_gates': [{'gate_id': 'GATE-001', 'blocking': True, 'pass_criteria': '性能指标量化'},
                       {'gate_id': 'GATE-005', 'blocking': True, 'pass_criteria': '测试场景覆盖'}],
     'timeout_minutes': 60, 'retry': {'max_attempts': 2, 'backoff': 'fixed'}},
    {'id': 'phase-2', 'name': '测试环境准备', 'order': 2, 'optional': False,
     'trigger_condition': '性能需求分析完成',
     'agents': {'primary': ['devops-engineer', 'performance-tester'], 'supporting': []},
     'inputs': [{'name': '性能测试计划', 'type': 'document', 'required': True, 'source_phase': 'phase-1'}],
     'outputs': [{'name': '环境就绪报告', 'type': 'document', 'validation': '测试环境就绪'}],
     'quality_gates': [{'gate_id': 'GATE-005', 'blocking': True, 'pass_criteria': '环境就绪且脚本有效'}],
     'timeout_minutes': 90, 'retry': {'max_attempts': 2, 'backoff': 'fixed'}},
    {'id': 'phase-3', 'name': '测试脚本开发', 'order': 3, 'optional': False,
     'trigger_condition': '测试环境准备完成',
     'agents': {'primary': ['performance-tester'], 'supporting': []},
     'inputs': [{'name': '环境就绪报告', 'type': 'document', 'required': True, 'source_phase': 'phase-2'}],
     'outputs': [{'name': '测试脚本', 'type': 'code', 'validation': '脚本验证通过'}],
     'quality_gates': [{'gate_id': 'GATE-005', 'blocking': True, 'pass_criteria': '脚本验证通过'}],
     'timeout_minutes': 120, 'retry': {'max_attempts': 2, 'backoff': 'fixed'}},
    {'id': 'phase-4', 'name': '性能测试执行', 'order': 4, 'optional': False,
     'trigger_condition': '测试脚本开发完成',
     'agents': {'primary': ['performance-tester', 'devops-engineer'], 'supporting': []},
     'inputs': [{'name': '测试脚本', 'type': 'code', 'required': True, 'source_phase': 'phase-3'}],
     'outputs': [{'name': '性能测试原始数据', 'type': 'document', 'validation': '测试执行完成'}],
     'quality_gates': [{'gate_id': 'TEST-PASS', 'blocking': True, 'pass_criteria': '测试执行完成'}],
     'timeout_minutes': 180, 'retry': {'max_attempts': 2, 'backoff': 'fixed'}},
    {'id': 'phase-5', 'name': '性能分析与调优', 'order': 5, 'optional': False,
     'trigger_condition': '性能测试执行完成',
     'agents': {'primary': ['system-architect', 'performance-tester'], 'supporting': []},
     'inputs': [{'name': '性能测试原始数据', 'type': 'document', 'required': True, 'source_phase': 'phase-4'}],
     'outputs': [{'name': '性能分析报告', 'type': 'document', 'validation': '瓶颈已定位'},
                 {'name': '调优建议', 'type': 'document', 'validation': '优化方案可行'}],
     'quality_gates': [{'gate_id': 'PERFORMANCE', 'blocking': True, 'pass_criteria': '瓶颈已定位且优化方案可行'}],
     'timeout_minutes': 120, 'retry': {'max_attempts': 2, 'backoff': 'fixed'}},
    {'id': 'phase-6', 'name': '优化验证与报告', 'order': 6, 'optional': False,
     'trigger_condition': '性能分析与调优完成',
     'agents': {'primary': ['performance-tester', 'system-architect'], 'supporting': []},
     'inputs': [{'name': '性能分析报告', 'type': 'document', 'required': True, 'source_phase': 'phase-5'}],
     'outputs': [{'name': '最终性能测试报告', 'type': 'document', 'validation': '性能基线达标'},
                 {'name': '性能回归测试套件', 'type': 'code', 'validation': '回归测试可执行'}],
     'quality_gates': [{'gate_id': 'PERFORMANCE', 'blocking': True, 'pass_criteria': '性能基线达标'},
                       {'gate_id': 'DOC-COMPLETENESS', 'blocking': True, 'pass_criteria': '报告完整'}],
     'timeout_minutes': 90, 'retry': {'max_attempts': 2, 'backoff': 'fixed'}},
]

CUSTOM_PHASES = {
    'security-audit': SECURITY_AUDIT_PHASES,
    'acceptance': ACCEPTANCE_PHASES,
    'performance-test': PERFORMANCE_TEST_PHASES,
}

CUSTOM_AGENT_MATRIX = {
    'security-audit': {
        'security-auditor': {'phases': ['phase-1', 'phase-2', 'phase-3', 'phase-4', 'phase-5', 'phase-6'], 'role': 'primary', 'max_parallel_instances': 1},
        'code-reviewer': {'phases': ['phase-2'], 'role': 'supporting', 'max_parallel_instances': 1},
        'penetration-tester': {'phases': ['phase-4'], 'role': 'primary', 'max_parallel_instances': 1},
        'compliance-officer': {'phases': ['phase-5', 'phase-6'], 'role': 'primary', 'max_parallel_instances': 1},
    },
    'acceptance': {
        'product-manager': {'phases': ['phase-1', 'phase-2', 'phase-5', 'phase-6'], 'role': 'primary', 'max_parallel_instances': 1},
        'test-architect': {'phases': ['phase-1'], 'role': 'primary', 'max_parallel_instances': 1},
        'e2e-tester': {'phases': ['phase-2', 'phase-3-7', 'phase-6'], 'role': 'primary', 'max_parallel_instances': 1},
        'performance-tester': {'phases': ['phase-3'], 'role': 'primary', 'max_parallel_instances': 1},
        'security-auditor': {'phases': ['phase-3'], 'role': 'primary', 'max_parallel_instances': 1},
        'desktop-developer': {'phases': ['phase-3-5', 'phase-3-6', 'phase-3-7'], 'role': 'primary', 'max_parallel_instances': 1},
        'build-release-engineer': {'phases': ['phase-3-5', 'phase-3-6'], 'role': 'primary', 'max_parallel_instances': 1},
        'documentation-engineer': {'phases': ['phase-4'], 'role': 'primary', 'max_parallel_instances': 1},
        'technical-writer': {'phases': ['phase-4'], 'role': 'primary', 'max_parallel_instances': 1},
    },
    'performance-test': {
        'performance-tester': {'phases': ['phase-1', 'phase-2', 'phase-3', 'phase-4', 'phase-5', 'phase-6'], 'role': 'primary', 'max_parallel_instances': 1},
        'system-architect': {'phases': ['phase-1', 'phase-5', 'phase-6'], 'role': 'primary', 'max_parallel_instances': 1},
        'devops-engineer': {'phases': ['phase-2', 'phase-4'], 'role': 'primary', 'max_parallel_instances': 1},
    },
}

def fix_quality_gates(phases):
    changed = False
    for p in phases:
        new_gates = []
        for g in p.get('quality_gates', []):
            old_id = g.get('gate_id', '')
            if old_id in GATE_MAP:
                g['gate_id'] = GATE_MAP[old_id]
                changed = True
            new_gates.append(g)
        p['quality_gates'] = new_gates
    return changed

def fix_trigger_conditions(phases):
    changed = False
    for i, p in enumerate(phases):
        if 'trigger_condition' not in p or not p['trigger_condition']:
            if i == 0:
                p['trigger_condition'] = '工作流启动'
            else:
                prev_name = phases[i-1].get('name', '上一阶段')
                p['trigger_condition'] = f'{prev_name}完成'
            changed = True
    return changed

def fix_from_yaml_source(f, md_path, yaml_path, content, m):
    with open(yaml_path, 'r', encoding='utf-8') as fh:
        yaml_data = yaml.safe_load(fh)

    body = content[m.end():]
    old_fm_text = m.group(1)

    try:
        old_data = yaml.safe_load(old_fm_text)
        has_encoding_issue = False
    except:
        has_encoding_issue = True

    file_changes = []

    if has_encoding_issue:
        new_fm_text = yaml.dump(yaml_data, allow_unicode=True, default_flow_style=False, sort_keys=False)
        new_content = '---\n' + new_fm_text + '---\n' + body
        with open(md_path, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(new_content)
        file_changes.append('Replaced corrupted frontmatter with content from .yaml file')
    else:
        needs_update = False
        old_meta = old_data.get('metadata', {})
        yaml_meta = yaml_data.get('metadata', {})
        for key in ['name','version','description','platform','min_agents','max_agents']:
            if key not in old_meta:
                file_changes.append(f'Added missing metadata.{key}')
                needs_update = True
            elif old_meta.get(key) != yaml_meta.get(key):
                file_changes.append(f'Updated metadata.{key}: {old_meta.get(key)} -> {yaml_meta.get(key)}')
                needs_update = True

        old_phases = old_data.get('phases', [])
        yaml_phases = yaml_data.get('phases', [])
        if len(old_phases) != len(yaml_phases):
            file_changes.append(f'Phase count: {len(old_phases)} -> {len(yaml_phases)}')
            needs_update = True

        old_eh = old_data.get('exception_handling', {})
        yaml_eh = yaml_data.get('exception_handling', {})
        for key in ['phase_failure','agent_unavailable','quality_gate_blocked']:
            if key not in old_eh:
                file_changes.append(f'Added missing exception_handling.{key}')
                needs_update = True

        if needs_update:
            new_fm_text = yaml.dump(yaml_data, allow_unicode=True, default_flow_style=False, sort_keys=False)
            new_content = '---\n' + new_fm_text + '---\n' + body
            with open(md_path, 'w', encoding='utf-8', newline='\n') as fh:
                fh.write(new_content)

    return file_changes

changes_log = {}

for f in files:
    md_path = os.path.join(base, f + '.md')
    yaml_path = os.path.join(yaml_base, f + '.yaml')

    with open(md_path, 'r', encoding='utf-8', errors='replace') as fh:
        content = fh.read()
    m = re.match(r'^---\r?\n(.*?)\r?\n---', content, re.DOTALL)
    if not m:
        print(f'{f}: NO FRONTMATTER - SKIP')
        continue

    body = content[m.end():]

    try:
        data = yaml.safe_load(m.group(1))
    except Exception as e:
        if os.path.exists(yaml_path):
            file_changes = fix_from_yaml_source(f, md_path, yaml_path, content, m)
            if file_changes:
                changes_log[f] = file_changes
                print(f'{f}: FIXED from yaml source')
                for c in file_changes:
                    print(f'  - {c}')
            continue
        print(f'{f}: YAML PARSE ERROR: {e}')
        continue

    file_changes = []

    if f in CUSTOM_PHASES:
        data['phases'] = CUSTOM_PHASES[f]
        file_changes.append(f'Reconstructed phases to match body ({len(CUSTOM_PHASES[f])} phases)')

    if f in CUSTOM_AGENT_MATRIX:
        data['agent_matrix'] = CUSTOM_AGENT_MATRIX[f]
        file_changes.append('Reconstructed agent_matrix to match phases')

    if fix_quality_gates(data.get('phases', [])):
        file_changes.append('Mapped quality_gates to standard IDs')

    if fix_trigger_conditions(data.get('phases', [])):
        file_changes.append('Added missing trigger_conditions')

    meta = data.get('metadata', {})
    for key in ['name','version','description','platform','min_agents','max_agents']:
        if key not in meta:
            file_changes.append(f'Added missing metadata.{key}')

    eh = data.get('exception_handling', {})
    for key in ['phase_failure','agent_unavailable','quality_gate_blocked']:
        if key not in eh:
            file_changes.append(f'Added missing exception_handling.{key}')

    if file_changes:
        new_fm = yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
        new_content = '---\n' + new_fm + '---\n' + body
        with open(md_path, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(new_content)
        changes_log[f] = file_changes
        print(f'{f}: FIXED')
        for c in file_changes:
            print(f'  - {c}')
    else:
        print(f'{f}: OK')

print()
print('=== SUMMARY ===')
print(f'Files with changes: {len(changes_log)}')
for f, changes in changes_log.items():
    print(f'  {f}:')
    for c in changes:
        print(f'    - {c}')
