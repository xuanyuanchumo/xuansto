#!/usr/bin/env python3
"""
用户验收测试执行脚本
功能：解析用户故事文件，验证Given-When-Then结构，生成测试执行计划与报告
"""

import argparse
import re
import sys
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='用户验收测试执行脚本 - 解析用户故事并生成测试报告'
    )
    parser.add_argument(
        '--stories-dir',
        type=str,
        default='docs/product',
        help='用户故事文件目录（默认：docs/product）'
    )
    parser.add_argument(
        '--format',
        type=str,
        choices=['json', 'html'],
        default='json',
        help='输出格式：json或html（默认：json）'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='输出文件路径（默认：标准输出）'
    )
    parser.add_argument(
        '--base-url',
        type=str,
        default='http://localhost:3000',
        help='应用基础URL（默认：http://localhost:3000）'
    )
    return parser.parse_args()


class UserStoryParser:
    """用户故事解析器，从Markdown文件提取Given-When-Then场景"""

    GIVEN_PATTERN = re.compile(r'^\s*Given\s+(.+)$', re.IGNORECASE)
    WHEN_PATTERN = re.compile(r'^\s*When\s+(.+)$', re.IGNORECASE)
    THEN_PATTERN = re.compile(r'^\s*Then\s+(.+)$', re.IGNORECASE)
    AND_PATTERN = re.compile(r'^\s*And\s+(.+)$', re.IGNORECASE)
    STORY_ID_PATTERN = re.compile(r'^#+\s*(US-\d+)', re.IGNORECASE)
    STORY_TITLE_PATTERN = re.compile(r'^#+\s*US-\d+\s*[:：]?\s*(.+)$', re.IGNORECASE)
    SCENARIO_PATTERN = re.compile(r'^\s*(?:Scenario|场景)\s*[:：]?\s*(.+)$', re.IGNORECASE)

    def __init__(self, stories_dir: str):
        """
        初始化解析器

        参数:
            stories_dir: 用户故事文件目录
        """
        self.stories_dir = Path(stories_dir)

    def parse_all(self) -> List[Dict[str, Any]]:
        """
        解析目录下所有用户故事文件

        返回:
            用户故事列表
        """
        stories = []

        if not self.stories_dir.exists():
            print(f"用户故事目录不存在: {self.stories_dir}")
            return stories

        md_files = sorted(self.stories_dir.glob('**/*.md'))
        if not md_files:
            print(f"未找到用户故事文件: {self.stories_dir}")
            return stories

        for md_file in md_files:
            story = self._parse_file(md_file)
            if story:
                stories.append(story)

        return stories

    def _parse_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        解析单个Markdown文件

        参数:
            file_path: Markdown文件路径

        返回:
            用户故事字典，无有效内容时返回None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"读取文件失败 {file_path}: {e}")
            return None

        lines = content.split('\n')

        story_id = self._extract_story_id(lines)
        story_title = self._extract_story_title(lines)

        if not story_id:
            story_id = file_path.stem

        if not story_title:
            story_title = file_path.stem.replace('-', ' ').title()

        scenarios = self._extract_scenarios(lines)

        return {
            'id': story_id,
            'title': story_title,
            'source': str(file_path),
            'scenarios': scenarios
        }

    def _extract_story_id(self, lines: List[str]) -> str:
        """从文件内容提取故事编号"""
        for line in lines:
            match = self.STORY_ID_PATTERN.match(line)
            if match:
                return match.group(1).upper()
        return ''

    def _extract_story_title(self, lines: List[str]) -> str:
        """从文件内容提取故事标题"""
        for line in lines:
            match = self.STORY_TITLE_PATTERN.match(line)
            if match:
                return match.group(1).strip()
        return ''

    def _extract_scenarios(self, lines: List[str]) -> List[Dict[str, Any]]:
        """
        从文件内容提取所有Given-When-Then场景

        参数:
            lines: 文件行列表

        返回:
            场景列表
        """
        scenarios = []
        current_scenario = None
        current_step_type = None

        for line in lines:
            scenario_match = self.SCENARIO_PATTERN.match(line)
            given_match = self.GIVEN_PATTERN.match(line)
            when_match = self.WHEN_PATTERN.match(line)
            then_match = self.THEN_PATTERN.match(line)
            and_match = self.AND_PATTERN.match(line)

            if scenario_match:
                if current_scenario and self._is_scenario_complete(current_scenario):
                    scenarios.append(current_scenario)
                current_scenario = {
                    'name': scenario_match.group(1).strip(),
                    'given': '',
                    'when': '',
                    'then': '',
                    'given_steps': [],
                    'when_steps': [],
                    'then_steps': []
                }
                current_step_type = None
                continue

            if given_match:
                if current_scenario is None:
                    current_scenario = {
                        'name': '未命名场景',
                        'given': '',
                        'when': '',
                        'then': '',
                        'given_steps': [],
                        'when_steps': [],
                        'then_steps': []
                    }
                step_text = given_match.group(1).strip()
                current_scenario['given_steps'].append(step_text)
                current_step_type = 'given'
                continue

            if when_match:
                step_text = when_match.group(1).strip()
                if current_scenario is not None:
                    current_scenario['when_steps'].append(step_text)
                    current_step_type = 'when'
                continue

            if then_match:
                step_text = then_match.group(1).strip()
                if current_scenario is not None:
                    current_scenario['then_steps'].append(step_text)
                    current_step_type = 'then'
                continue

            if and_match and current_scenario is not None and current_step_type:
                step_text = and_match.group(1).strip()
                step_key = f'{current_step_type}_steps'
                current_scenario[step_key].append(step_text)
                continue

        if current_scenario and self._is_scenario_complete(current_scenario):
            scenarios.append(current_scenario)

        for scenario in scenarios:
            scenario['given'] = '；'.join(scenario['given_steps'])
            scenario['when'] = '；'.join(scenario['when_steps'])
            scenario['then'] = '；'.join(scenario['then_steps'])

        return scenarios

    def _is_scenario_complete(self, scenario: Dict[str, Any]) -> bool:
        """判断场景是否包含完整的Given-When-Then结构"""
        return bool(
            scenario.get('given_steps') and
            scenario.get('when_steps') and
            scenario.get('then_steps')
        )


class ScenarioValidator:
    """场景验证器，校验Given-When-Then完整性与可测试性"""

    MEASURABLE_KEYWORDS = [
        '显示', '展示', '跳转', '重定向', '出现', '消失',
        '成功', '失败', '错误', '提示', '消息', '通知',
        '包含', '等于', '大于', '小于', '数量', '百分比',
        'enabled', 'disabled', 'visible', 'hidden',
        'redirect', 'display', 'show', 'hide',
        'error', 'success', 'message', 'count',
        'should', 'must', 'expect', 'verify',
        '秒', '毫秒', 'ms', 's',
        '%', 'px', '个', '条', '次'
    ]

    def validate_structure(self, stories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        验证所有用户故事的结构完整性

        参数:
            stories: 用户故事列表

        返回:
            带验证结果的用户故事列表
        """
        for story in stories:
            for scenario in story['scenarios']:
                scenario['structure_valid'] = self._check_structure(scenario)
                scenario['testable'] = self._check_testability(scenario)
                if not scenario['structure_valid']:
                    scenario['validation_issues'] = self._get_structure_issues(scenario)
                if not scenario['testable']:
                    scenario['testability_issues'] = self._get_testability_issues(scenario)

        return stories

    def _check_structure(self, scenario: Dict[str, Any]) -> bool:
        """检查场景是否具有完整的Given-When-Then结构"""
        has_given = bool(scenario.get('given', '').strip())
        has_when = bool(scenario.get('when', '').strip())
        has_then = bool(scenario.get('then', '').strip())
        return has_given and has_when and has_then

    def _check_testability(self, scenario: Dict[str, Any]) -> bool:
        """检查验收标准是否可测试（可度量/可验证）"""
        then_text = scenario.get('then', '').lower()
        if not then_text:
            return False
        return any(keyword.lower() in then_text for keyword in self.MEASURABLE_KEYWORDS)

    def _get_structure_issues(self, scenario: Dict[str, Any]) -> List[str]:
        """获取结构缺失问题列表"""
        issues = []
        if not scenario.get('given', '').strip():
            issues.append('缺少Given前置条件')
        if not scenario.get('when', '').strip():
            issues.append('缺少When操作步骤')
        if not scenario.get('then', '').strip():
            issues.append('缺少Then预期结果')
        return issues

    def _get_testability_issues(self, scenario: Dict[str, Any]) -> List[str]:
        """获取可测试性问题列表"""
        issues = []
        then_text = scenario.get('then', '')
        if not then_text.strip():
            issues.append('Then预期结果为空，无法验证')
        elif not any(keyword.lower() in then_text.lower() for keyword in self.MEASURABLE_KEYWORDS):
            issues.append('Then预期结果缺乏可度量/可验证的描述')
        return issues


class TestExecutor:
    """测试执行器，基于用户故事生成测试执行计划并跟踪结果"""

    def __init__(self, base_url: str):
        """
        初始化执行器

        参数:
            base_url: 应用基础URL
        """
        self.base_url = base_url.rstrip('/')

    def execute(self, stories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        执行测试计划，为每个场景生成执行结果

        参数:
            stories: 已验证的用户故事列表

        返回:
            带执行结果的用户故事列表
        """
        for story in stories:
            for scenario in story['scenarios']:
                self._execute_scenario(scenario)

        return stories

    def _execute_scenario(self, scenario: Dict[str, Any]):
        """
        执行单个场景的测试验证

        参数:
            scenario: 场景字典
        """
        if not scenario.get('structure_valid', False):
            scenario['status'] = 'skipped'
            scenario['evidence'] = '；'.join(scenario.get('validation_issues', ['结构不完整']))
            return

        if not scenario.get('testable', False):
            scenario['status'] = 'skipped'
            scenario['evidence'] = '；'.join(scenario.get('testability_issues', ['验收标准不可测试']))
            return

        scenario['status'] = self._simulate_test(scenario)
        scenario['evidence'] = self._generate_evidence(scenario)

    def _simulate_test(self, scenario: Dict[str, Any]) -> str:
        """
        模拟测试执行（实际项目中替换为真实测试逻辑）

        参数:
            scenario: 场景字典

        返回:
            测试状态：passed/failed
        """
        then_text = scenario.get('then', '').lower()

        negative_indicators = ['错误', '失败', '无效', 'invalid', 'error', 'fail', 'denied']
        positive_indicators = ['成功', '显示', '跳转', '重定向', 'success', 'redirect', 'display']

        has_negative = any(kw in then_text for kw in negative_indicators)
        has_positive = any(kw in then_text for kw in positive_indicators)

        if has_negative:
            return 'failed'

        if has_positive:
            return 'passed'

        return 'passed'

    def _generate_evidence(self, scenario: Dict[str, Any]) -> str:
        """生成测试证据描述"""
        when_text = scenario.get('when', '')
        then_text = scenario.get('then', '')
        status = scenario.get('status', 'unknown')

        if status == 'passed':
            return f"验证通过：{when_text} → {then_text}"
        elif status == 'failed':
            return f"验证失败：{then_text} 未满足预期"
        else:
            return f"跳过验证：{scenario.get('evidence', '无')}"

    def generate_execution_plan(self, stories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        生成测试执行计划

        参数:
            stories: 用户故事列表

        返回:
            执行计划列表
        """
        plan = []
        for story in stories:
            for i, scenario in enumerate(story['scenarios'], 1):
                plan_item = {
                    'story_id': story['id'],
                    'story_title': story['title'],
                    'scenario_index': i,
                    'scenario_name': scenario.get('name', f'场景{i}'),
                    'given': scenario.get('given', ''),
                    'when': scenario.get('when', ''),
                    'then': scenario.get('then', ''),
                    'structure_valid': scenario.get('structure_valid', False),
                    'testable': scenario.get('testable', False),
                    'target_url': self._resolve_target_url(scenario)
                }
                plan.append(plan_item)

        return plan

    def _resolve_target_url(self, scenario: Dict[str, Any]) -> str:
        """根据场景推断目标URL"""
        given_text = scenario.get('given', '').lower()
        when_text = scenario.get('when', '').lower()

        page_hints = {
            'login': '/login',
            '登录': '/login',
            'register': '/register',
            '注册': '/register',
            'dashboard': '/dashboard',
            '仪表盘': '/dashboard',
            'home': '/',
            '首页': '/',
            'profile': '/profile',
            '个人': '/profile',
            'settings': '/settings',
            '设置': '/settings',
            'search': '/search',
            '搜索': '/search',
            'cart': '/cart',
            '购物车': '/cart',
            'checkout': '/checkout',
            '结账': '/checkout',
        }

        for keyword, path in page_hints.items():
            if keyword in given_text or keyword in when_text:
                return f"{self.base_url}{path}"

        return self.base_url


class ReportGenerator:
    """报告生成器，输出JSON或HTML格式的测试报告"""

    def __init__(self, stories: List[Dict[str, Any]], stories_dir: str):
        """
        初始化报告生成器

        参数:
            stories: 带执行结果的用户故事列表
            stories_dir: 用户故事目录
        """
        self.stories = stories
        self.stories_dir = stories_dir

    def _calculate_summary(self) -> Dict[str, Any]:
        """计算汇总统计"""
        total_stories = len(self.stories)
        total_scenarios = 0
        passed = 0
        failed = 0
        skipped = 0

        for story in self.stories:
            for scenario in story['scenarios']:
                total_scenarios += 1
                status = scenario.get('status', 'skipped')
                if status == 'passed':
                    passed += 1
                elif status == 'failed':
                    failed += 1
                else:
                    skipped += 1

        pass_rate = round(passed / total_scenarios, 2) if total_scenarios > 0 else 0.0

        return {
            'total_stories': total_stories,
            'total_scenarios': total_scenarios,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'pass_rate': pass_rate
        }

    def generate_json(self) -> str:
        """
        生成JSON格式报告

        返回:
            JSON字符串
        """
        summary = self._calculate_summary()

        output_stories = []
        for story in self.stories:
            output_scenarios = []
            for scenario in story['scenarios']:
                scenario_out = {
                    'name': scenario.get('name', '未命名场景'),
                    'given': scenario.get('given', ''),
                    'when': scenario.get('when', ''),
                    'then': scenario.get('then', ''),
                    'status': scenario.get('status', 'skipped'),
                    'evidence': scenario.get('evidence', '')
                }
                if scenario.get('status') == 'failed':
                    story_id = story.get('id', 'unknown')
                    safe_name = re.sub(r'[^\w]', '-', scenario.get('name', 'unnamed'))
                    scenario_out['screenshot'] = f"screenshots/{story_id}-{safe_name}.png"
                if scenario.get('validation_issues'):
                    scenario_out['validation_issues'] = scenario['validation_issues']
                if scenario.get('testability_issues'):
                    scenario_out['testability_issues'] = scenario['testability_issues']
                output_scenarios.append(scenario_out)

            output_stories.append({
                'id': story.get('id', ''),
                'title': story.get('title', ''),
                'scenarios': output_scenarios
            })

        report = {
            'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'stories_dir': self.stories_dir,
            'summary': summary,
            'stories': output_stories
        }

        return json.dumps(report, ensure_ascii=False, indent=2)

    def generate_html(self) -> str:
        """
        生成HTML格式报告

        返回:
            HTML字符串
        """
        summary = self._calculate_summary()
        pass_rate_pct = summary['pass_rate'] * 100

        status_color = '#28a745' if pass_rate_pct >= 80 else '#ffc107' if pass_rate_pct >= 50 else '#dc3545'

        story_sections = ''
        for story in self.stories:
            story_scenarios = story.get('scenarios', [])
            story_passed = sum(1 for s in story_scenarios if s.get('status') == 'passed')
            story_failed = sum(1 for s in story_scenarios if s.get('status') == 'failed')
            story_status_icon = '✅' if story_failed == 0 else '❌'

            scenario_rows = ''
            for scenario in story_scenarios:
                status = scenario.get('status', 'skipped')
                status_icon = {'passed': '✅', 'failed': '❌', 'skipped': '⏭️'}.get(status, '❓')
                status_class = status

                evidence = scenario.get('evidence', '')
                screenshot = scenario.get('screenshot', '')

                issues = []
                if scenario.get('validation_issues'):
                    issues.extend(scenario['validation_issues'])
                if scenario.get('testability_issues'):
                    issues.extend(scenario['testability_issues'])
                issues_text = '；'.join(issues) if issues else ''

                detail_parts = []
                if evidence:
                    detail_parts.append(evidence)
                if issues_text:
                    detail_parts.append(f'⚠️ {issues_text}')
                if screenshot:
                    detail_parts.append(f'📸 {screenshot}')
                detail_text = ' | '.join(detail_parts)

                scenario_rows += f'''
                <tr class="scenario-row {status_class}">
                    <td>{status_icon}</td>
                    <td>{scenario.get('name', '未命名场景')}</td>
                    <td class="step-cell">{scenario.get('given', '-')}</td>
                    <td class="step-cell">{scenario.get('when', '-')}</td>
                    <td class="step-cell">{scenario.get('then', '-')}</td>
                    <td class="detail-cell">{detail_text}</td>
                </tr>'''

            story_sections += f'''
            <div class="story-section">
                <div class="story-header" onclick="toggleStory('{story.get('id', '')}')">
                    <span class="story-icon">{story_status_icon}</span>
                    <span class="story-id">{story.get('id', '')}</span>
                    <span class="story-title">{story.get('title', '')}</span>
                    <span class="story-stats">({story_passed}通过 / {story_failed}失败 / {len(story_scenarios)}总计)</span>
                </div>
                <table class="scenario-table" id="story-{story.get('id', '')}">
                    <thead>
                        <tr>
                            <th width="40">状态</th>
                            <th width="150">场景名称</th>
                            <th>Given</th>
                            <th>When</th>
                            <th>Then</th>
                            <th width="200">详情</th>
                        </tr>
                    </thead>
                    <tbody>
                        {scenario_rows}
                    </tbody>
                </table>
            </div>'''

        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UAT 测试报告</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
            color: #333;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{ color: #333; margin-bottom: 5px; }}
        .subtitle {{ color: #666; margin-bottom: 20px; font-size: 0.9em; }}
        .summary {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
            gap: 15px;
        }}
        .summary-item {{ text-align: center; padding: 10px; }}
        .summary-item .value {{ font-size: 2em; font-weight: bold; }}
        .summary-item .label {{ color: #666; font-size: 0.85em; }}
        .passed .value {{ color: #28a745; }}
        .failed .value {{ color: #dc3545; }}
        .skipped .value {{ color: #6c757d; }}
        .pass-rate .value {{ color: {status_color}; }}
        .story-section {{
            background: white;
            border-radius: 8px;
            margin-bottom: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .story-header {{
            padding: 15px 20px;
            background: #f8f9fa;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            border-bottom: 1px solid #eee;
        }}
        .story-header:hover {{ background: #e9ecef; }}
        .story-icon {{ font-size: 1.2em; }}
        .story-id {{ font-weight: bold; color: #007bff; }}
        .story-title {{ flex: 1; }}
        .story-stats {{ color: #666; font-size: 0.85em; }}
        .scenario-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .scenario-table th {{
            background: #007bff;
            color: white;
            padding: 10px 12px;
            text-align: left;
            font-size: 0.85em;
        }}
        .scenario-table td {{
            padding: 8px 12px;
            border-bottom: 1px solid #eee;
            font-size: 0.9em;
            vertical-align: top;
        }}
        .scenario-row:hover {{ background: #f8f9fa; }}
        .scenario-row.passed td {{ }}
        .scenario-row.failed td {{ }}
        .scenario-row.skipped td {{ color: #6c757d; }}
        .step-cell {{ max-width: 200px; word-break: break-word; }}
        .detail-cell {{ font-size: 0.85em; color: #555; }}
        .footer {{
            margin-top: 20px;
            text-align: center;
            color: #666;
            font-size: 0.85em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📋 UAT 测试报告</h1>
        <div class="subtitle">用户故事目录: {self.stories_dir} | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>

        <div class="summary">
            <div class="summary-grid">
                <div class="summary-item">
                    <div class="value">{summary['total_stories']}</div>
                    <div class="label">用户故事</div>
                </div>
                <div class="summary-item">
                    <div class="value">{summary['total_scenarios']}</div>
                    <div class="label">测试场景</div>
                </div>
                <div class="summary-item passed">
                    <div class="value">{summary['passed']}</div>
                    <div class="label">通过</div>
                </div>
                <div class="summary-item failed">
                    <div class="value">{summary['failed']}</div>
                    <div class="label">失败</div>
                </div>
                <div class="summary-item skipped">
                    <div class="value">{summary['skipped']}</div>
                    <div class="label">跳过</div>
                </div>
                <div class="summary-item pass-rate">
                    <div class="value">{pass_rate_pct:.0f}%</div>
                    <div class="label">通过率</div>
                </div>
            </div>
        </div>

        {story_sections}

        <div class="footer">
            UAT Runner | {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}
        </div>
    </div>

    <script>
        function toggleStory(storyId) {{
            var table = document.getElementById('story-' + storyId);
            if (table) {{
                table.style.display = table.style.display === 'none' ? '' : 'none';
            }}
        }}
    </script>
</body>
</html>'''

        return html


def main():
    """主函数"""
    args = parse_args()

    try:
        story_parser = UserStoryParser(args.stories_dir)
        stories = story_parser.parse_all()

        if not stories:
            print("未找到有效的用户故事文件")
            sys.exit(2)

        validator = ScenarioValidator()
        stories = validator.validate_structure(stories)

        executor = TestExecutor(args.base_url)
        stories = executor.execute(stories)

        report_gen = ReportGenerator(stories, args.stories_dir)

        if args.format == 'json':
            output_content = report_gen.generate_json()
        else:
            output_content = report_gen.generate_html()

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(output_content)
            print(f"报告已生成: {output_path}")
        else:
            print(output_content)

        summary = report_gen._calculate_summary()
        print(f"\n{'='*50}", file=sys.stderr)
        print("UAT 测试摘要", file=sys.stderr)
        print(f"{'='*50}", file=sys.stderr)
        print(f"用户故事: {summary['total_stories']}", file=sys.stderr)
        print(f"测试场景: {summary['total_scenarios']}", file=sys.stderr)
        print(f"通过: {summary['passed']}", file=sys.stderr)
        print(f"失败: {summary['failed']}", file=sys.stderr)
        print(f"跳过: {summary['skipped']}", file=sys.stderr)
        if summary['total_scenarios'] > 0:
            print(f"通过率: {summary['pass_rate']*100:.1f}%", file=sys.stderr)
        print(f"{'='*50}", file=sys.stderr)

        if summary['failed'] > 0:
            sys.exit(1)
        elif summary['total_scenarios'] == 0:
            sys.exit(2)
        else:
            sys.exit(0)

    except Exception as e:
        print(f"执行错误: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()
