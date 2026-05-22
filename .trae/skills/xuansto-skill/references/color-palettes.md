# 行业配色方案数据库

> 版本: 3.0.0 | 更新日期: 2026-05-05 | 编码: UTF-8 | 行尾: LF

## 概述

本文件包含161套行业配色方案，供Design System Generator Agent按行业匹配使用。每套配色包含主色、辅色、CTA色、背景色、文字色及使用场景注释。Agent应基于产品类型按需搜索，不预加载全部数据。

## 搜索策略

- 按行业关键词搜索匹配配色方案
- BM25排序权重：行业匹配(50%) + 场景匹配(30%) + 色彩协调度(20%)
- 每次搜索返回Top 3配色供推理引擎选择
- 配色选择后必须通过反模式过滤（见行业反模式清单）

## 配色格式说明

每套配色格式：`名称 | 主色 | 辅色 | CTA色 | 背景色 | 文字色 | 注释`

***

## SaaS（15套）

| # | 名称 | 主色 | 辅色 | CTA色 | 背景色 | 文字色 | 注释 |
|---|------|------|------|-------|--------|--------|------|
| 1 | SaaS-Blue | #3B82F6 | #6366F1 | #F59E0B | #F8FAFC | #1E293B | 通用SaaS，蓝色信任感 |
| 2 | SaaS-Indigo | #6366F1 | #8B5CF6 | #EC4899 | #FAFAFA | #18181B | 创意SaaS，靛蓝专业感 |
| 3 | SaaS-Teal | #14B8A6 | #06B6D4 | #F97316 | #F0FDFA | #134E4A | 数据分析SaaS，青绿清新 |
| 4 | SaaS-Violet | #8B5CF6 | #A78BFA | #10B981 | #FAF5FF | #3B0764 | 协作SaaS，紫罗兰创新感 |
| 5 | SaaS-Slate | #475569 | #64748B | #3B82F6 | #F8FAFC | #0F172A | 企业级SaaS，石板灰稳重 |
| 6 | SaaS-Emerald | #10B981 | #34D399 | #F59E0B | #ECFDF5 | #064E3B | 增长SaaS，翡翠绿积极感 |
| 7 | SaaS-Rose | #F43F5E | #FB7185 | #3B82F6 | #FFF1F2 | #881337 | 营销SaaS，玫瑰红活力 |
| 8 | SaaS-Sky | #0EA5E9 | #38BDF8 | #F97316 | #F0F9FF | #0C4A6E | 通信SaaS，天空蓝开放感 |
| 9 | SaaS-Amber | #F59E0B | #FBBF24 | #6366F1 | #FFFBEB | #78350F | 生产力SaaS，琥珀黄温暖 |
| 10 | SaaS-Cyan | #06B6D4 | #22D3EE | #EC4899 | #ECFEFF | #164E63 | DevOps SaaS，青色技术感 |
| 11 | SaaS-Neutral | #525252 | #737373 | #3B82F6 | #FAFAFA | #171717 | 极简SaaS，中性灰专业 |
| 12 | SaaS-Lime | #84CC16 | #A3E635 | #6366F1 | #F7FEE7 | #365314 | 效率SaaS，青柠绿活力 |
| 13 | SaaS-Fuchsia | #D946EF | #E879F9 | #10B981 | #FDF4FF | #701A75 | 设计SaaS，紫红创意 |
| 14 | SaaS-Orange | #F97316 | #FB923C | #3B82F6 | #FFF7ED | #7C2D12 | 项目管理SaaS，橙色行动感 |
| 15 | SaaS-DeepBlue | #1D4ED8 | #2563EB | #F59E0B | #EFF6FF | #1E3A5F | 安全SaaS，深蓝可靠感 |

***

## Fintech（15套）

| # | 名称 | 主色 | 辅色 | CTA色 | 背景色 | 文字色 | 注释 |
|---|------|------|------|-------|--------|--------|------|
| 1 | Fintech-Navy | #1E3A5F | #2D5F8A | #10B981 | #F8FAFC | #0F172A | 银行/支付，深蓝稳重 |
| 2 | Fintech-Trust | #0F766E | #14B8A6 | #F59E0B | #F0FDFA | #134E4A | 保险/信托，青绿信任 |
| 3 | Fintech-Growth | #059669 | #10B981 | #F97316 | #ECFDF5 | #064E3B | 投资/基金，绿色增长 |
| 4 | Fintech-Gold | #B45309 | #D97706 | #1D4ED8 | #FFFBEB | #78350F | 财富管理，金色尊贵 |
| 5 | Fintech-Slate | #334155 | #475569 | #10B981 | #F8FAFC | #0F172A | 会计/审计，石板灰严谨 |
| 6 | Fintech-Blue | #1D4ED8 | #2563EB | #F59E0B | #EFF6FF | #1E3A5F | 交易/券商，蓝色专业 |
| 7 | Fintech-Teal | #0D9488 | #14B8A6 | #F97316 | #F0FDFA | #134E4A | 税务/合规，青绿规范 |
| 8 | Fintech-Steel | #475569 | #64748B | #10B981 | #F1F5F9 | #1E293B | 风控/合规，钢铁灰冷静 |
| 9 | Fintech-Emerald | #047857 | #059669 | #F59E0B | #ECFDF5 | #064E3B | 储蓄/理财，翡翠绿稳健 |
| 10 | Fintech-Indigo | #4338CA | #4F46E5 | #10B981 | #EEF2FF | #312E81 | 加密货币，靛蓝科技感 |
| 11 | Fintech-Cobalt | #1E40AF | #2563EB | #FBBF24 | #EFF6FF | #1E3A5F | 企业银行，钴蓝权威 |
| 12 | Fintech-Sage | #4D7C0F | #65A30D | #1D4ED8 | #F7FEE7 | #365314 | ESG投资，鼠尾草绿可持续 |
| 13 | Fintech-Copper | #B45309 | #D97706 | #0F766E | #FFF7ED | #7C2D12 | 铜交易/大宗商品 |
| 14 | Fintech-Midnight | #1E1B4B | #312E81 | #10B981 | #F8FAFC | #0F172A | 量化交易，午夜蓝深邃 |
| 15 | Fintech-Pine | #166534 | #15803D | #F59E0B | #F0FDF4 | #14532D | 绿色金融/碳交易 |

***

## Healthcare（15套）

| # | 名称 | 主色 | 辅色 | CTA色 | 背景色 | 文字色 | 注释 |
|---|------|------|------|-------|--------|--------|------|
| 1 | Health-Blue | #0284C7 | #0EA5E9 | #10B981 | #F0F9FF | #0C4A6E | 综合医疗，蓝色专业 |
| 2 | Health-Teal | #0D9488 | #14B8A6 | #F59E0B | #F0FDFA | #134E4A | 诊所/门诊，青绿安心 |
| 3 | Health-Sage | #4D7C0F | #65A30D | #0EA5E9 | #F7FEE7 | #365314 | 中医/自然疗法，鼠尾草绿 |
| 4 | Health-Calm | #6366F1 | #818CF8 | #10B981 | #EEF2FF | #312E81 | 心理健康，靛蓝平静 |
| 5 | Health-Rose | #E11D48 | #F43F5E | #0EA5E9 | #FFF1F2 | #881337 | 妇幼保健，玫瑰红关怀 |
| 6 | Health-Sky | #0284C7 | #0369A1 | #10B981 | #F0F9FF | #0C4A6E | 远程医疗，天空蓝开放 |
| 7 | Health-Mint | #34D399 | #6EE7B7 | #0EA5E9 | #ECFDF5 | #064E3B | 健康管理，薄荷绿清新 |
| 8 | Health-Soft | #7C3AED | #8B5CF6 | #10B981 | #FAF5FF | #4C1D95 | 康复/理疗，柔紫温和 |
| 9 | Health-Warm | #EA580C | #F97316 | #0EA5E9 | #FFF7ED | #7C2D12 | 急诊/急救，暖橙紧急 |
| 10 | Health-Pine | #166534 | #15803D | #F59E0B | #F0FDF4 | #14532D | 药房/制药，松绿专业 |
| 11 | Health-Lavender | #7C3AED | #A78BFA | #0EA5E9 | #F5F3FF | #4C1D95 | 老年护理，薰衣草柔和 |
| 12 | Health-Coral | #F43F5E | #FB7185 | #0EA5E9 | #FFF1F2 | #881337 | 血液/器官，珊瑚红生命 |
| 13 | Health-Ice | #06B6D4 | #22D3EE | #10B981 | #ECFEFF | #164E63 | 牙科/眼科，冰蓝洁净 |
| 14 | Health-Earth | #92400E | #B45309 | #0EA5E9 | #FFFBEB | #78350F | 兽医/动物保健 |
| 15 | Health-Pure | #0369A1 | #0284C7 | #10B981 | #F0F9FF | #0C4A6E | 实验室/检验，纯蓝科学 |

***

## E-commerce（15套）

| # | 名称 | 主色 | 辅色 | CTA色 | 背景色 | 文字色 | 注释 |
|---|------|------|------|-------|--------|--------|------|
| 1 | Ecom-Orange | #EA580C | #F97316 | #10B981 | #FFF7ED | #7C2D12 | 综合电商，橙色购物欲 |
| 2 | Ecom-Red | #DC2626 | #EF4444 | #F59E0B | #FEF2F2 | #7F1D1D | 促销/闪购，红色紧迫感 |
| 3 | Ecom-Black | #18181B | #27272A | #F59E0B | #FAFAFA | #09090B | 奢侈品电商，黑色高端 |
| 4 | Ecom-Pink | #EC4899 | #F472B6 | #10B981 | #FDF2F8 | #831843 | 美妆/女性电商 |
| 5 | Ecom-Green | #16A34A | #22C55E | #F97316 | #F0FDF4 | #14532D | 生鲜/有机食品 |
| 6 | Ecom-Blue | #2563EB | #3B82F6 | #F59E0B | #EFF6FF | #1E3A5F | 电子产品/数码 |
| 7 | Ecom-Purple | #7C3AED | #8B5CF6 | #F59E0B | #FAF5FF | #4C1D95 | 时尚/潮流电商 |
| 8 | Ecom-Teal | #0D9488 | #14B8A6 | #F97316 | #F0FDFA | #134E4A | 家居/生活用品 |
| 9 | Ecom-Coral | #F43F5E | #FB7185 | #10B981 | #FFF1F2 | #881337 | 母婴/儿童用品 |
| 10 | Ecom-Indigo | #4F46E5 | #6366F1 | #F59E0B | #EEF2FF | #312E81 | 书籍/文创电商 |
| 11 | Ecom-Gold | #B45309 | #D97706 | #1D4ED8 | #FFFBEB | #78350F | 珠宝/奢侈品 |
| 12 | Ecom-Lime | #65A30D | #84CC16 | #6366F1 | #F7FEE7 | #365314 | 运动/户外电商 |
| 13 | Ecom-Slate | #475569 | #64748B | #F97316 | #F8FAFC | #0F172A | B2B批发/工业品 |
| 14 | Ecom-Rose | #E11D48 | #F43F5E | #10B981 | #FFF1F2 | #881337 | 花店/礼品电商 |
| 15 | Ecom-Cyan | #0891B2 | #06B6D4 | #F97316 | #ECFEFF | #164E63 | 宠物用品电商 |

***

## Education（10套）

| # | 名称 | 主色 | 辅色 | CTA色 | 背景色 | 文字色 | 注释 |
|---|------|------|------|-------|--------|--------|------|
| 1 | Edu-Blue | #2563EB | #3B82F6 | #10B981 | #EFF6FF | #1E3A5F | 在线教育，蓝色知识 |
| 2 | Edu-Purple | #7C3AED | #8B5CF6 | #F59E0B | #FAF5FF | #4C1D95 | 创意教育，紫色想象 |
| 3 | Edu-Teal | #0D9488 | #14B8A6 | #F97316 | #F0FDFA | #134E4A | STEM教育，青绿探索 |
| 4 | Edu-Green | #16A34A | #22C55E | #6366F1 | #F0FDF4 | #14532D | 环保教育，绿色成长 |
| 5 | Edu-Orange | #EA580C | #F97316 | #2563EB | #FFF7ED | #7C2D12 | K12教育，橙色活力 |
| 6 | Edu-Indigo | #4338CA | #4F46E5 | #10B981 | #EEF2FF | #312E81 | 高等教育，靛蓝学术 |
| 7 | Edu-Sky | #0284C7 | #0EA5E9 | #F59E0B | #F0F9FF | #0C4A6E | 语言学习，天空蓝开放 |
| 8 | Edu-Rose | #E11D48 | #F43F5E | #0EA5E9 | #FFF1F2 | #881337 | 艺术教育，玫瑰红热情 |
| 9 | Edu-Amber | #D97706 | #F59E0B | #6366F1 | #FFFBEB | #78350F | 职业培训，琥珀黄专注 |
| 10 | Edu-Slate | #475569 | #64748B | #10B981 | #F8FAFC | #0F172A | 企业培训，石板灰专业 |

***

## Social Media（10套）

| # | 名称 | 主色 | 辅色 | CTA色 | 背景色 | 文字色 | 注释 |
|---|------|------|------|-------|--------|--------|------|
| 1 | Social-Pink | #EC4899 | #F472B6 | #3B82F6 | #FDF2F8 | #831843 | 照片分享，粉色社交 |
| 2 | Social-Blue | #2563EB | #3B82F6 | #10B981 | #EFF6FF | #1E3A5F | 职业社交，蓝色信任 |
| 3 | Social-Purple | #8B5CF6 | #A78BFA | #F59E0B | #FAF5FF | #4C1D95 | 创作者社区，紫色创意 |
| 4 | Social-Red | #DC2626 | #EF4444 | #F59E0B | #FEF2F2 | #7F1D1D | 视频平台，红色热情 |
| 5 | Social-Teal | #14B8A6 | #2DD4BF | #F97316 | #F0FDFA | #134E4A | 兴趣社区，青绿和谐 |
| 6 | Social-Indigo | #4F46E5 | #6366F1 | #10B981 | #EEF2FF | #312E81 | 知识社区，靛蓝深度 |
| 7 | Social-Green | #16A34A | #22C55E | #F97316 | #F0FDF4 | #14532D | 环保社区，绿色自然 |
| 8 | Social-Orange | #EA580C | #F97316 | #3B82F6 | #FFF7ED | #7C2D12 | 活动社交，橙色活力 |
| 9 | Social-Cyan | #06B6D4 | #22D3EE | #EC4899 | #ECFEFF | #164E63 | 匿名社交，青色自由 |
| 10 | Social-Rose | #F43F5E | #FB7185 | #3B82F6 | #FFF1F2 | #881337 | 约会社交，玫瑰红浪漫 |

***

## Travel（10套）

| # | 名称 | 主色 | 辅色 | CTA色 | 背景色 | 文字色 | 注释 |
|---|------|------|------|-------|--------|--------|------|
| 1 | Travel-Sky | #0284C7 | #0EA5E9 | #F59E0B | #F0F9FF | #0C4A6E | 机票/酒店，天空蓝自由 |
| 2 | Travel-Teal | #0D9488 | #14B8A6 | #F97316 | #F0FDFA | #134E4A | 度假/海岛，青绿放松 |
| 3 | Travel-Orange | #EA580C | #F97316 | #2563EB | #FFF7ED | #7C2D12 | 背包客/探险，橙色冒险 |
| 4 | Travel-Gold | #B45309 | #D97706 | #1D4ED8 | #FFFBEB | #78350F | 奢华旅行，金色尊贵 |
| 5 | Travel-Green | #16A34A | #22C55E | #F97316 | #F0FDF4 | #14532D | 生态旅游，绿色自然 |
| 6 | Travel-Indigo | #4338CA | #4F46E5 | #F59E0B | #EEF2FF | #312E81 | 商务旅行，靛蓝专业 |
| 7 | Travel-Coral | #F43F5E | #FB7185 | #0EA5E9 | #FFF1F2 | #881337 | 游轮/度假村，珊瑚红欢快 |
| 8 | Travel-Purple | #7C3AED | #8B5CF6 | #10B981 | #FAF5FF | #4C1D95 | 文化旅行，紫色神秘 |
| 9 | Travel-Cyan | #0891B2 | #06B6D4 | #F97316 | #ECFEFF | #164E63 | 潜水/水上运动 |
| 10 | Travel-Slate | #475569 | #64748B | #10B981 | #F8FAFC | #0F172A | 旅行攻略/指南 |

***

## Food & Beverage（10套）

| # | 名称 | 主色 | 辅色 | CTA色 | 背景色 | 文字色 | 注释 |
|---|------|------|------|-------|--------|--------|------|
| 1 | Food-Orange | #EA580C | #F97316 | #10B981 | #FFF7ED | #7C2D12 | 外卖/餐饮，橙色食欲 |
| 2 | Food-Red | #DC2626 | #EF4444 | #F59E0B | #FEF2F2 | #7F1D1D | 火锅/烧烤，红色热辣 |
| 3 | Food-Green | #16A34A | #22C55E | #F97316 | #F0FDF4 | #14532D | 有机/健康食品，绿色天然 |
| 4 | Food-Brown | #92400E | #B45309 | #10B981 | #FFFBEB | #78350F | 咖啡/烘焙，棕色温暖 |
| 5 | Food-Gold | #B45309 | #D97706 | #1D4ED8 | #FFFBEB | #78350F | 高端餐饮，金色品质 |
| 6 | Food-Cream | #A16207 | #CA8A04 | #0EA5E9 | #FEFCE8 | #713F12 | 甜品/面包，奶油色甜蜜 |
| 7 | Food-Teal | #0D9488 | #14B8A6 | #F97316 | #F0FDFA | #134E4A | 日料/寿司，青绿清新 |
| 8 | Food-Rose | #E11D48 | #F43F5E | #F59E0B | #FFF1F2 | #881337 | 蛋糕/甜品，玫瑰红浪漫 |
| 9 | Food-Sage | #4D7C0F | #65A30D | #F97316 | #F7FEE7 | #365314 | 素食/健康餐，鼠尾草绿 |
| 10 | Food-Amber | #D97706 | #F59E0B | #6366F1 | #FFFBEB | #78350F | 啤酒/酒类，琥珀黄醇厚 |

***

## Real Estate（10套）

| # | 名称 | 主色 | 辅色 | CTA色 | 背景色 | 文字色 | 注释 |
|---|------|------|------|-------|--------|--------|------|
| 1 | RE-Navy | #1E3A5F | #2D5F8A | #F59E0B | #F8FAFC | #0F172A | 房产平台，深蓝稳重 |
| 2 | RE-Gold | #B45309 | #D97706 | #1D4ED8 | #FFFBEB | #78350F | 高端地产，金色尊贵 |
| 3 | RE-Green | #16A34A | #22C55E | #F97316 | #F0FDF4 | #14532D | 新房/楼盘，绿色新生活 |
| 4 | RE-Teal | #0D9488 | #14B8A6 | #F59E0B | #F0FDFA | #134E4A | 装修/家居，青绿舒适 |
| 5 | RE-Slate | #475569 | #64748B | #10B981 | #F8FAFC | #0F172A | 商业地产，石板灰专业 |
| 6 | RE-Blue | #2563EB | #3B82F6 | #F59E0B | #EFF6FF | #1E3A5F | 租房平台，蓝色信任 |
| 7 | RE-Earth | #92400E | #B45309 | #10B981 | #FFFBEB | #78350F | 乡村/别墅，大地色自然 |
| 8 | RE-Indigo | #4338CA | #4F46E5 | #F59E0B | #EEF2FF | #312E81 | 物业管理，靛蓝规范 |
| 9 | RE-Warm | #EA580C | #F97316 | #2563EB | #FFF7ED | #7C2D12 | 中介/代理，暖橙热情 |
| 10 | RE-Pine | #166534 | #15803D | #F59E0B | #F0FDF4 | #14532D | 园林/景观，松绿生态 |

***

## Gaming（10套）

| # | 名称 | 主色 | 辅色 | CTA色 | 背景色 | 文字色 | 注释 |
|---|------|------|------|-------|--------|--------|------|
| 1 | Game-Purple | #7C3AED | #8B5CF6 | #F59E0B | #1A1025 | #E2E8F0 | RPG/奇幻，紫色魔法 |
| 2 | Game-Neon | #22D3EE | #06B6D4 | #F43F5E | #0A0A0A | #F0FDFA | 赛博朋克，霓虹冲击 |
| 3 | Game-Red | #DC2626 | #EF4444 | #FBBF24 | #1C0A0A | #FEF2F2 | FPS/射击，红色战斗 |
| 4 | Game-Green | #16A34A | #22C55E | #F97316 | #0A1C0A | #F0FDF4 | 策略/模拟，绿色策略 |
| 5 | Game-Orange | #EA580C | #F97316 | #3B82F6 | #1C0F0A | #FFF7ED | 竞速/体育，橙色速度 |
| 6 | Game-Blue | #2563EB | #3B82F6 | #F59E0B | #0A0F1C | #EFF6FF | 太空/科幻，蓝色探索 |
| 7 | Game-Pink | #EC4899 | #F472B6 | #10B981 | #1C0A14 | #FDF2F8 | 休闲/益智，粉色趣味 |
| 8 | Game-Gold | #B45309 | #D97706 | #6366F1 | #1C150A | #FFFBEB | MMORPG，金色史诗 |
| 9 | Game-Cyan | #06B6D4 | #22D3EE | #F43F5E | #0A141C | #ECFEFF | 电子竞技，青色竞技 |
| 10 | Game-Indigo | #4338CA | #4F46E5 | #10B981 | #0F0A1C | #EEF2FF | 解谜/冒险，靛蓝神秘 |

***

## Creative/Design（10套）

| # | 名称 | 主色 | 辅色 | CTA色 | 背景色 | 文字色 | 注释 |
|---|------|------|------|-------|--------|--------|------|
| 1 | Creative-Purple | #8B5CF6 | #A78BFA | #F59E0B | #FAF5FF | #3B0764 | 设计工具，紫色创意 |
| 2 | Creative-Pink | #EC4899 | #F472B6 | #10B981 | #FDF2F8 | #831843 | 摄影平台，粉色艺术 |
| 3 | Creative-Black | #18181B | #27272A | #F59E0B | #FAFAFA | #09090B | 作品集，黑色聚焦 |
| 4 | Creative-Orange | #EA580C | #F97316 | #2563EB | #FFF7ED | #7C2D12 | 创意机构，橙色活力 |
| 5 | Creative-Teal | #14B8A6 | #2DD4BF | #F97316 | #F0FDFA | #134E4A | UI设计，青绿现代 |
| 6 | Creative-Indigo | #4F46E5 | #6366F1 | #10B981 | #EEF2FF | #312E81 | 插画平台，靛蓝想象 |
| 7 | Creative-Rose | #F43F5E | #FB7185 | #3B82F6 | #FFF1F2 | #881337 | 时尚设计，玫瑰红大胆 |
| 8 | Creative-Lime | #65A30D | #84CC16 | #6366F1 | #F7FEE7 | #365314 | 可持续设计，青柠绿 |
| 9 | Creative-Fuchsia | #C026D3 | #D946EF | #10B981 | #FDF4FF | #701A75 | 3D/动画，紫红动感 |
| 10 | Creative-Sky | #0284C7 | #0EA5E9 | #F97316 | #F0F9FF | #0C4A6E | 视频编辑，天空蓝专业 |

***

## Government（5套）

| # | 名称 | 主色 | 辅色 | CTA色 | 背景色 | 文字色 | 注释 |
|---|------|------|------|-------|--------|--------|------|
| 1 | Gov-Navy | #1E3A5F | #2D5F8A | #10B981 | #F8FAFC | #0F172A | 政府门户，深蓝权威 |
| 2 | Gov-Blue | #1D4ED8 | #2563EB | #F59E0B | #EFF6FF | #1E3A5F | 政务服务，蓝色公信 |
| 3 | Gov-Red | #B91C1C | #DC2626 | #2563EB | #FEF2F2 | #7F1D1D | 党政机关，红色庄重 |
| 4 | Gov-Slate | #334155 | #475569 | #10B981 | #F1F5F9 | #0F172A | 公共服务，石板灰中立 |
| 5 | Gov-Teal | #0F766E | #14B8A6 | #F59E0B | #F0FDFA | #134E4A | 环保/城建，青绿民生 |

***

## Non-profit（5套）

| # | 名称 | 主色 | 辅色 | CTA色 | 背景色 | 文字色 | 注释 |
|---|------|------|------|-------|--------|--------|------|
| 1 | NPO-Green | #16A34A | #22C55E | #F97316 | #F0FDF4 | #14532D | 环保组织，绿色希望 |
| 2 | NPO-Blue | #2563EB | #3B82F6 | #10B981 | #EFF6FF | #1E3A5F | 教育公益，蓝色信任 |
| 3 | NPO-Orange | #EA580C | #F97316 | #2563EB | #FFF7ED | #7C2D12 | 救助/扶贫，橙色温暖 |
| 4 | NPO-Teal | #0D9488 | #14B8A6 | #F59E0B | #F0FDFA | #134E4A | 医疗公益，青绿关怀 |
| 5 | NPO-Purple | #7C3AED | #8B5CF6 | #10B981 | #FAF5FF | #4C1D95 | 文化保护，紫色传承 |

***

## 其他行业（21套）

| # | 名称 | 主色 | 辅色 | CTA色 | 背景色 | 文字色 | 注释 |
|---|------|------|------|-------|--------|--------|------|
| 1 | Legal-Navy | #1E3A5F | #2D5F8A | #F59E0B | #F8FAFC | #0F172A | 法律服务 |
| 2 | Legal-Slate | #334155 | #475569 | #10B981 | #F1F5F9 | #0F172A | 律师事务所 |
| 3 | Auto-Blue | #1D4ED8 | #2563EB | #F59E0B | #EFF6FF | #1E3A5F | 汽车/出行 |
| 4 | Auto-Red | #DC2626 | #EF4444 | #1D4ED8 | #FEF2F2 | #7F1D1D | 跑车/运动汽车 |
| 5 | Energy-Green | #16A34A | #22C55E | #F97316 | #F0FDF4 | #14532D | 新能源 |
| 6 | Energy-Blue | #0284C7 | #0EA5E9 | #10B981 | #F0F9FF | #0C4A6E | 电力/电网 |
| 7 | Logistics-Orange | #EA580C | #F97316 | #2563EB | #FFF7ED | #7C2D12 | 物流/快递 |
| 8 | Logistics-Blue | #2563EB | #3B82F6 | #F59E0B | #EFF6FF | #1E3A5F | 供应链 |
| 9 | Media-Red | #DC2626 | #EF4444 | #F59E0B | #FEF2F2 | #7F1D1D | 新闻/媒体 |
| 10 | Media-Purple | #7C3AED | #8B5CF6 | #10B981 | #FAF5FF | #4C1D95 | 流媒体 |
| 11 | Telecom-Blue | #1D4ED8 | #2563EB | #F59E0B | #EFF6FF | #1E3A5F | 电信/通信 |
| 12 | Telecom-Cyan | #0891B2 | #06B6D4 | #F97316 | #ECFEFF | #164E63 | 5G/物联网 |
| 13 | Agri-Green | #15803D | #22C55E | #F97316 | #F0FDF4 | #14532D | 农业/种植 |
| 14 | Agri-Earth | #92400E | #B45309 | #10B981 | #FFFBEB | #78350F | 畜牧/渔业 |
| 15 | Mining-Amber | #B45309 | #D97706 | #1D4ED8 | #FFFBEB | #78350F | 矿业/资源 |
| 16 | Space-Indigo | #4338CA | #4F46E5 | #10B981 | #0F0A1C | #EEF2FF | 航天/航空 |
| 17 | Space-Blue | #1E40AF | #2563EB | #FBBF24 | #EFF6FF | #1E3A5F | 卫星/导航 |
| 18 | Sports-Green | #16A34A | #22C55E | #F97316 | #F0FDF4 | #14532D | 体育/健身 |
| 19 | Sports-Orange | #EA580C | #F97316 | #2563EB | #FFF7ED | #7C2D12 | 运动装备 |
| 20 | Religion-Gold | #B45309 | #D97706 | #1D4ED8 | #FFFBEB | #78350F | 宗教/信仰 |
| 21 | Religion-Indigo | #4338CA | #4F46E5 | #F59E0B | #EEF2FF | #312E81 | 冥想/灵性 |

***

## 行业反模式清单

> 以下配色组合在对应行业中应严格避免，Agent推理引擎必须过滤。

| 行业 | 反模式 | 原因 |
|------|--------|------|
| Healthcare | 霓虹色(#00FF00, #FF00FF, #00FFFF) | 不专业、引发焦虑 |
| Healthcare | 纯黑背景+红色文字 | 暗示危险/血液，引发恐慌 |
| Healthcare | 高饱和荧光色 | 刺激性强，不适合医疗场景 |
| Fintech | AI紫粉渐变(#8B5CF6→#EC4899) | 轻浮不稳重，缺乏信任感 |
| Fintech | 霓虹绿(#00FF00) | 暗示黑客/非法交易 |
| Fintech | 高饱和红色为主色 | 暗示亏损/危险 |
| Government | 鲜艳色(荧光粉/荧光绿/荧光黄) | 不庄重，缺乏公信力 |
| Government | 渐变背景 | 不正式，花哨 |
| Government | 圆角过大(>16px) | 不严肃 |
| Non-profit | 纯黑+金色 | 过于奢华，与公益形象冲突 |
| Non-profit | 军事色彩(迷彩绿/军灰) | 暗示暴力/冲突 |
| Education | 纯黑背景 | 压抑，不适合学习环境 |
| Education | 过多荧光色 | 分散注意力 |
| E-commerce | 灰色CTA按钮 | 缺乏行动引导力 |
| E-commerce | 大面积紫色 | 非主流，降低购买欲 |
| Legal | 渐变/彩虹色 | 不专业，缺乏权威 |
| Legal | 圆角>12px | 不严肃 |
| Gaming | 纯白背景+灰色文字 | 缺乏沉浸感 |
| Social Media | 纯灰配色 | 缺乏社交活力 |
| Fintech | 粉色主色 | 不专业，缺乏金融严肃性 |
| Healthcare | 紫色渐变 | 神秘感与医疗专业冲突 |
