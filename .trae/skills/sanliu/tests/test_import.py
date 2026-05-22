#!/usr/bin/env python3
import sys
from pathlib import Path

print(f"Current file: {__file__}")
print(f"Parent: {Path(__file__).parent}")
print(f"Parent's parent: {Path(__file__).parent.parent}")
print(f"Skillscripts dir: {Path(__file__).parent.parent / 'skillscripts'}")
print(f"Exists: {(Path(__file__).parent.parent / 'skillscripts').exists()}")

sys.path.insert(0, str(Path(__file__).parent.parent / "skillscripts"))
print(f"Python path: {sys.path[0]}")

try:
    from core.cross_project_knowledge_sharing import CrossProjectKnowledgeSharing
    print("✅ Import successful!")
except ImportError as e:
    print(f"❌ Import failed: {e}")
