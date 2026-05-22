---
name: xukezheng_shenji_si
description: 许可证审计司，负责开源许可证合规性检查、许可证冲突检测。工具集成License-checker/FOSSA/spdx-tools。
---

# 许可证审计司技能指令

## 职责定义

许可证审计司作为合规审计局的知识产权核心，承担以下职责：

| 职责类别 | 具体职责 | 关键产出 |
|----------|----------|----------|
| **许可证识别** | 开源组件许可证类型识别 | 许可证清单 |
| **合规性检查** | 许可证义务与使用方式匹配检查 | 合规报告 |
| **冲突检测** | 许可证间兼容性/冲突检测 | 冲突报告 |
| **策略执行** | 组织许可证白名单/黑名单策略执行 | 策略执行记录 |

---

## 许可证知识库

### 常见开源许可证分类

```yaml
license_taxonomy:
  
  permissive_licenses:
    category: "宽松许可"
    description: "几乎无限制，可闭源使用"
    examples:
      - id: "MIT"
        name: "MIT License"
        obligations: ["保留版权声明和许可证文本"]
        can_close_source: true
        can_modify: true
        can_sublicense: true
        commercial_use: true
        risk_level: "very_low"
        
      - id: "Apache-2.0"
        name: "Apache License 2.0"
        obligations: ["保留版权声明、许可证文本和NOTICE文件"]
        patent_grant: true
        can_close_source: true
        can_modify: true
        commercial_use: true
        risk_level: "very_low"
        
      - id: "BSD-2-Clause"
        name: "BSD 2-Clause License"
        obligations: ["保留版权声明和许可证文本"]
        can_close_source: true
        risk_level: "very_low"
        
      - id: "BSD-3-Clause"
        name: "BSD 3-Clause License"
        obligations: ["保留版权声明，不得用项目名背书"]
        can_close_source: true
        risk_level: "low"
        
      - id: "ISC"
        name: "ISC License"
        obligations: similar_to: "MIT (simplified)"
        risk_level: "very_low"
        
  copyleft_licenses:
    category: "著佐权（传染性）"
    description: "修改后的代码必须以相同许可证开源"
    
    weak_copyleft:
      subcategory: "弱著佐权（文件级传染）"
      examples:
        - id: "LGPL-2.1"
          name: "GNU Lesser General Public License v2.1"
          obligations: [
            "链接时提供库源代码或允许替换",
            "保留版权声明和许可证文本"
          ]
          file_level_infection: true  # 仅修改的文件需要开源
          project_level_infection: false
          static_link_risk: "medium"  # 静态链接可能触发GPL传染
          dynamic_link_allowed: true
          can_close_source: "部分（仅自有代码）"
          
        - id: "LGPL-3.0"
          name: "GNU Lesser General Public License v3.0"
          similar_to: "LGPL-2.1 but with stronger terms"
          additional_requirements: "Anti-Tivoization clause"
          
        - id: "MPL-2.0"
          name: "Mozilla Public License 2.0"
          obligations: [
            "修改的文件必须以MPL开源",
            "保留原有许可证",
            "提供Source Code Form"
          ]
          file_level_infection: true
          can_combine_with: ["GPL-2.0+", "Apache-2.0", "LGPL"]
          compatibility: "good"
          
    strong_copyleft:
      subcategory: "强著佐权（项目级传染）"
      examples:
        - id: "GPL-2.0"
          name: "GNU General Public License v2.0"
          obligations: [
            "整个派生作品必须以GPL-2.0开源",
            "提供完整源代码",
            "保留版权声明和许可证",
            "说明修改内容"
          ]
          project_level_infection: true  # 整个项目受影响
          can_close_source: false
          can_use_in_proprietary_software: "only_as_separate_process"
          compatibility_warning: "与Apache-2.0不兼容！"
          
        - id: "GPL-3.0"
          name: "GNU General Public License v3.0"
          obligations: "类似GPL-2.0但更严格"
          additional: ["Anti-Tivoization (用户可安装修改版软件)"]
          patent_termination: "explicit (专利侵权则授权终止)"
          
        - id: "AGPL-3.0"
          name: "Affero General Public License v3.0"
          obligations: "GPL-3.0 + 网络交互条款"
          network_provision: true  # SaaS场景也需提供源码
          cloud_risk: "high"  # 云服务部署需特别注意
          
  proprietary_and_special:
    category: "专有及特殊许可证"
    examples:
      - id: "Proprietary"
        name: "专有许可证"
        use_restriction: "不可用于开源项目"
        action: "reject_or_seek_alternative"
        
      - id: "CC-BY-NC"
        name: "Creative Commons Non-Commercial"
        restriction: "禁止商业用途"
        commercial_project_compatible: false
        
      - id: "SSPL"
        name: "Server Side Public License"
        controversy: "high (MongoDB引发争议)"
        cloud_restriction: "SaaS化需购买商业许可"
```

### 许可证兼容性矩阵

```yaml
license_compatibility_matrix:
  # 格式: license_A + license_B = compatible?
  # Y=兼容, N=不兼容, P=有条件兼容, ?=需法律评估
  
  MIT:
    Apache-2.0: "Y"
    BSD: "Y"
    GPL: "Y"  # MIT代码可并入GPL项目
    LGPL: "Y"
    MPL: "Y"
    
  Apache-2.0:
    GPL-2.0: "N"  # ⚠️ 不兼容！Apache-2.0的专利终止条款与GPL-2.0冲突
    GPL-3.0: "Y"  # Apache-2.0明确兼容GPL-3.0+
    LGPL: "Y"
    MPL-2.0: "Y"
    
  GPL-2.0:
    Apache-2.0: "N"  # ⚠️ 双向不兼容
    MIT: "Y"  # 接收更宽松许可的代码没问题
    
  GPL-3.0:
    Apache-2.0: "Y"
    MIT: "Y"
    LGPL-3.0: "Y"
    AGPL-3.0: "Y"
    
  MPL-2.0:
    GPL: "P"  # 可作为并存文件存在，但不能合并为单一文件
    Apache-2.0: "Y"
    LGPL: "Y"
    
  compatibility_rules_summary:
    rule_1: "宽松许可(Permissive)可以合入任何许可证的项目"
    rule_2: "强Copyleft(GPL)项目只能接收同等级或更宽松的代码"
    rule_3: "GPL-2.0与Apache-2.0不兼容（专利条款冲突）"
    rule_4: "MPL是'中间地带'，文件级感染，与其他多数许可兼容"
    rule_5: "AGPL对云服务/SaaS场景有额外要求"
```

---

## 工具集成

### 核心工具链

| 工具 | 用途 | 特点 |
|------|------|------|
| **license-checker** | Node.js依赖许可证扫描 | npm生态原生支持 |
| **FOSSA** | 企业级合规平台 | SaaS，深度分析+自动化修复 |
| **spdx-tools** | SPDX标准格式生成/解析 | 互操作性标准 |
| ** licensee** | CLI许可证检测器 | 快速识别文件许可证 |
| **scancode-toolkit** | 全面许可证扫描 | 支持多语言、深度检测 |

### 工具配置模板

```yaml
tool_configurations:
  license_checker:
    config_file: ".license-checker-config.json"
    settings: {
      "exclude": [
        "**/test/**",
        "**/tests/**",
        "**/node_modules/**",
        "**/*.min.js",
        "**/dist/**",
        ".git"
      ],
      "excludePrivatePackages": true,
      "onlyAllow": [  # 白名单模式
        "MIT",
        "Apache-2.0",
        "BSD-2-Clause",
        "BSD-3-Clause",
        "ISC",
        "0BSD",
        "Unlicense"
      ],
      "output": {
        "format": ["json", "table", "markdown"],
        "path": "reports/license-audit/"
      }
    }
    
  spdx_tools:
    output_format: "SPDX 2.3 (JSON + tag-value)"
    document_namespace: "https://company.com/spdx/project-name"
    creator: {
      "Tool": "spdxtools-0.7.0",
      "Organization": "Company Name - Compliance Team"
    }
    
  scancode:
    scan_mode: "full"  # or "quick" for faster scans
    output_formats: ["json-pp", "spdx-tv", "html"]
    license_score_threshold: 100  # 0-100, higher=more confident
    include_text_matches: true  # 记录匹配到的许可证文本位置
```

---

## 工作流程

### 阶段一：依赖清单生成

```
触发审计（定期/PR事件/手动）
    ↓
[1] 解析包管理文件
    ↓
[2] 构建完整依赖树
    ↓
[3] 识别直接和传递依赖
    ↓
[4] 收集版本信息
    ↓
[5] 生成初始清单
    ↓
进入许可证识别阶段
```

#### 多语言依赖解析

```yaml
dependency_resolution:
  package_managers:
    python:
      manifest_files: ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile"]
      resolver: "pip-tools or pipdeptree"
      lock_files: ["requirements.lock", "Pipfile.lock"]
      
    javascript:
      manifest_files: ["package.json"]
      resolver: "npm ls --all || yarn why"
      lock_files: ["package-lock.json", "yarn.lock"]
      
    java:
      manifest_files: ["pom.xml", "build.gradle"]
      resolver: "mvn dependency:tree || gradle dependencies"
      
    go:
      manifest_files: ["go.mod"]
      resolver: "go mod graph"
      
    rust:
      manifest_files: ["Cargo.toml"]
      resolver: "cargo tree"
      
  dependency_tree_output_format:
    json: |
      {
        "project_name": "my-project",
        "scan_timestamp": "2024-01-08T14:30:00Z",
        "dependencies": [
          {
            "name": "express",
            "version": "4.18.2",
            "type": "direct",
            "license": "MIT",
            "repository": "https://github.com/expressjs/express",
            "homepage": "http://expressjs.com/",
            "transitive_dependencies": [
              {
                "name": "accepts",
                "version": "1.3.8",
                "type": "transitive",
                "license": "MIT",
                "required_by": ["express@4.18.2"]
              },
              {
                "name": "body-parser",
                "version": "1.20.1",
                "license": "MIT"
              },
              {
                "name": "cookie",
                "version": "0.5.0",
                "license": "MIT"
              }
            ]
          },
          {
            "name": "sequelize",
            "version": "6.35.0",
            "type": "direct",
            "license": "MIT",
            "transitive_dependencies": [
              {
                "name": "lodash",
                "version": "4.17.21",
                "license": "MIT"
              }
            ]
          }
        ],
        "statistics": {
          "total_direct_dependencies": 25,
          "total_transitive_dependencies": 180,
          "unique_packages": 155,
          "licenses_found": {
            "MIT": 85,
            "Apache-2.0": 42,
            "BSD-3-Clause": 15,
            "ISC": 10,
            "unknown": 3
          }
        }
      }
```

---

### 阶段二：许可证识别与分类

```
依赖清单完成
    ↓
[1] 查询许可证数据库
    ↓
[2] 解析包内嵌许可证文件
    ↓
[3] 使用AI辅助识别模糊情况
    ↓
[4] 分类到风险等级
    ↓
[5] 标记未知/自定义许可证
    ↓
输出许可证分类结果
```

#### 许可证识别流程详解

```python
"""
许可证识别引擎示例
"""

class LicenseIdentifier:
    """多源许可证识别器"""
    
    def __init__(self):
        self.spdx_license_list = self._load_spdx_database()
        self.known_exceptions = self._load_exception_patterns()
        
    def identify(self, package_name: str, package_version: str) -> LicenseResult:
        """
        综合多种方法识别许可证
        
        Priority:
        1. 包注册表声明的许可证（最权威）
        2. 包内的LICENSE/COPYING文件内容
        3. 文件头部的许可证声明
        4. SPDX表达式解析
        5. AI/ML辅助识别（最后手段）
        """
        
        result = LicenseResult(package=package_name, version=package_version)
        
        # Step 1: 从包注册表获取
        registry_license = self._query_package_registry(package_name)
        if registry_license:
            result.add_source("registry", registry_license, confidence=0.95)
            
        # Step 2: 扫描包内许可证文件
        file_licenses = self._scan_license_files(package_name)
        for lic in file_licenses:
            result.add_source("file_content", lic, confidence=0.90)
            
        # Step 3: 解析SPDX表达式
        if result.has_spdx_expression():
            parsed = self._parse_spdx_expression(result.spdx_expression)
            result.set_parsed_license(parsed)
            
        # Step 4: 处理未知/模糊情况
        if not result.is_confident():
            ai_result = self._ai_identify(result.raw_text)
            result.add_source("ai_assisted", ai_result, confidence=0.70)
            result.flag_for_manual_review()
            
        return result
        
    def _classify_risk(self, license_id: str) -> RiskClassification:
        """根据组织策略对许可证进行风险分类"""
        
        whitelist = self.load_whitelist()  # MIT, Apache-2.0, BSD, ISC...
        blacklist = self.load_blacklist()  # GPL-AGPL for certain uses, SSPL...
        graylist = self.load_graylist()   # LGPL, MPL (需要审核)
        
        if license_id in whitelist:
            return RiskClassification(level="approved", action="allow")
        elif license_id in blacklist:
            return RiskClassification(level="blocked", action="reject")
        elif license_id in graylist:
            return RiskClassification(level="review_required", 
                                    action="legal_review_needed")
        else:
            return RiskClassification(level="unknown", 
                                    action="manual_identification_needed")
```

---

### 阶段三：合规性检查与冲突检测

```
许可证识别完成
    ↓
[1] 对照组织白名单/黑名单
    ↓
[2] 检查许可证义务履行情况
    ↓
[3] 分析许可证间兼容性
    ↓
[4] 检测许可证冲突
    ↓
[5) 生成风险评估
    ↓
输出合规审计报告
```

#### 合规审计报告格式

```markdown
# 开源软件许可证合规审计报告

**报告编号**: LICENSE-AUDIT-20240108  
**审计日期**: 2024-01-08  
**审计范围**: 项目全量依赖  
**审计工具**: FOSSA + license-checker + scancode  
**编制**: 许可证审计司  

---

## 📊 执行摘要

### 总体评级: ⚠️ 有条件通过 (Conditional Pass)

| 指标 | 数值 | 状态 |
|------|------|------|
| 总依赖数 | 180 | - |
| 已识别许可证 | 177 (98.3%) | ✅ 良好 |
| 白名单许可证 | 152 (84.4%) | ✅ 合规 |
| 需审核(灰名单) | 22 (12.2%) | ⚠️ 待审 |
| 黑名单/阻止 | 1 (0.6%) | ❌ 违规 |
| 未知许可证 | 3 (1.7%) | 🔍 待查 |
| 许可证冲突 | 2 处 | ⚠️ 需解决 |

### 关键发现

- 🟢 **大部分依赖使用宽松许可证(MIT/Apache/BSD)**，合规风险低
- 🟡 **22个灰名单依赖(LGPL/MPL)**需要法务审核使用方式
- 🔴 **发现1个黑名单依赖(SSPL)**必须移除或获得例外批准
- ⚠️ **检测到2处潜在的许可证兼容性问题**

---

## 📋 详细审计结果

### ✅ 白名单依赖 (152项)

这些依赖使用完全合规的开源许可证：

| 许可证类型 | 数量 | 占比 | 示例 |
|------------|------|------|------|
| MIT | 85 | 47.2% | express, lodash, debug |
| Apache-2.0 | 42 | 23.3% | axios, webpack, react |
| BSD-3-Clause | 15 | 8.3% | sequelize-cli |
| ISC | 10 | 5.6% | winston, cors |
| 0BSD / Unlicense | 5 | 2.8% | - |

**状态**: ✅ 全部合规，无需特殊处理

---

### ⚠️ 灰名单依赖 - 需审核 (22项)

这些依赖使用有条件的开源许可证，需确认使用方式是否触发了额外义务：

| 包名 | 版本 | 许可证 | 风险点 | 审核建议 |
|------|------|--------|--------|----------|
| libxml2 | 2.9.14 | LGPL-2.1 | 动态链接OK，静态链接可能触发GPL | 确认链接方式 |
| Qt | 5.15.2 | LGPL-3.0 | 同上 + Anti-Tivoization | 确认部署形态 |
| Firefox SDK | 112.0 | MPL-2.0 | 修改的文件须开源 | 检查是否有修改 |
| ... | ... | ... | ... | ... |

**处理方案**: 提交法务团队审核，预计3个工作日

---

### ❌ 黑名单/阻止依赖 (1项)

| 包名 | 版本 | 许可证 | 问题 | 必要行动 |
|------|------|--------|------|----------|
| mongodb-driver-sync | 4.11.0 | **SSPL** | 商业SaaS使用需付费 | **立即移除** |

**问题详情**:
- SSPL (Server Side Public License) 要求：如果将此软件作为服务提供给第三方用户，必须公开所有服务端源代码（不仅是该软件本身）
- 这与我们产品的SaaS商业模式严重冲突
- MongoDB Inc. 已因SSPL在开源社区引发广泛争议

**替代方案**:
1. 切换至 PostgreSQL (PostgreSQL License / MIT-like)
2. 或使用 AWS DocumentDB / Azure Cosmos DB (托管服务)
3. 如确需MongoDB功能，购买MongoDB Enterprise商业许可

**截止日期**: 本周内完成迁移

---

### 🔍 未知许可证 (3项)

| 包名 | 版本 | 原因 | 建议 |
|------|------|------|------|
| internal-utils | 1.0.0 | 内部包，无许可证声明 | 添加MIT/Apache许可证 |
| legacy-component | 2.3.1 | 许可证文件损坏 | 联系原作者确认 |
| vendor-sdk | 0.9.0 | 自定义许可证文本 | 法务审核许可证条款 |

---

## ⚔️ 许可证兼容性冲突检测

### 冲突 #1: Apache-2.0 + GPL-2.0 混用

**涉及组件**:
- `apache-library` (Apache-2.0) - 直接依赖
- `gpl-plugin` (GPL-2.0) - 间接依赖，被apache-library引用

**问题分析**:
- Apache-2.0 的专利终止条款与 GPL-2.0 的专利条款不完全兼容
- 虽然单向兼容（GPL项目可以使用Apache代码），但双向合并存在问题
- 如果我们的项目需要同时分发这两个组件的二进制组合，可能产生冲突

**影响范围**: 中等（仅在特定分发场景下）

**解决方案**:
1. **首选**: 寻找 `gpl-plugin` 的非GPL替代品
2. **次选**: 将GPL组件隔离为独立进程（IPC通信），避免衍生作品形成
3. **最后**: 法律意见书确认当前使用方式的合规性

---

### 冲突 #2: LGPL静态链接风险

**涉及组件**:
- `libnative` (LGPL-2.1) - 通过Node.js native addon链接

**问题分析**:
- Node.js addon编译后形成静态链接
- LGPL规定：静态链接时需提供目标文件的object code以便用户重新链接
- 或者选择以LGPL发布我们自己的代码

**当前状态**: ⚠️ 可能违规

**解决方案**:
1. 将native addon改为独立子进程（动态链接）
2. 或联系作者获取双重许可（LGPL + Commercial）
3. 或改写为纯JavaScript实现

---

## 📈 许可证分布可视化

```
许可证类型分布 (Total: 180)

MIT ████████████████████████████ 85 (47.2%)
Apache ████ 42 (23.3%)
BSD ██ 15 (8.3%)
LGPL/MPL ██ 22 (12.2%) [⚠️ 审核]
Unknown ▏ 3 (1.7%) [🔍 待查]
Blocked ▏ 1 (0.6%) [❌ 移除]
Other █ 12 (6.7%)
```

---

## 🎯 行动计划

### 立即行动 (本周)
- [ ] **P0**: 移除 SSPL 依赖 (mongodb-driver-sync)
- [ ] **P0**: 为内部包添加许可证声明
- [ ] **P1**: 解决 LGPL 静态链接问题

### 近期行动 (本月)
- [ ] 完成22个灰名单依赖的法务审核
- [ ] 解决 Apache-2.0 + GPL 兼容性问题
- [ ] 更新 `.license-checker-config.json` 白名单

### 持续改进
- [ ] 建立 PR 级别的自动许可证检查
- [ ] 定期（每月）更新许可证数据库
- [ ] 团队许可证培训

---

## 📎 附件

1. [完整依赖清单](./attachments/full_dependency_tree.json)
2. [SPDX标准格式报告](./attachments/report.spdx.json)
3. [FOSSA详细扫描结果](./attachments/fossa_scan.pdf)
4. [许可证白名单策略文档](../policies/license-whitelist-policy.md)

---

**报告审核**: 许可证审计司  
**法务审核**: 待定 (已提交)  
**下次审计**: 下月8日或重大依赖变更时
```

---

## 与MARC资源协调器的资源需求

```yaml
marc_resource_requirements:
  compute_resources:
    cpu_cores: 2
    memory_gb: 4
    
  execution_time:
    dependency_scan: "< 3 minutes"
    full_audit_with_conflict_detection: "< 10 minutes"
    
  external_data_sources:
    license_databases:
      - "SPDX License List (latest)"
      - "ChooseALicense.com API"
      - "ClearlyDefined (package metadata)"
      - "OSADL (Open Source Audit Database)"
      
    package_registries:
      - "npm registry"
      - "PyPI"
      - "Maven Central"
      - "Go Proxy"
      
  storage:
    audit_history: "Retain all reports permanently (compliance records)"
    spdx_documents: "Version controlled alongside source"
    
  collaboration:
    legal_team_integration:
      review_request_workflow: true
      escalation_path: "dev → tech_lead → legal → cto"
      sla_for_legal_review: "5 business days"
```

---

## 协同调用接口

| 接口名称 | 接口描述 | 调用方 |
|----------|----------|--------|
| `audit_licenses` | 执行完整许可证审计 | CI/CD流水线、门禁把控司 |
| `check_pr_dependencies` | 检查PR新增依赖的许可证 | Pre-commit/pre-push hook |
| `generate_sbom` | 生成软件物料清单(SBOM) | 发布流程、安全合规司 |
| `update_whitelist` | 更新许可证白名单 | 法务团队、架构师 |

---

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2026-04-06 | 初始版本，包含完整的许可证识别、合规检查、冲突检测能力 |
