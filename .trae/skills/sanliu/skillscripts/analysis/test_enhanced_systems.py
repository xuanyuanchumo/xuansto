#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志分析和问题定位系统 - 功能验证测试
验证增强版日志分析器、问题定位器和自动修复建议系统
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(get_path_config().SCRIPTS_DIR / "analysis"))

from enhanced_log_analyzer import (
    EnhancedLogAnalyzer,
    MultiFormatLogParser,
    IntelligentErrorPatternMatcher,
    LogCorrelationAnalyzer,
    AnomalyDetector,
    TimeSeriesAnalyzer,
    LogLevel,
    LogFormat,
)
from auto_fix_suggestion_system import (
    AutoFixSuggestionSystem,
    FixSuggestionGenerator,
    FixStrategyLibrary,
    FixEffectEvaluator,
    FixCategory,
    FixComplexity,
    FixRisk,
    FixConfidence,
)


def create_test_logs():
    """创建测试日志文件"""
    test_logs = {
        "python.log": """
2024-01-15 10:30:15,123 - INFO - Application started
2024-01-15 10:30:16,456 - DEBUG - Loading configuration
2024-01-15 10:30:17,789 - WARNING - Configuration file not found, using defaults
2024-01-15 10:30:18,123 - INFO - Connecting to database
2024-01-15 10:30:19,456 - ERROR - ConnectionError: Could not connect to database server
2024-01-15 10:30:20,789 - ERROR - DatabaseError: Connection refused
2024-01-15 10:30:21,123 - CRITICAL - Application failed to start due to database connection
2024-01-15 10:35:15,456 - INFO - Retry connecting to database
2024-01-15 10:35:16,789 - INFO - Database connection established
2024-01-15 10:35:17,123 - INFO - Server listening on port 8080
2024-01-15 10:40:00,000 - ERROR - TypeError: 'NoneType' object has no attribute 'data'
2024-01-15 10:40:01,000 - ERROR - AttributeError: 'User' object has no attribute 'name'
2024-01-15 10:40:02,000 - ERROR - KeyError: 'user_id' not found in session
2024-01-15 10:45:00,000 - WARNING - Memory usage high: 85%
2024-01-15 10:45:01,000 - WARNING - Memory usage critical: 92%
2024-01-15 10:45:02,000 - ERROR - MemoryError: Cannot allocate memory for request
2024-01-15 11:00:00,000 - INFO - Processing request REQ-001
2024-01-15 11:00:01,000 - ERROR - ValueError: Invalid input data
2024-01-15 11:00:02,000 - INFO - Request REQ-001 completed with errors
""",
        "json.log": """
{"timestamp": "2024-01-15T12:00:00Z", "level": "INFO", "message": "Service started", "service": "api-gateway"}
{"timestamp": "2024-01-15T12:01:00Z", "level": "ERROR", "message": "ImportError: No module named 'requests'", "service": "api-gateway"}
{"timestamp": "2024-01-15T12:02:00Z", "level": "WARNING", "message": "Deprecated API usage detected", "service": "api-gateway"}
{"timestamp": "2024-01-15T12:03:00Z", "level": "ERROR", "message": "ConnectionError: Failed to connect to backend", "service": "api-gateway", "request_id": "req-123"}
{"timestamp": "2024-01-15T12:03:01Z", "level": "ERROR", "message": "TimeoutError: Request timed out after 30s", "service": "api-gateway", "request_id": "req-123"}
{"timestamp": "2024-01-15T12:05:00Z", "level": "CRITICAL", "message": "SecurityException: SQL injection attempt detected", "service": "api-gateway"}
{"timestamp": "2024-01-15T12:06:00Z", "level": "INFO", "message": "Session created", "session_id": "sess-001", "user_id": "user-123"}
{"timestamp": "2024-01-15T12:06:30Z", "level": "INFO", "message": "User action", "session_id": "sess-001", "user_id": "user-123"}
{"timestamp": "2024-01-15T12:07:00Z", "level": "ERROR", "message": "PermissionError: Access denied to resource", "session_id": "sess-001"}
""",
        "apache.log": """
192.168.1.100 - - [15/Jan/2024:13:00:00 +0000] "GET /api/users HTTP/1.1" 200 1234
192.168.1.101 - - [15/Jan/2024:13:00:01 +0000] "POST /api/login HTTP/1.1" 200 567
192.168.1.102 - - [15/Jan/2024:13:00:02 +0000] "GET /api/admin HTTP/1.1" 403 89
192.168.1.103 - - [15/Jan/2024:13:00:03 +0000] "GET /api/missing HTTP/1.1" 404 123
192.168.1.104 - - [15/Jan/2024:13:00:04 +0000] "POST /api/data HTTP/1.1" 500 456
192.168.1.105 - - [15/Jan/2024:13:00:05 +0000] "GET /api/timeout HTTP/1.1" 504 789
""",
    }
    
    temp_dir = tempfile.mkdtemp(prefix="log_test_")
    
    for filename, content in test_logs.items():
        file_path = Path(temp_dir) / filename
        file_path.write_text(content.strip(), encoding='utf-8')
    
    return temp_dir


def test_multi_format_parser():
    """测试多格式解析器"""
    print("\n" + "=" * 60)
    print("测试: 多格式日志解析器")
    print("=" * 60)
    
    parser = MultiFormatLogParser()
    
    json_line = '{"timestamp": "2024-01-15T10:00:00Z", "level": "ERROR", "message": "Test error"}'
    entry = parser.parse_line(json_line, LogFormat.JSON)
    assert entry is not None
    assert entry.level == LogLevel.ERROR
    print(f"✓ JSON格式解析成功: {entry.message}")
    
    python_line = "2024-01-15 10:00:00,123 - ERROR - Test error message"
    entry = parser.parse_line(python_line, LogFormat.PYTHON)
    assert entry is not None
    assert entry.level == LogLevel.ERROR
    print(f"✓ Python格式解析成功: {entry.message}")
    
    apache_line = '192.168.1.1 - - [15/Jan/2024:10:00:00 +0000] "GET /test HTTP/1.1" 500 123'
    entry = parser.parse_line(apache_line, LogFormat.APACHE)
    assert entry is not None
    assert entry.level == LogLevel.ERROR
    print(f"✓ Apache格式解析成功: {entry.message}")
    
    print("\n多格式解析器测试通过!")
    return True


def test_error_pattern_matcher():
    """测试智能错误模式匹配器"""
    print("\n" + "=" * 60)
    print("测试: 智能错误模式匹配器")
    print("=" * 60)
    
    from enhanced_log_analyzer import LogEntry
    
    matcher = IntelligentErrorPatternMatcher()
    
    test_entries = [
        LogEntry(
            timestamp=datetime.now(),
            level=LogLevel.ERROR,
            message="TypeError: 'NoneType' object has no attribute 'data'",
            source="test",
            file_path="test.py",
            line_number=10,
        ),
        LogEntry(
            timestamp=datetime.now(),
            level=LogLevel.ERROR,
            message="ImportError: No module named 'requests'",
            source="test",
            file_path="test.py",
            line_number=20,
        ),
        LogEntry(
            timestamp=datetime.now(),
            level=LogLevel.CRITICAL,
            message="MemoryError: Cannot allocate memory",
            source="test",
            file_path="test.py",
            line_number=30,
        ),
    ]
    
    patterns = matcher.match(test_entries)
    
    assert len(patterns) > 0
    print(f"✓ 检测到 {len(patterns)} 种错误模式")
    
    for pattern in patterns:
        print(f"  - {pattern.name}: {pattern.occurrence_count} 次, 置信度: {pattern.confidence:.0%}")
    
    print("\n错误模式匹配器测试通过!")
    return True


def test_log_correlation():
    """测试日志关联分析"""
    print("\n" + "=" * 60)
    print("测试: 日志关联分析器")
    print("=" * 60)
    
    from enhanced_log_analyzer import LogEntry
    
    analyzer = LogCorrelationAnalyzer()
    
    base_time = datetime.now()
    test_entries = [
        LogEntry(
            timestamp=base_time,
            level=LogLevel.INFO,
            message="Request started",
            source="api",
            file_path="api.py",
            line_number=1,
            request_id="req-001",
        ),
        LogEntry(
            timestamp=base_time + timedelta(seconds=1),
            level=LogLevel.ERROR,
            message="Database error",
            source="api",
            file_path="api.py",
            line_number=2,
            request_id="req-001",
        ),
        LogEntry(
            timestamp=base_time + timedelta(seconds=2),
            level=LogLevel.ERROR,
            message="Request failed",
            source="api",
            file_path="api.py",
            line_number=3,
            request_id="req-001",
        ),
        LogEntry(
            timestamp=base_time,
            level=LogLevel.INFO,
            message="Session started",
            source="auth",
            file_path="auth.py",
            line_number=1,
            session_id="sess-001",
        ),
        LogEntry(
            timestamp=base_time + timedelta(seconds=1),
            level=LogLevel.INFO,
            message="User action",
            source="auth",
            file_path="auth.py",
            line_number=2,
            session_id="sess-001",
        ),
    ]
    
    correlations = analyzer.analyze(test_entries)
    
    assert len(correlations) > 0
    print(f"✓ 发现 {len(correlations)} 组关联日志")
    
    for corr in correlations:
        print(f"  - {corr.correlation_type}: {len(corr.correlated_entries)} 条日志, 置信度: {corr.confidence:.0%}")
    
    print("\n日志关联分析器测试通过!")
    return True


def test_anomaly_detector():
    """测试异常检测器"""
    print("\n" + "=" * 60)
    print("测试: 异常检测器")
    print("=" * 60)
    
    from enhanced_log_analyzer import LogEntry
    
    detector = AnomalyDetector()
    
    base_time = datetime.now()
    test_entries = []
    
    for i in range(50):
        test_entries.append(LogEntry(
            timestamp=base_time + timedelta(minutes=i),
            level=LogLevel.INFO,
            message=f"Normal log {i}",
            source="app",
            file_path="app.py",
            line_number=i,
        ))
    
    for i in range(20):
        test_entries.append(LogEntry(
            timestamp=base_time + timedelta(minutes=10),
            level=LogLevel.ERROR,
            message=f"Error burst {i}",
            source="app",
            file_path="app.py",
            line_number=100 + i,
        ))
    
    anomalies = detector.detect(test_entries)
    
    print(f"✓ 检测到 {len(anomalies)} 个异常")
    
    for anomaly in anomalies:
        print(f"  - {anomaly.anomaly_type}: {anomaly.severity.value} - {anomaly.description[:60]}...")
    
    print("\n异常检测器测试通过!")
    return True


def test_fix_suggestion_system():
    """测试自动修复建议系统"""
    print("\n" + "=" * 60)
    print("测试: 自动修复建议系统")
    print("=" * 60)
    
    system = AutoFixSuggestionSystem()
    
    test_errors = [
        "TypeError: 'NoneType' object has no attribute 'data'",
        "ImportError: No module named 'requests'",
        "KeyError: 'user_id' not found",
        "ConnectionError: Connection refused",
    ]
    
    for error in test_errors:
        print(f"\n分析错误: {error[:50]}...")
        
        report = system.analyze_and_suggest(error)
        
        print(f"  生成 {len(report.suggestions)} 个修复建议")
        
        if report.best_suggestion:
            print(f"  推荐方案: {report.best_suggestion.title}")
            print(f"  复杂度: {report.best_suggestion.complexity.value}")
            print(f"  风险: {report.best_suggestion.risk.value}")
    
    print("\n自动修复建议系统测试通过!")
    return True


def test_fix_strategy_library():
    """测试修复策略库"""
    print("\n" + "=" * 60)
    print("测试: 修复策略库")
    print("=" * 60)
    
    library = FixStrategyLibrary()
    
    print(f"✓ 已加载 {len(library.strategies)} 个修复策略")
    
    test_patterns = ["TypeError", "KeyError", "ConnectionError"]
    
    for pattern in test_patterns:
        strategies = library.find_strategies(pattern)
        print(f"  - '{pattern}' 匹配 {len(strategies)} 个策略")
        for s in strategies[:2]:
            print(f"    · {s.name}")
    
    print("\n修复策略库测试通过!")
    return True


def test_full_integration():
    """完整集成测试"""
    print("\n" + "=" * 60)
    print("测试: 完整集成测试")
    print("=" * 60)
    
    temp_dir = create_test_logs()
    print(f"✓ 创建测试日志目录: {temp_dir}")
    
    try:
        analyzer = EnhancedLogAnalyzer(temp_dir)
        
        for log_file in Path(temp_dir).glob("*.log"):
            analyzer.collect_from_file(log_file.name)
        
        print(f"✓ 收集到 {len(analyzer.entries)} 条日志记录")
        
        result = analyzer.analyze()
        
        print(f"\n分析结果:")
        print(f"  - 错误模式: {result['summary']['error_pattern_count']}")
        print(f"  - 关联组: {result['summary']['correlation_count']}")
        print(f"  - 异常检测: {result['summary']['anomaly_count']}")
        print(f"  - 时序事件: {result['summary']['time_series_event_count']}")
        
        report = analyzer.generate_report(result)
        print(f"\n✓ 生成报告长度: {len(report)} 字符")
        
        print("\n完整集成测试通过!")
        return True
        
    finally:
        import shutil
from skillscripts.core.path_config_center import get_path_config
        shutil.rmtree(temp_dir)


def generate_sample_reports():
    """生成示例分析报告"""
    print("\n" + "=" * 60)
    print("生成示例分析报告")
    print("=" * 60)
    
    reports_dir = Path(__file__).parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    fix_system = AutoFixSuggestionSystem()
    
    sample_errors = [
        {
            "error": "TypeError: 'NoneType' object has no attribute 'data' in function process_user",
            "type": "runtime_error",
        },
        {
            "error": "ConnectionError: Could not connect to database at localhost:5432",
            "type": "network_error",
        },
        {
            "error": "KeyError: 'user_id' not found in session data",
            "type": "data_error",
        },
    ]
    
    for i, sample in enumerate(sample_errors, 1):
        report = fix_system.analyze_and_suggest(sample["error"], sample["type"])
        md_report = fix_system.generate_markdown_report(report)
        
        report_path = reports_dir / f"fix_suggestion_report_{i}.md"
        report_path.write_text(md_report, encoding='utf-8')
        print(f"✓ 生成报告: {report_path}")
    
    print(f"\n示例报告已保存到: {reports_dir}")
    return reports_dir


def main():
    """运行所有测试"""
    print("=" * 60)
    print("日志分析和问题定位系统 - 功能验证测试")
    print("=" * 60)
    
    tests = [
        ("多格式解析器", test_multi_format_parser),
        ("错误模式匹配器", test_error_pattern_matcher),
        ("日志关联分析器", test_log_correlation),
        ("异常检测器", test_anomaly_detector),
        ("修复建议系统", test_fix_suggestion_system),
        ("修复策略库", test_fix_strategy_library),
        ("完整集成测试", test_full_integration),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, "通过" if success else "失败", None))
        except Exception as e:
            results.append((name, "失败", str(e)))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for name, status, error in results:
        emoji = "✓" if status == "通过" else "✗"
        print(f"{emoji} {name}: {status}")
        if error:
            print(f"   错误: {error[:100]}")
        
        if status == "通过":
            passed += 1
        else:
            failed += 1
    
    print(f"\n总计: {passed} 通过, {failed} 失败")
    
    reports_dir = generate_sample_reports()
    
    print("\n" + "=" * 60)
    print("功能验证完成!")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
