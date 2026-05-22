import os
import re
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--skill-dir', default=os.getcwd())
args = parser.parse_args()
base = args.skill_dir

with open(os.path.join(base, 'references', 'quality-gates.md'), 'r', encoding='utf-8') as f:
    qg_content = f.read()

gate_ids = set()
for m in re.finditer(r'^\|\s*([A-Z][A-Z0-9_\-]+[A-Z0-9])\s*\|', qg_content, re.MULTILINE):
    val = m.group(1)
    if val not in ('ID', 'BLOCK', 'WARN', 'YES', 'NO', 'BLOCK+WARN'):
        gate_ids.add(val)

print(f"=== QUALITY GATE IDs in quality-gates.md: {len(gate_ids)} ===")
for g in sorted(gate_ids):
    print(f"  {g}")
print()

wf_dir = os.path.join(base, 'workflows')
mismatches = []

for fn in sorted(os.listdir(wf_dir)):
    if not fn.endswith('.md'):
        continue
    fp = os.path.join(wf_dir, fn)
    if '_yaml' in fp:
        continue

    wf_name = fn[:-3]
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()

    wf_gates = set()

    yaml_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if yaml_match:
        yaml_text = yaml_match.group(1)
        for m in re.finditer(r'([A-Z][A-Z0-9_\-]+[A-Z0-9])', yaml_text):
            val = m.group(1)
            if val in gate_ids:
                wf_gates.add(val)

    qg_section = re.search(r'质量门禁(.+?)(?=\n---\n|\n## |\Z)', content, re.DOTALL)
    if qg_section:
        section_text = qg_section.group(1)
        for m in re.finditer(r'([A-Z][A-Z0-9_\-]+[A-Z0-9])', section_text):
            val = m.group(1)
            if val not in ('BLOCK', 'WARN', 'YES', 'NO', 'BLOCK+WARN'):
                if val in gate_ids:
                    wf_gates.add(val)
                else:
                    if re.match(r'^(GATE|TEST|REVIEW|SEC|PERF|DOC|UX|DESKTOP|IPC|LOOP|PLAN|SESSION|SIMPLIFY|CHESTERTON|BRAIN|SUBAGENT|PLAYWRIGHT|VISUAL|CONSOLE|SPEC|AGENTIC|AI|ANTI|DESIGN|ACCESS|INFRA|TOKEN|SCRIPT|FILE|COMMENT|MULTI)', val):
                        wf_gates.add(val)

    for m in re.finditer(r'(?:gate[_\s:]*(?:id)?|门禁标识|quality_gate)\s*[:=]?\s*([A-Z][A-Z0-9_\-]+[A-Z0-9])', content, re.IGNORECASE):
        val = m.group(1)
        if val not in ('BLOCK', 'WARN', 'YES', 'NO'):
            wf_gates.add(val)

    if qg_section:
        section_text = qg_section.group(1)
        for m in re.finditer(r'\|\s*([A-Z][A-Z0-9_\-]+[A-Z0-9])\s*\|', section_text):
            val = m.group(1)
            if val not in ('BLOCK', 'WARN', 'YES', 'NO', 'BLOCK+WARN'):
                wf_gates.add(val)

    wf_mismatches = []
    for gate in sorted(wf_gates):
        if gate not in gate_ids:
            wf_mismatches.append(gate)
            mismatches.append(f"  {wf_name} -> Gate NOT in quality-gates.md: '{gate}'")

    gates_str = ', '.join(sorted(wf_gates)) if wf_gates else '(none)'
    mismatch_str = f" [MISMATCH: {', '.join(wf_mismatches)}]" if wf_mismatches else ""
    print(f"Workflow: {wf_name} -> Gates: {gates_str}{mismatch_str}")

print()
print("=== WORKFLOW-GATE MISMATCHES ===")
if not mismatches:
    print("No mismatches found. All workflow-gate references are consistent.")
else:
    print(f"Found {len(mismatches)} mismatches:")
    for m in mismatches:
        print(m)
