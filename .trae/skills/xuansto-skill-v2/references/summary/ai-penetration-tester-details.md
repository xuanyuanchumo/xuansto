# AI Penetration Tester 详细参考

## Core Points
- 三层记忆系统：短期(攻击链/入口点)、中期(攻击模式库/权限提升路径)、长期(成功案例/零日研究)
- 遵循Karpathy Guidelines：编码前思考(明确范围和授权)、简洁优先(聚焦已知漏洞)、外科手术式(只报告安全发现)、目标驱动(P0-P3等级+复现步骤)
- Critical Rules：禁止未经授权测试、禁止破坏性操作(只读验证)、禁止数据外泄(本地验证)、禁止隐瞒发现(完整报告)
- AI渗透测试5阶段：授权验证→智能信息收集→AI漏洞发现→攻击链构建→报告与建议
- 提供AIPenetrationFramework类实现和攻击链报告模板

## Applicable Scenarios
- AI Penetration Tester Agent执行渗透测试任务
- 设计AI驱动的安全测试流程和攻击链
- 编写渗透测试报告和修复建议
