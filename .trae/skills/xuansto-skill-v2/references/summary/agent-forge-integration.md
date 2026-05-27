# AgentForge 执行验证多Agent框架参考文档

## Core Points
- AgentForge是执行验证型框架，所有Agent输出必须通过Docker沙箱验证，SWE-bench Lite达40.0%解决率
- 五大核心角色：Planner(规划)、Coder(编码)、Tester(测试)、Debugger(调试)、Critic(评审)，最多3轮修改循环
- Docker沙箱验证流程：代码提交→容器创建→依赖安装→编译验证→测试执行→结果收集→容器销毁
- 执行验证门禁(EXEC-VERIFY)检查编译成功、依赖安装、测试套件通过、无资源泄漏
- 5角色映射到xuansto：Planner→system-architect, Coder→fullstack-engineer, Tester→unit-tester, Debugger→bug-scanner, Critic→code-reviewer

## Applicable Scenarios
- 设计执行验证型多Agent协作流程
- 配置Docker沙箱验证环境和门禁
- 参考AgentForge角色映射实现xuansto Agent能力对齐
