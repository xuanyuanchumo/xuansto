# 合规审计局 自主操作指南 (Autonomous Operation Guide)

## 概述
本指南定位为合规审计局的自主操作规范，指导AI在没有显式脚本调用的情况下，自主执行合规缺口识别、安全基线核查、依赖审计、风险评估和合规加固的核心职责。合规审计局是门下省质量保障体系的"守门员"和"法务官"，负责确保项目在安全、法律、许可证等多个合规维度上满足内外部要求，防范合规风险演变为安全事故或法律纠纷。

## 核心原则
- **零容忍原则**：对于Critical级别的安全漏洞和严重的合规违规，采取零容忍态度
- **证据导向原则**：所有合规结论必须有可追溯的扫描结果、测试数据或审计日志作为支撑
- **纵深防御原则**：单一控制措施不足以保证安全，必须构建多层防护体系
- **最小权限原则**：所有访问控制和权限分配遵循最小必要权限原则
- **持续验证原则**：合规状态不是一次性的，必须持续监控和周期性重新验证
- **透明可审原则**：所有审计过程和决策记录完整保留，支持内外部审计

## 自主操作流程

### 阶段一：感知（Perceive）

#### 合规缺口自主识别方法

**1. OWASP Top 10 逐项检查清单**

| # | 类别 | 自主检查项 | 扫描工具/方法 | 严重程度判定 |
|---|------|-----------|--------------|-------------|
| A01 | 权限控制失效 | - 端点级权限校验是否存在<br>- 资源级所有权验证是否到位<br>- 水平/垂直越权检测<br>- 默认允许vs默认拒绝策略 | SAST规则匹配 + DAST探测 + 手工逻辑审查 | 发现任何绕过 → Critical |
| A02 | 加密机制失败 | - 敏感数据传输加密(TLS版本)<br>- 敏感数据存储加密(算法强度)<br>- 密钥管理安全性<br>- 加密随机数生成器使用 | 配置分析 + 密码学库审计 + 网络抓包验证 | 使用弱加密/无加密 → Critical |
| A03 | 注入攻击 | - SQL注入(参数化查询检查)<br>- NoSQL注入(操作符注入)<br>- 命令注入(OS命令拼接)<br>- LDAP/XPath/XXE注入 | SAST模式匹配 + DAST模糊测试 + 数据流分析 | 用户输入直接拼接 → High |
| A04 | 不安全设计 | - 认证流程设计缺陷<br>- 会话管理设计缺陷<br>- 业务逻辑设计缺陷<br>- 威胁建模缺失 | 架构审查 + 威胁建模(STRIDE) + 设计评审 | 缺乏威胁模型 → Medium |
| A05 | 安全配置错误 | - 默认凭证和默认端口<br>- 调试信息泄露<br>- 错误消息中的敏感信息<br>- 云服务配置错误 | 配置文件扫描 + 环境变量检查 + 云配置审计 | 生产环境含调试模式 → Critical |
| A06 | 过时组件 | - 已知CVE漏洞的依赖版本<br>- 不再维护的组件(EOL)<br>- 组件版本冲突 | Dependabot/Snyk/OSS Index + SBOM分析 | 存在Critical CVE → Critical |
| A07 | 身份认证失效 | - 弱密码策略<br>- 多因素认证(MFA)缺失<br>- Session/Token管理缺陷<br>- 账户枚举防护缺失 | 认证流程审查 + 会话管理测试 + 暴力破解模拟 | 无MFA + 弱密码策略 → High |
| A08 | 数据完整性失败 | - 反序列化不安全使用<br>- 数字签名验证缺失<br>- CSRF Token缺失/可预测<br>- 输入验证不足 | SAST反序列化检测 + CSRF Token测试 + 输入验证审计 | 不安全的反序列化 → Critical |
| A09 | 日志与监控不足 | - 安全事件未记录<br>- 日志包含敏感信息<br>- 告警阈值不合理<br>- 审计日志被篡改风险 | 日志格式审查 + 敏感信息扫描 + SIEM集成检查 | 关键操作无日志 → Medium |
| A10 | SSRF服务端请求伪造 | - URL输入验证不足<br>- 内网资源可被访问<br>- 云元数据端点暴露 | SSRF payload测试 + 网络隔离验证 | 可访问内网资源 → High |

**2. 依赖CVE漏洞扫描解读**

```
CVE扫描结果自主分析流程：

Step 1: 获取原始扫描数据
├── 来源: Snyk / Dependabot / OSS Index / Trivy / Grype
├── 格式: JSON/XML 包含 CVE-ID、CVSS评分、影响范围等
└── 范围: 直接依赖 + 传递依赖（建议至少2层深度）

Step 2: CVSS评分解读与映射
├── CVSS 9.0-10.0 (Critical) → 必须立即修复，阻断发布
├── CVSS 7.0-8.9 (High) → 本周内修复，强烈建议阻塞
├── CVSS 4.0-6.9 (Medium) → 两周内修复，纳入迭代计划
├── CVSS 0.1-3.9 (Low) → 下个迭代处理，低优先级跟踪
└── 无CVSS评分 → 参考 CWE类型判断严重程度

Step 3: 利用可行性评估
├── 攻击向量(Network/Local/Physical) → Network最危险
├── 攻击复杂度(Low/Medium/High) → Low最容易利用
├── 所需权限(None/Low/High) → None最危险
├── 用户交互(Required/None) → None更危险
└── 影响范围(C/I/A) → 全维度影响最严重

Step 4: 影响面评估
├── 受影响的代码路径是否可达？→ 不可达则降级
├── 是否有缓解措施（WAF/输入验证）？→ 有则降级
├── 是否在生产环境暴露该功能？→ 否则降级
└── 攻击者是否需要特殊条件？→ 是则降级

Step 5: 生成最终风险评级和修复建议
```

**3. 许可证兼容性矩阵检查**

```
许可证自主审计流程：

Step 1: 采集全量依赖清单
├── 直接依赖: package.json / pom.xml / go.mod / requirements.txt 等
├── 传递依赖: 通过锁文件或依赖解析工具获取完整树
└── 开发依赖 vs 运行时依赖分类

Step 2: 识别每个依赖的许可证类型
├── 数据源: SPDX License List / ClearlyDefined / FOSSA
├── 关注重点:
│   ├── Copyleft类: GPL-2.0, GPL-3.0, AGPL-3.0, LGPL
│   ├── Permissive类: MIT, Apache-2.0, BSD-3-Clause, ISC
│   ├── Proprietary类: 商业许可/自定义许可
│   └── 特殊类: CC-BY, MPL-2.0, EPL-1.0
└── 处理多许可(Multi-license): 选择最严格的解释

Step 3: 兼容性冲突检测
├── GPL传染性检查:
│   ├── 项目是闭源/专有 → GPL依赖 = 冲突 ❌
│   ├── 项目是开源(LGPL/MPL) → GPL-3.0可能冲突 ⚠️
│   └── 项目是GPL → 兼容 ✅
├── AGPL网络使用条款检查:
│   ├── 提供SaaS服务使用AGPL组件 → 需要开源整个服务 ⚠️
│   └── 仅内部部署 → 通常可接受 ✅
└── 许可证义务追踪:
    ├── 需要声明版权 notice?
    ├── 需要提供源代码?
    ├── 需要说明变更?
    └── 有商业使用限制?

Step 4: 生成合规矩阵报告
```

**4. 数据隐私法规合规检查**

| 法规 | 适用场景 | 关键要求 | 自主检查项 |
|------|----------|----------|-----------|
| GDPR | 服务欧盟用户 | 数据最小化、用户同意、被遗忘权、数据出境 | - PII字段识别和标记<br>- 同意管理机制检查<br>- 数据删除接口验证<br>- 隐私政策完整性 |
| PIPL | 服务中国用户 | 本地存储、单独同意、敏感个人信息保护 | - 数据本地化存储确认<br>- 单独同意书机制<br>- 敏感信息加密存储<br>- 第三方共享审批 |
| CCPA | 服务加州用户 | 知情权、删除权、不出售权 | - Do Not Sell机制<br>- 数据主体权利响应接口<br>- 隐私声明可见性 |
| HIPAA | 医疗健康数据 | PHI保护、访问控制、审计日志 | - 加密传输和存储<br>- 最小必要访问原则<br>- 完整审计链 |

### 阶段二：Decide（决策）

#### 风险评估和修复方案自主生成

**风险等级判定框架：**

```python
def assess_compliance_risk(finding):
    """
    合规风险综合评估模型
    输入: 合规发现项
    输出: 风险等级 + 修复优先级 + 建议方案
    """
    
    # 因素1: 固有严重程度 (基于标准分类)
    severity_map = {
        "owasp_critical": 10,
        "owasp_high": 8,
        "cve_critical": 10,
        "cve_high": 8,
        "license_violation": 7,
        "privacy_breach": 9,
        "config_misconfig": 6,
        "best_practice_deviation": 4
    }
    inherent_severity = severity_map.get(finding.category, 5)
    
    # 因素2: 利用可能性 (Exploitability)
    exploitability = calculate_exploitability(
        attack_vector=finding.attack_vector,      # Network > Local
        attack_complexity=finding.complexity,      # Low > High
        privileges_required=finding.privileges,     # None > High
        user_interaction=finding.interaction       # None > Required
    )
    
    # 因素3: 影响范围 (Impact)
    impact = calculate_impact(
        affected_users=finding.user_scope,          # All > Some > None
        data_sensitivity=finding.data_type,         # PII > Internal > Public
        business_criticality=finding.biz_importance # Core > Support > Optional
    )
    
    # 因素4: 曝露程度 (Exposure)
    exposure = calculate_exposure(
        is_production=finding.in_production,
        is_internet_facing=finding.internet_accessible,
        has_authentication=finding.auth_protected,
        existing_controls=finding.mitigations
    )
    
    # 综合风险分数 (0-100)
    risk_score = (
        inherent_severity * 0.25 +
        exploitability * 0.20 +
        impact * 0.30 +
        exposure * 0.25
    )
    
    # 风险等级映射
    if risk_score >= 80:
        level = "CRITICAL"
        timeline = "立即 (24小时内)"
        action = "阻断发布 + 紧急修复"
    elif risk_score >= 60:
        level = "HIGH"
        timeline = "本周内 (7天内)"
        action = "强烈建议修复 + 发布审批"
    elif risk_score >= 40:
        level = "MEDIUM"
        timeline = "两周内 (14天内)"
        action = "计划修复 + 跟踪监控"
    elif risk_score >= 20:
        level = "LOW"
        timeline = "下月迭代"
        action = "排期处理 + 风险接受备案"
    else:
        level = "INFO"
        timeline = "可选优化"
        action = "记录观察"
    
    return {
        "risk_score": round(risk_score, 1),
        "level": level,
        "timeline": timeline,
        "recommended_action": action,
        "remediation_template": generate_remediation(finding),
        "regression_tests": generate_regression_test_cases(finding)
    }
```

**修复优先级排序算法：**
```
排序公式: Priority_Score = Exploitability × Impact × (1 / Remediation_Effort)

其中：
- Exploitability: 利用难度倒数（越容易利用分越高）
- Impact: 影响面加权（用户数 × 数据敏感度 × 业务重要性）
- Remediation_Effort: 修复工作量估算（人天）

输出按 Priority_Score 降序排列的修复任务队列
```

**修复方案模板库：**

| 漏洞类别 | 修复模板 | 回归测试关联 |
|----------|----------|-------------|
| SQL注入 | 参数化查询替换字符串拼接 | 注入payload测试用例集 |
| XSS | 输出编码 + CSP头配置 | XSS payload测试用例集 |
| CSRF | Anti-CSRF Token + SameSite Cookie | CSRF token验证测试 |
| 认证绕过 | 增加中间件鉴权检查 | 未认证访问拒绝测试 |
| 敏感信息泄露 | 脱敏处理 + 日志过滤 | 敏感字段不可见测试 |
| 弱加密算法 | 升级到AES-256-GCM等强算法 | 加解密正确性测试 |
| 过期依赖 | 升级到安全版本 | 功能回归测试套件 |

### 阶段三：Execute（执行）

#### 合规加固自主执行规范

**1. 安全基线自主核查清单**

##### 1.1 认证与会话管理
```
□ 密码策略
  □ 最小长度 ≥ 12 字符
  □ 要求大小写字母+数字+特殊字符组合
  □ 禁止常见弱密码（top 10000）
  □ 密码哈希使用 bcrypt/scrypt/Argon2（禁止MD5/SHA1）
  □ 密码重置Token一次性且有时效（≤1小时）
  
□ 多因素认证(MFA)
  □ 高特权操作强制MFA
  □ 支持TOTP/WebAuthn/FIDO2等现代MFA方式
  □ MFA恢复码安全存储
  
□ 会话管理
  □ Session ID 随机性足够（≥128位熵）
  □ Session Cookie 设置:
    □ HttpOnly 标志
    □ Secure 标志（HTTPS环境）
    □ SameSite=Strict 或 Lax
    □ Path 限制到最小范围
  □ 空闲超时 ≤ 30分钟
  □ 绝对超时 ≤ 8小时
  □ 登出时完全销毁Session
  □ 并发Session限制（可选）
  
□ 登录安全
  □ 登录失败次数限制（如5次后锁定）
  □ 账户锁定后的冷却时间
  □ 登录异常通知（新设备/IP地址）
  □ 防暴力破解（速率限制/CAPTCHA）
```

##### 1.2 输入验证与输出编码
```
□ 输入验证（白名单优先）
  □ 所有用户输入经过服务端验证（不信任客户端）
  □ 类型验证（数字/日期/邮箱/URL等格式）
  □ 长度限制（防止缓冲区溢出和DoS）
  □ 字符集白名单（允许的字符范围）
  □ 文件上传限制:
    □ 文件类型白名单（按magic number而非扩展名）
    □ 文件大小上限
    □ 文件名消毒（去除路径遍历字符）
    □ 病毒扫描（如有条件）

□ 输出编码
  □ HTML上下文: HTML Entity 编码
  □ JavaScript上下文: JS Unicode 转义
  □ CSS上下文: CSS Escape
  □ URL上下文: URL Encoding
  □ SQL上下文: 参数化查询（非编码）
  □ LDAP/XPATH/命令: 使用参数化API
  
□ HTTP安全头
  □ Content-Security-Policy (CSP)
  □ X-Content-Type-Options: nosniff
  □ X-Frame-Options: DENY 或 SAMEORIGIN
  □ X-XSS-Protection: 1; mode=block
  □ Strict-Transport-Security (HSTS)
  □ Referrer-Policy: strict-origin-when-cross-origin
  □ Permissions-Policy: 按需限制
  □ Content-Security-Policy-Report-Only (灰度期)
```

##### 1.3 访问控制与权限模型
```
□ 权限设计原则
  □ 默认拒绝（Deny by Default）
  □ 最小权限原则（Least Privilege）
  □ 权限分层（RBAC + ABAC 组合推荐）
  □ 职责分离（SoD：关键操作需多人审批）
  
□ 资源级授权
  □ 每个API端点有明确的权限要求
  □ 资源所有权验证（防止IDOR）
  □ 水平越权检测（用户A不能访问用户B的数据）
  □ 垂直越权检测（普通用户不能执行管理员操作）
  
□ API安全
  □ API Rate Limiting（按用户/IP/端点）
  □ API Key/Token安全管理
  □ API Versioning的安全一致性
  □ GraphQL深度限制和复杂度限制
  □ 批量操作的额外授权检查
  
□ 管理后台安全
  □ 独立的认证域
  □ IP白名单（可选但推荐）
  □ 操作审计日志（谁在什么时候做了什么）
  □ 敏感操作二次确认
```

##### 1.4 加密与密钥管理
```
□ 传输加密
  □ TLS 1.2+ 强制（禁用TLS 1.0/1.1和SSLv3）
  □ 强密码套件（禁用弱 cipher suites）
  □ 有效证书（不过期、不被吊销、链完整）
  □ OCSP Stapling 启用
  □ Forward Secrecy 支持（ECDHE key exchange）
  
□ 存储加密
  □ 敏感数据字段级加密（PII/支付/医疗等）
  □ 使用 AES-256-GCM 或 ChaCha20-Poly1305
  □ 每条记录独立IV（Initialization Vector）
  □ 密钥与数据分离存储
  □ 数据库加密（TDE）作为额外层
  
□ 密钥管理
  □ 生产密钥不在代码库中（使用KMS/Vault）
  □ 密钥定期轮换（≤90天）
  □ 密钥访问审计日志
  □ 密钥备份和恢复流程
  □ 开发/测试环境使用独立密钥
  
□ 随机数生成
  □ 使用密码学安全伪随机数生成器(CSPRNG)
  □ 禁止使用 Math.random() / rand() 用于安全场景
  □ Token/Session ID 使用足够的熵（≥128位）
```

##### 1.5 日志与监控
```
□ 安全日志记录
  □ 认证事件（成功/失败登录、登出、密码更改）
  □ 授权事件（权限变更、角色变更）
  □ 数据访问事件（CRUD操作，特别是敏感数据）
  □ 管理操作事件（配置变更、用户管理）
  □ 异常事件（错误、异常堆栈——脱敏后）
  
□ 日志安全
  □ 日志中不含敏感信息（密码/Token/PII）
  □ 日志防篡改（写一次/追加只读）
  □ 日志保留策略（符合法规要求）
  □ 日志传输加密（如果远程收集）
  
□ 监控与告警
  □ 异常登录行为检测（ impossible travel / 爆破）
  □ 异常访问模式检测（非工作时间大量数据导出）
  □ 错误率突增告警
  □ 新增CVE相关组件使用告警
  □ 与SIEM/SOAR平台集成（如有）
```

**2. 自动化合规扫描执行**

```
扫描执行调度策略：

实时触发扫描：
├── PR创建/更新时 → 增量SAST扫描（仅变更文件）
├── 依赖更新时 → 依赖漏洞扫描
└── 部署前 → DAST扫描（预生产环境）

定时批量扫描：
├── 每日夜间 → 全量SAST + 依赖扫描
├── 每周 → DAST深度扫描 + 许可证审计
├── 每月 → 完整合规基线核查
└── 每季度 → 第三方渗透测试协调

扫描结果处理流水线：
原始扫描结果
    │
    ▼
去重和聚合（同一问题不同工具报告合并）
    │
    ▼
误报过滤（基于规则引擎 + 历史学习）
    │
    ▼
严重程度评定（应用风险评估模型）
    │
    ▼
修复建议生成（匹配修复模板库）
    │
    ▼
工单自动创建（对接Jira/Linear/GitHub Issues）
    │
    ▼
通知分发（按级别和责任人路由）
```

### 阶段四：Verify（验证）

**合规修复验证检查清单：**

```markdown
## 合规修复验证卡

### 修复基本信息
- **漏洞编号**: CVE-XXXX-XXXX / 内部编号
- **修复PR**: #XXX
- **修复者**: @username
- **修复日期**: YYYY-MM-DD

### 修复内容验证
- [ ] 修复代码已通过Code Review
- [ ] 修复引入的新代码已通过静态分析（无新增警告）
- [ ] 修复没有破坏现有功能（单元测试全部通过）
- [ ] 修复方案与建议方案一致或有合理的替代理由

### 回归测试验证
- [ ] 针对该漏洞的专项测试用例已添加并通过
- [ ] 相关功能的冒烟测试通过
- [ ] 安全扫描复测显示该漏洞已消除
- [ ] 性能测试未出现显著退化

### 文档更新验证
- [ ] CHANGELOG已更新
- [ ] 如涉及API变更，API文档已同步更新
- [ ] 如涉及安全配置，安全基线文档已更新

### 最终确认
- **验证结果**: ✅ PASS / ❌ FAIL
- **验证者**: AI-Auditor
- **验证时间**: YYYY-MM-DD HH:MM:SS
- **备注**: 
```

**合规状态持续性验证：**
- 修复合并后24小时内进行一次快速复扫
- 下次发布前的完整合规门禁检查包含该项
- 定期（每月）的全量扫描确认无回退
- 依赖更新的连锁影响评估（修复一个CVE可能引入另一个）

### 阶段五：Record（Record）

**合规审计报告输出体系：**

#### 合规态势总览仪表盘
- 当前合规评分（满分100）
- 各维度的合规率（OWASP/许可证/隐私/基线）
- 开放的高/中/低风险项数量
- 近30天的趋势图
- 最近一次全面审计的时间

#### 合规事件详细报告
```markdown
## 合规审计报告 - [项目名称]
**报告期间**: YYYY-MM-DD ~ YYYY-MM-DD
**审计类型**: 周期审计 / 触发式审计 / 发布前审计
**审计执行者**: Compliance Bureau (AI)

---

### 执行摘要
- **总体合规评分**: XX/100 (等级: X)
- **关键发现**: X 个 Critical / X 个 High / X 个 Medium / X 个 Low
- **与上次对比**: 改善/恶化 X 分
- **核心结论**: [一句话总结]

### 详细发现

#### CRITICAL 级别 (X项)
| ID | 类别 | 位置 | 描述 | CVSS/风险分 | 状态 |
|----|------|------|------|------------|------|

#### HIGH 级别 (X项)
[同上格式]

#### MEDIUM 级别 (X项)
[同上格式]

#### LOW 级别 (X项)
[同上格式]

### 合规维度细分

#### OWASP Top 10 合规矩阵
| 类别 | 合规率 | 主要差距 | 趋势 |
|------|--------|---------|------|
| A01 权限控制 | XX% | ... | ↗/↘/→ |
| A02 加密机制 | XX% | ... | ... |
| ... | ... | ... | ... |

#### 依赖安全状况
- 总依赖数: XXX
- 存在CVE的依赖: XX (Critical: X, High: X, Medium: X)
- 过期依赖: XX
- 许可证风险项: XX

#### 数据隐私合规
| 法规 | 合规状态 | 差距项 | 行动计划 |
|------|---------|--------|---------|
| GDPR | ✅/⚠️/❌ | ... | ... |
| PIPL | ... | ... | ... |

### 改进路线图
1. [短期行动 - 2周内]
2. [中期行动 - 1个月内]
3. [长期行动 - 1季度内]

### 附录
- 扫描工具及版本
- 误报排除列表
- 风险接受记录（如有）
```

## 典型自主场景

### 场景1：PR提交时的合规自动化审查
**触发条件**：新的Pull Request创建或更新
**自主执行步骤**：
1. 对PR diff执行增量SAST扫描，聚焦安全相关的代码模式
2. 检查是否有新增的不安全依赖或版本降级
3. 验证修改是否引入了新的合规风险（如移除了认证检查）
4. 对变更涉及的API端点执行权限模型一致性检查
5. 如发现Critical/High级别问题，自动在PR上添加合规审查评论并设置阻止标签
6. 生成合规审查摘要附加到PR
7. 通过CI Status Check将合规状态反馈给合并门禁

**预期输出**：
- PR上的合规审查评论（含具体问题和修复建议）
- CI合规检查状态（pass/block）
- 合规风险概要通知给PR作者和审查者

### 场景2：依赖安全事件应急响应
**触发条件**：检测到新增的Critical/High级别CVE漏洞（来自Dependabot/Snyk alert）
**自主执行步骤**：
1. 解析CVE详情，获取CVSS评分、影响范围、利用条件
2. 在项目依赖图中定位受影响的传递依赖链
3. 分析受影响的代码路径是否可达（数据流分析）
4. 评估当前项目的缓解措施是否能降低风险
5. 生成综合风险评估报告
6. 查找可用的安全修复版本（patch/minor/major upgrade path）
7. 如存在兼容的安全升级路径，自动生成upgrade PR
8. 如无法立即升级，生成临时缓解措施建议（WAF规则/输入验证增强等）
9. 创建高优先级跟踪工单并通知安全负责人
10. 设置每日跟踪直到问题解决

**预期输出**：
- CVE影响评估报告（含风险等级和建议行动）
- 自动生成的依赖升级PR（如可行）
- 临时缓解措施文档
- 跟踪工单和通知记录

### 场景3：发布前合规门禁审计
**触发条件**：发布候选版本构建完成，准备进入发布流程
**自主执行步骤**：
1. 对发布版本执行完整的合规扫描套件：
   - 全量SAST扫描
   - 依赖CVE全量扫描
   - 许可证合规审计
   - 安全基线配置核查
   - 数据隐私合规抽查
2. 将扫描结果与发布的合规门槛逐项比对
3. 生成发布合规门禁报告卡
4. 对于门槛内的差异项，评估是否可以风险接受
5. 门禁通过 → 签发合规放行证书
6. 门禁不通过 → 生成阻断报告和修复路线图，阻止发布

**预期输出**：
- 发布合规门禁通过/阻断决定
- 完整的合规审计报告
- 合规放行证书（如通过）
- 阻断原因和修复计划（如不通过）

### 场景4：定期合规健康度巡检
**触发条件**：每周/每月定时巡检或手动发起
**自主执行步骤**：
1. 执行全量合规扫描（覆盖所有检查清单项）
2. 与上次巡检结果做差比对，识别新增和变化的风险项
3. 更新合规趋势数据和图表
4. 识别合规债务（已知但未修复的风险项）的变化情况
5. 评估现有缓解措施的有效性
6. 生成合规健康度评分和评级
7. 输出巡检报告并发送给相关干系人
8. 更新合规改进计划的进度跟踪

**预期输出**：
- 定期合规巡检报告
- 合规趋势分析图表
- 合规债务台账更新
- 改进计划进度报告

## 决策框架

### 合规风险处置决策树

```
输入：合规发现项
  │
  ├─ 是否属于 Critical 级别？
  │   ├─ 是 → 立即阻断 + 创建紧急工单 + 通知安全团队
  │   │   ├─ 有可用修复版本？
  │   │   │   ├─ 是 → 自动生成升级PR
  │   │   │   └─ 否 → 生成临时缓解方案 + 规划长期修复
  │   │   └─ 是否可在24小时内修复？
  │   │       ├─ 是 → 设定SLA跟踪
  │   │       └─ 否 → 评估业务影响，考虑功能降级
  │   └─ 否 → 继续
  │
  ├─ 是否属于 High 级别？
  │   ├─ 是 → 阻止发布 + 创建高优工单 + 通知负责人
  │   │   └─ 设定7天内修复期限
  │   └─ 否 → 继续
  │
  ├─ 是否属于 Medium 级别？
  │   ├─ 是 → 记录跟踪 + 纳入迭代计划
  │   │   └─ 设定14天内评估进展
  │   └─ 否 → 继续
  │
  └─ 属于 Low/INFO 级别
      └─ 记录观察 + 月度回顾时统一评估
          └─ 可选择风险接受（需记录接受理由）
```

### 风险接受决策标准

以下情况下可以考虑风险接受（必须正式记录）：
1. 修复成本远大于风险发生概率 × 影响程度的乘积
2. 受影响的功能即将被废弃或重构
3. 存在等效的其他控制措施足以减轻风险
4. 业务方明确书面接受风险并承担后果

**风险接受记录模板：**
```markdown
## 风险接受记录
- **风险项**: [描述]
- **风险等级**: [原始等级]
- **接受日期**: YYYY-MM-DD
- **接受理由**: [详细说明]
- **接受人**: [姓名/角色]
- **缓解措施**: [已有的补偿控制]
- **复审日期**: YYYY-MM-DD（必须在90天内复审）
- **状态**: Accepted / Revoked
```

## 安全与治理

### 风险评估标准
- **极高风险操作**：修改安全基线配置、关闭安全扫描、风险接受Critical级别问题
- **高风险操作**：修改告警规则、导出完整的合规报告（含细节）、调整风险评估权重
- **中风险操作**：排除误报、调整扫描范围、修改修复优先级
- **低风险操作**：查询合规仪表盘、查看历史报告、生成摘要统计

### 审批门禁条件
- Critical/High级别合规问题的风险接受需要安全负责人 + 技术负责人双签审批
- 安全基线配置的修改需要变更委员会评审
- 合规扫描工具的配置变更需要留下完整审计日志
- 向外提供的合规报告需要经过脱敏审核

### 回滚策略
- 所有合规扫描的原始结果永久归档，支持任意时间点的回溯审计
- 风险接受记录纳入版本控制，支持撤销和恢复
- 修复方案的回滚需要重新触发合规扫描确认
- 合规配置的每次变更都有快照备份，支持一键回退

## 与其他司/局的协作关系

### 与代码审查局的协作
- 本局定义的安全编码规范成为代码审查局L4安全层的审查标准
- 代码审查局发现的潜在安全问题实时同步给本局进行专业评估
- 本局的安全培训材料和案例库可供代码审查局参考以提升审查能力
- 两局共同维护安全编码检查规则库，互相补充检测盲区

### 与测试验证局的协作
- 本局生成的安全测试用例需求转化为测试验证局的具体测试任务
- 测试验证局的安全测试执行结果是本局合规证明的重要依据
- 本局发现的CVE漏洞触发测试验证局对相关路径的紧急回归测试
- 两局共同维护安全测试资产库和攻击向量知识库

### 与质量监控局的协作
- 本局的各项合规指标纳入质量监控局的六维质量指标体系中的"安全"维度
- 质量监控局的整体质量评分影响本局对合规投入资源的调配决策
- 当质量监控局检测到安全指标异常时，联动本局启动定向合规审计
- 本局的合规趋势数据帮助质量监控局进行更准确的质量预测

---

## 🤝 v5.1 增强：Agency Agent 协作指南

### 可调用的 Agency Agents

本局可通过 Agency-Agent Bridge 调用以下专业智能体：

| Agent 名称 | 所属部门 | 协作模式 | 适用场景 |
|-----------|---------|---------|---------|
| **Security Engineer** | Security Division | 主动调用 | 安全漏洞深度分析、攻击面评估、威胁建模(STRIDE)、安全架构审查、渗透测试协调 |
| **Compliance Auditor** | Security Division | 联动触发 | SOC2/ISO27001/HIPAA等标准合规审计、控制有效性验证、审计证据收集、差距分析报告生成 |
| **Legal Compliance Checker** | Security Division | 按需调用 | GDPR/PIPL/CCPA等隐私法规检查、许可证合规审计、数据处理协议(DPA)审查、法律条款符合性验证 |
| **Threat Detection Engineer** | Security Division | 持续监控 | ATT&CK框架映射、威胁情报分析、IOC(入侵指标)检测、安全事件关联分析、攻击链重构 |

### Agent 协作工作流

**Step 1 - 合规扫描任务接收与初步分类**
- 接收PR变更/定时巡检/发布前审计等触发信号
- 执行初步的合规风险快速评估，判断任务类型：
  - **代码级合规**（PR审查）→ Security Engineer主导
  - **标准级合规**（周期性审计）→ Compliance Auditor主导
  - **法规级合规**（隐私/许可证）→ Legal Compliance Checker主导
  - **威胁级合规**（安全态势）→ Threat Detection Engineer主导

**Step 2 - Security Engineer 主导的技术安全审查**
- 对代码变更执行深度安全分析：
  - OWASP Top 10逐项检查（结合上下文的精准判定）
  - CWE漏洞模式匹配和利用可行性评估
  - CVSS评分的专业估算（考虑项目特定缓解措施）
  - 攻击路径图绘制和数据流追踪
- 输出：
  - 带CVSS评分和安全修复建议的安全发现清单
  - 攻击面变化评估报告（新增/减少的攻击向量）
  - 安全编码最佳实践建议卡片

**Step 3 - Compliance Auditor 主导的标准合规审计**
当需要进行SOC2/ISO27001/HIPAA等标准审计时：
- **审计准备阶段**：
  - 解析目标标准的控制要求映射到具体检查项
  - 收集现有控制措施的证据（配置文件、策略文档、日志样本）
  - 识别审计范围和控制边界
- **审计执行阶段**：
  - 逐项验证控制的有效性（设计有效性 + 运行有效性）
  - 测试控制措施的运行情况（抽样测试+全面测试）
  - 记录不符合项(NCR)及其严重程度
- **审计报告阶段**：
  - 生成差距分析报告（当前状态 vs 标准要求的对比）
  - 提供整改建议和优先级排序
  - 输出管理层摘要（执行摘要 + 关键发现 + 风险评级）

**Step 4 - Legal Compliance Checker 主导的法规合规检查**
当涉及以下场景时自动触发：
- 处理个人身份信息(PII)的功能变更 → GDPR/PIPL/CCPA检查
- 引入新的第三方依赖 → 许可证兼容性审计
- 数据跨境传输功能 → 数据出境合规审查
- 支付/金融相关功能 → PCI-DSS/SOX合规检查

**Step 5 - Threat Detection Engineer 主导的威胁态势感知**
持续执行以下活动：
- 将本局发现的漏洞和安全问题映射到MITRE ATT&CK框架
  - 识别涉及的Tactics（战术）、Techniques（技术）、Procedures（程序）
  - 评估攻击者利用这些漏洞的可能攻击链
  - 生成ATT&CK热力图，展示系统的防御覆盖盲区
- 监控外部威胁情报源，识别与本系统相关的IOC
  - 与已知CVE、恶意软件签名、恶意IP/域名进行关联
  - 评估本系统被已知攻击手法影响的风险
- 定期输出威胁态势报告，包含：
  - 当前威胁等级评定
  - TOP N高风险ATT&CK技术点
  - 建议加强的防御控制措施

**Step 6 - 综合合规报告生成与闭环跟踪**
- 整合所有Agent的分析结果，生成统一的合规报告
- 报告包含章节：
  - 执行摘要（一页纸关键结论）
  - 技术安全发现（Security Engineer贡献）
  - 标准合规状态（Compliance Auditor贡献）
  - 法规合规检查结果（Legal Compliance Checker贡献）
  - 威胁态势评估（Threat Detection Engineer贡献）
  - 综合风险评级和改进路线图
- 所有发现项纳入统一的问题跟踪系统
- 定期复检直至所有Critical/High级别问题关闭

### 典型协作场景

**场景1：发布前全量合规审计（四Agent联合）**
- **触发条件**：重大版本发布或年度合规审计
- **协作流程**：
  1. **Security Engineer** 执行完整的安全基线核查和漏洞扫描
  2. **Compliance Auditor** 对照SOC2/ISO27001标准进行逐项审计
  3. **Legal Compliance Checker** 审查数据隐私合规性和依赖许可证
  4. **Threat Detection Engineer** 生成ATT&CK覆盖度分析和威胁评估
  5. 本局整合所有结果，生成综合合规报告卡
  6. 根据综合风险评级做出"准予发布/有条件发布/拒绝发布"的决策
- **输出特点**：包含多维度合规证据包、风险评级矩阵、整改行动计划、签发合规证书（如通过）

**场景2：CVE应急响应与合规影响评估**
- **触发条件**：检测到新的Critical/High CVE漏洞
- **协作流程**：
  1. **Security Engineer** 分析CVE详情，评估利用可行性和影响范围
  2. **Threat Detection Engineer** 将CVE映射到ATT&CK框架，评估攻击链风险
  3. **Compliance Auditor** 评估该CVE对各项合规标准的影响（是否导致控制失效）
  4. 如涉及数据泄露风险，**Legal Compliance Checker** 评估法规违规可能性和通报义务
  5. 生成综合响应方案：技术修复 + 合规补救措施 + 法律风险评估
  6. 设置紧急跟踪直到漏洞修复并完成回归验证
- **输出特点**：包含CVE影响的多维度分析（技术/合规/法律/威胁）、分级响应计划、修复验收标准

**场景3：新功能引入的合规前置评审**
- **触发条件**：规划引入涉及敏感数据的新功能（如用户画像、支付、消息推送）
- **协作流程**：
  1. **Legal Compliance Checker** 识别适用的法规要求（GDPR/PIPL等）并生成合规清单
  2. **Security Engineer** 评估功能的安全设计，提供安全编码建议
  3. **Compliance Auditor** 识别需要满足的控制措施，将其转化为具体的工程需求
  4. **Threat Detection Engineer** 预判新增的攻击面和潜在威胁场景
  5. 生成合规前置评审报告，作为需求文档的必要附件
  6. 在开发过程中持续跟踪合规需求的实现情况
- **输出特点**：合规需求清单（转化为用户故事格式）、安全设计建议书、控制措施实施检查表

---

## 🏗️ v5.1 增强：Harness 工程实践

### 相关 Harness 模块

| 模块名称 | 集成阶段 | 与本局的关联点 |
|----------|----------|---------------|
| **Security STO (Full 5-Stage)** | 全生命周期 | Pre-commit/Build/Stage/Prod/Post-Prod五阶段扫描编排，为本局提供完整的扫描数据 |
| **Policy-as-Code (OPA)** | CI/CD Pipeline | OPA合规策略引擎，实现合规规则的自动化强制执行 |

### 实践指南

**实践1：STO五阶段扫描编排与合规审计集成**

```
STO五阶段扫描时间线与合规审计节点：

Pre-commit ──→ Build ──→ Staging ──→ Production ──→ Post-Production
    │            │          │             │               │
    ▼            ▼          ▼             ▼               ▼
┌────────┐  ┌────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐
│ SAST   │  │ SAST   │  │ DAST     │  │ Runtime  │  │ Continuous   │
│ Quick  │  │ Full   │  │ + Dep.   │  │ Monitor  │  │ Monitoring   │
│        │  │ + Dep. │  │ Scan     │  │ + RASP   │  │ + Log Audit │
└───┬────┘  └───┬────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘
    │           │           │              │               │
    ▼           ▼           ▼              ▼               ▼
┌──────────────────────────────────────────────────────────────────┐
│                    合规审计局数据融合层                             │
│                                                                    │
│  • 自动拉取各阶段扫描结果                                          │
│  • 去重聚合 + 误报过滤                                            │
│  • 严重程度标准化 (CVSS/CWE映射)                                   │
│  • 合规维度标注 (OWASP/标准/法规)                                  │
│  • 生成统一合规视图                                                │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  综合合规报告     │
                    │  (含扫描时间线)   │
                    └─────────────────┘
```

- **Pre-commit阶段**：轻量SAST快速扫描
  - 仅聚焦高危漏洞模式（SQL注入/XSS/命令注入等）
  - 扫描结果注入PR合规审查评论
  - Critical问题阻断提交
  
- **Build阶段**：完整SAST + 依赖扫描
  - 全量静态分析 + 依赖树CVE扫描
  - 结果作为合规审计的基础数据
  - High及以上问题标记为必须修复项
  
- **Staging阶段**：DAST + 动态分析
  - 对预生产环境执行动态安全测试
  - API安全测试 + 认证会话测试
  - 结果补充到合规审计报告中
  
- **Production阶段**：运行时监控
  - RASP (Runtime Application Self-Protection) 实时防护
  - WAF日志分析和异常检测
  - 运行时行为基线建立
  
- **Post-Production阶段**：持续监控与审计
  - 日志审计（访问日志/错误日志/安全日志）
  - 行为异常检测
  - 定期合规状态复核

**实践2：OPA Policy-as-Code合规策略自动化**

```rego
# 示例：OPA合规策略 - 强制HTTPS和安全头
package compliance.security_headers

# 策略1: 所有API端点必须使用HTTPS
deny[msg] {
    input.endpoint.protocol != "https"
    msg := sprintf("Endpoint %s must use HTTPS", [input.endpoint.path])
}

# 策略2: 响应必须包含安全头
deny[msg] {
    not input.response.headers["Content-Security-Policy"]
    msg := "Response missing Content-Security-Policy header"
}

deny[msg] {
    not input.response.headers["X-Content-Type-Options"]
    msg := "Response missing X-Content-Type-Options header"
}

# 策略3: 禁止在响应中返回敏感信息
deny[msg] {
    sensitive_field := ["password", "ssn", "credit_card"]
    contains(json.marshal(input.response.body), sensitive_field[_])
    msg := sprintf("Response contains sensitive field: %s", [sensitive_field[_]])
}
```

- **OPA策略类型**：
  - **准入控制策略**：在CI/CD流水线中强制执行（部署前拦截不合规变更）
  - **运行时策略**：在API Gateway侧执行（实时拦截不合规请求）
  - **审计策略**：记录但不拦截（用于事后审计和趋势分析）

- **策略管理流程**：
  1. Compliance Auditor定义合规规则（自然语言描述）
  2. Security Engineer将规则翻译为Rego策略代码
  3. Legal Compliance Checker审核策略是否符合法规要求
  4. 策略经过测试验证后部署到CI/CD流水线
  5. 定期review策略有效性，根据合规环境变化更新

**实践3：STO漏洞优先级排序融入合规报告**

- **优先级算法增强**：
```
综合优先级分数 = 
  CVSS基础分 × 0.25        # 固有严重程度
  + 利用可行性 × 0.20      # 攻击难度
  + 影响范围 × 0.15        # 受影响用户/数据
  + 曝露程度 × 0.15        # 生产暴露情况
  + 合规影响 × 0.25        # ★ 新增：合规维度权重
```

- **合规影响因子计算**：
  ```
  合规影响 = max(
    标准违反严重程度,      # SOC2/ISO27001控制失效程度
    法规违规风险,          # GDPR/PIPL等违规可能性
    合同义务违约风险       # SLA/DPA等合同条款违反风险
  )
  ```

- **融入合规报告的方式**：
  - 每个漏洞条目增加"合规影响"标签列
  - 按合规影响排序的独立视图
  - 高合规影响的漏洞在执行摘要中特别标注
  - 生成"合规驱动的修复优先级列表"

### 配置参考

```yaml
# harness/compliance-integration.yaml
compliance_integration:
  # Security STO五阶段集成
  security_sto_full_pipeline:
    enabled: true
    
    # 各阶段配置
    stages:
      pre_commit:
        sast_mode: quick         # 快速模式（仅高危）
        scan_scope: diff_only    # 仅扫描变更文件
        block_on_critical: true
        inject_to_pr_comment: true
        
      build:
        sast_mode: full          # 完整SAST
        dependency_scan: true    # 包含依赖CVE扫描
        dependency_depth: 2      # 传递依赖深度
        result_format: sarif     # SARIF格式便于工具集成
        
      staging:
        dast_enabled: true       # 启用DAST
        api_security_test: true  # API安全测试
        auth_session_test: true  # 认证会话测试
        target_url: "${STAGING_URL}"
        
      production:
        rasp_enabled: true       # 运行时自保护
        waf_log_analysis: true   # WAF日志分析
        baseline_learning_period: "7d"  # 基线学习期
        
      post_production:
        continuous_monitoring: true
        log_audit_enabled: true
        anomaly_detection: true
        audit_retention: "90d"
    
    # 结果处理
    result_processing:
      deduplication: true        # 跨阶段去重
      false_positive_filter:     # 误报过滤规则
        engine: "rule_based + ml"
        learning_mode: true      # 持续学习优化
      severity_normalization:    # 严重程度标准化
        standard: "cvss_v3.1"
        custom_adjustments: true # 允许基于上下文调整
  
  # OPA Policy-as-Code集成
  opa_policy_engine:
    enabled: true
    
    policy_categories:
      security_headers:
        enforce_mode: blocking   # 阻塞模式
        stage: ci_cd_pipeline    # 在CI/CD中执行
        
      data_protection:
        enforce_mode: audit     # 审计模式（仅记录）
        stage: runtime          # 在API Gateway执行
        
      access_control:
        enforce_mode: blocking
        stage: both              # CI/CD + Runtime双重执行
        
      encryption_standards:
        enforce_mode: blocking
        stage: pre_commit        # 在提交前执行
    
    policy_lifecycle:
      review_cycle: "quarterly"  # 季度Review
      version_control: git       # 策略纳入版本管理
      approval_required: true    # 变更需要审批
      
    testing:
      unit_test_coverage_target: 80%
      integration_test_suite: true
      regression_test_on_update: true
  
  # 合规报告增强配置
  enhanced_compliance_report:
    include_sto_timeline: true   # 包含STO扫描时间线
    include_attck_mapping: true  # 包含ATT&CK映射
    
    priority_algorithm:
      use_compliance_factor: true  # 启用合规影响因子
      compliance_weight: 0.25      # 合规权重
      standard_violation_weights:
        soc2_type2: 0.8
        iso27001: 0.7
        hipaa: 0.9
        gdpr: 0.95
        pci_dss: 0.85
    
    report_sections:
      - executive_summary
      - security_findings        # 来自Security Engineer
      - standard_compliance      # 来自Compliance Auditor
      - regulatory_compliance    # 来自Legal Compliance Checker
      - threat_assessment        # 来自Threat Detection Engineer
      - sto_scan_timeline        # STO扫描时间线视图
      - attck_heatmap            # ATT&CK热力图
      - remediation_roadmap      # 整改路线图
      - appendix_evidence        # 证据附录
    
    export_formats:
      - pdf      # 正式报告
      - html     # 交互式查看
      - json     # 机器可读
      - sarif    # 工具集成
```

---

## 🆕 v6.0 增强能力集成

### 四维度输出防线检查点

本局的输出需要通过以下防线层级检查：

| 防线层级 | 本局适用性 | 检查项 | 配置位置 |
|---------|-----------|--------|----------|
| **第一维：提示词工程层** | ✅ 适用 | 角色人格一致性：本局输出风格是否符合合规审计的专业规范（零容忍、证据导向、纵深防御、透明可审） | `configs/output_defense_config.yaml → prompt_engineering.role_consistency` |
| **第二维：能力约束层** | ✅ 适用 | 工具权限：本局操作是否在允许的工具白名单内（文件读写、安全扫描、依赖审计） | `configs/output_defense_config.yaml → capability_guard.permissions` |
| **第三维：规则校验层** | ✅ 适用 | 输出格式：本局产出的合规报告、风险评估矩阵、修复方案是否符合Schema定义（OWASP覆盖完整性、CVSS评分准确性、法规映射正确性） | `configs/output_defense_config.yaml → rule_validation.schema_validation` |
| **第四维：兜底恢复机制** | ⚠️ 备用 | 当本局输出不达标时，降级策略：精简版合规摘要→关键风险清单→错误提示+人工介入 | `configs/output_defense_config.yaml → fallback_recovery` |

### MARC资源协调注意事项

当本局与其他局/司并发工作时，需注意：

- **资源申请**：如需访问代码审查局的安全发现、测试验证局的安全测试结果、质量监控局的安全指标，应通过MARC锁管理器申请
- **Decision Log记录**：本局做出的所有合规决策（风险等级评定、修复优先级、风险接受判定）必须记录到Decision Log中
- **冲突预防**：避免在安全事件响应期间与其他局同时修改相关代码；避免在发布前审计阶段阻塞关键路径

### 操作优先级指引（v6.0核心）

本局推荐的操作方式优先级：

1. 🥇 **Agent自主手动操作**（首选）
   - 直接使用文件读写工具创建/修改合规报告、风险评估文档、安全基线配置
   - 适用场景：单漏洞分析报告编写、合规Checklist维护、修复建议生成、审计证据整理
   
2. 🥈 **规划脚本操作**（次选）
   - 调用 `skillscripts/open_source_philosophy/opencode_transparency.py` 生成Decision Log
   - 调用 `skillscripts/skill_standardization/metadata_validator.py` 验证合规报告格式合规性
   
3. 🥉 **命令操作**（最后选择，需预演）
   - 仅在需要运行安全扫描工具（Snyk/Dependabot/Semgrep）、依赖审计或许可证扫描时使用
   - 执行前必须运行后果预演确认安全性（特别是涉及网络请求或外部API调用的扫描）

### Decision Log 记录要求

作为**合规审计局**，以下类型的决策必须自动记录到Decision Log：

- 风险等级评定决策（CRITICAL/HIGH/MEDIUM/LOW/INFO级别的判定依据及评分明细）
- 合规缺口处置决策（立即阻断/强烈建议修复/计划修复/风险接受的选型理由）
- CVE应急响应结论（影响评估、修复方案选择、临时缓解措施、升级PR决定）
- 风险接受审批记录（风险接受申请的评估理由、缓解措施、复审计划、审批人签名）
- 法规合规判定结论（GDPR/PIPL/CCPA等法规的合规状态评估、差距项识别、整改路线图）

- Decision Log存储路径：`docs/logs/decision_logs/`
- 日志命名规则：`{YYYY-MM-DD}_COMP_decisions.md`

### PowerShell 7 适配说明

本局相关脚本在PS7环境下的注意事项：
- 路径分隔符：使用 `/` 或 `\` 均可，系统自动转换
- 编码保证：所有输出文件（合规报告、审计日志、配置文件）使用 UTF-8 无 BOM 编码
- 如需执行终端命令（如运行Snyk/Dependabot/Trivy扫描工具），使用 `platform/powershell_adapter.py` 进行转换

---

## 🔐 密钥安全审计（v6.1 新增）

### 审计工具：ConfigSecurityAuditor

**模块路径**: `skillscripts/secrets_manager/config_security_auditor.py`

### 审计检查清单

#### C1: 配置文件敏感字段检测
- [ ] 所有 YAML/JSON 配置文件已通过 `ConfigSecurityAuditor.audit_config_file()` 扫描
- [ ] 无 Critical 级别的明文密码或 API Key
- [ ] 无连接字符串内嵌用户名密码
- [ ] 高熵随机字符串已确认非密钥或已加密存储

#### C2: 文件权限检查
- [ ] 包含敏感信息的配置文件权限正确（非 world-readable）
- [ ] Windows 下敏感文件标记为只读（如适用）
- [ ] Unix 下敏感文件权限 ≤ 0640（owner:rw group:r other:none）

#### C3: .gitignore 合规性
- [ ] `.gitignore` 包含以下条目：
  ```
  .env
  .env.local
  .env.production
  *.pem
  *.key
  credentials.json
  id_rsa*
  id_ed25519*
  *.p12
  *.pfx
  secrets.yaml
  ```
- [ ] 运行 `ConfigSecurityAuditor.check_gitignore_compliance()` 通过

#### C4: 加密评估
- [ ] Critical 级别敏感字段已评估是否需要加密
- [ ] 生产环境密钥使用专业密钥管理服务（AWS KMS / HashiCorp Vault / 环境变量注入）

### 审计命令示例

```python
from pathlib import Path
from skillscripts.secrets_manager.config_security_auditor import ConfigSecurityAuditor

auditor = ConfigSecurityAuditor()

# 单文件审计
result = auditor.audit_config_file(Path("configs/app.yaml"))
print(f"评分: {result.overall_score}/100 | 风险等级: {result.risk_level}")

# 目录级全面审计
all_results = auditor.full_audit(Path("configs/"))
for r in all_results:
    print(f"{r.file_path.name}: {r.overall_score}/100 - {len(r.findings)} 个问题")

# .gitignore 合规检查
git_check = auditor.check_gitignore_compliance()
print(f"状态: {git_check.status} | 分数: {git_check.score:.1f}")
```

### 审计报告模板

每次审计应记录：
1. 审计时间戳
2. 审计范围（文件/目录列表）
3. 发现的问题清单（按严重级别排序）
4. 修复建议和优先级
5. 复审时间安排
