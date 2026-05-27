# Go 开发规范

## Core Points
- 命名规范：驼峰命名、导出标识符首字母大写、接口名以-er结尾、包名小写单词
- 项目布局：cmd/(入口)、internal/(私有包)、pkg/(公共包)、api/(协议定义)
- 依赖管理：Go Modules、最小依赖原则、定期更新、私有代理配置
- 并发安全：优先channel而非共享内存、context超时控制、sync.Mutex保护共享状态
- 错误处理：显式错误检查、自定义错误类型、errors.Is/As包装、panic仅用于不可恢复错误

## Applicable Scenarios
- Backend Developer Agent开发Go服务
- Code Reviewer Agent检查Go代码规范
- Go项目初始化和架构设计
