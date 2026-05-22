# ADR-0001: 选择FastAPI作为Web框架

- **状态**: accepted
- **日期**: 2026-04-02
- **作者**: Architecture Bureau
- **标签**: web-framework
- **标签**: tech-selection

## Context (上下文)
项目需要高性能异步Web服务，同时要求良好的API文档自动化能力。

## Decision (决策)
采用FastAPI作为主要Web框架，基于Pydantic进行数据校验。

## Consequences (后果)
团队需要学习异步编程模式；获得原生OpenAPI支持和优异性能。

## Alternatives (备选方案)
- Django + DRF
- Flask + connexion
- Tornado