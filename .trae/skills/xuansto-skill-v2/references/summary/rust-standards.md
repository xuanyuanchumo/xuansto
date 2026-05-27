# Rust 开发规范

## Core Points
- API指南命名：类型PascalCase、方法snake_case、常量SCREAMING_SNAKE_CASE、生命周期小写
- 代码风格：rustfmt自动格式化、clippy静态检查、避免unwrap()、优先Result而非panic
- 项目结构：Cargo.toml管理依赖、src/lib.rs+src/bin/布局、模块化组织
- 安全编码：unsafe最小化、输入验证、边界检查、零拷贝优先
- 错误处理：thiserror/anyhow、自定义Error类型、?操作符传播、避免嵌套Result

## Applicable Scenarios
- Native Module Developer Agent开发Rust原生模块
- Backend Developer Agent开发Rust服务
- Rust项目代码规范检查和审查
