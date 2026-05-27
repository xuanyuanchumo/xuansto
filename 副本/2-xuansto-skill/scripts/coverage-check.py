#!/usr/bin/env python3
"""
代码覆盖率检查脚本
功能：运行测试并生成覆盖率报告
"""

import argparse
import importlib.util
import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='代码覆盖率检查脚本 - 运行测试并生成覆盖率报告'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=80.0,
        help='覆盖率阈值百分比（默认：80.0）'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='coverage-report',
        help='输出目录名称（默认：coverage-report）'
    )
    parser.add_argument(
        '--format',
        type=str,
        choices=['html', 'xml', 'json', 'term'],
        default='html',
        help='报告格式（默认：html）'
    )
    parser.add_argument(
        '--source',
        type=str,
        default='src',
        help='源代码目录（默认：src）'
    )
    parser.add_argument(
        '--test-dir',
        type=str,
        default='tests',
        help='测试目录（默认：tests）'
    )
    parser.add_argument(
        '--fail-under',
        action='store_true',
        help='低于阈值时返回非零退出码'
    )
    return parser.parse_args()


def check_coverage_tool():
    """检查覆盖率工具是否安装"""
    return importlib.util.find_spec('coverage') is not None


def install_coverage_tool():
    """提示用户手动安装覆盖率工具（不执行安装）"""
    print("未检测到 coverage 模块，请手动安装：")
    print("  pip install coverage pytest-cov")
    return False


def run_coverage(source_dir, output_dir, report_format, threshold, test_dir):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"\n开始运行覆盖率测试...")
    print(f"源代码目录: {source_dir}")
    print(f"测试目录: {test_dir}")
    print(f"输出目录: {output_dir}")
    print(f"报告格式: {report_format}")
    print(f"覆盖率阈值: {threshold}%")

    try:
        run_cmd = [
            sys.executable, "-m", "coverage", "run",
            "-m", "pytest", test_dir,
            "--source", source_dir,
        ]
        result = subprocess.run(run_cmd, capture_output=True, text=True)
        if result.returncode != 0 and result.stderr:
            print(f"覆盖率运行警告: {result.stderr}")

        report_cmd = [sys.executable, "-m", "coverage", "report"]
        report_result = subprocess.run(report_cmd, capture_output=True, text=True)

        coverage_percent = 0.0
        for line in report_result.stdout.splitlines():
            if "TOTAL" in line:
                parts = line.split()
                for part in parts:
                    if part.endswith("%"):
                        try:
                            coverage_percent = float(part.rstrip("%"))
                        except ValueError:
                            pass
                        break
                break

        if report_format == 'html':
            subprocess.run(
                [sys.executable, "-m", "coverage", "html", "-d", output_dir],
                capture_output=True, text=True,
            )
        elif report_format == 'xml':
            xml_file = output_path / 'coverage.xml'
            subprocess.run(
                [sys.executable, "-m", "coverage", "xml", "-o", str(xml_file)],
                capture_output=True, text=True,
            )
        elif report_format == 'json':
            json_file = output_path / 'coverage.json'
            subprocess.run(
                [sys.executable, "-m", "coverage", "json", "-o", str(json_file)],
                capture_output=True, text=True,
            )

        return coverage_percent

    except Exception as e:
        print(f"覆盖率测试运行失败: {e}")
        return 0.0


def generate_summary(output_dir, coverage_percent, threshold, passed):
    """
    生成覆盖率摘要报告

    参数:
        output_dir: 输出目录
        coverage_percent: 覆盖率百分比
        threshold: 阈值
        passed: 是否通过
    """
    summary = {
        'timestamp': datetime.now().isoformat(),
        'coverage_percent': coverage_percent,
        'threshold': threshold,
        'passed': passed,
        'status': '通过' if passed else '未通过'
    }

    summary_path = Path(output_dir) / 'summary.json'
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print("覆盖率检查结果")
    print(f"{'='*50}")
    print(f"覆盖率: {coverage_percent:.2f}%")
    print(f"阈值: {threshold}%")
    print(f"状态: {'✅ 通过' if passed else '❌ 未通过'}")
    print(f"报告目录: {output_dir}")
    print(f"{'='*50}")


def main():
    """主函数"""
    args = parse_args()

    if not check_coverage_tool():
        install_coverage_tool()
        print("无法运行覆盖率工具，退出")
        sys.exit(1)

    coverage_percent = run_coverage(
        args.source,
        args.output,
        args.format,
        args.threshold,
        args.test_dir
    )

    passed = coverage_percent >= args.threshold

    generate_summary(args.output, coverage_percent, args.threshold, passed)

    if not passed and args.fail_under:
        print(f"\n覆盖率 {coverage_percent:.2f}% 低于阈值 {args.threshold}%")
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
