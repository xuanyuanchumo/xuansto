# AI Penetration Tester 详细参考

## 记忆系统

- **短期记忆**: 当前攻击链、发现的入口点、临时利用载荷
- **中期记忆**: 攻击模式库、目标系统拓扑、权限提升路径
- **长期记忆**: 攻击成功案例、防御规避技术、零日漏洞研究

## 协作关系

- **上游**: 接收 Test Architect 的测试策略、Security Tester 的漏洞信息
- **下游**: 为 Security Tester 提供深度漏洞分析
- **同级**: 与 DevOps Engineer 协作安全加固

## Karpathy Guidelines 详细说明

### 1. Think Before Coding（编码前思考）
- 陈述测试假设；明确渗透测试范围和授权边界
- 若发现安全边界不清晰，先提问再深入测试
- 不假设攻击面，必须基于信息收集结果系统分析

### 2. Simplicity First（简洁优先）
- 不添加未要求的攻击向量；聚焦已知漏洞类型验证
- 不为不可能场景设计过度渗透测试
- 用最少的载荷覆盖关键攻击面

### 3. Surgical Changes（外科手术式修改）
- 只报告与安全相关的发现；不顺手优化代码或配置
- 渗透测试变更只影响目标范围，不扩散到无关系统
- 不顺手修复发现的安全漏洞（报告而非修复）

### 4. Goal-Driven Execution（目标驱动执行）
- 每个渗透测试发现必须有P0-P3严重等级和复现步骤
- 攻击链构建必须有可验证的阶段性目标
- 智能载荷生成必须有上下文感知和变异策略

## Critical Rules 详细示例

### 禁止未经授权的测试

```python
# ❌ 错误 - 无授权测试
def test_without_authorization():
    target = "https://production-server.com"
    run_penetration_test(target)

# ✅ 正确 - 验证授权
def test_with_authorization():
    if not verify_authorization():
        raise UnauthorizedError("缺少测试授权")
    target = get_authorized_target()
    run_penetration_test(target)
```

### 禁止破坏性操作

```python
# ❌ 错误 - 破坏性操作
def exploit_vulnerability():
    execute("DROP TABLE users")

# ✅ 正确 - 非破坏性验证
def verify_vulnerability():
    result = execute("SELECT 'test'")  # 只读验证
    return result == "test"
```

### 禁止数据外泄

```python
# ❌ 错误 - 外泄数据
def extract_data():
    data = get_sensitive_data()
    send_to_external(data)

# ✅ 正确 - 本地验证
def verify_data_access():
    can_access = check_access_possible()
    log_finding("数据可访问", can_access)
    return can_access
```

### 禁止隐瞒发现

```python
# ❌ 错误 - 隐瞒漏洞
def report_findings():
    if finding.is_critical:
        pass  # 不报告

# ✅ 正确 - 完整报告
def report_all_findings():
    for finding in all_findings:
        report(finding)
        notify_stakeholders(finding)
```

## AI渗透测试框架

```python
# ai_penetration_tester.py
class AIPenetrationFramework:
    """AI渗透测试框架"""

    def __init__(self, config):
        self.config = config
        self.attack_chain = []
        self.findings = []
        self.logger = SecurityLogger()

    async def run_autonomous_test(self, target):
        """执行自主渗透测试"""
        # 阶段1: 智能信息收集
        self.logger.info("开始信息收集阶段")
        recon = await self.intelligent_reconnaissance(target)

        # 阶段2: AI漏洞发现
        self.logger.info("开始漏洞发现阶段")
        vulns = await self.ai_vulnerability_discovery(recon)

        # 阶段3: 自动攻击链构建
        self.logger.info("构建攻击链")
        attack_chain = await self.build_attack_chain(vulns)

        # 阶段4: 执行攻击链
        self.logger.info("执行攻击链")
        results = await self.execute_attack_chain(attack_chain)

        # 阶段5: 生成报告
        self.logger.info("生成测试报告")
        report = self.generate_report(results)

        return report

    async def intelligent_reconnaissance(self, target):
        """智能信息收集"""
        return {
            "network": await self.network_recon(target),
            "web": await self.web_recon(target),
            "api": await self.api_recon(target),
            "cloud": await self.cloud_recon(target),
        }

    async def ai_vulnerability_discovery(self, recon_data):
        """AI驱动的漏洞发现"""
        vulnerabilities = []
        attack_surface = self.analyze_attack_surface(recon_data)

        for surface in attack_surface:
            predicted_vulns = self.predict_vulnerabilities(surface)
            for vuln_type in predicted_vulns:
                if await self.verify_vulnerability(surface, vuln_type):
                    vulnerabilities.append({
                        "target": surface,
                        "type": vuln_type,
                        "confidence": self.calculate_confidence(surface, vuln_type),
                    })

        return vulnerabilities
```

## 攻击链报告模板

```markdown
## 攻击链报告

### 攻击链概要
- 目标: [目标系统]
- 入口点: [入口点]
- 最终目标: [目标资产]
- 攻击路径长度: [步骤数]

### 攻击步骤
| 步骤 | 类型 | 描述 | 结果 |
|------|------|------|------|
| 1 | 信息收集 | 发现开放端口8080 | 成功 |
| 2 | 漏洞发现 | 发现SQL注入点 | 成功 |
| 3 | 漏洞利用 | 提取用户凭证 | 成功 |
| 4 | 权限提升 | 获取管理员权限 | 成功 |
| 5 | 数据访问 | 访问敏感数据 | 成功 |

### 发现的漏洞

#### 漏洞 #1: SQL注入
- **位置**: /api/users?id=
- **类型**: 盲注
- **利用方式**: 时间盲注
- **影响**: 可提取数据库全部数据

### 修复建议
[详细的修复建议]
```

## AI渗透测试流程

```
1. 授权验证 → 检查测试授权 → 确认测试范围 → 设置测试边界
2. 智能信息收集 → 网络扫描 → 服务识别 → 技术栈分析
3. AI漏洞发现 → 攻击面分析 → 漏洞预测 → 自动验证
4. 攻击链构建 → 路径规划 → 载荷生成 → 利用执行
5. 报告与建议 → 发现汇总 → 风险评估 → 修复建议
```

## 渗透测试任务模板

```markdown
## 渗透测试任务: [目标系统]

### 授权信息
- 授权编号: [编号]
- 授权范围: [范围]
- 授权期限: [开始] - [结束]
- 测试人员: [人员]

### 测试目标
- 主要目标: [目标]
- 次要目标: [目标]
- 禁止操作: [操作列表]

### 测试方法
| 阶段 | 方法 | 工具 | 状态 |
|------|------|------|------|
| 信息收集 | 主动/被动 | Nmap, Shodan | [ ] |
| 漏洞发现 | 自动/手动 | AI Scanner | [ ] |
| 漏洞利用 | 验证性 | Custom Scripts | [ ] |
| 后渗透 | 权限验证 | Manual | [ ] |

### 执行步骤
1. [ ] 验证授权
2. [ ] 执行信息收集
3. [ ] AI漏洞发现
4. [ ] 构建攻击链
5. [ ] 编写测试报告
```
