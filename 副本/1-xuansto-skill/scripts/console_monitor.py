#!/usr/bin/env python3
"""
Browser console monitor script.
Uses Playwright to navigate to a page and capture console logs.
"""

import argparse
import importlib.util
import json
import sys
from datetime import datetime


def check_playwright():
    return importlib.util.find_spec('playwright') is not None


def print_install_hint():
    print("Playwright is not installed. Please install it with:")
    print("  pip install playwright")
    print("  playwright install")
    print("\nAfter installation, re-run this script.")


def parse_args():
    parser = argparse.ArgumentParser(
        description='Monitor browser console logs using Playwright'
    )
    parser.add_argument(
        '--url', type=str, required=True,
        help='Target page URL'
    )
    parser.add_argument(
        '--duration', type=int, default=10,
        help='Monitoring duration in seconds (default: 10)'
    )
    parser.add_argument(
        '--filter', type=str, choices=['all', 'error', 'warning', 'info'],
        default='all',
        help='Log level filter (default: all)'
    )
    parser.add_argument(
        '--output', type=str, default=None,
        help='Output file path (JSON format)'
    )
    return parser.parse_args()


def main():
    if not check_playwright():
        print_install_hint()
        sys.exit(1)

    args = parse_args()

    from playwright.sync_api import sync_playwright

    level_map = {
        'error': ['error'],
        'warning': ['warning', 'error'],
        'info': ['info', 'warning', 'error'],
        'all': ['log', 'info', 'warning', 'error', 'debug'],
    }
    allowed_levels = level_map[args.filter]

    console_logs = []

    def on_console(msg):
        log_entry = {
            'type': msg.type,
            'text': msg.text,
            'timestamp': datetime.now().isoformat(),
            'location': {
                'url': msg.location.get('url', ''),
                'lineNumber': msg.location.get('lineNumber', 0),
                'columnNumber': msg.location.get('columnNumber', 0),
            } if msg.location else None,
        }
        console_logs.append(log_entry)

    result = {
        'url': args.url,
        'duration': args.duration,
        'filter': args.filter,
        'timestamp': datetime.now().isoformat(),
        'logs': [],
        'summary': {},
    }

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = context.new_page()

        page.on('console', on_console)

        print(f"Navigating to: {args.url}")
        try:
            page.goto(args.url, wait_until='networkidle', timeout=30000)
        except Exception as e:
            print(f"Error: Failed to navigate to {args.url}: {e}")
            browser.close()
            sys.exit(1)

        print(f"Monitoring console for {args.duration} seconds (filter: {args.filter})...")
        page.wait_for_timeout(args.duration * 1000)

        browser.close()

    filtered_logs = [log for log in console_logs if log['type'] in allowed_levels]
    result['logs'] = filtered_logs

    summary = {}
    for log in filtered_logs:
        log_type = log['type']
        summary[log_type] = summary.get(log_type, 0) + 1
    result['summary'] = summary

    print(f"\nCaptured {len(filtered_logs)} console log entries:")
    for log_type, count in sorted(summary.items()):
        print(f"  {log_type}: {count}")

    output_data = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_data)
        print(f"\nResults saved to: {args.output}")
    else:
        print(f"\n{output_data}")

    if args.filter in ('error',) and summary.get('error', 0) > 0:
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
