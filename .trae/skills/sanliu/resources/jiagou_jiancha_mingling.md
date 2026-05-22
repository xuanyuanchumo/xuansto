# 架构检查命令资源

## 架构检查命令示例

```bash
grep -r "class " --include="*.py" | grep -E "(Manager|Handler|Controller|Service|Util)"
python -c "import module_dependency; module_dependency.analyze('src/')"
radon cc src/ -a -s
radon cc src/ -s --total-average
pyreverse -o png -p ProjectName src/
```

## 架构检查配置

```yaml
architecture_check:
  commands:
    - name: "耦合度分析"
      tool: "radon"
      command: "radon cc src/ -s"
      
    - name: "依赖分析"
      tool: "pydeps"
      command: "pydeps src/ --no-output -T png"
      
  thresholds:
    max_class_methods: 15
    max_class_lines: 500
    max_inheritance_depth: 4
    max_coupling_between_objects: 20
    min_cohesion: 0.5
```
