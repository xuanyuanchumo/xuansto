"""
Agency Bridge 模块快速验证脚本
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """测试所有类导入"""
    print("=" * 60)
    print("🧪 模块导入测试")
    print("=" * 60)

    from agency_bridge import (
        AgentRegistry, AgentMetadata, RegistryStats,
        AgentRouter, RoutingRequest, RoutingResult,
        AgentOrchestrator, OrchestrationPhase, OrchestrationSession, PipelineStage,
        DepartmentMapper, DepartmentID, MappingEntry,
        AgentContextBuilder, AgentContext,
        AgentResultCollector, AgentResult, CollectedResult, ConflictResolutionStrategy,
    )

    print(f"✅ 所有 17 个公共类导入成功!")
    print(f"   OrchestrationPhase: {[p.value for p in OrchestrationPhase]}")
    print(f"   DepartmentID 总数: {len(DepartmentID)} (24司 + 8局)")
    print(f"   ConflictResolutionStrategy: {[s.value for s in ConflictResolutionStrategy]}")
    return True


def test_department_mapper():
    """测试部门映射器核心功能"""
    print("\n" + "=" * 60)
    print("🧪 部门映射器测试")
    print("=" * 60)

    from agency_bridge import DepartmentMapper, DepartmentID

    mapper = DepartmentMapper()
    coverage = mapper.validate_mapping_coverage()

    print(f"📊 映射覆盖率:")
    print(f"   总部门数: {coverage['total_departments']}")
    print(f"   已映射: {coverage['mapped_departments']} ({coverage['coverage_percentage']}%)")
    print(f"   覆盖Agents数: {coverage['unique_agents_covered']}")
    print(f"   总映射关系: {coverage['total_agent_mappings']}")
    print(f"   平均每部门: {coverage['avg_agents_per_department']} agents")

    # 测试查询
    test_deps = ["code_generation_si", "testing_bureau", "requirements_bureau"]
    print(f"\n📋 部门查询示例:")
    for dep_id in test_deps:
        agents = mapper.get_agents_for_department(dep_id)
        mode = mapper.get_collaboration_pattern(dep_id)
        print(f"   {dep_id}: {len(agents)} agents ({mode.value})")
        if agents:
            print(f"      → {agents[:3]}")

    # 测试反向查询
    print(f"\n🔄 反向查询示例:")
    for agent_id in ["engineering_senior_developer", "testing_evidence_collector"]:
        depts = mapper.get_department_for_agent(agent_id)
        print(f"   {agent_id}: {[d.value for d in depts]}")

    # 测试关联发现
    related = mapper.find_related_departments("code_generation_si", max_related=3)
    print(f"\n🔗 关联部门 (code_generation_si):")
    for dept, score in related:
        print(f"   {dept.value}: {score:.2f}")

    # 导出矩阵预览
    matrix_md = mapper.export_mapping_matrix()
    print(f"\n📄 映射矩阵长度: {len(matrix_md)} 字符")
    print(matrix_md[:400])

    return coverage["coverage_percentage"] == 100.0


def test_context_builder():
    """测试上下文构建器"""
    print("\n" + "=" * 60)
    print("🧪 上下文构建器测试")
    print("=" * 60)

    from agency_bridge import AgentContextBuilder

    builder = AgentContextBuilder()

    # 任务背景提取
    task_bg = builder.extract_task_background(
        "开发一个用户认证 REST API，使用 Python FastAPI 和 PostgreSQL，"
        "支持 JWT 和 OAuth2 双因素认证"
    )
    print(f"📝 任务背景提取结果:")
    print(f"   意图: {task_bg.get('intents')}")
    print(f"   技术栈: {task_bg.get('tech_stack')}")
    print(f"   语言: {task_bg.get('language')}")
    print(f"   框架: {task_bg.get('framework')}")
    print(f"   数据库: {task_bg.get('database')}")
    print(f"   复杂度: {task_bg.get('estimated_complexity')}")

    # 完整上下文构建
    full_ctx = builder.build_full_context(
        task_description="重构用户认证模块，添加双因素认证支持",
        file_extensions=[".py", ".md"],
    )
    print(f"\n🏗️ 完整上下文:")
    print(f"   项目信息项: {len(full_ctx.project_info)}")
    print(f"   相关文件: {len(full_ctx.relevant_files)}")
    print(f"   代码片段: {len(full_ctx.code_snippets)}")
    print(f"   约束条件: {list(full_ctx.constraints.keys())}")

    return True


def test_result_collector():
    """测试结果收集器"""
    print("\n" + "=" * 60)
    print("🧪 结果收集器测试")
    print("=" * 60)

    from agency_bridge import (
        AgentResultCollector, ConflictResolutionStrategy
    )
    from agency_bridge.agent_result_collector import ResultStatus

    collector = AgentResultCollector()

    # 收集多个结果
    r1 = collector.collect_result(
        agent_id="engineering_frontend_developer",
        output="完成了React组件的开发，使用了TypeScript和Hooks模式。组件支持响应式设计。",
        status=ResultStatus.SUCCESS,
        artifacts={"component.jsx": "// React component code..."},
        metrics={"quality_score": 8.5, "speed": 9.0},
    )
    print(f"✅ 结果1: {r1.agent_id} - {r1.status.value}")

    r2 = collector.collect_result(
        agent_id="design_ui_designer",
        output="建议使用更现代的设计系统，但要注意保持与现有品牌一致性。",
        status=ResultStatus.SUCCESS,
        artifacts={"design_spec.md": "# Design specifications..."},
        metrics={"quality_score": 7.8, "creativity": 9.2},
    )
    print(f"✅ 结果2: {r2.agent_id} - {r2.status.value}")

    r3 = collector.collect_result(
        agent_id="testing_evidence_collector",
        output="测试用例编写完成，覆盖了主要用户场景。但是边界情况还需要补充。",
        status=ResultStatus.PARTIAL,
        metrics={"coverage": 78.0},
    )
    print(f"✅ 结果3: {r3.agent_id} - {r3.status.value}")

    # 合并结果
    merged = collector.merge_results(r1, [r2, r3], ConflictResolutionStrategy.MERGE)
    print(f"\n📦 合并结果:")
    print(f"   Collection ID: {merged.collection_id}")
    print(f"   Strategy: {merged.resolution_strategy.value}")
    print(f"   Merged output length: {len(merged.merged_output)}")
    print(f"   Artifacts: {list(merged.merged_artifacts.keys())}")
    print(f"   Conflicts detected: {len(merged.conflicts_detected)}")

    if merged.conflicts_detected:
        for c in merged.conflicts_detected[:2]:
            print(f"   ⚠️  {c.get('type')}: {c.get('resolution')}")

    # 聚合指标
    metrics = merged.aggregated_metrics
    print(f"\n📊 聚合指标:")
    print(f"   Success rate: {metrics.get('success_rate')}")
    print(f"   Avg quality score: {metrics.get('quality_score_avg')}")
    print(f"   Total agents: {int(metrics.get('total_agents', 0))}")

    # 格式化输出预览
    formatted = collector.format_unified_output(merged, "markdown")
    print(f"\n📝 格式化输出 (前500字符):")
    print(formatted[:500])

    return True


def main():
    """运行所有测试"""
    print("\n" + "🚀" * 30)
    print(" Agency Bridge (AAB) 模块验证套件")
    print("🚀" * 30 + "\n")

    results = []

    try:
        results.append(("模块导入", test_imports()))
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        results.append(("模块导入", False))

    try:
        results.append(("部门映射器", test_department_mapper()))
    except Exception as e:
        print(f"❌ 部门映射器测试失败: {e}")
        results.append(("部门映射器", False))

    try:
        results.append(("上下文构建器", test_context_builder()))
    except Exception as e:
        print(f"❌ 上下文构建器测试失败: {e}")
        results.append(("上下文构建器", False))

    try:
        results.append(("结果收集器", test_result_collector()))
    except Exception as e:
        print(f"❌ 结果收集器测试失败: {e}")
        results.append(("结果收集器", False))

    # 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}  {name}")

    print(f"\n{'=' * 60}")
    print(f"总计: {passed}/{total} 测试通过")
    if passed == total:
        print("🎉 所有测试通过! agency_bridge 模块就绪!")
    else:
        print(f"⚠️  {total - passed} 个测试需要检查")
    print("=" * 60)


if __name__ == "__main__":
    main()
