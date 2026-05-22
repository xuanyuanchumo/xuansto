from app.main import app

print("=== New API Endpoints ===")
print()

skill_health_endpoints = []
path_validation_endpoints = []
evolution_knowledge_endpoints = []

for route in app.routes:
    if not hasattr(route, 'path'):
        continue
    path = route.path
    methods = ','.join(route.methods) if hasattr(route, 'methods') and route.methods else 'WS'
    
    if '/skill/health' in path:
        skill_health_endpoints.append((methods, path))
    elif '/skill/paths' in path:
        path_validation_endpoints.append((methods, path))
    elif '/evolution/patterns' in path or '/evolution/recommendations' in path or '/evolution/predict' in path or '/evolution/trigger' in path or '/evolution/status' in path or '/evolution/history' in path or '/evolution/statistics' in path or '/evolution/ws' in path:
        evolution_knowledge_endpoints.append((methods, path))

print("=== Skill Health API ===")
for methods, path in skill_health_endpoints:
    print(f"{methods:8} {path}")

print()
print("=== Path Validation API ===")
for methods, path in path_validation_endpoints:
    print(f"{methods:8} {path}")

print()
print("=== Evolution Knowledge API ===")
for methods, path in evolution_knowledge_endpoints:
    print(f"{methods:8} {path}")

print()
print(f"Total new endpoints: {len(skill_health_endpoints) + len(path_validation_endpoints) + len(evolution_knowledge_endpoints)}")
