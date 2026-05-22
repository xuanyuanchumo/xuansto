# 产品类型推理规则数据库

> 版本: 3.0.0 | 更新日期: 2026-05-05 | 编码: UTF-8 | 行尾: LF

## 概述

本文件包含161种产品类型的UI推理规则，供Design System Generator Agent推理引擎使用。每种产品类型包含UI分类规则、推荐风格、推荐配色行业和反模式。Agent应基于产品描述按需搜索，不预加载全部数据。

## 推理引擎说明

### 产品→UI分类规则映射

1. 输入产品类型关键词
2. 匹配产品分类表中的UI分类规则
3. 基于规则确定设计方向

### 风格优先级排序

1. 从推荐风格列表中按优先级选择
2. 结合项目约束（性能要求、可访问性要求）过滤
3. 最终选择Top 1风格 + 1个备选风格

### 反模式过滤

1. 检查推荐配色是否命中行业反模式清单（见color-palettes.md）
2. 检查推荐风格是否与产品类型冲突
3. 过滤后重新排序推荐列表

### 搜索策略

- BM25排序权重：产品类型匹配(50%) + 行业匹配(30%) + 功能匹配(20%)
- 每次搜索返回Top 5产品类型规则
- 支持模糊匹配（如"CRM"匹配"客户关系管理"）

***

## SaaS平台（20种）

| # | 产品类型 | UI分类规则 | 推荐风格(优先级排序) | 推荐配色行业 | 反模式(AVOID) |
|---|---------|-----------|---------------------|-------------|--------------|
| 1 | CRM客户管理 | Dashboard-first + 数据表格 | Clean Design > Minimalism > Carbon | SaaS-Blue, SaaS-Slate | Brutalism, Maximalism |
| 2 | 项目管理 | Dashboard-first + 看板 | Clean Design > Flat Design 2.0 > Primer | SaaS-Orange, SaaS-Blue | Art Deco, Steampunk |
| 3 | 协作工具 | Mobile-first + 实时通信 | Clean Design > Material Design 3 > iOS HIG | SaaS-Indigo, SaaS-Sky | Brutalism, Grunge |
| 4 | HR人力资源 | Dashboard-first + 表单密集 | Clean Design > Carbon > Corporate | SaaS-Slate, SaaS-Blue | Cyberpunk, Memphis |
| 5 | 营销自动化 | Dashboard-first + 数据可视化 | Flat Design 2.0 > Clean Design > Spectrum | SaaS-Rose, SaaS-Amber | Steampunk, Pixel |
| 6 | 财务SaaS | Dashboard-first + 严格表单 | Carbon > Clean Design > Corporate | SaaS-DeepBlue, SaaS-Slate | Cyberpunk, Memphis, Pop Art |
| 7 | 数据分析 | Dashboard-first + 图表密集 | Carbon > Clean Design > Data-driven | SaaS-Teal, SaaS-Cyan | Hand-drawn, Doodle |
| 8 | DevOps工具 | Dashboard-first + 终端风格 | Primer > Carbon > Clean Design | SaaS-Cyan, SaaS-Slate | Watercolor, Vintage |
| 9 | 安全合规 | Dashboard-first + 审计日志 | Carbon > Corporate > Clean Design | SaaS-DeepBlue, SaaS-Slate | Cyberpunk, Neon, Memphis |
| 10 | API管理 | Dashboard-first + 代码编辑 | Primer > Carbon > Clean Design | SaaS-Cyan, SaaS-Neutral | Watercolor, Collage |
| 11 | 知识管理 | Editorial + 搜索优先 | Clean Design > Swiss Style > Primer | SaaS-Indigo, SaaS-Blue | Brutalism, Punk |
| 12 | 电子签名 | Mobile-first + 表单流程 | Clean Design > Material Design 3 | SaaS-Blue, SaaS-Slate | Cyberpunk, Grunge |
| 13 | 视频会议 | Mobile-first + 实时通信 | Clean Design > Material Design 3 > iOS HIG | SaaS-Sky, SaaS-Blue | Brutalism, Pixel |
| 14 | 邮件营销 | Dashboard-first + 编辑器 | Clean Design > Flat Design 2.0 | SaaS-Rose, SaaS-Amber | Steampunk, Dada |
| 15 | 客服系统 | Dashboard-first + 实时通信 | Clean Design > Material Design 3 | SaaS-Sky, SaaS-Blue | Brutalism, Grunge |
| 16 | 低代码平台 | Dashboard-first + 拖拽编辑 | Spectrum > Clean Design > Flat Design 2.0 | SaaS-Violet, SaaS-Indigo | Brutalism, Pixel |
| 17 | 表单构建 | Mobile-first + 拖拽编辑 | Clean Design > Flat Design 2.0 | SaaS-Blue, SaaS-Neutral | Cyberpunk, Memphis |
| 18 | 日程管理 | Mobile-first + 日历视图 | Clean Design > Material Design 3 > iOS HIG | SaaS-Amber, SaaS-Blue | Brutalism, Steampunk |
| 19 | 文档协作 | Editorial + 实时协作 | Clean Design > Swiss Style > Primer | SaaS-Blue, SaaS-Indigo | Brutalism, Punk |
| 20 | 自动化工作流 | Dashboard-first + 流程图 | Clean Design > Flat Design 2.0 > Primer | SaaS-Lime, SaaS-Teal | Watercolor, Collage |

***

## 电商（15种）

| # | 产品类型 | UI分类规则 | 推荐风格(优先级排序) | 推荐配色行业 | 反模式(AVOID) |
|---|---------|-----------|---------------------|-------------|--------------|
| 21 | 综合电商 | Mobile-first + 商品网格 | Flat Design 2.0 > Clean Design > Material Design 3 | Ecom-Orange, Ecom-Red | Corporate, Carbon |
| 22 | 奢侈品电商 | Magazine + 大图展示 | Minimalism > Clean Design > Editorial | Ecom-Black, Ecom-Gold | Memphis, Doodle, Pixel |
| 23 | 美妆电商 | Magazine + 视频优先 | Glassmorphism > Flat Design 2.0 > Clean Design | Ecom-Pink, Ecom-Purple | Brutalism, Primer |
| 24 | 生鲜电商 | Mobile-first + 快速下单 | Flat Design 2.0 > Clean Design > Material Design 3 | Ecom-Green, Ecom-Orange | Cyberpunk, Steampunk |
| 25 | 跨境电商 | Mobile-first + 多语言 | Clean Design > Flat Design 2.0 | Ecom-Blue, Ecom-Orange | Brutalism, Grunge |
| 26 | 二手电商 | Mobile-first + 商品网格 | Clean Design > Flat Design 2.0 | Ecom-Teal, Ecom-Slate | Luxury styles |
| 27 | 母婴电商 | Mobile-first + 信任感 | Soft UI > Clean Design > Flat Design 2.0 | Ecom-Coral, Ecom-Pink | Brutalism, Cyberpunk |
| 28 | 3C数码 | Dashboard-first + 参数对比 | Clean Design > Carbon > Flat Design 2.0 | Ecom-Blue, Ecom-Slate | Watercolor, Doodle |
| 29 | 家居电商 | Magazine + 场景展示 | Clean Design > Swiss Style > Flat Design 2.0 | Ecom-Teal, Ecom-Indigo | Cyberpunk, Punk |
| 30 | 书籍电商 | Editorial + 阅读体验 | Swiss Style > Editorial > Clean Design | Ecom-Indigo, Ecom-Blue | Brutalism, Cyberpunk |
| 31 | 潮流电商 | Magazine + 视觉冲击 | Neo-Brutalism > Flat Design 2.0 > Glassmorphism | Ecom-Purple, Ecom-Orange | Corporate, Carbon |
| 32 | 宠物电商 | Mobile-first + 可爱风 | Soft UI > Claymorphism > Clean Design | Ecom-Cyan, Ecom-Coral | Brutalism, Carbon |
| 33 | B2B批发 | Dashboard-first + 批量操作 | Corporate > Clean Design > Carbon | Ecom-Slate, Ecom-Blue | Cyberpunk, Memphis |
| 34 | 礼品电商 | Magazine + 情感化 | Soft UI > Clean Design > Flat Design 2.0 | Ecom-Rose, Ecom-Pink | Brutalism, Carbon |
| 35 | 运动电商 | Mobile-first + 动感 | Flat Design 2.0 > Clean Design > Neo-Brutalism | Ecom-Lime, Ecom-Orange | Vintage, Art Deco |

***

## 社交媒体（10种）

| # | 产品类型 | UI分类规则 | 推荐风格(优先级排序) | 推荐配色行业 | 反模式(AVOID) |
|---|---------|-----------|---------------------|-------------|--------------|
| 36 | 短视频 | Mobile-first + 全屏视频 | Material Design 3 > iOS HIG > Clean Design | Social-Red, Social-Pink | Corporate, Carbon |
| 37 | 照片分享 | Mobile-first + 图片网格 | Clean Design > Flat Design 2.0 > iOS HIG | Social-Pink, Social-Purple | Carbon, Primer |
| 38 | 职业社交 | Dashboard-first + 个人主页 | Clean Design > Corporate > Carbon | Social-Blue, Social-Indigo | Cyberpunk, Memphis |
| 39 | 即时通讯 | Mobile-first + 聊天界面 | iOS HIG > Material Design 3 > Clean Design | Social-Blue, Social-Teal | Brutalism, Grunge |
| 40 | 匿名社交 | Mobile-first + 信息流 | Clean Design > Flat Design 2.0 | Social-Cyan, Social-Indigo | Corporate, Carbon |
| 41 | 知识社区 | Editorial + 问答 | Clean Design > Swiss Style > Primer | Social-Indigo, Social-Blue | Brutalism, Cyberpunk |
| 42 | 兴趣社区 | Mobile-first + 内容流 | Flat Design 2.0 > Clean Design | Social-Teal, Social-Orange | Corporate, Carbon |
| 43 | 约会应用 | Mobile-first + 卡片滑动 | Soft UI > Clean Design > Glassmorphism | Social-Rose, Social-Pink | Carbon, Primer |
| 44 | 活动社交 | Mobile-first + 地图集成 | Flat Design 2.0 > Clean Design | Social-Orange, Social-Teal | Corporate, Carbon |
| 45 | 创作者平台 | Dashboard-first + 内容编辑 | Spectrum > Clean Design > Flat Design 2.0 | Social-Purple, Social-Pink | Corporate, Carbon |

***

## 金融科技（10种）

| # | 产品类型 | UI分类规则 | 推荐风格(优先级排序) | 推荐配色行业 | 反模式(AVOID) |
|---|---------|-----------|---------------------|-------------|--------------|
| 46 | 数字银行 | Dashboard-first + 安全感 | Corporate > Clean Design > Carbon | Fintech-Navy, Fintech-Blue | Cyberpunk, Memphis, Neon |
| 47 | 支付钱包 | Mobile-first + 快速操作 | Clean Design > Material Design 3 > iOS HIG | Fintech-Navy, Fintech-Trust | Cyberpunk, Brutalism |
| 48 | 投资理财 | Dashboard-first + 图表 | Carbon > Clean Design > Data-driven | Fintech-Growth, Fintech-Emerald | Cyberpunk, Memphis, Pop Art |
| 49 | 保险平台 | Dashboard-first + 表单 | Corporate > Clean Design > Carbon | Fintech-Trust, Fintech-Steel | Cyberpunk, Neon, Memphis |
| 50 | 借贷平台 | Dashboard-first + 流程 | Clean Design > Corporate > Carbon | Fintech-Blue, Fintech-Navy | Cyberpunk, Memphis |
| 51 | 加密货币 | Dashboard-first + 实时数据 | Dark Mode > Carbon > Clean Design | Fintech-Indigo, Fintech-Midnight | Watercolor, Doodle, Vintage |
| 52 | 量化交易 | Dashboard-first + 终端 | Carbon > Primer > Dark Mode | Fintech-Midnight, Fintech-Cobalt | Watercolor, Collage, Soft UI |
| 53 | 会计软件 | Dashboard-first + 表格 | Corporate > Carbon > Clean Design | Fintech-Slate, Fintech-Teal | Cyberpunk, Memphis, Neon |
| 54 | 税务平台 | Dashboard-first + 表单 | Corporate > Clean Design > Carbon | Fintech-Teal, Fintech-Steel | Cyberpunk, Memphis, Neon |
| 55 | 财富管理 | Dashboard-first + 图表 | Corporate > Clean Design > Minimalism | Fintech-Gold, Fintech-Copper | Cyberpunk, Memphis, Brutalism |

***

## 医疗健康（10种）

| # | 产品类型 | UI分类规则 | 推荐风格(优先级排序) | 推荐配色行业 | 反模式(AVOID) |
|---|---------|-----------|---------------------|-------------|--------------|
| 56 | 在线问诊 | Mobile-first + 视频通话 | Clean Design > Material Design 3 > iOS HIG | Health-Blue, Health-Sky | Cyberpunk, Neon, Brutalism |
| 57 | 健康管理 | Mobile-first + 数据追踪 | Clean Design > Flat Design 2.0 > Material Design 3 | Health-Mint, Health-Teal | Cyberpunk, Neon, Brutalism |
| 58 | 电子病历 | Dashboard-first + 表单 | Corporate > Clean Design > Carbon | Health-Blue, Health-Pure | Cyberpunk, Neon, Memphis |
| 59 | 药品电商 | Mobile-first + 搜索 | Clean Design > Flat Design 2.0 | Health-Pine, Health-Teal | Cyberpunk, Neon, Brutalism |
| 60 | 心理健康 | Mobile-first + 柔和交互 | Soft UI > Clean Design > Organic | Health-Calm, Health-Lavender | Brutalism, Cyberpunk, Neon |
| 61 | 健身应用 | Mobile-first + 数据追踪 | Flat Design 2.0 > Clean Design > Material Design 3 | Health-Warm, Health-Teal | Vintage, Art Deco |
| 62 | 医学教育 | Editorial + 视频学习 | Clean Design > Swiss Style | Health-Blue, Health-Pure | Cyberpunk, Neon, Brutalism |
| 63 | 远程监护 | Dashboard-first + 实时数据 | Clean Design > Carbon > Data-driven | Health-Sky, Health-Ice | Cyberpunk, Neon, Brutalism |
| 64 | 体检预约 | Mobile-first + 日历 | Clean Design > Material Design 3 | Health-Teal, Health-Blue | Cyberpunk, Neon, Brutalism |
| 65 | 康复管理 | Mobile-first + 进度追踪 | Soft UI > Clean Design > Organic | Health-Soft, Health-Sage | Brutalism, Cyberpunk, Neon |

***

## 教育学习（10种）

| # | 产品类型 | UI分类规则 | 推荐风格(优先级排序) | 推荐配色行业 | 反模式(AVOID) |
|---|---------|-----------|---------------------|-------------|--------------|
| 66 | 在线课程 | Editorial + 视频播放 | Clean Design > Swiss Style > Flat Design 2.0 | Edu-Blue, Edu-Indigo | Brutalism, Cyberpunk |
| 67 | 编程教育 | Dashboard-first + 代码编辑 | Primer > Carbon > Clean Design | Edu-Teal, Edu-Blue | Watercolor, Collage |
| 68 | 语言学习 | Mobile-first + 游戏化 | Flat Design 2.0 > Clean Design > Material Design 3 | Edu-Sky, Edu-Orange | Brutalism, Carbon |
| 69 | K12教育 | Mobile-first + 游戏化 | Soft UI > Claymorphism > Clean Design | Edu-Orange, Edu-Purple | Brutalism, Cyberpunk |
| 70 | 职业培训 | Editorial + 视频学习 | Clean Design > Corporate > Swiss Style | Edu-Amber, Edu-Slate | Cyberpunk, Memphis |
| 71 | 考试系统 | Dashboard-first + 表单 | Clean Design > Corporate > Carbon | Edu-Blue, Edu-Slate | Cyberpunk, Brutalism |
| 72 | 知识问答 | Editorial + 搜索 | Swiss Style > Clean Design > Primer | Edu-Indigo, Edu-Blue | Brutalism, Cyberpunk |
| 73 | 学术论文 | Editorial + 阅读优化 | Swiss Style > Editorial > Print-inspired | Edu-Indigo, Edu-Blue | Brutalism, Cyberpunk, Memphis |
| 74 | 艺术教育 | Magazine + 画廊 | Spectrum > Clean Design > Glassmorphism | Edu-Rose, Edu-Purple | Corporate, Carbon |
| 75 | 企业培训 | Dashboard-first + 进度追踪 | Corporate > Clean Design > Carbon | Edu-Slate, Edu-Blue | Cyberpunk, Brutalism |

***

## 其他类别（86种）

| # | 产品类型 | UI分类规则 | 推荐风格(优先级排序) | 推荐配色行业 | 反模式(AVOID) |
|---|---------|-----------|---------------------|-------------|--------------|
| 76 | 旅行预订 | Mobile-first + 搜索 | Clean Design > Flat Design 2.0 > Material Design 3 | Travel-Sky, Travel-Teal | Brutalism, Carbon |
| 77 | 酒店预订 | Mobile-first + 日历 | Clean Design > Material Design 3 | Travel-Gold, Travel-Sky | Brutalism, Cyberpunk |
| 78 | 航空出行 | Mobile-first + 行程 | Clean Design > Corporate > Flat Design 2.0 | Travel-Sky, Travel-Indigo | Brutalism, Cyberpunk |
| 79 | 地图导航 | Mobile-first + 地图 | Material Design 3 > iOS HIG > Clean Design | Travel-Sky, Travel-Teal | Brutalism, Grunge |
| 80 | 外卖配送 | Mobile-first + 快速下单 | Flat Design 2.0 > Clean Design > Material Design 3 | Food-Orange, Food-Red | Corporate, Carbon |
| 81 | 餐厅预订 | Mobile-first + 日历 | Clean Design > Soft UI > Flat Design 2.0 | Food-Orange, Food-Brown | Brutalism, Cyberpunk |
| 82 | 食谱应用 | Mobile-first + 视频步骤 | Clean Design > Flat Design 2.0 > Magazine | Food-Green, Food-Cream | Brutalism, Carbon |
| 83 | 咖啡品牌 | Magazine + 品牌展示 | Vintage > Organic > Clean Design | Food-Brown, Food-Gold | Cyberpunk, Neon |
| 84 | 房产平台 | Mobile-first + 地图搜索 | Clean Design > Corporate > Flat Design 2.0 | RE-Navy, RE-Blue | Brutalism, Cyberpunk |
| 85 | 装修设计 | Magazine + 画廊 | Clean Design > Swiss Style > Magazine | RE-Teal, RE-Earth | Cyberpunk, Brutalism |
| 86 | 物业管理 | Dashboard-first + 表单 | Corporate > Clean Design > Carbon | RE-Indigo, RE-Slate | Cyberpunk, Memphis |
| 87 | 游戏平台 | Mobile-first + 游戏网格 | Dark Mode > Neo-Brutalism > Cyberpunk | Game-Purple, Game-Neon | Corporate, Carbon |
| 88 | 电竞平台 | Dashboard-first + 直播 | Dark Mode > Cyberpunk > Neon | Game-Cyan, Game-Neon | Corporate, Clean Design |
| 89 | 游戏社区 | Mobile-first + 论坛 | Clean Design > Flat Design 2.0 > Dark Mode | Game-Blue, Game-Purple | Corporate, Carbon |
| 90 | 设计工具 | Dashboard-first + 画布 | Spectrum > Clean Design > Carbon | Creative-Purple, Creative-Teal | Brutalism, Pixel |
| 91 | 摄影平台 | Magazine + 画廊 | Minimalism > Clean Design > Dark Mode | Creative-Pink, Creative-Black | Corporate, Carbon |
| 92 | 视频编辑 | Dashboard-first + 时间线 | Spectrum > Carbon > Dark Mode | Creative-Sky, Creative-Purple | Watercolor, Doodle |
| 93 | 3D建模 | Dashboard-first + 视口 | Carbon > Dark Mode > Spectrum | Creative-Fuchsia, Creative-Black | Watercolor, Vintage |
| 94 | 音乐流媒体 | Mobile-first + 播放器 | Dark Mode > Glassmorphism > Clean Design | Social-Red, Creative-Purple | Corporate, Carbon |
| 95 | 播客应用 | Mobile-first + 播放器 | Clean Design > Dark Mode > Flat Design 2.0 | Social-Indigo, Social-Blue | Brutalism, Cyberpunk |
| 96 | 新闻门户 | Editorial + 信息流 | Swiss Style > Newspaper > Clean Design | Media-Red, Edu-Blue | Cyberpunk, Memphis |
| 97 | 天气应用 | Mobile-first + 数据展示 | Clean Design > Glassmorphism > Flat Design 2.0 | Travel-Sky, Travel-Teal | Brutalism, Grunge |
| 98 | 日历应用 | Mobile-first + 日历视图 | Clean Design > Material Design 3 > iOS HIG | SaaS-Amber, SaaS-Blue | Brutalism, Cyberpunk |
| 99 | 笔记应用 | Mobile-first + 编辑器 | Clean Design > Swiss Style > Minimalism | SaaS-Blue, SaaS-Neutral | Brutalism, Cyberpunk |
| 100 | 密码管理 | Mobile-first + 安全感 | Clean Design > Corporate > Carbon | SaaS-DeepBlue, SaaS-Slate | Cyberpunk, Memphis |
| 101 | VPN工具 | Mobile-first + 一键连接 | Clean Design > Dark Mode > Corporate | SaaS-DeepBlue, SaaS-Cyan | Watercolor, Doodle |
| 102 | 云存储 | Dashboard-first + 文件管理 | Clean Design > Carbon > Corporate | SaaS-Blue, SaaS-Sky | Brutalism, Cyberpunk |
| 103 | 项目展示 | Magazine + 画廊 | Minimalism > Swiss Style > Clean Design | Creative-Black, SaaS-Indigo | Brutalism, Cyberpunk |
| 104 | 个人博客 | Editorial + 阅读 | Swiss Style > Editorial > Clean Design | Edu-Blue, SaaS-Neutral | Brutalism, Cyberpunk |
| 105 | 企业官网 | Magazine + 品牌展示 | Clean Design > Corporate > Swiss Style | SaaS-Blue, SaaS-Slate | Brutalism, Cyberpunk |
| 106 | 政府门户 | Editorial + 信息架构 | Corporate > Clean Design > Accessible-first | Gov-Navy, Gov-Blue | Cyberpunk, Memphis, Neon |
| 107 | 政务服务 | Mobile-first + 表单流程 | Accessible-first > Corporate > Clean Design | Gov-Blue, Gov-Slate | Cyberpunk, Memphis, Neon |
| 108 | 公共交通 | Mobile-first + 实时数据 | Clean Design > Material Design 3 > Accessible-first | Gov-Teal, Gov-Slate | Cyberpunk, Brutalism |
| 109 | 环保组织 | Magazine + 数据展示 | Organic > Clean Design > Biophilic | NPO-Green, NPO-Teal | Brutalism, Cyberpunk |
| 110 | 教育公益 | Editorial + 捐赠 | Clean Design > Corporate > Swiss Style | NPO-Blue, NPO-Orange | Cyberpunk, Brutalism |
| 111 | 法律服务 | Editorial + 表单 | Corporate > Clean Design > Carbon | Legal-Navy, Legal-Slate | Cyberpunk, Memphis, Neon |
| 112 | 律师事务所 | Magazine + 品牌展示 | Corporate > Clean Design > Editorial | Legal-Slate, Legal-Navy | Cyberpunk, Memphis, Neon |
| 113 | 汽车品牌 | Magazine + 3D展示 | Clean Design > Dark Mode > Corporate | Auto-Blue, Auto-Red | Watercolor, Doodle |
| 114 | 新能源 | Dashboard-first + 数据 | Clean Design > Data-driven > Carbon | Energy-Green, Energy-Blue | Brutalism, Cyberpunk |
| 115 | 物流追踪 | Mobile-first + 地图 | Clean Design > Material Design 3 > Data-driven | Logistics-Orange, Logistics-Blue | Brutalism, Cyberpunk |
| 116 | 供应链 | Dashboard-first + 流程图 | Corporate > Carbon > Clean Design | Logistics-Blue, Logistics-Orange | Cyberpunk, Memphis |
| 117 | 流媒体 | Mobile-first + 视频播放 | Dark Mode > Clean Design > Material Design 3 | Media-Purple, Media-Red | Corporate, Carbon |
| 118 | 电信服务 | Dashboard-first + 表单 | Corporate > Clean Design > Carbon | Telecom-Blue, Telecom-Cyan | Cyberpunk, Memphis |
| 119 | 农业 | Dashboard-first + 数据 | Organic > Clean Design > Biophilic | Agri-Green, Agri-Earth | Cyberpunk, Brutalism |
| 120 | 航天航空 | Dashboard-first + 3D | Dark Mode > Carbon > Clean Design | Space-Indigo, Space-Blue | Watercolor, Doodle |
| 121 | 体育健身 | Mobile-first + 数据追踪 | Flat Design 2.0 > Clean Design > Material Design 3 | Sports-Green, Sports-Orange | Vintage, Art Deco |
| 122 | 宗教信仰 | Editorial + 阅读 | Editorial > Clean Design > Print-inspired | Religion-Gold, Religion-Indigo | Cyberpunk, Brutalism, Neon |
| 123 | 冥想应用 | Mobile-first + 柔和交互 | Organic > Soft UI > Clean Design | Health-Calm, NPO-Teal | Brutalism, Cyberpunk, Neon |
| 124 | 睡眠追踪 | Mobile-first + 数据 | Soft UI > Dark Mode > Clean Design | Health-Lavender, Health-Calm | Brutalism, Cyberpunk, Neon |
| 125 | 宠物服务 | Mobile-first + 可爱风 | Soft UI > Claymorphism > Clean Design | Ecom-Cyan, Ecom-Coral | Brutalism, Carbon |
| 126 | 婚礼策划 | Magazine + 画廊 | Soft UI > Clean Design > Glassmorphism | Social-Rose, Ecom-Rose | Brutalism, Cyberpunk |
| 127 | 活动策划 | Magazine + 日历 | Clean Design > Flat Design 2.0 | Social-Orange, Social-Teal | Brutalism, Cyberpunk |
| 128 | 志愿者平台 | Mobile-first + 列表 | Clean Design > Corporate > Accessible-first | NPO-Orange, NPO-Green | Cyberpunk, Brutalism |
| 129 | 慈善捐赠 | Mobile-first + 支付 | Clean Design > Corporate > Soft UI | NPO-Orange, NPO-Blue | Cyberpunk, Brutalism |
| 130 | 社区服务 | Mobile-first + 信息流 | Clean Design > Flat Design 2.0 > Accessible-first | Gov-Teal, NPO-Green | Cyberpunk, Brutalism |
| 131 | 智能家居 | Mobile-first + 设备控制 | Clean Design > Material Design 3 > Soft UI | SaaS-Teal, SaaS-Blue | Brutalism, Cyberpunk |
| 132 | IoT平台 | Dashboard-first + 实时数据 | Carbon > Clean Design > Data-driven | SaaS-Cyan, Energy-Blue | Watercolor, Doodle |
| 133 | 车联网 | Mobile-first + 地图 | Clean Design > Material Design 3 > Dark Mode | Auto-Blue, Logistics-Orange | Brutalism, Cyberpunk |
| 134 | AR/VR应用 | Mobile-first + 3D交互 | Dark Mode > Glassmorphism > Holographic UI | Game-Neon, Creative-Fuchsia | Corporate, Carbon |
| 135 | AI助手 | Mobile-first + 对话 | Clean Design > Material Design 3 > iOS HIG | SaaS-Indigo, SaaS-Blue | Brutalism, Grunge |
| 136 | AI绘画 | Dashboard-first + 画布 | Spectrum > Dark Mode > Clean Design | Creative-Purple, Creative-Fuchsia | Corporate, Carbon |
| 137 | AI写作 | Editorial + 编辑器 | Clean Design > Swiss Style > Primer | SaaS-Indigo, SaaS-Blue | Brutalism, Cyberpunk |
| 138 | AI翻译 | Mobile-first + 对话 | Clean Design > Material Design 3 | SaaS-Sky, SaaS-Blue | Brutalism, Cyberpunk |
| 139 | AI代码 | Dashboard-first + 代码编辑 | Primer > Carbon > Dark Mode | SaaS-Cyan, SaaS-Neutral | Watercolor, Doodle |
| 140 | 区块链 | Dashboard-first + 数据 | Dark Mode > Carbon > Clean Design | Fintech-Indigo, Game-Purple | Watercolor, Vintage |
| 141 | NFT平台 | Magazine + 画廊 | Dark Mode > Glassmorphism > Neo-Brutalism | Game-Purple, Creative-Fuchsia | Corporate, Carbon |
| 142 | 元宇宙 | Mobile-first + 3D | Dark Mode > Cyberpunk > Holographic UI | Game-Neon, Game-Purple | Corporate, Carbon |
| 143 | 数据可视化 | Dashboard-first + 图表 | Data-driven > Carbon > Clean Design | SaaS-Teal, SaaS-Cyan | Watercolor, Doodle |
| 144 | BI工具 | Dashboard-first + 图表 | Carbon > Clean Design > Data-driven | SaaS-Teal, SaaS-Slate | Watercolor, Doodle |
| 145 | 报表系统 | Dashboard-first + 表格 | Corporate > Carbon > Clean Design | SaaS-Slate, SaaS-Blue | Cyberpunk, Memphis |
| 146 | 监控告警 | Dashboard-first + 实时 | Carbon > Dark Mode > Clean Design | SaaS-Cyan, SaaS-DeepBlue | Watercolor, Doodle |
| 147 | 日志分析 | Dashboard-first + 终端 | Primer > Carbon > Dark Mode | SaaS-Cyan, SaaS-Neutral | Watercolor, Doodle |
| 148 | CI/CD | Dashboard-first + 流水线 | Primer > Carbon > Clean Design | SaaS-Cyan, SaaS-Teal | Watercolor, Doodle |
| 149 | 容器管理 | Dashboard-first + 终端 | Carbon > Primer > Dark Mode | SaaS-Cyan, SaaS-Neutral | Watercolor, Doodle |
| 150 | 微信小程序 | Mobile-first + 轻量 | Clean Design > Flat Design 2.0 | SaaS-Blue, SaaS-Green | Brutalism, Cyberpunk |
| 151 | 桌面应用 | Dashboard-first + 原生 | Fluent Design > Clean Design > Carbon | SaaS-Blue, SaaS-Slate | Brutalism, Cyberpunk |
| 152 | 浏览器扩展 | Mobile-first + 轻量 | Clean Design > Minimalism | SaaS-Blue, SaaS-Neutral | Brutalism, Cyberpunk |
| 153 | 命令行工具 | 终端 + 最小UI | Primer > Carbon | SaaS-Cyan, SaaS-Neutral | Watercolor, Magazine |
| 154 | 开源项目 | Editorial + 文档 | Primer > Clean Design > Swiss Style | SaaS-Neutral, SaaS-Blue | Brutalism, Cyberpunk |
| 155 | 技术博客 | Editorial + 阅读 | Swiss Style > Primer > Clean Design | Edu-Blue, SaaS-Neutral | Brutalism, Cyberpunk |
| 156 | API文档 | Editorial + 搜索 | Primer > Clean Design > Carbon | SaaS-Cyan, SaaS-Neutral | Watercolor, Doodle |
| 157 | 设计系统 | Editorial + 组件展示 | Spectrum > Clean Design > Swiss Style | Creative-Purple, Creative-Teal | Brutalism, Cyberpunk |
| 158 | 品牌官网 | Magazine + 品牌展示 | Clean Design > Swiss Style > Magazine | SaaS-Blue, SaaS-Indigo | Brutalism, Cyberpunk |
| 159 | 招聘平台 | Dashboard-first + 表单 | Clean Design > Corporate > Flat Design 2.0 | SaaS-Blue, SaaS-Indigo | Brutalism, Cyberpunk |
| 160 | 在线问卷 | Mobile-first + 表单 | Clean Design > Material Design 3 | SaaS-Blue, SaaS-Neutral | Brutalism, Cyberpunk |
| 161 | 电子签名 | Mobile-first + 流程 | Clean Design > Corporate > Carbon | SaaS-Blue, SaaS-DeepBlue | Cyberpunk, Brutalism |
