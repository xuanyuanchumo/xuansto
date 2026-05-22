import py_compile
import os

base = r'd:\Projects\TraeProjects\skiller\.trae\skills\sanliu'
files = [
    'skillscripts/core/path_config_center.py',
    'skillscripts/pipeline/sdd_tdd_fusion_engine.py',
    'backend/app/api/realtime_quality.py',
    'backend/app/api/health_comprehensive.py',
    'skillscripts/pipeline/pipeline_intelligence.py',
    'skillscripts/core/department_logic_checker.py',
    'skillscripts/core/skill_call_chain_checker.py',
    'skillscripts/pipeline/ui_ux_integration.py',
    'skillscripts/core/continuous_evolution_controller.py',
]

print("Syntax Check for Critical Files")
print("=" * 50)

errors = []
for f in files:
    full_path = os.path.join(base, f)
    try:
        py_compile.compile(full_path, doraise=True)
        print(f"PASS: {f}")
    except py_compile.PyCompileError as e:
        errors.append((f, str(e)))
        print(f"FAIL: {f}")

print("=" * 50)
if errors:
    print(f"RESULT: {len(errors)} files have syntax errors")
else:
    print("RESULT: All critical files pass syntax check")
