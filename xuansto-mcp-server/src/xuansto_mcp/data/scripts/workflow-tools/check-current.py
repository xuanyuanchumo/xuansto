import yaml, re, os

base = r'd:\Projects\TraeProjects\skiller\.trae\skills\xuansto-skill\workflows'
for f in ['security-audit','acceptance','performance-test']:
    path = os.path.join(base, f + '.md')
    with open(path, 'r', encoding='utf-8', errors='replace') as fh:
        content = fh.read()
    m = re.match(r'^---\r?\n(.*?)\r?\n---', content, re.DOTALL)
    if m:
        data = yaml.safe_load(m.group(1))
        phases = data.get('phases', [])
        print(f'{f}: {len(phases)} phases in YAML')
        for p in phases:
            pid = p.get('id', '?')
            pname = p.get('name', '?')
            print(f'  - {pid}: {pname}')
    else:
        print(f'{f}: NO FRONTMATTER')
