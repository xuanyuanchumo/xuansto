#!/usr/bin/env python3
import sys
from pathlib import Path

skillscripts_dir = Path(__file__).parent.parent / "skillscripts"
print(f"Skillscripts dir: {skillscripts_dir}")

sys.path.insert(0, str(skillscripts_dir.parent))
print(f"Python path: {sys.path[0]}")

print("\nTrying to import skillscripts package...")
try:
    import skillscripts
    print(f"✅ skillscripts imported from: {skillscripts.__file__}")
except ImportError as e:
    print(f"❌ Failed to import skillscripts: {e}")

print("\nTrying to import core package...")
try:
    from skillscripts import core
    print(f"✅ core imported from: {core.__file__}")
except ImportError as e:
    print(f"❌ Failed to import core: {e}")

print("\nTrying to import CrossProjectKnowledgeSharing...")
try:
    from skillscripts.core.cross_project_knowledge_sharing import CrossProjectKnowledgeSharing
    print("✅ CrossProjectKnowledgeSharing imported successfully!")
except ImportError as e:
    print(f"❌ Failed to import CrossProjectKnowledgeSharing: {e}")
    import traceback
    traceback.print_exc()
