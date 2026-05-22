# 三省六部软件开发管理技能（Sanliu）

## 🏷️ 版本信息

- **当前版本**: v3.1.0
- **发布日期**: 2026-04-01
- **许可证**: MIT License

---

## 项目简介

三省六部软件开发管理技能是一个基于中国古代三省六部制度理念构建的高级软件开发管理系统。该系统将传统的行政管理模式与现代软件开发流程相结合，实现了需求分析、设计、开发、测试、部署的全流程管理。

### 核心功能

- **需求分析**：中书省负责需求结构化、可行性研究、架构预检
- **设计管理**：系统架构设计、模块划分、技术选型
- **开发执行**：尚书省协调六部执行TDD开发循环
- **测试验证**：兵部负责测试先行，确保代码质量
- **部署管理**：工部负责测试执行与部署

### 设计理念

本项目借鉴中国古代三省六部制度的管理智慧：

- **三省制衡**：中书省（决策）、门下省（审议）、尚书省（执行）相互协作与制衡
- **六部分工**：吏部（人员）、户部（资源）、礼部（规范）、兵部（测试）、刑部（重构）、工部（实现）各司其职
- **TDD循环**：红（兵部测试）→ 绿（工部实现）→ 蓝（刑部重构）的持续迭代

## 目录结构

```
sanliu/
├── SKILL.md                    # 主技能文件
├── README.md                   # 项目说明文档
├── docker-compose.yml          # Docker编排配置
├── package.json                # 项目依赖配置
├── .env.example                # 环境变量示例
├── subskills/                  # 子技能文件目录
│   ├── baihehua_liushuixian.md # 白盒化流水线
│   ├── tdd_liucheng.md         # TDD流程
│   ├── sdd_liucheng.md         # SDD流程
│   ├── xuqiu_fenxi.md          # 需求分析
│   ├── daima_chonggou.md       # 代码重构
│   ├── ceshi.md                # 测试体系
│   └── ...                     # 其他子技能
├── resources/                  # 资源文件目录
│   ├── best_practices/         # 最佳实践
│   │   ├── sdd_shijian.md      # SDD实践
│   │   ├── tdd_shijian.md      # TDD实践
│   │   ├── tuandui_xiezuo.md   # 团队协作
│   │   └── xiangmu_qidong.md   # 项目启动
│   ├── templates/              # 项目模板
│   │   ├── ai_xiangmu.md       # AI项目模板
│   │   ├── mcp_fuwuqi.md       # MCP服务器模板
│   │   ├── sdd_xiangmu.md      # SDD项目模板
│   │   └── web_xiangmu.md      # Web项目模板
│   ├── daima_guifan.md         # 代码规范
│   ├── tdd_guifan.md           # TDD规范
│   ├── anquan_guifan.md        # 安全规范
│   └── ...                     # 其他规范文件
├── scripts/                    # 脚本目录
│   ├── start_services.py       # 启动服务
│   ├── stop_services.py        # 停止服务
│   ├── health_check.py         # 健康检查
│   ├── check_environment.py    # 环境检测
│   ├── docker_manager.py       # Docker管理
│   ├── architecture_check.py   # 架构检查
│   └── ...                     # 其他脚本
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── api/                # API路由
│   │   ├── models/             # 数据模型
│   │   ├── services/           # 业务服务
│   │   ├── config.py           # 配置文件
│   │   └── main.py             # 应用入口
│   ├── scripts/                # 后端脚本
│   ├── requirements.txt        # Python依赖
│   └── run.py                  # 启动脚本
├── frontend/                   # 前端界面
│   ├── src/
│   │   ├── api/                # API接口
│   │   ├── components/         # Vue组件
│   │   ├── composables/        # 组合式函数
│   │   ├── router/             # 路由配置
│   │   ├── stores/             # 状态管理
│   │   ├── utils/              # 工具函数
│   │   ├── views/              # 页面视图
│   │   ├── App.vue             # 根组件
│   │   └── main.ts             # 入口文件
│   ├── package.json            # 前端依赖
│   └── vite.config.ts          # Vite配置
├── zhongshusheng/              # 中书省
│   └── SKILL.md                # 中书省技能定义
├── menxiasheng/                # 门下省
│   └── SKILL.md                # 门下省技能定义
├── shangshusheng/              # 尚书省（含六部）
│   ├── SKILL.md                # 尚书省技能定义
│   ├── libu/                   # 吏部
│   ├── hubu/                   # 户部
│   ├── liibu/                  # 礼部
│   ├── bingbu/                 # 兵部
│   ├── xingbu/                 # 刑部
│   └── gongbu/                 # 工部
├── tests/                      # 测试文件
│   ├── conftest.py             # 测试配置
│   ├── pytest.ini              # Pytest配置
│   └── test_*.py               # 测试文件
└── data/                       # 数据目录
    └── agent_calls.db          # Agent调用数据库
```

## 快速开始

### 启动服务

```bash
# 进入项目目录
cd .trae/skills/sanliu

# 启动所有服务（数据库、后端、前端）
python scripts/start_services.py
```

### 检查服务状态

```bash
# 健康检查
python scripts/health_check.py

# 环境检测
python scripts/check_environment.py
```

### 服务访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 后端 API | http://localhost:8000 | FastAPI 后端服务 |
| API 文档 | http://localhost:8000/docs | Swagger API 文档 |
| 前端界面 | http://localhost:5173 | Vue 前端界面 |

### 基本使用流程

1. **提供项目需求描述**
   ```bash
   /skill sanliu <项目需求描述>
   ```

2. **中书省进行需求分析**
   - 需求结构化
   - 可行性研究
   - 架构预检
   - 输出需求规格说明书

3. **门下省审议方案**
   - 评审需求完整性
   - 测试覆盖验证
   - 架构合规性评审

4. **尚书省协调六部执行**
   - TDD开发循环
   - 持续集成验证
   - 外部技能调用

5. **持续跟踪项目进度**
   - 状态监控
   - 报告生成

## 使用说明

### 工作流程概述

| 阶段 | 负责机构 | 核心职责 | 输出物 |
|------|----------|----------|--------|
| 服务启动 | 系统 | 启动数据库、后端、前端服务 | 服务状态报告 |
| 环境检测 | 系统 | 检测服务状态、Docker、依赖关系 | 环境检测报告 |
| SDD规范定义 | 中书省 | 定义接口、数据模型、行为规范 | 规范文件 |
| 需求分析 | 中书省 | 需求结构化、可行性研究、架构预检 | 需求规格说明书、验收测试用例 |
| 概要设计 | 中书省 | 系统架构、模块划分、技术选型 | 概要设计说明书 |
| 方案审议 | 门下省 | 评审需求、测试覆盖、架构合规性 | 审议意见 |
| 规范解析 | 系统 | 解析规范生成测试用例和代码骨架 | 测试代码、代码骨架 |
| 执行统筹 | 尚书省 | 协调六部、TDD循环、外部技能调用 | 执行计划 |
| 状态记录 | 系统 | 记录技能调用、透明度数据 | 状态日志 |

### 三省协调机制

| 机构 | 核心职责 | 说明 |
|------|----------|------|
| 中书省 | 需求分析、概要设计、SDD规范定义 | 负责项目决策与规划 |
| 门下省 | 方案审议、架构合规性评审 | 负责质量把关与审议 |
| 尚书省 | 执行统筹、六部协调、TDD循环 | 负责具体执行与协调 |

### 六部协调机制

| 部门 | 核心职责 | TDD角色 | 说明 |
|------|----------|---------|------|
| 吏部 | 人员调度、Agent分配 | 分配TDD角色 | 管理开发人员与Agent |
| 户部 | 资源管理 | 管理测试环境资源 | 管理项目资源 |
| 礼部 | 规范制定 | 制定TDD编码规范 | 制定开发规范 |
| 兵部 | 测试先行 ⭐ | 编写单元/集成/E2E测试 | TDD红阶段 |
| 刑部 | 持续重构 ⭐ | 优化代码质量、验证覆盖率 | TDD蓝阶段 |
| 工部 | 测试执行 ⭐ | 实现代码使测试通过 | TDD绿阶段 |

### TDD开发循环

```
红 🔴 → 绿 🟢 → 蓝 🔵 → 红 🔴 → ...
│       │       │
│       │       └── 刑部：重构优化代码质量
│       └── 工部：编写最小代码使测试通过
└── 兵部：编写失败的测试用例
```

## 开发指南

### 环境要求

- **Python**: 3.10+
- **Node.js**: 18+
- **Docker**: 可选，用于容器化部署
- **PostgreSQL**: 数据库（可选，默认使用SQLite）

### 安装依赖

```bash
# 后端依赖
cd backend
pip install -r requirements.txt

# 前端依赖
cd frontend
npm install
```

### 测试命令

```bash
# 运行后端测试
cd tests
pytest

# 运行架构检查
python scripts/architecture_check.py --full

# 运行覆盖率分析
python scripts/coverage_analyzer.py
```

### 核心脚本命令

```bash
# 服务管理
python scripts/start_services.py      # 启动服务
python scripts/stop_services.py       # 停止服务
python scripts/health_check.py        # 健康检查
python scripts/check_environment.py   # 环境检测

# Docker管理
python scripts/docker_manager.py --start    # 启动Docker
python scripts/docker_manager.py --stop     # 停止Docker
python scripts/docker_manager.py --restart  # 重启Docker

# 架构检查
python scripts/architecture_check.py --full  # 完整架构检查

# 技能调用记录
python scripts/record_skill_call.py --skill <技能名> --status <start|end|update> --details <JSON>

# Agent分配
python scripts/assign_agent.py --role <角色> --task <任务描述> --call_id <关联调用ID>

# 状态查询
python scripts/query_status.py --call_id <ID>
```

### 命名规范

- 所有目录、文件名采用**小写拼音**，下划线分隔
- 映射关系：`liibu` = 礼部，`libu` = 吏部，以此类推
- 测试文件命名：`test_<模块名>.py`
- 测试函数命名：`test_<功能描述>`

### 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 许可证

本项目采用 MIT 许可证。

```
MIT License

Copyright (c) 2024 Sanliu Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
