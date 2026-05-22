import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

SKILL_PATH = Path(__file__).resolve().parent.parent.parent.parent / ".trae" / "skills" / "xuansto-skill"
