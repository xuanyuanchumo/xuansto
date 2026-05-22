---
name: anquan_hegui_si
description: 安全合规司，负责安全标准合规检查（SOC2/GDPR/ISO27001）、渗透测试协调。集成SecretsManager安全审计。
---

# 安全合规司技能指令

## 职责定义

安全合规司作为合规审计局的安全保障核心，承担以下职责：

| 职责类别 | 具体职责 | 关键产出 |
|----------|----------|----------|
| **标准合规** | SOC2/GDPR/ISO27001等框架合规检查 | 合规评估报告 |
| **渗透协调** | 渗透测试规划与结果跟踪 | 渗透测试报告 |
| **安全审计** | 安全控制有效性审计 | 安全审计报告 |
| **密钥集成** | SecretsManager安全审计与密钥生命周期审计 | 密钥审计报告 |

---

## 合规框架体系

### 主要合规框架映射

```yaml
compliance_frameworks:
  
  soc2_type_ii:
    name: "SOC 2 Type II"
    category: "Service Organization Control"
    focus: "Trust Service Criteria - Security, Availability, Processing Integrity, Confidentiality, Privacy"
    
    trust_criteria:
      CC6 (Logical & Physical Access Control):
        requirements:
          - "CC6.1: Access control criteria are defined"
          - "CC6.2: Logical access is restricted and monitored"
          - "CC6.3: Access is granted based on least privilege"
          - "CC6.4: Access is terminated upon change in status"
          - "CC6.5: System activity is logged and reviewed"
          - "CC6.6: Physical access is restricted"
          - "CC6.7: Transmission of data is protected"
          - "CC6.8: Data at rest is protected via encryption"
          - "CC6.9: Backup and recovery procedures exist"
          
      CC7 (System Operations):
        requirements:
          - "CC7.1: Change management process exists"
          - "CC7.2: Changes are authorized and tested before deployment"
          - "CC7.3: Development/test environments separate from production"
          - "CC7.4: Problem/incident handling procedures exist"
          - "CC7.5: Environmental controls protect facilities"
          
    evidence_mapping:
      CC6.2:
        evidence_items:
          - "IAM policy documents"
          - "Access control list exports"
          - "Authentication mechanism documentation"
          - "MFA implementation proof"
        collection_frequency: "continuous_monitoring + quarterly_sample"
        
      CC7.2:
        evidence_items:
          - "CI/CD pipeline configuration showing approval gates"
          - "Deployment runbooks with rollback procedures"
          - "Test coverage reports"
          - "Change request logs with approvals"
        collection_frequency: "per_release"
        
  gdpr:
    name: "General Data Protection Regulation"
    region: "European Union"
    category: "Data Privacy"
    key_articles:
      Article_32_Security_of_Processing:
        title: "Security of Processing"
        requirements:
          - "Implement appropriate technical and organizational measures"
          - "Ensure level of security appropriate to the risk"
          - measures_include:
              - "Pseudonymization and encryption"
              - "Ability to ensure confidentiality, integrity, availability"
              - "Ability to restore availability in timely manner"
              - "Regular testing of effectiveness"
              
      Article_33_Breach_Notification:
        title: "Notification of personal data breach"
        requirements:
          - "Notify supervisory authority within 72 hours"
          - "Notify data subjects without undue delay if high risk"
          - "Document all breaches regardless of notification threshold"
          
      Article_35_Data_Protection_by_Design_Default:
        title: "Data protection by design and by default"
        requirements:
          - "Implement appropriate technical and organizational measures"
          - "Data minimization principle"
          - "Purpose limitation"
          - "Storage limitation"
          
    evidence_mapping:
      Art32:
        evidence_items:
          - "Encryption standards documentation (AES-256, TLS 1.3)"
          - "Access control matrices"
          - "Penetration test results (annual)"
          - "Security training records"
          - "Incident response plan and drill results"
          
      Art33:
        evidence_items:
          - "Breach notification procedure document"
          - "Incident log with timestamps"
          - "Communication templates for authority/data subjects"
          - "Breach classification criteria"
          
  iso27001:
    name: "ISO/IEC 27001:2022"
    category: "Information Security Management System (ISMS)"
    structure:
      Clause_4_Context:
        scope: "ISMS scope definition"
        requirements: "Understand organization context, needs of interested parties"
        
      Clause_5_Leadership:
        requirements: "Management commitment, policy, roles & responsibilities"
        
      Clause_6_Planning:
        requirements: "Risk assessment, treatment objectives, planning to achieve objectives"
        
      Clause_7_Support:
        requirements: "Competence, awareness, communication, documented information"
        
      Clause_8_Operation:
        requirements: "Operational planning, change management, supplier relationships"
        
      Clause_9_Performance:
        requirements: "Monitoring measurement analysis evaluation internal audit management review"
        
      Annex_A_Controls:
        total_controls: 93
        domains:
          A.5 Organizational (17 controls)
          A.6 Human Resource Security (7 controls)
          A.7 Physical & Environmental (14 controls)
          A.8 Technology (13 controls)
          A.9 Access Control (14 controls)
          A.10 Cryptography (8 controls)
          A.11 Operations Security (14 controls)
          A.12 Communications Security (6 controls)
          A.13 System Acquisition Development Maintenance (13 controls)
          A.14 Supplier Relationships (7 controls)
          A.15 Incident Management (7 controls)
          A.16 Business Continuity (4 controls)
          A.17 Compliance (11 controls)
```

---

## SecretsManager集成

```yaml
secrets_manager_integration:
  purpose: "审计密钥管理系统的安全性、合规性和操作有效性"
  
  audit_scope:
    secret_lifecycle:
      creation:
        checks:
          - "Secret created through approved channels only"
          - "Secret has proper naming convention"
          - "Secret has appropriate rotation policy set"
          - "Creator has authorization to create secrets at this path"
          - "Creation logged with full audit trail"
          
      storage:
        checks:
          - "Secret encrypted at rest (AES-256 or equivalent)"
          - "Secret versioning enabled"
          - "Access logging enabled (who accessed, when, from where)"
          - "No plaintext secrets in logs or backups"
          - "HSM used for master keys (if applicable)"
          
      access:
        checks:
          - "Principle of least privilege enforced"
          - "Access reviews conducted quarterly"
          - "Emergency/break-glass procedures documented and audited"
          - "No permanent admin/root access tokens"
          - "Time-bound access grants (JIT - Just In Time)"
          
      rotation:
        checks:
          - "Rotation policies enforced automatically"
          - "Rotation history maintained"
          - "Post-rotation validation (service still works)"
          - "Compromised secrets rotated immediately (< 1 hour SLA)"
          - "Rotation notifications sent to stakeholders"
          
      revocation_destruction:
        checks:
          - "Revocation process documented and tested"
          - "Destroyed secrets cannot be recovered"
          - "Destruction logged and verifiable"
          
  security_audits:
    configuration_security:
      - "Vault server hardened per CIS benchmark"
      - "TLS 1.3 only for all communications"
      - "Sealed/unsealed state properly managed"
      - "Auto-unseal disabled in production (requires manual quorum)"
      
    operational_security:
      - "High availability configured (multi-node cluster)"
      - "Backup encryption verified"
      - "Disaster recovery tested (RTO/RPO met)"
      - "Monitoring and alerting comprehensive"
      
  compliance_mapping:
    soc2_cc6:
      mapping: "SecretsManager directly supports CC6.2 (access restriction), CC6.4 (termination), CC6.8 (encryption at rest)"
      
    gdpr_art32:
      mapping: "Encryption of secrets supports Art.32 requirement for pseudonymization/encryption"
      
    iso27001_annex_a:
      mappings:
        A.9.1.1: "Access control policy covers secrets"
        A.10.1.1: "Cryptography policy covers secret encryption"
        A.12.4.1: "Backups of vault data encrypted"
        A.16.1.14: "Protection of records from leakage (audit logs)"
```

---

## 工作流程

### 阶段一：合规差距分析

```
收到审计请求或定期审计触发
    ↓
[1] 确定适用框架（SOC2/GDPR/ISO27001）
    ↓
[2] 加载框架控制要求清单
    ↓
[3] 收集现有证据和文档
    ↓
[4] 逐条对照评估
    ↓
[5] 识别差距和不足
    ↓
输出差距分析报告
```

#### 差距分析报告格式

```json
{
  "gap_analysis_report_id": "GAP-ANALYSIS-2024-Q1",
  "framework": "SOC 2 Type II",
  "scope": "Cloud-hosted application platform",
  "assessment_period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-03-31T23:59:59Z"
  },
  
  "executive_summary": {
    "overall_maturity_level": 3.2,
    "maturity_scale": {
      1: "Initial/Ad-hoc",
      2: "Developing",
      3: "Defined",
      4: "Managed",
      5: "Optimizing"
    },
    "controls_assessed": 93,
    "fully_satisfied": 71,
    "partially_satisfied": 15,
    "not_satisfied": 5,
    "not_applicable: 2,
    "overall_compliance_percent": 76.3,
    "vs_previous_assessment": "+5.2%",
    "target_for_next_audit": 85.0
  },
  
  "gap_details_by_domain": {
    "CC6_Logical_Physical_Access_Control": {
      "domain_score": 82,
      "controls": [
        {
          "control_id": "CC6.2",
          "control_name": "Logical access is restricted and monitored",
          "status": "SATISFIED",
          "evidence_references": [
            "IAM-POLICY-001-v3.pdf",
            "ACCESS-MATRIX-Q1-2024.xlsx",
            "MFA-IMPLEMENTATION-REPORT.pdf"
          ],
          "evidence_quality": "strong",
          "assessor_notes": "Comprehensive RBAC implementation with MFA for all privileged access. Real-time monitoring via SIEM."
        },
        {
          "control_id": "CC6.8",
          "control_name: "Data at rest is protected via encryption",
          "status": "PARTIALLY_SATISFIED",
          "gap_description": "Database encryption implemented (AES-256), but backup files stored in object storage without server-side encryption.",
          "risk_rating": "medium",
          "remediation_plan": {
            "action": "Enable SSE-KMS encryption for backup S3 bucket",
            "owner": "Infrastructure Team",
            "due_date": "2024-04-15",
            "effort": "2 hours",
            "estimated_cost": "$50/month (KMS key cost)"
          }
        },
        {
          "control_id": "CC6.9",
          "control_name: "Backup and recovery procedures exist",
          "status": "NOT_SATISFIED",
          "gap_description": "Backup procedures documented but RTO/RPO targets not validated through actual restore tests in past 6 months.",
          "risk_rating": "high",
          "remediation_plan": {
            "action: "Conduct quarterly disaster recovery drills with documented RTO/RPO measurements",
            "owner": "SRE Team",
            "due_date": "2024-04-30",
            "effort": "2 days (planning + execution)",
            "validation_method": "DR drill report with timing metrics"
          }
        }
      ]
    },
    
    "CC7_System_Operations": {
      "domain_score": 78,
      "controls": [...]
    }
  },
  
  "prioritized_gaps": [
    {
      "rank": 1,
      "control": "CC6.9 - Backup recovery procedures",
      "status": "NOT_SATISFIED",
      "risk": "high",
      "business_impact: "Data loss could be catastrophic; RPO unknown means potential significant data loss",
      "effort": "Medium (2 days)",
      "due_date": "2024-04-30"
    },
    {
      "rank": 2,
      "control": "CC6.8 - Encryption at rest (backups)",
      "status": "PARTIALLY_SATISFIED",
      "risk": "medium",
      "effort": "Low (2 hours)",
      "due_date": "2024-04-15"
    },
    {
      "rank": 3,
      "control": "CC7.3 - Environment separation",
      "status": "PARTIALLY_SATISFIED",
      "risk": "medium",
      "effort": "Medium (1 week)",
      "due_date": "2024-05-15"
    }
  ],
  
  "recommendations": {
    immediate_actions: [
      "Schedule DR drill within 2 weeks",
      "Enable backup encryption immediately"
    ],
    strategic_improvements: [
      "Implement automated compliance monitoring (continuous vs annual)",
      "Expand security awareness training program",
      "Consider GRC platform investment for centralized compliance management"
    ],
    budget_estimate: {
      tools: "$15,000/year (GRC platform)",
      consulting: "$25,000 (one-time gap remediation support)",
      training: "$5,000/year",
      total_first_year: "$45,000"
    }
  }
}
```

---

### 阶段二：渗透测试协调与管理

```
差距分析完成（或独立触发）
    ↓
[1] 定义渗透测试范围和规则
    ↓
[2] 选择测试方法（黑盒/灰盒/白盒）
    ↓
[3] 选择并签约渗透测试供应商
    ↓
[4] 协调测试环境准备
    ↓
[5] 监控测试进度
    ↓
[6] 接收测试报告
    ↓
[7] 协调漏洞修复
    ↓
[8] 验证修复效果
    ↓
输出渗透测试闭环报告
```

#### 渗透测试管理流程

```yaml
penetration_testing_management:
  
  test_planning:
    scope_definition:
      in_scope:
        - "Production-like staging environment (staging.company.com)"
        - "Web application (all endpoints)"
        - "REST APIs (/api/*)"
        - "Authentication system"
        - "Payment processing flows"
        - "Admin panel"
        - "Mobile API endpoints"
        
      out_of_scope:
        - "Production environment (production.company.com)"
        - "DDoS testing"
        - "Social engineering attacks against employees"
        - "Physical security testing"
        - "Third-party services (payment gateway, email provider)"
        - "Denial of service attacks"
        
    rules_of_engagement:
      testing_window: "2024-02-15 to 2024-02-28 (2 weeks)"
      working_hours: "09:00-18:00 UTC (outside hours by prior arrangement only)"
      attack_methods_allowed:
        - "OWASP Top 10 vulnerability testing"
        - "Authentication bypass attempts"
        - "Authorization testing (horizontal/vertical)"
        - "Input validation testing (XSS, SQLi, etc.)"
        - "Business logic testing"
        - "Session management testing"
        - "API security testing (OWASP API Security Top 10)"
      attack_methods_explicitly_forbidden:
        - "Any action that could cause data loss or corruption"
        - "Phishing of real employees"
        - "Uploading malware"
        - "Modifying production data without explicit permission"
        - "Physical access attempts"
      data_handling:
        exfiltration_allowed: false
        sample_data_only: true
        all_findings_reported_to_vendor_first: true
        
  vendor_selection:
    criteria:
      certifications: ["CREST", "OSCP", "OSCE", "CISSP"]
      experience_in_industry: "fintech/saas preferred"
      methodology: "PTES (Penetration Testing Execution Standard) or similar"
      reporting_quality: "clear executive summary + detailed technical findings"
      nda_signing: required
      
    coordination_checklist:
      pre_test:
        - [ ] Legal approval obtained
        - [ ] NDA signed with vendor
        - [ ] Staging environment prepared and isolated
        - [ ] Test accounts created with appropriate privileges
        - [ ] Database backed up before testing
        - [ ] Monitoring team notified (to distinguish pentest traffic from attacks)
        - [ ] Incident response team on standby
        
      during_test:
        - [ ] Daily standup with pentesters (15 min)
        - [ ] Monitor for unexpected production impact
        - [ ] Document any deviations from RoE
        - [ ] Maintain communication channel (Slack channel dedicated)
        
      post_test:
        - [ ] Receive draft report
        - [ ] Review findings for accuracy
        - [ ] Clarification meeting with pentesters
        - [ ] Receive final report
        - [ ] Executive summary prepared for leadership
        - [ ] Findings entered into issue tracker (Jira/GitHub Issues)
        
  findings_management:
    severity_classification:
      critical:
        definition: "Exploitable vulnerability that provides immediate unauthorized access, data exposure, or system compromise"
        example: "SQL injection returning user passwords, authentication bypass granting admin rights"
        remediation_sla: "24-72 hours"
        escalation: "Immediate CTO notification, consider emergency release"
        
      high:
        definition: "Significant vulnerability that could lead to compromise with additional steps or under specific conditions"
        example: "Stored XSS in admin area, IDOR exposing other users' data"
        remediation_sla: "1-2 weeks"
        escalation: "Tech lead + Security team lead notification"
        
      medium:
        definition: "Security weakness that requires specific conditions or user interaction to exploit"
        example: "Missing security headers, informational leaks in error messages"
        remediation_sla: "1 month (next sprint)"
        escalation: "Track in backlog, address in normal cadence"
        
      low:
        definition: "Minor security issues or best practice violations with limited exploitation potential"
        example: "Missing cookie flags, verbose version headers"
        remediation_sla: "Quarterly cleanup"
        escalation: "Technical debt backlog"
        
      informational:
        definition: "Observations and recommendations that don't represent vulnerabilities but improve security posture"
        example: "Recommendation to implement CSP header, suggestion to upgrade TLS version"
        remediation_sla: "As convenient"
        
    remediation_workflow:
      finding_received:
        → Create issue in tracker with full details
        → Assign to appropriate team
        → Set priority and due date based on severity
        → Notify stakeholders
        
      fix_developed:
        → Developer implements fix
        → Code review with security focus
        → Unit tests added for the fix
        → Deploy to staging
        
      verification:
        → Request re-test from pentester or internal security team
        → Confirm vulnerability is no longer exploitable
        → Update issue status to "Verified Closed"
        → Document fix details for audit trail
        
      post_verification:
        → Add to regression test suite
        → Update secure coding guidelines if new pattern discovered
        → Share lessons learned with development teams
```

---

### 阶段三：综合合规审计报告

```
所有审计活动完成
    ↓
[1] 整合差距分析结果
    ↓
[2] 整合渗透测试结果
    ↓
[3] 整合密钥审计结果
    ↓
[4] 计算综合合规评分
    ↓
[5] 生成最终报告
    ↓
[6] 分发利益相关方
    ↓
输出综合安全合规报告
```

---

## 输出物

### 报告目录结构

```
docs/compliance/security/
├── 2024/
│   ├── Q1/
│   │   ├── gap_analysis_soc2.json
│   │   ├── gap_analysis_gdpr.json
│   │   ├── gap_analysis_iso27001.json
│   │   ├── pentest_report_Q1_2024.pdf
│   │   ├── pentest_findings_tracker.xlsx
│   │   ├── secrets_audit_report_Q1.json
│   │   └── comprehensive_compliance_report_Q1.md
│   └── ...
├── policies/
│   ├── security_policy_v2.1.pdf
│   ├── acceptable_use_policy.pdf
│   ├── incident_response_plan.md
│   └── data_classification_policy.md
├── evidence/
│   ├── access_control_matrices/
│   ├── encryption_evidence/
│   ├── penetration_test_reports/
│   └── training_records/
└── index.md
```

---

## 与MARC资源协调器的资源需求

```yaml
marc_resource_requirements:
  compute_resources:
    cpu_cores: 2
    memory_gb: 4
    
  execution_time:
    gap_analysis: "< 30 minutes (automated parts)"
    report_generation: "< 15 minutes"
    full_audit_cycle: "2-4 weeks (including coordination)"
    
  external_services:
    penetration_testing_vendors:
      - budget_allocation: "$15,000-$30,000 per engagement"
      - scheduling_lead_time: "2-4 weeks"
      
    compliance_consultants:
      - gap_analysis_support: available_on_demand
      
    certification_bodies:
      - SOC 2 auditor: annual engagement ($20,000-$50,000)
      - ISO 27001 certifier: initial + surveillance audits
      
  domain_knowledge_requirements:
    frameworks_expertise:
      - "SOC 2 Trust Service Criteria (2017)"
      - "GDPR (EU General Data Protection Regulation)"
      - "ISO/IEC 27001:2022"
      - "NIST Cybersecurity Framework"
      - "PCI DSS (if payment data involved)"
      
    regulatory_updates_monitoring:
      sources:
        - "ICO guidance updates"
        - "AICPA SOC 2 guidance"
        - "ISO 27001 amendments"
      frequency: "weekly digest review"
```

---

## 协同调用接口

| 接口名称 | 接口描述 | 调用方 |
|----------|----------|--------|
| `run_gap_analysis` | 执行合规差距分析 | 定期审计、管理层请求 |
| `coordinate_pentest` | 协调渗透测试全流程 | 安全团队、发布前检查 |
| `audit_secrets_manager` | 审计密钥管理系统 | 定期审计、事件响应后 |
| `generate_compliance_report` | 生成综合合规报告 | 向监管机构/客户提交 |

---

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2026-04-06 | 初始版本，包含完整的SOC2/GDPR/ISO27001合规检查、渗透测试协调、密钥管理审计能力 |
