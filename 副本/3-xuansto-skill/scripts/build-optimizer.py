#!/usr/bin/env python3
"""构建产物优化器 - 分析构建输出并建议优化

分析构建产物体积分布，检查bundle大小，提供优化建议。

用法:
    python build-optimizer.py [--platform auto] [--output-dir dist] [--analyze-only]
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="构建产物优化器 - 分析构建输出并建议优化"
    )
    parser.add_argument(
        "--platform",
        type=str,
        default="auto",
        help="目标平台: react, vue, angular, next, nuxt, svelte, auto (默认: auto)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="dist",
        help="构建输出目录 (默认: dist)",
    )
    parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="仅分析，不执行优化",
    )
    return parser.parse_args()


def detect_platform(output_dir: str) -> str:
    parent = Path(output_dir).parent if Path(output_dir).exists() else Path(".")
    pkg_path = parent / "package.json"
    if pkg_path.exists():
        try:
            with open(pkg_path, "r", encoding="utf-8") as f:
                pkg = json.load(f)
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "next" in deps:
                return "next"
            if "nuxt" in deps:
                return "nuxt"
            if "@angular/core" in deps:
                return "angular"
            if "vue" in deps:
                return "vue"
            if "svelte" in deps:
                return "svelte"
            if "react" in deps:
                return "react"
        except (json.JSONDecodeError, OSError):
            pass
    return "unknown"


def analyze_build_output(output_dir: str) -> dict:
    dist_path = Path(output_dir)
    if not dist_path.exists():
        return {
            "status": "FAIL",
            "details": f"构建输出目录不存在: {output_dir}",
            "artifacts": [],
            "total_size": 0,
        }

    artifacts = []
    total_size = 0
    for root, _dirs, files in os.walk(dist_path):
        for fname in files:
            fpath = Path(root) / fname
            try:
                size = fpath.stat().st_size
                rel = fpath.relative_to(dist_path)
                ext = fpath.suffix.lower()
                ftype = "other"
                if ext in (".js", ".mjs", ".cjs"):
                    ftype = "js"
                elif ext in (".css",):
                    ftype = "css"
                elif ext in (".html",):
                    ftype = "html"
                elif ext in (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico"):
                    ftype = "asset"
                elif ext in (".woff", ".woff2", ".ttf", ".eot"):
                    ftype = "font"
                artifacts.append(
                    {"name": str(rel), "size": size, "type": ftype}
                )
                total_size += size
            except OSError:
                continue

    return {
        "status": "PASS",
        "details": f"发现 {len(artifacts)} 个构建产物",
        "artifacts": artifacts,
        "total_size": total_size,
    }


def check_bundle_size(analysis: dict) -> dict:
    js_files = [a for a in analysis.get("artifacts", []) if a["type"] == "js"]
    warnings = []
    large_threshold = 512 * 1024
    for f in js_files:
        if f["size"] > large_threshold:
            warnings.append(
                f"大文件警告: {f['name']} ({f['size'] / 1024:.1f}KB > 512KB)"
            )

    if warnings:
        return {"name": "Bundle大小检查", "status": "WARN", "details": "; ".join(warnings)}
    return {"name": "Bundle大小检查", "status": "PASS", "details": "所有JS文件均在512KB以内"}


def suggest_optimizations(analysis: dict) -> list:
    suggestions = []
    artifacts = analysis.get("artifacts", [])

    js_files = [a for a in artifacts if a["type"] == "js"]
    total_js = sum(f["size"] for f in js_files)
    if total_js > 1024 * 1024:
        suggestions.append("JS总体积超过1MB，建议启用代码分割和Tree-shaking")

    css_files = [a for a in artifacts if a["type"] == "css"]
    total_css = sum(f["size"] for f in css_files)
    if total_css > 256 * 1024:
        suggestions.append("CSS总体积超过256KB，建议启用CSS压缩和去重")

    asset_files = [a for a in artifacts if a["type"] == "asset"]
    total_assets = sum(f["size"] for f in asset_files)
    if total_assets > 2 * 1024 * 1024:
        suggestions.append("静态资源总体积超过2MB，建议启用图片压缩和格式转换")

    font_files = [a for a in artifacts if a["type"] == "font"]
    if font_files:
        suggestions.append("检测到字体文件，建议启用字体子集化")

    if not suggestions:
        suggestions.append("构建产物体积正常，无需额外优化")

    return suggestions


def main():
    args = parse_args()

    platform = args.platform
    if platform == "auto":
        platform = detect_platform(args.output_dir)

    print(f"\n{'='*50}")
    print("构建产物优化器")
    print(f"{'='*50}")
    print(f"平台: {platform}")
    print(f"输出目录: {args.output_dir}")
    print(f"仅分析: {'是' if args.analyze_only else '否'}")

    analysis = analyze_build_output(args.output_dir)
    print(f"\n构建产物分析: {analysis['details']}")

    if analysis["status"] == "FAIL":
        print(f"分析失败: {analysis['details']}")
        sys.exit(1)

    total_kb = analysis["total_size"] / 1024
    print(f"总大小: {total_kb:.1f}KB ({len(analysis['artifacts'])} 个文件)")

    bundle_check = check_bundle_size(analysis)
    print(f"\nBundle大小检查: {bundle_check['status']} - {bundle_check['details']}")

    suggestions = suggest_optimizations(analysis)
    print(f"\n优化建议:")
    for i, s in enumerate(suggestions, 1):
        print(f"  {i}. {s}")

    report = {
        "timestamp": datetime.now().isoformat(),
        "platform": platform,
        "output_dir": args.output_dir,
        "analyze_only": args.analyze_only,
        "analysis": {
            "total_size": analysis["total_size"],
            "artifact_count": len(analysis["artifacts"]),
        },
        "bundle_check": bundle_check,
        "suggestions": suggestions,
    }

    report_path = Path(args.output_dir) / "optimization-report.json"
    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n报告已保存: {report_path}")
    except OSError as e:
        print(f"\n报告保存失败: {e}")

    print(f"\n{'='*50}")
    sys.exit(0)


if __name__ == "__main__":
    main()
