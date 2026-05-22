#!/usr/bin/env python3
"""
Visual capture and comparison script.
Uses Playwright to capture screenshots and compare against baselines.
"""

import argparse
import importlib.util
import json
import math
import sys
from datetime import datetime
from pathlib import Path


def check_playwright():
    return importlib.util.find_spec('playwright') is not None


def check_pillow():
    return importlib.util.find_spec('PIL') is not None


def print_install_hint():
    print("Playwright is not installed. Please install it with:")
    print("  pip install playwright")
    print("  playwright install")
    print("\nFor pixel comparison, also install Pillow:")
    print("  pip install Pillow")
    print("\nAfter installation, re-run this script.")


def parse_args():
    parser = argparse.ArgumentParser(
        description='Capture screenshots and compare against baselines using Playwright'
    )
    parser.add_argument(
        '--url', type=str, required=True,
        help='Target page URL'
    )
    parser.add_argument(
        '--baseline', type=str, default=None,
        help='Baseline screenshot path for comparison'
    )
    parser.add_argument(
        '--output', type=str, default=None,
        help='Output screenshot path'
    )
    parser.add_argument(
        '--threshold', type=float, default=0.1,
        help='Difference threshold percentage (default: 0.1)'
    )
    return parser.parse_args()


def compare_images(baseline_path, current_path):
    from PIL import Image
    import hashlib

    img1 = Image.open(baseline_path).convert('RGBA')
    img2 = Image.open(current_path).convert('RGBA')

    if img1.size != img2.size:
        max_w = max(img1.width, img2.width)
        max_h = max(img1.height, img2.height)
        img1 = img1.resize((max_w, max_h), Image.Resampling.LANCZOS)
        img2 = img2.resize((max_w, max_h), Image.Resampling.LANCZOS)

    data1 = list(img1.getdata())
    data2 = list(img2.getdata())

    total_pixels = len(data1)
    diff_pixels = 0

    for p1, p2 in zip(data1, data2):
        if p1 != p2:
            r_diff = abs(p1[0] - p2[0])
            g_diff = abs(p1[1] - p2[1])
            b_diff = abs(p1[2] - p2[2])
            a_diff = abs(p1[3] - p2[3])
            if (r_diff + g_diff + b_diff + a_diff) > 0:
                diff_pixels += 1

    diff_percentage = (diff_pixels / total_pixels * 100) if total_pixels > 0 else 0
    diff_percentage = round(diff_percentage, 4)

    return {
        'total_pixels': total_pixels,
        'diff_pixels': diff_pixels,
        'diff_percentage': diff_percentage,
    }


def main():
    if not check_playwright():
        print_install_hint()
        sys.exit(1)

    args = parse_args()

    from playwright.sync_api import sync_playwright

    output_path = args.output
    if output_path is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f'screenshot_{timestamp}.png'

    output_dir = Path(output_path).parent
    if output_dir and str(output_dir) != '.':
        output_dir.mkdir(parents=True, exist_ok=True)

    result = {
        'url': args.url,
        'timestamp': datetime.now().isoformat(),
        'screenshot_path': output_path,
        'baseline_path': args.baseline,
        'threshold': args.threshold,
        'comparison': None,
        'status': 'captured',
    }

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = context.new_page()

        print(f"Navigating to: {args.url}")
        try:
            page.goto(args.url, wait_until='networkidle', timeout=30000)
        except Exception as e:
            print(f"Error: Failed to navigate to {args.url}: {e}")
            browser.close()
            sys.exit(1)

        print(f"Capturing full-page screenshot...")
        page.screenshot(path=output_path, full_page=True)
        print(f"Screenshot saved to: {output_path}")

        browser.close()

    if args.baseline:
        baseline = Path(args.baseline)
        if not baseline.exists():
            print(f"Warning: Baseline not found at {args.baseline}, skipping comparison")
            result['status'] = 'captured_no_baseline'
        else:
            if not check_pillow():
                print("Pillow is not installed. Cannot perform pixel comparison.")
                print("Install with: pip install Pillow")
                result['status'] = 'captured_no_pillow'
            else:
                print(f"Comparing with baseline: {args.baseline}")
                comparison = compare_images(args.baseline, output_path)
                result['comparison'] = comparison

                passed = comparison['diff_percentage'] <= args.threshold
                result['status'] = 'pass' if passed else 'fail'

                print(f"\nComparison result:")
                print(f"  Total pixels: {comparison['total_pixels']}")
                print(f"  Different pixels: {comparison['diff_pixels']}")
                print(f"  Difference: {comparison['diff_percentage']}%")
                print(f"  Threshold: {args.threshold}%")
                print(f"  Status: {'PASS' if passed else 'FAIL'}")
    else:
        print("\nNo baseline specified, screenshot captured without comparison.")

    output_data = json.dumps(result, ensure_ascii=False, indent=2)
    print(f"\n{output_data}")

    if result['status'] == 'fail':
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
