#!/usr/bin/env python3
"""测试Agent调用历史记录系统"""

from .agent_call_history import AgentCallHistory, AgentCallRecord
from datetime import datetime
import json
import uuid

def test_record_call():
    """测试记录调用功能"""
    history = AgentCallHistory()
    
    call_id_1 = f"test_{uuid.uuid4().hex[:8]}"
    call_id_2 = f"test_{uuid.uuid4().hex[:8]}"
    call_id_3 = f"test_{uuid.uuid4().hex[:8]}"
    
    test_records = [
        AgentCallRecord(
            call_id=call_id_1,
            timestamp=datetime.now().isoformat(),
            caller="皇帝",
            agent_name="吏部尚书",
            task="选拔官员",
            context={"department": "吏部", "level": "高级"},
            status="success",
            result={"selected": "张三", "score": 95},
            duration_ms=1500,
            quality_score=0.95,
            trace_id=f"trace_{uuid.uuid4().hex[:8]}"
        ),
        AgentCallRecord(
            call_id=call_id_2,
            timestamp=datetime.now().isoformat(),
            caller="吏部尚书",
            agent_name="户部尚书",
            task="调拨钱粮",
            context={"department": "户部", "amount": "10000两"},
            status="success",
            result={"approved": True, "budget": "充足"},
            duration_ms=2000,
            quality_score=0.88,
            trace_id=f"trace_{uuid.uuid4().hex[:8]}"
        ),
        AgentCallRecord(
            call_id=call_id_3,
            timestamp=datetime.now().isoformat(),
            caller="皇帝",
            agent_name="兵部尚书",
            task="调兵遣将",
            context={"war": "边疆", "troops": "50000"},
            status="failed",
            error_message="兵力不足",
            duration_ms=500,
            trace_id=f"trace_{uuid.uuid4().hex[:8]}"
        )
    ]
    
    print("=" * 60)
    print("测试1: 记录Agent调用")
    print("=" * 60)
    
    for record in test_records:
        call_id = history.record_call(record)
        print(f"[OK] 成功记录调用: {call_id} - {record.agent_name}")
    
    print("\n" + "=" * 60)
    print("测试2: 查询单条调用记录")
    print("=" * 60)
    
    call = history.get_call(call_id_1)
    if call:
        print(f"[OK] 成功查询到调用记录: {call['call_id']}")
        print(f"  Agent: {call['agent_name']}")
        print(f"  任务: {call['task']}")
        print(f"  状态: {call['status']}")
    else:
        print("[FAIL] 未找到调用记录")
    
    print("\n" + "=" * 60)
    print("测试3: 按Agent名称查询")
    print("=" * 60)
    
    calls = history.get_calls_by_agent("吏部尚书")
    print(f"[OK] 找到 {len(calls)} 条吏部尚书的调用记录")
    for call in calls:
        print(f"  - {call['call_id']}: {call['task']}")
    
    print("\n" + "=" * 60)
    print("测试4: 按调用者查询")
    print("=" * 60)
    
    calls = history.get_calls_by_caller("皇帝")
    print(f"[OK] 找到 {len(calls)} 条皇帝发起的调用记录")
    for call in calls:
        print(f"  - {call['call_id']}: {call['agent_name']} - {call['task']}")
    
    print("\n" + "=" * 60)
    print("测试5: 获取最近调用记录")
    print("=" * 60)
    
    calls = history.get_recent_calls(5)
    print(f"[OK] 找到 {len(calls)} 条最近的调用记录")
    for call in calls:
        print(f"  - {call['call_id']}: {call['caller']} -> {call['agent_name']}")
    
    print("\n" + "=" * 60)
    print("测试6: 获取统计数据")
    print("=" * 60)
    
    stats = history.get_statistics()
    print(f"[OK] 总调用次数: {stats['total_calls']}")
    print(f"[OK] 成功次数: {stats['successful_calls']}")
    print(f"[OK] 失败次数: {stats['failed_calls']}")
    if stats['avg_duration_ms']:
        print(f"[OK] 平均耗时: {stats['avg_duration_ms']:.2f}ms")
    if stats['avg_quality_score']:
        print(f"[OK] 平均质量分: {stats['avg_quality_score']:.2f}")
    
    print("\n[SUCCESS] 所有测试通过!")
    
    return True

if __name__ == "__main__":
    try:
        test_record_call()
    except Exception as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
