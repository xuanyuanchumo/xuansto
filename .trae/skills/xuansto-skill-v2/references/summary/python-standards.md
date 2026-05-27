# Python 开发规范

## Core Points
- PEP 8命名规范：函数/变量snake_case、类PascalCase、常量UPPER_SNAKE_CASE、模块snake_case
- 类型注解：Python 3.10+使用内置类型(list[str]而非List[str])、Protocol定义接口、TypedDict定义结构
- 项目结构：src/布局、pyproject.toml配置、__init__.py控制公开API
- 测试规范：pytest框架、fixtures管理测试数据、参数化测试、覆盖率≥80%
- 安全规范：输入验证、SQL参数化、敏感数据环境变量、依赖审计(pip-audit)

## Applicable Scenarios
- Backend Developer Agent开发Python服务
- Code Reviewer Agent检查Python代码规范
- Python项目初始化和架构设计
