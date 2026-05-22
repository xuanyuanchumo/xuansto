#!/usr/bin/env python3
import sys
from pathlib import Path

skillscripts_dir = Path(__file__).parent.parent / "skillscripts"
print(f"Skillscripts dir: {skillscripts_dir}")
print(f"Exists: {skillscripts_dir.exists()}")

sys.path.insert(0, str(skillscripts_dir))
print(f"Python path: {sys.path[0]}")

print("\nListing skillscripts directory:")
for item in skillscripts_dir.iterdir():
    print(f"  - {item.name}")

print("\nTrying to import using importlib...")
import importlib.util

spec = importlib.util.spec_from_file_location(
    "core.cross_project_knowledge_sharing",
    skillscripts_dir / "core" / "cross_project_knowledge_sharing.py"
)
print(f"Spec: {spec}")

if spec and spec.loader:
    module = importlib.util.module_from_spec(spec)
    sys.modules["core.cross_project_knowledge_sharing"] = module
    try:
        spec.loader.exec_module(module)
        print("✅ Module loaded successfully!")
        print(f"CrossProjectKnowledgeSharing: {hasattr(module, 'CrossProjectKnowledgeSharing')}")
    except Exception as e:
        print(f"❌ Failed to load module: {e}")
        import traceback
        traceback.print_exc()
