# MCP集成策略

## MCP集成策略概述

定义MCP上下文窗口预算管理，确保MCP工具使用不挤占核心推理空间。

## 上下文预算

每个MCP工具占用约5-10%上下文窗口，同时启用不超过10个。

## 懒加载

MCP配置按Phase和命令按需加载：

- Phase 0-1: 无MCP需求
- Phase 2-3: 可加载Context7（docs lookup）
- Phase 4-5: 可加载Playwright（E2E测试）
- Phase 8: 可加载部署相关MCP

## 降级策略

Token≥80%时禁用非关键MCP，释放上下文空间用于核心推理。

## CLI替代

CLI功能完善的平台优先使用CLI+Skill组合：

- GitHub → gh CLI
- Supabase → supabase CLI
- Vercel → vercel CLI
- Cloudflare → wrangler CLI

## MCP健康检查

SessionStart Hook检查MCP可用性，不可用时降级为CLI。

## 上下文窗口管理建议

20-30个MCP在配置中，保持<10个启用/<80个工具活跃。
