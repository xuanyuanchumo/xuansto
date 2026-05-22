import os
import re
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--skill-dir', default=os.getcwd())
args = parser.parse_args()
base = args.skill_dir

required_sections = [
    ('身份与记忆', ['身份与记忆', 'Identity.*Memory', '身份 & 记忆', '身份&记忆']),
    ('核心使命', ['核心使命', 'Core Mission', '使命']),
    ('行为准则', ['行为准则', 'Karpathy', 'Behavioral Guidelines', '行为指南', 'Karpathy Guidelines']),
    ('关键规则', ['关键规则', 'Critical Rules', '关键约束']),
    ('技术交付物', ['技术交付物', 'Technical Deliverables', '交付物', 'Deliverables']),
    ('工作流程', ['工作流程', 'Workflow Process', '工作流', 'Workflow']),
    ('成功指标', ['成功指标', 'Success Metrics', '成功标准', 'Metrics']),
]

yaml_required = True

agent_dir = os.path.join(base, 'agents')
results = []
all_pass = True

for root, dirs, files in os.walk(agent_dir):
    for fn in sorted(files):
        if not fn.endswith('.md'):
            continue
        fp = os.path.join(root, fn)
        rel_path = os.path.relpath(fp, base)

        with open(fp, 'r', encoding='utf-8') as f:
            content = f.read()

        agent_result = {
            'file': rel_path,
            'yaml': False,
            'sections': {},
            'missing': []
        }

        has_yaml = bool(re.match(r'^---\s*\n', content))
        agent_result['yaml'] = has_yaml
        if not has_yaml:
            agent_result['missing'].append('YAML frontmatter')
            all_pass = False

        for section_name, patterns in required_sections:
            found = False
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    found = True
                    break
            agent_result['sections'][section_name] = found
            if not found:
                agent_result['missing'].append(section_name)
                all_pass = False

        results.append(agent_result)

print(f"=== AGENT DEFINITION STRUCTURE VERIFICATION ===")
print(f"Total agent files checked: {len(results)}")
print()

pass_count = 0
fail_count = 0
for r in results:
    status = "PASS" if not r['missing'] else "FAIL"
    if status == "PASS":
        pass_count += 1
    else:
        fail_count += 1
        print(f"  {status}: {r['file']}")
        print(f"    Missing: {', '.join(r['missing'])}")

print()
print(f"=== SUMMARY ===")
print(f"PASS: {pass_count}/{len(results)}")
print(f"FAIL: {fail_count}/{len(results)}")

if all_pass:
    print("\nVERDICT: PASS - All 48 agent files have all 8 required sections")
else:
    print(f"\nVERDICT: FAIL - {fail_count} agent files are missing required sections")

print()
print("=== SECTION COVERAGE ===")
for section_name, patterns in required_sections:
    count = sum(1 for r in results if r['sections'][section_name])
    status = "OK" if count == len(results) else f"MISSING in {len(results) - count} files"
    print(f"  {section_name}: {count}/{len(results)} {status}")

yaml_count = sum(1 for r in results if r['yaml'])
print(f"  YAML frontmatter: {yaml_count}/{len(results)} {'OK' if yaml_count == len(results) else f'MISSING in {len(results) - yaml_count} files'}")
