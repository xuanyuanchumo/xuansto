#!/usr/bin/env python3
"""
Page element discovery script.
Uses Playwright to navigate to a page and discover interactive elements.
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
        description='Discover page elements using Playwright'
    )
    parser.add_argument(
        '--url', type=str, required=True,
        help='Target page URL'
    )
    parser.add_argument(
        '--output', type=str, default=None,
        help='Output file path (JSON format)'
    )
    parser.add_argument(
        '--browser', type=str, choices=['chromium', 'firefox', 'webkit'],
        default='chromium',
        help='Browser engine (default: chromium)'
    )
    return parser.parse_args()


def discover_elements(page):
    elements = []

    selectors_config = [
        {
            'tag': 'button',
            'selector': 'button, [role="button"], input[type="button"], input[type="submit"], input[type="reset"]',
            'type': 'button'
        },
        {
            'tag': 'a',
            'selector': 'a[href]',
            'type': 'link'
        },
        {
            'tag': 'input',
            'selector': 'input:not([type="button"]):not([type="submit"]):not([type="reset"]):not([type="hidden"]), textarea, select',
            'type': 'input'
        },
        {
            'tag': 'form',
            'selector': 'form',
            'type': 'form'
        },
        {
            'tag': 'img',
            'selector': 'img',
            'type': 'image'
        },
        {
            'tag': 'heading',
            'selector': 'h1, h2, h3, h4, h5, h6',
            'type': 'heading'
        },
    ]

    for config in selectors_config:
        locator = page.locator(config['selector'])
        count = locator.count()

        for i in range(count):
            try:
                el = locator.nth(i)
                box = el.bounding_box()
                text_content = el.text_content() or ''
                attributes = el.evaluate('el => { const attrs = {}; for (const attr of el.attributes) { attrs[attr.name] = attr.value; } return attrs; }')
                tag_name = el.evaluate('el => el.tagName.toLowerCase()')

                element_info = {
                    'selector': config['selector'],
                    'tag': tag_name,
                    'type': config['type'],
                    'text': text_content.strip()[:200],
                    'attributes': attributes,
                    'position': {
                        'x': box['x'] if box else None,
                        'y': box['y'] if box else None,
                        'width': box['width'] if box else None,
                        'height': box['height'] if box else None,
                    } if box else None,
                }
                elements.append(element_info)
            except Exception:
                continue

    return elements


def main():
    if not check_playwright():
        print_install_hint()
        sys.exit(1)

    args = parse_args()

    from playwright.sync_api import sync_playwright

    browser_type_map = {
        'chromium': 'chromium',
        'firefox': 'firefox',
        'webkit': 'webkit',
    }

    result = {
        'url': args.url,
        'browser': args.browser,
        'timestamp': datetime.now().isoformat(),
        'elements': [],
        'summary': {},
    }

    with sync_playwright() as p:
        browser_launcher = getattr(p, browser_type_map[args.browser])
        browser = browser_launcher.launch()
        context = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = context.new_page()

        print(f"Navigating to: {args.url}")
        try:
            page.goto(args.url, wait_until='networkidle', timeout=30000)
        except Exception as e:
            print(f"Error: Failed to navigate to {args.url}: {e}")
            browser.close()
            sys.exit(1)

        print("Discovering page elements...")
        elements = discover_elements(page)
        result['elements'] = elements

        summary = {}
        for el in elements:
            el_type = el['type']
            summary[el_type] = summary.get(el_type, 0) + 1
        result['summary'] = summary

        browser.close()

    print(f"\nDiscovered {len(elements)} elements:")
    for el_type, count in sorted(summary.items()):
        print(f"  {el_type}: {count}")

    output_data = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_data)
        print(f"\nResults saved to: {args.output}")
    else:
        print(f"\n{output_data}")

    sys.exit(0)


if __name__ == '__main__':
    main()
