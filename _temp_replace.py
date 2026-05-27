import os

root = r'c:\Users\86156\.trae-cn\worktrees\skiller\feat-develop-main-branch-H3MhdQ\.trae\skills\xuansto-skill-v2\scripts\knowledge_server'
count = 0
old = 'make_response("ok"'
new = 'make_response("success"'

for dirpath, dirnames, filenames in os.walk(root):
    for fn in filenames:
        if fn.endswith('.py'):
            fp = os.path.join(dirpath, fn)
            with open(fp, 'r', encoding='utf-8') as f:
                content = f.read()
            new_content = content.replace(old, new)
            if new_content != content:
                with open(fp, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                count += 1
                print(f'Updated: {fp}')

print(f'Total files updated: {count}')
