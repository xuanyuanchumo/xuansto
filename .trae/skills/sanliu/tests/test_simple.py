#!/usr/bin/env python3
import sys
from pathlib import Path

SANLIU_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SANLIU_DIR))

try:
    from skillscripts.core.unified_script_entry import UnifiedScriptEntry
    
    print("创建UnifiedScriptEntry实例...")
    entry = UnifiedScriptEntry(base_path=SANLIU_DIR)
    
    print("实例创建成功！")
    print(f"已注册脚本数量: {len(entry.registry.scripts)}")
    
except Exception as e:
    import traceback
    print(f"错误: {e}")
    print("\n完整堆栈跟踪:")
    traceback.print_exc()
