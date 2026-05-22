#!/usr/bin/env python3
import sys
from pathlib import Path

skillscripts_dir = Path(__file__).parent.parent / "skillscripts"
print(f"Skillscripts dir: {skillscripts_dir}")
print(f"Exists: {skillscripts_dir.exists()}")

sys.path.insert(0, str(skillscripts_dir))
print(f"Python path: {sys.path[0]}")

print("\nTrying to import core module directly...")
try:
    import core
    print(f"✅ core module imported from: {core.__file__}")
except ImportError as e:
    print(f"❌ Failed to import core: {e}")

print("\nTrying to import cross_project_knowledge_sharing...")
try:
    from core import cross_project_knowledge_sharing
    print(f"✅ cross_project_knowledge_sharing imported")
    print(f"Module file: {cross_project_knowledge_sharing.__file__}")
except ImportError as e:
    print(f"❌ Failed to import cross_project_knowledge_sharing: {e}")

print("\nTrying to import CrossProjectKnowledgeSharing...")
try:
    from core.cross_project_knowledge_sharing import CrossProjectKnowledgeSharing
    print("✅ CrossProjectKnowledgeSharing imported successfully!")
except ImportError as e:
    print(f"❌ Failed to import CrossProjectKnowledgeSharing: {e}")
