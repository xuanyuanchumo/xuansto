import yaml, re, os

base = r'd:\Projects\TraeProjects\skiller\.trae\skills\xuansto-skill\workflows'
ref_base = r'd:\Projects\TraeProjects\skiller\.trae\skills\xuansto-skill\references'

files = [
    'sdd-tdd-full','sdd-tdd-medium','sdd-tdd-fast','ui-ux-workflow',
    'desktop-build-workflow','security-audit','ai-pentest','acceptance',
    'bug-fix','cross-platform-workflow','flutter-desktop-workflow',
    'performance-test','brainstorming-workflow','subagent-driven-workflow',
    'webapp-testing-workflow'
]

valid_gates = set()
with open(os.path.join(ref_base, 'quality-gates.md'), 'r', encoding='utf-8') as f:
    content = f.read()
for line in content.split('\n'):
    if line.startswith('|') and not line.startswith('| ---') and not line.startswith('| 阶段') and not line.startswith('| 门禁ID'):
        parts = [p.strip() for p in line.split('|')]
        if len(parts) > 2 and parts[1]:
            gate_id = parts[1]
            if gate_id and gate_id not in ('名称', '') and not gate_id.startswith('**'):
                valid_gates.add(gate_id)

valid_agents = set()
with open(os.path.join(ref_base, 'agent-registry.md'), 'r', encoding='utf-8') as f:
    content = f.read()
for m in re.finditer(r'\|\s+([A-Z][a-zA-Z\s]+?)\s+\|', content):
    name = m.group(1).strip()
    if name and name != '名称':
        agent_key = name.lower().replace(' ', '-')
        valid_agents.add(agent_key)

print(f'Valid gates ({len(valid_gates)}): {sorted(valid_gates)}')
print(f'Valid agents ({len(valid_agents)}): {sorted(valid_agents)}')
print()

all_ok = True
for f in files:
    path = os.path.join(base, f + '.md')
    with open(path, 'r', encoding='utf-8', errors='replace') as fh:
        content = fh.read()
    m = re.match(r'^---\r?\n(.*?)\r?\n---', content, re.DOTALL)
    if not m:
        print(f'{f}: NO FRONTMATTER')
        all_ok = False
        continue

    try:
        data = yaml.safe_load(m.group(1))
    except Exception as e:
        print(f'{f}: YAML PARSE ERROR: {e}')
        all_ok = False
        continue

    issues = []

    meta = data.get('metadata', {})
    for key in ['name','version','description','platform','min_agents','max_agents']:
        if key not in meta:
            issues.append(f'metadata missing: {key}')

    phases = data.get('phases', [])
    phase_ids = set()
    for i, p in enumerate(phases):
        pid = p.get('id', '?')
        phase_ids.add(pid)
        for key in ['id','name','order','trigger_condition','agents','inputs','outputs','quality_gates']:
            if key not in p:
                issues.append(f'phase[{i}]({pid}) missing: {key}')
        for g in p.get('quality_gates', []):
            gid = g.get('gate_id', '')
            if gid not in valid_gates:
                issues.append(f'phase[{i}]({pid}) invalid quality_gate: {gid}')

    am = data.get('agent_matrix', {})
    if not am:
        issues.append('agent_matrix is empty')

    eh = data.get('exception_handling', {})
    for key in ['phase_failure','agent_unavailable','quality_gate_blocked']:
        if key not in eh:
            issues.append(f'exception_handling missing: {key}')

    if issues:
        all_ok = False
        print(f'{f}:')
        for iss in issues:
            print(f'  - {iss}')
    else:
        print(f'{f}: OK (phases={len(phases)})')

print()
if all_ok:
    print('ALL FILES PASSED VALIDATION')
else:
    print('SOME FILES HAVE ISSUES')
