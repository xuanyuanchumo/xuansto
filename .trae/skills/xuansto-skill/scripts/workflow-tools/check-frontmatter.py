import yaml, re, os, sys

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
for m in re.finditer(r'\| (GATE-\d+|DESIGN-\w+|TEST-PASS|SPEC-CONSISTENCY|AGENTIC-SECURITY|AI-PENTEST|VISUAL-REGRESSION|ACCESSIBILITY|PERFORMANCE|UX-ACCEPTANCE|INFRA-HEALTH|DOC-COMPLETENESS|SIMPLIFICATION-BEHAVIOR|CHESTERTON-FENCE|DESKTOP-\w+|IPC-CONTRACT|TOKEN-BUDGET|SCRIPT-SECURITY|SCRIPT-CLEANUP|BRAINSTORM-COMPLETE|PLAN-ATOMIC|SUBAGENT-REVIEW|PLAYWRIGHT-E2E-PASS|VISUAL-REGRESSION-PASS|CONSOLE-ERROR-FREE|LOOP-COMPLETION|ITERATION-BUDGET|PLAN-PERSISTENCE|SESSION-RECOVERY|REVIEW-CONFIDENCE|MULTI-PERSPECTIVE-COVERAGE|FILE-ENCODING|COMMENT-LANGUAGE) ', content):
    valid_gates.add(m.group(1))

gate_aliases = {
    'REQ-COMPLETENESS': 'GATE-001', 'SPEC-DOC-CONSISTENCY': 'GATE-002',
    'ARCH-REVIEW': 'GATE-003', 'CONTRACT': 'GATE-004',
    'COVERAGE': 'GATE-005', 'TEST-DESIGN': 'GATE-006',
    'LINT': 'GATE-007', 'CODE-REVIEW': 'GATE-009',
    'E2E-TEST': 'GATE-011', 'SECURITY': 'GATE-012',
    'SPEC-DRIFT': 'SPEC-CONSISTENCY', 'AGENTIC-SEC': 'AGENTIC-SECURITY',
    'AI-PENTEST': 'AI-PENTEST', 'VISUAL-REG': 'VISUAL-REGRESSION',
    'A11Y': 'ACCESSIBILITY', 'PERFORMANCE': 'PERFORMANCE',
    'DEPLOY-READY': 'GATE-013', 'PROD-VERIFY': 'GATE-014',
    'UAT': 'GATE-013', 'ITERATION-CLOSE': 'GATE-015',
    'DOCUMENTATION': 'DOC-COMPLETENESS',
}

valid_agents = set()
with open(os.path.join(ref_base, 'agent-registry.md'), 'r', encoding='utf-8') as f:
    content = f.read()
for m in re.finditer(r'\|\s+(\S+(?:\s+\S+)*?)\s+\|.*?\|.*?\|.*?\|', content):
    name = m.group(1).strip()
    if name and name != '名称' and not name.startswith('---'):
        agent_key = name.lower().replace(' ', '-')
        valid_agents.add(agent_key)

def read_file(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as fh:
        return fh.read()

for f in files:
    path = os.path.join(base, f + '.md')
    content = read_file(path)
    m = re.match(r'^---\r?\n(.*?)\r?\n---', content, re.DOTALL)
    if not m:
        print(f'{f}: NO FRONTMATTER')
        continue
    fm_text = m.group(1)
    try:
        data = yaml.safe_load(fm_text)
    except Exception as e:
        print(f'{f}: YAML PARSE ERROR: {e}')
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
            if gid not in valid_gates and gid not in gate_aliases:
                issues.append(f'phase[{i}]({pid}) invalid quality_gate: {gid}')
        agents_in_phase = p.get('agents', {})
        for role in ['primary', 'supporting']:
            for agent in agents_in_phase.get(role, []):
                if agent not in valid_agents:
                    issues.append(f'phase[{i}]({pid}) invalid agent: {agent} (role: {role})')

    am = data.get('agent_matrix', {})
    if not am:
        issues.append('agent_matrix is empty')
    else:
        for agent_name, agent_info in am.items():
            if agent_name not in valid_agents:
                issues.append(f'agent_matrix invalid agent: {agent_name}')
            for phase_ref in agent_info.get('phases', []):
                if phase_ref not in phase_ids:
                    issues.append(f'agent_matrix({agent_name}) invalid phase ref: {phase_ref}')

    eh = data.get('exception_handling', {})
    for key in ['phase_failure','agent_unavailable','quality_gate_blocked']:
        if key not in eh:
            issues.append(f'exception_handling missing: {key}')

    body = content[m.end():]
    phase_headers = re.findall(r'^##\s+Phase\s+(\d+)', body, re.MULTILINE)
    yaml_phase_count = len(phases)
    md_phase_count = len(phase_headers)
    if yaml_phase_count != md_phase_count:
        issues.append(f'phase count mismatch: yaml={yaml_phase_count} md={md_phase_count} (md phases: {phase_headers})')

    if issues:
        print(f'{f}:')
        for iss in issues:
            print(f'  - {iss}')
    else:
        print(f'{f}: OK (phases={yaml_phase_count})')
