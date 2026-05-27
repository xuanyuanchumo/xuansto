#!/usr/bin/env python3
import shutil
from pathlib import Path

src = Path(r"d:\Projects\TraeProjects\skiller\.trae\skills\xuansto-skill")
dst = Path(r"d:\Projects\TraeProjects\skiller\.trae\skills\xuansto-skill-v2")

def copy_scripts():
    src_scripts = src / "scripts"
    dst_scripts = dst / "scripts"
    dst_scripts.mkdir(parents=True, exist_ok=True)
    
    for f in src_scripts.iterdir():
        if f.is_file() and f.suffix in ('.py', '.js', '.ps1'):
            shutil.copy2(str(f), str(dst_scripts / f.name))
            print(f"  Copied: {f.name}")
        elif f.is_dir() and f.name != '__pycache__':
            dst_sub = dst_scripts / f.name
            if dst_sub.exists():
                shutil.rmtree(str(dst_sub))
            shutil.copytree(str(f), str(dst_sub), ignore=shutil.ignore_patterns('*.pyc', '__pycache__'))
            count = sum(1 for _ in dst_sub.rglob("*") if _.is_file())
            print(f"  Copied dir: {f.name}/ ({count} files)")

def copy_memory():
    files_to_copy = [
        "memory/patterns/testing/README.md",
        "memory/fixes/refactoring/README.md",
        "memory/fixes/README.md",
    ]
    for rel in files_to_copy:
        src_file = src / rel
        dst_file = dst / rel
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        if src_file.exists():
            shutil.copy2(str(src_file), str(dst_file))
            print(f"  Copied: {rel}")
        else:
            dst_file.write_text(f"# {rel.split('/')[-2].title()}\n\nThis directory stores {rel.split('/')[-2]} data.\n", encoding='utf-8')
            print(f"  Created minimal: {rel}")

def copy_examples():
    for name in ["desktop-app-development.md", "web-app-development.md"]:
        src_file = src / "examples" / name
        dst_file = dst / "examples" / name
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        if src_file.exists():
            shutil.copy2(str(src_file), str(dst_file))
            print(f"  Copied: examples/{name}")

def create_migrations():
    gitkeep = dst / "migrations" / ".gitkeep"
    gitkeep.parent.mkdir(parents=True, exist_ok=True)
    gitkeep.write_text("", encoding='utf-8')
    print("  Created: migrations/.gitkeep")

if __name__ == "__main__":
    print("Copying scripts...")
    copy_scripts()
    print("\nCopying memory...")
    copy_memory()
    print("\nCopying examples...")
    copy_examples()
    print("\nCreating migrations...")
    create_migrations()
    print("\nDone!")
