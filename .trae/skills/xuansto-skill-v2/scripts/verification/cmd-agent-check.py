import os
import re
import glob
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--skill-dir', default=os.getcwd())
args = parser.parse_args()
base = args.skill_dir

with open(os.path.join(base, 'references', 'agent-registry.md'), 'r', encoding='utf-8') as f:
    registry = f.read()

title_agents = set()
for line in registry.split('\n'):
    m = re.match(r'^\|\s*([A-Z][A-Za-z\s&/\-]+[A-Za-z])\s*\|', line)
    if m:
        name = m.group(1).strip()
        if name not in ('名称', '下游Agent', 'Agent组', '合计'):
            title_agents.add(name)

agent_dir = os.path.join(base, 'agents')
kebab_agents = set()
for root, dirs, files in os.walk(agent_dir):
    for fn in files:
        if fn.endswith('.md'):
            kebab_agents.add(fn[:-3])

def title_to_kebab(title):
    k = title.lower().replace(' ', '-').replace('&', '').replace('/', '-')
    k = re.sub(r'-+', '-', k)
    return k.strip('-')

title_kebab_map = {}
for k in kebab_agents:
    parts = k.split('-')
    t = ' '.join(p.capitalize() for p in parts)
    title_kebab_map[t] = k

title_kebab_map['Full-Stack Engineer'] = 'fullstack-engineer'
title_kebab_map['Build & Release Engineer'] = 'build-release-engineer'
title_kebab_map['CI/CD Specialist'] = 'cicd-specialist'
title_kebab_map['Subagent Dispatcher'] = 'subagent-dispatcher'
title_kebab_map['E2E Tester'] = 'e2e-tester'
title_kebab_map['AI Penetration Tester'] = 'ai-penetration-tester'
title_kebab_map['DBA'] = 'dba'

print("=== REGISTERED AGENTS ===")
print(f"Title Case agents: {len(title_agents)}")
print(f"Kebab Case agents: {len(kebab_agents)}")
print()

cmd_dir = os.path.join(base, 'commands')
mismatches = []
all_cmd_agents = {}

for fn in sorted(os.listdir(cmd_dir)):
    if not fn.endswith('.md'):
        continue
    cmd_name = fn[:-3]
    with open(os.path.join(cmd_dir, fn), 'r', encoding='utf-8') as f:
        content = f.read()

    agent_section = re.search(r'涉及Agent(.+?)(?=\n---\n|\n## )', content, re.DOTALL)
    if not agent_section:
        print(f"Command: /{cmd_name} -> NO '涉及Agent' section found!")
        continue

    section_text = agent_section.group(1)

    cmd_agents = set()

    for m in re.finditer(r'\|\s*([a-z][a-z0-9\-]+[a-z0-9])\s*\|', section_text):
        val = m.group(1)
        if val not in ('agent',):
            cmd_agents.add(val)

    for m in re.finditer(r'\|\s*([A-Z][A-Za-z\s&/\-]+[A-Za-z0-9])\s*\|', section_text):
        val = m.group(1).strip()
        if val not in ('Agent',):
            cmd_agents.add(val)

    all_cmd_agents[cmd_name] = cmd_agents

    for agent in sorted(cmd_agents):
        found = False
        if agent in kebab_agents:
            found = True
        elif agent in title_agents:
            found = True
        elif agent in title_kebab_map.values():
            found = True
        elif agent in title_kebab_map:
            found = True
        else:
            if re.match(r'^[a-z]', agent):
                found = agent in kebab_agents
            else:
                k = title_to_kebab(agent)
                found = k in kebab_agents

        if not found:
            mismatches.append(f"  /{cmd_name} -> Agent NOT in registry: '{agent}'")

    agents_str = ', '.join(sorted(cmd_agents)) if cmd_agents else '(none)'
    print(f"Command: /{cmd_name} -> Agents: {agents_str}")

print()
print("=== COMMAND-AGENT MISMATCHES ===")
if not mismatches:
    print("No mismatches found. All command-agent references are consistent.")
else:
    print(f"Found {len(mismatches)} mismatches:")
    for m in mismatches:
        print(m)
