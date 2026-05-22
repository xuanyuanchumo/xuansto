# 文档自动修复器 (Document Auto Fixer)

专门针对文档问题的自动修复器，支持Markdown文档的链接修复和格式修复。

## 功能特性

### 1. 链接自动修复

- **断裂链接检测**: 自动检测Markdown文档中的断裂链接
- **智能路径定位**: 通过文件缓存快速定位正确的文件路径
- **自动修复**: 自动更新链接引用到正确路径
- **支持类型**:
  - Markdown链接 `[text](url)`
  - 图片链接 `![alt](url)`
  - HTML链接 `href="url"`

### 2. 格式自动修复

- **编码问题修复**: 自动修复常见的编码错误（如乱码字符）
- **Markdown语法修复**: 
  - 标题后缺少空格
  - 列表项后缺少空格
- **图片alt文本**: 自动为缺少alt文本的图片添加描述
- **格式一致性**: 保持文档格式的一致性

### 3. 修复验证

- **预览功能**: 在应用修复前预览修改内容
- **差异对比**: 显示修改前后的差异
- **修复报告**: 生成详细的修复报告
- **批量处理**: 支持批量处理多个文档

## 安装使用

### 基本使用

```python
from doc_auto_fixer import DocumentAutoFixer

# 创建修复器实例
fixer = DocumentAutoFixer()

# 检测文档问题
issues = fixer.detect_issues("README.md")
print(f"检测到 {len(issues)} 个问题")

# 预览修复结果
report = fixer.preview_fix("README.md")
print(f"将修复 {report.fixed_issues} 个问题")

# 应用修复
report = fixer.apply_fix("README.md")
print(f"已修复 {report.fixed_issues} 个问题")
```

### 批量处理

```python
from doc_auto_fixer import DocumentAutoFixer

fixer = DocumentAutoFixer()

# 批量处理多个文件
file_paths = ["README.md", "docs/guide.md", "docs/api.md"]
reports = fixer.batch_fix(file_paths, auto_apply=False)

# 查看批量处理结果
for report in reports:
    print(f"{report.file_path}: 修复 {report.fixed_issues} 个问题")
```

### 自定义项目根目录

```python
from pathlib import Path
from doc_auto_fixer import DocumentAutoFixer

# 指定项目根目录
project_root = Path("/path/to/project")
fixer = DocumentAutoFixer(project_root=project_root)

# 修复文档
report = fixer.fix_document("docs/README.md")
```

## 命令行使用

```bash
# 预览修复结果
python doc_auto_fixer.py README.md --preview

# 应用修复
python doc_auto_fixer.py README.md --apply

# 批量修复
python doc_auto_fixer.py --batch files.json --apply
```

## API 参考

### DocumentAutoFixer

主类，提供文档自动修复功能。

#### 方法

- `detect_issues(file_path)`: 检测文档问题
- `preview_fix(file_path)`: 预览修复结果（不修改文件）
- `apply_fix(file_path)`: 应用修复（修改文件）
- `batch_fix(file_paths, auto_apply)`: 批量处理文档
- `generate_report_summary(report)`: 生成修复报告摘要

### LinkFixer

链接修复器，专门处理链接相关问题。

#### 方法

- `detect_broken_links(content, file_path)`: 检测断裂链接
- `fix_link(issue)`: 修复链接问题

### FormatFixer

格式修复器，专门处理格式相关问题。

#### 方法

- `detect_format_issues(content, file_path)`: 检测格式问题
- `fix_format(issue)`: 修复格式问题

## 问题类型

### DocIssueType

- `BROKEN_LINK`: 断裂的链接
- `BROKEN_IMAGE_LINK`: 断裂的图片链接
- `ENCODING_ERROR`: 编码错误
- `MARKDOWN_SYNTAX_ERROR`: Markdown语法错误
- `MISSING_ALT_TEXT`: 缺少alt文本
- `FORMAT_ERROR`: 格式错误
- `INCONSISTENT_FORMAT`: 格式不一致

## 修复状态

### FixStatus

- `SUCCESS`: 修复成功
- `PARTIAL`: 部分修复
- `FAILED`: 修复失败
- `SKIPPED`: 跳过修复
- `NEEDS_MANUAL_REVIEW`: 需要人工审查

## 测试

运行测试以验证功能：

```bash
python test_doc_auto_fixer.py
```

测试覆盖：
- 链接检测和修复
- 格式问题检测和修复
- 完整工作流
- 批量处理

## 示例

查看 `doc_auto_fixer_example.py` 获取更多使用示例。

## 注意事项

1. **备份重要文件**: 在应用修复前，建议备份重要文档
2. **预览修复**: 使用 `preview_fix()` 查看修改内容
3. **人工审查**: 某些修复可能需要人工审查确认
4. **项目根目录**: 确保正确设置项目根目录以便链接定位

## 版本历史

### v1.0.0 (2026-04-01)

- 初始版本
- 实现链接自动修复功能
- 实现格式自动修复功能
- 支持批量处理
- 提供预览和报告功能

## 许可证

MIT License
