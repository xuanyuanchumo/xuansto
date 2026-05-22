---
name: shuju_yinsi_si
description: 数据隐私司，负责PII数据处理审计、GDPR合规检查、数据脱敏验证。集成ConfigSecurityAuditor。
---

# 数据隐私司技能指令

## 职责定义

数据隐私司作为合规审计局的隐私保护核心，承担以下职责：

| 职责类别 | 具体职责 | 关键产出 |
|----------|----------|----------|
| **PII识别** | 个人身份信息(PII)发现与分类 | PII清单与数据地图 |
| **处理审计** | 数据全生命周期处理合规性审计 | 隐私审计报告 |
| **GDPR检查** | GDPR各项条款合规验证 | GDPR合规报告 |
| **脱敏验证** | 数据脱敏/匿名化有效性验证 | 脱敏验证报告 |

---

## 核心概念

### PII（个人身份信息）分类体系

```yaml
pii_classification:
  direct_identifiers:
    definition: "单独即可唯一标识个人的信息"
    examples:
      - id: "full_name"
        name: "真实姓名"
        sensitivity: "critical"
        gdpr_category: "identifier"
        handling: "encryption_required, access_restricted"
        
      - id: "national_id_number"
        name: "身份证号/护照号"
        sensitivity: "critical"
        pseudonymization_possible: false  # 无法假名化
        
      - id: "email_address"
        name: "电子邮箱地址"
        sensitivity: "high"
        pseudonymization_possible: true  # 可hash化
        
      - id: "phone_number"
        name: "电话号码"
        sensitivity: "high"
        
      - id: "home_address"
        name: "家庭住址"
        sensitivity: "critical"
        
      - id: "biometric_data"
        name: "生物特征数据（指纹、面部等）"
        sensitivity: "critical"
        special_gdpr_protection: true  # Article 9 特殊类别数据
        
      - id: "financial_account"
        name: "银行账户/信用卡号"
        sensitivity: "critical"
        pci_dss_scope: true  # 同时属于PCI DSS范围
        
  quasi_identifiers:
    definition: "结合其他信息可识别个人的数据"
    examples:
      - id: "date_of_birth"
        name: "出生日期"
        sensitivity: "medium-high"
        k_anonymity_risk: "高（配合邮编可高概率识别）"
        
      - id: "zip_code"
        name: "邮政编码"
        sensitivity: "medium"
        
      - id: "ip_address"
        name: "IP地址"
        sensitivity: "high"
        gdpr_note: "在某些司法管辖区视为PII"
        
      - id: "device_id"
        name: "设备ID/MAC地址"
        sensitivity: "medium-high"
        
      - id: "geolocation"
        name: "地理位置坐标"
        sensitivity: "high"
        precision_concerns: "精确到街道级别 = 高风险"
        
  sensitive_categories_gdpr_article_9:
    name: "特殊类别数据 (GDPR Art.9)"
    explicit_consent_required: true
    categories:
      - racial_or_ethnic_origin
      - political_opinions
      - religious_philosophical_beliefs
      - trade_union_membership
      - genetic_data
      - biometric_data
      - health_data
      - sexual_orientation
```

### ConfigSecurityAuditor集成

```yaml
config_security_auditor_integration:
  purpose: "自动化检测配置文件中的隐私和安全问题"
  
  audit_targets:
    configuration_files:
      - ".env / .env.production"
      - "config/settings.py / config.yaml / application.yml"
      - "docker-compose.yml / Dockerfile"
      - "kubernetes manifests (*.yaml)"
      - "CI/CD pipeline configs (.github/workflows/*.yml)"
      
    code_patterns:
      - "Hardcoded connection strings containing credentials"
      - "Debug endpoints exposed in production config"
      - "CORS policies too permissive (*)"
      - "Cookie security flags missing (Secure, HttpOnly, SameSite)"
      - "Session timeout too long or infinite"
      - "Logging of sensitive data (PII in log files)"
      - "Error messages exposing stack traces with data"
      
  privacy_specific_checks:
    pii_in_logs_detection:
      enabled: true
      patterns:
        - regex: "(email|phone|ssn|passport|address).*(log|print|logger|debug)"
          severity: "high"
          description: "Possible PII being logged"
          
        - regex: "(user|customer|patient).*(name|email|phone|address|id)"
          context_lines: 3
          severity: "medium"
          description: "User personal field access near logging call"
          
    data_retention_config:
      checks:
        - "Database retention periods defined and enforced"
        - "Log rotation configured with appropriate retention"
        - "Backup encryption verified"
        - "Data anonymization for analytics pipelines verified"
        
    consent_management_config:
      checks:
        - "Consent collection mechanism exists in application config"
        - "Consent versioning/tracking enabled"
        - "Consent withdrawal process configured"
        - "Cookie consent banner configuration present (if web app)"
```

---

## 工作流程

### 阶段一：PII数据发现与映射

```
启动隐私审计
    ↓
[1] 扫描代码库中的PII引用
    ↓
[2] 分析数据库Schema中的PII字段
    ↓
[3] 检查API请求/响应中的PII传输
    ↓
[4] 审计日志文件中的PII记录
    ↓
[5] 检查第三方服务的数据共享
    ↓
[6] 构建PII数据地图
    ↓
输出PII清单与数据流图
```

#### PII数据地图格式

```yaml
pii_data_map:
  project: "Customer Management System"
  version: "1.0"
  last_updated: "2024-01-08"
  
  data_stores:
    database_primary:
      type: "PostgreSQL"
      name: "customers_db"
      tables_with_pii:
        users_table:
          pii_fields:
            - column: "full_name"
              pii_type: "direct_identifier.full_name"
              encryption: "AES-256-GCM at rest"
              access_control: "role-based (admin, support_readonly)"
              retention: "account_lifetime + 7 years post-deletion"
              
            - column: "email"
              pii_type: "direct_identifier.email_address"
              encryption: "AES-256-GCM"
              masking: "partial_mask (***@domain.com) for non-privileged views"
              
            - column: "phone"
              pii_type: "direct_identifier.phone_number"
              encryption: "AES-256-GCM"
              tokenization: "optionally tokenized for analytics"
              
            - column: "date_of_birth"
              pii_type: "quasi_identifier.date_of_birth"
              generalization: "stored as date only (no time), precision reduced to month for reporting"
              
            - column: "address"
              pii_type: "direct_identifier.home_address"
              encryption: "AES-256-GCM"
              separation: "split into street/city/state/zip for partial queries"
              
            - column: "government_id"
              pii_type: "direct_identifier.national_id_number"
              encryption: "AES-256-GCM"
              special_handling: "never logged, never cached, accessed via secure API only"
              
    cache_layer:
      type: "Redis"
      pii_storage_policy: "NO_PII_IN_CACHE"  # 策略：缓存中不存储任何PII
      exception_handling: "If PII must be cached (session), use encrypted values only with TTL < 15min"
      
    log_systems:
      application_logs:
        pii_policy: "STRICT_NO_PII"
        enforcement: "Log sanitizer middleware strips all PII patterns before writing"
        verification: "Automated weekly scan of log samples for PII leakage"
        
      audit_logs:
        pii_allowed: ["user_id_hashed", "action_type", "timestamp", "ip_anonymized"]
        pii_prohibited: ["username", "email", "name", "raw_query_params"]
        
  data_flows:
    user_registration_flow:
      steps:
        - step: "Form submission"
          pii_collected: ["email", "full_name", "phone", "dob", "address"]
          consent_required: true
          consent_types: ["marketing_opt_in", "terms_acceptance"]
          storage_encrypted: true
          
        - step: "Email verification"
          pii_used: ["email"]
          verification_token: "sent separately, not linked to email in logs"
          
        - step: "Profile creation"
          pii_stored: all_above
          pii_hashed_for_analytics: ["email → sha256(email+salt)"]
          
    api_endpoints_with_pii:
      GET /api/users/me:
        response_pii: ["email", "name", "phone_masked"]
        authentication: "required (JWT with user scope)"
        rate_limiting: "strict (prevent enumeration)"
        
      PUT /api/users/profile:
        request_pii: ["name", "phone", "address"]
        validation: "Input sanitization + length limits"
        audit_log: "record change with hashed user identifier"
        
      GET /api/users/{id}/orders:
        response_pii: ["shipping_address_masked"]
        authorization: "own_resource_or_admin_only"
```

---

### 阶段二：GDPR合规性逐条检查

```
PII数据地图完成
    ↓
[1] Article 5 (数据处理原则) 检查
    ↓
[2] Article 6 (合法依据) 验证
    ↓
[3] Articles 13-14 (信息透明) 审核
    ↓
[4] Article 15-22 (数据主体权利) 验证
    ↓
[5] Article 25-32 (安全义务) 检查
    ↓
[6] Article 33-34 ( breach通知) 准备就绪
    ↓
输出GDPR合规检查表
```

#### GDPR合规检查清单（节选）

```markdown
# GDPR 合规性检查报告 - Customer Management System

**报告编号**: GDPR-COMP-2024-Q1  
**评估日期**: 2024-01-08  
**适用法律**: EU General Data Protection Regulation (Regulation 2016/679)  
**编制**: 数据隐私司  

---

## 📋 总体合规状态: ⚠️ 基本符合 (需改进项: 8)

### 评分概览

| 原则域 | 文章 | 检查项数 | 通过 | 部分通过 | 不通过 | 得分 |
|--------|------|----------|------|----------|--------|------|
| **数据处理原则** | Art. 5 | 8 | 6 | 2 | 0 | 85% |
| **合法依据** | Art. 6 | 5 | 4 | 1 | 0 | 90% |
| **信息透明** | Art. 13-14 | 10 | 7 | 2 | 1 | 75% |
| **数据主体权利** | Art. 15-22 | 12 | 8 | 3 | 1 | 72% |
| **安全义务** | Art. 25-32 | 15 | 11 | 3 | 1 | 77% |
| ** breach通知** | Art. 33-34 | 4 | 3 | 1 | 0 | 88% |
| **DPA任命** | Art. 37-39 | 3 | 3 | 0 | 0 | 100% |
| **PIA要求** | Art. 35 | 4 | 3 | 1 | 0 | 88% |
| **跨境传输** | Art. 44-49 | 3 | 2 | 0 | 1 | 67% |

**综合得分: 81.2/100 (B级)**

---

## 🔍 详细检查结果

### ✅ Art. 5 - 数据处理原则 (85%)

| # | 原则 | 要求 | 状态 | 证据/备注 |
|---|------|------|------|-----------|
| 5.1.a | **合法性、公平性和透明度** | 处理必须有合法依据 | ✅ 通过 | 有同意记录和合同依据 |
| 5.1.b | **目的限制** | 收集目的明确且不超出 | ⚠️ 部分 | 目的声明存在但某些第三方共享超出原始目的 |
| 5.1.c | **数据最小化** | 只收集必要数据 | ✅ 通过 | 注册表单已优化，移除了不必要的字段 |
| 5.1.d | **准确性** | 数据准确并保持更新 | ✅ 通过 | 用户可编辑资料，有数据质量校验 |
| 5.1.e | **存储限制** | 不超过必要时间 | ⚠️ 部分 | 删除用户后数据保留30天（应为7天），备份保留2年（过长） |
| 5.1.f | **完整性和保密性** | 安全处理 | ✅ 通过 | 加密、访问控制到位 |
| 5.1.g | **问责制** | 能证明合规 | ✅ 通过 | 审计日志完善，有合规官(DPO) |

**改进建议**:
- [ ] **P1**: 缩短删除后数据保留期至7天（当前30天）
- [ ] **P2**: 明确第三方数据共享的目的限制并在隐私政策中说明
- [ ] **P2**: 制定备份数据保留策略（加密归档 vs 明文）

---

### ⚠️ Art. 15-22 - 数据主体权利 (72%) - 需重点关注

| 权利 | 要求 | 当前实现 | 差距 | 优先级 |
|------|------|----------|------|--------|
| **知情权 (Art.15)** | 可获取正在处理的个人信息副本 | ✅ 有"导出我的数据"功能 | 无 | - |
| **更正权 (Art.16)** | 可更正不准确的信息 | ✅ 用户可编辑资料 | 无 | - |
| **删除权 (Art.17)** | 可请求删除 ("被遗忘权") | ⚠️ 基础功能存在 | 未覆盖所有系统（分析数据库未同步删除） | **P0** |
| **限制处理权 (Art.18)** | 可限制特定处理活动 | ❌ 未实现 | 需要开发"暂停处理"模式 | **P0** |
| **数据可携带权 (Art.20)** | 以机器可读格式导出 | ⚠️ JSON格式可用 | 缺少标准格式(CSV/JSON-LD)支持 | P1 |
| **反对权 (Art.21)** | 可反对基于合法利益的处理 | ⚠️ 仅营销反对已实现 | 缺少算法决策的反对机制 | **P1** |
| **自动化决策权 (Art.22)** | 反对纯自动化决策的权利 | ❌ 未涉及 | 如有信用评分等需实现 | P2 |

**关键差距**:
1. 🔴 **删除权不完整**: 用户删除账号后，分析数据仓库中仍有其数据
2. 🔴 **限制处理权缺失**: 用户无法要求暂停数据分析用途的处理
3. 🟠 **反对权有限**: 仅营销场景实现了opt-out

---

## 🎯 必须修复项 (P0)

### GAP-P0-001: 删除权完整性 (Art.17)
**问题描述**: 当用户行使删除权时，主数据库记录被删除，但以下位置仍有残留：
- Elasticsearch搜索索引（保留30天）
- 数据仓库分析副本（永久）
- CDN缓存（TTL 24h）
- 日志文件中的PII（保留90天）

**GDPR要求**: Art.17(1) - 控制者应有"合理步骤"告知正在处理的第三方删除

**解决方案**:
```python
# proposed implementation
class GDPRDeletionOrchestrator:
    async def execute_deletion_request(self, user_id: str):
        """完整的GDPR删除流程"""
        
        # 1. 主数据库软删除（立即生效）
        await self.db.soft_delete_user(user_id)
        
        # 2. 同步触发下游系统删除
        tasks = [
            self.search_index.delete_by_user(user_id),
            self.data_warehouse.purge_user_records(user_id),
            self.cache.invalidate_user_sessions(user_id),
            self.analytics.anonymize_historical_data(user_id),
            self.backup.mark_for_expiration(user_id, days=30),
            self.notify_third_parties_deletion(user_id)  # Art.17 requirement
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # 3. 记录删除操作（审计证据）
        await self.audit_log.record(
            action="gdpr_delete_executed",
            user_id=self.hash(user_id),  # 不记录明文ID
            systems_affected=len(tasks),
            timestamp=datetime.utcnow()
        )
        
        # 4. 向用户确认完成
        await self.notification.send_deletion_confirmation(user_id)
```

**截止日期**: 2024-02-28前实现  
**负责人**: 后端架构组 + 法务确认

### GAP-P0-002: 限制处理权 (Art.18)
**需求**: 用户应能要求我们停止对其数据进行特定类型的处理（如个性化推荐），而不必删除账户

**方案设计**: 在用户设置页添加"数据处理控制面板"

---

## 📊 数据保护影响评估 (DPIA) 状态

| 系统/流程 | DPIA完成? | 高风险? | 最后更新 |
|-----------|-----------|---------|----------|
| 用户注册流程 | ✅ 完成 | 否 | 2023-11-15 |
| 支付处理 | ✅ 完成 | 是 (金融数据) | 2024-01-05 |
| 行为分析/追踪 | ⚠️ 进行中 | 是 (画像构建) | 2023-12-20 |
| 客服系统访问用户数据 | ✅ 完成 | 否 | 2023-10-01 |
| 第三方数据共享 | ❌ 需更新 | 是 (新供应商) | 待定 |

---

## 📎 附录

1. [完整PII数据地图](./attachments/pii_data_map.yaml)
2. [隐私政策文本](../legal/privacy_policy.md)
3. [同意管理流程文档](./consent_management_flow.md)
4. [数据主体权利请求处理SOP](./dsr_sop.md)
5. [DPIA模板](./templates/dpia_template.md)

---

**审核**: 数据隐私司  
**DPO确认**: 待签字  
**下次审查**: 2024-04-08 或重大变更时
```

---

### 阶段三：数据脱敏验证

```
GDPR检查完成
    ↓
[1] 识别所有脱敏策略应用点
    ↓
[2] 验证静态数据脱敏效果
    ↓
[3] 验证动态数据遮蔽效果
    ↓
[4] 测试脱敏后的数据可用性
    ↓
[5] 尝试脱敏还原攻击（安全性测试）
    ↓
输出脱敏验证报告
```

---

## 与MARC资源协调器的资源需求

```yaml
marc_resource_requirements:
  compute_resources:
    cpu_cores: 2
    memory_gb: 4
    
  domain_expertise:
    required_knowledge:
      - "GDPR detailed requirements (99 articles)"
      - "Data protection principles (Privacy by Design)"
      - "Data minimization techniques"
      - "Anonymization vs Pseudonymization standards (ISO 25277)"
      - "Cookie consent frameworks (TCF 2.0, Google Consent Mode v2)"
      
  tool_dependencies:
    scanning_tools:
      - "git-secrets (for credential detection)"
      - "truffleHog (for secrets in git history)"
      - "semgrep with custom privacy rules"
      
    pii_detection_libraries:
      - "Microsoft Presidio (PII detection engine)"
      - "Google DLP API (optional cloud service)"
      
  collaboration:
    legal_team:
      review_required_for: ["privacy_policy_updates", "consent_mechanism_changes", "cross_border_transfers"]
      sla: "3 business days for standard questions"
      
    dpo_office:
      consultation_channel: "#privacy-compliance"
      escalation_path: "data_privacy_si → dpo → legal_counsel → external_privacy_counsel"
```

---

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2026-04-06 | 初始版本，包含完整的PII分类、GDPR合规检查、ConfigSecurityAuditor集成能力 |
