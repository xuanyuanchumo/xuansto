import re, os

base = r'd:\Projects\TraeProjects\skiller\.trae\skills\xuansto-skill\workflows'

for f in ['security-audit','acceptance','performance-test']:
    path = os.path.join(base, f + '.md')
    with open(path, 'r', encoding='utf-8', errors='replace') as fh:
        content = fh.read()
    m = re.match(r'^---\r?\n(.*?)\r?\n---', content, re.DOTALL)
    body = content[m.end():] if m else content

    phase_pattern = re.compile(r'^###\s+阶段[\d.]+[：:]\s*(.+?)(?:[（(](.+?)[)）])?\s*$', re.MULTILINE)
    phases = phase_pattern.findall(body)

    print(f'=== {f} ===')
    for i, (cn_name, en_name) in enumerate(phases):
        print(f'  Phase {i+1}: {cn_name} ({en_name})')
    print()
