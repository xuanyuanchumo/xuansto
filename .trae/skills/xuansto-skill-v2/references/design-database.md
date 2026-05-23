# UI风格设计数据库

> 版本: 3.0.0 | 更新日期: 2026-05-05 | 编码: UTF-8 | 行尾: LF

## 概述

本文件定义67种UI风格，供Design System Generator Agent和UI Designer Agent参考。Agent应使用BM25排序按需搜索本文件，不预加载全部数据。每种风格包含名称、关键词、最佳场景、性能评级、可访问性评级和框架特定实现提示。

## 按需搜索说明

- Agent应基于项目需求使用关键词搜索本文件，而非全量加载
- 推荐搜索策略：先按类别定位，再按关键词精确匹配
- BM25排序权重：关键词匹配(40%) + 场景匹配(30%) + 行业匹配(30%)
- 每次搜索返回Top 5风格供推理引擎排序

## 风格分类索引

| 类别 | 数量 | 风格列表 |
|------|------|----------|
| 现代简约类 | 10 | Minimalism, Clean Design, Swiss Style, Flat Design 2.0, Material Design 3, iOS HIG, Fluent Design, Spectrum, Carbon, Primer |
| 玻璃质感类 | 5 | Glassmorphism, Frosted Glass, Crystal, Ice, Aurora |
| 新拟物类 | 5 | Neumorphism, Soft UI, Claymorphism, Emboss, Cushion |
| 大胆表现类 | 8 | Brutalism, Neo-Brutalism, Maximalism, Memphis, Pop Art, Grunge, Punk, Dada |
| 渐变色彩类 | 5 | Gradient Mesh, Holographic, Iridescent, Sunset, Neon Gradient |
| 暗色主题类 | 5 | Dark Mode, OLED Black, Midnight, Carbon, Shadow |
| 复古怀旧类 | 5 | Retro, Vintage, Art Deco, Steampunk, Pixel |
| 自然有机类 | 5 | Organic, Biophilic, Earthy, Botanical, Wave |
| 科技未来类 | 5 | Cyberpunk, Neon, Synthwave, Quantum, Holographic UI |
| 手绘插画类 | 5 | Hand-drawn, Sketch, Watercolor, Doodle, Collage |
| 其他类 | 9 | Corporate, Editorial, Magazine, Newspaper, Dashboard-first, Mobile-first, Print-inspired, Data-driven, Accessible-first |

***

## 现代简约类（10种）

### 1. Minimalism

| 属性 | 值 |
|------|-----|
| 关键词 | 极简, 留白, 少即是多, 纯净, 精炼 |
| 最佳场景 | SaaS仪表盘, 企业官网, 作品集, 阅读应用 |
| 性能评级 | 5/5 |
| 可访问性评级 | 4/5 |

**框架实现提示**：
- React: 使用CSS-in-JS或Tailwind，保持组件props最小化
- Vue: Composition API + scoped styles，避免过度嵌套
- Tailwind: `space-y-4`, `px-6`, `max-w-4xl`, `text-gray-900`

### 2. Clean Design

| 属性 | 值 |
|------|-----|
| 关键词 | 清爽, 整洁, 规范, 一致, 有序 |
| 最佳场景 | 企业应用, 管理后台, 文档站点, 教育平台 |
| 性能评级 | 5/5 |
| 可访问性评级 | 5/5 |

**框架实现提示**：
- React: 标准化组件库(如shadcn/ui)，严格设计令牌
- Vue: Vuetify/Element Plus规范组件
- Tailwind: `bg-white`, `border`, `rounded-lg`, `shadow-sm`

### 3. Swiss Style

| 属性 | 值 |
|------|-----|
| 关键词 | 网格, 排版, 几何, 理性, 国际主义 |
| 最佳场景 | 新闻媒体, 杂志, 文化机构, 设计工作室 |
| 性能评级 | 5/5 |
| 可访问性评级 | 4/5 |

**框架实现提示**：
- React: CSS Grid布局，严格排版系统
- Vue: Grid组件 + 排版mixin
- Tailwind: `grid`, `gap-8`, `font-bold`, `uppercase`, `tracking-wide`

### 4. Flat Design 2.0

| 属性 | 值 |
|------|-----|
| 关键词 | 扁平, 微阴影, 层次, 简洁, 现代 |
| 最佳场景 | 移动应用, SaaS产品, 社交平台, 工具类应用 |
| 性能评级 | 5/5 |
| 可访问性评级 | 4/5 |

**框架实现提示**：
- React: 微阴影层级系统，z-index管理
- Vue: 过渡动画 + 阴影变量
- Tailwind: `shadow-sm`, `shadow-md`, `border`, `rounded-lg`

### 5. Material Design 3

| 属性 | 值 |
|------|-----|
| 关键词 | 动态色彩, 圆角, 海拔, 主题, Material You |
| 最佳场景 | Android应用, 跨平台应用, Google生态产品 |
| 性能评级 | 4/5 |
| 可访问性评级 | 5/5 |

**框架实现提示**：
- React: MUI/Material Web组件，动态主题引擎
- Vue: Vuetify 3 Material Design组件
- Tailwind: 自定义Material令牌映射 + `rounded-2xl`, `elevation-*`

### 6. iOS HIG

| 属性 | 值 |
|------|-----|
| 关键词 | 苹果, 原生, SF字体, 模糊, 弹性 |
| 最佳场景 | iOS应用, macOS应用, Apple生态产品 |
| 性能评级 | 4/5 |
| 可访问性评级 | 5/5 |

**框架实现提示**：
- React: React Native + 原生模块，SF Symbols
- Vue: Capacitor + iOS风格组件
- Tailwind: `backdrop-blur-xl`, `rounded-2xl`, `-apple-system`

### 7. Fluent Design

| 属性 | 值 |
|------|-----|
| 关键词 | 亚克力, 深度, 光效, Windows, 微软 |
| 最佳场景 | Windows应用, 企业工具, 桌面应用, Office插件 |
| 性能评级 | 3/5 |
| 可访问性评级 | 5/5 |

**框架实现提示**：
- React: Fluent UI React组件库
- Vue: 自定义Fluent风格组件
- Tailwind: `backdrop-blur`, `bg-white/80`, `shadow-lg`

### 8. Spectrum

| 属性 | 值 |
|------|-----|
| 关键词 | Adobe, 创意, 专业, 色彩丰富, 工具化 |
| 最佳场景 | 创意工具, 设计应用, 编辑器, 专业软件 |
| 性能评级 | 4/5 |
| 可访问性评级 | 4/5 |

**框架实现提示**：
- React: React Spectrum组件库
- Vue: 自定义Spectrum风格系统
- Tailwind: 自定义色彩令牌 + `ring-2`, `focus-visible`

### 9. Carbon

| 属性 | 值 |
|------|-----|
| 关键词 | IBM, 企业, 严谨, 数据, 工程 |
| 最佳场景 | 企业级应用, 数据平台, 工程工具, B2B产品 |
| 性能评级 | 5/5 |
| 可访问性评级 | 5/5 |

**框架实现提示**：
- React: Carbon Design System组件
- Vue: 自定义Carbon风格组件
- Tailwind: `bg-gray-100`, `border-l-4`, `font-mono`

### 10. Primer

| 属性 | 值 |
|------|-----|
| 关键词 | GitHub, 开发者, 代码, 协作, 仓库 |
| 最佳场景 | 开发者工具, 代码平台, DevOps面板, 技术文档 |
| 性能评级 | 5/5 |
| 可访问性评级 | 5/5 |

**框架实现提示**：
- React: Primer React组件
- Vue: 自定义Primer风格
- Tailwind: `bg-gray-900`, `text-green-400`, `font-mono`, `border`

***

## 玻璃质感类（5种）

### 11. Glassmorphism

| 属性 | 值 |
|------|-----|
| 关键词 | 磨砂玻璃, 半透明, 模糊, 渐变边框, 悬浮 |
| 最佳场景 | 登录页, 音乐播放器, 天气应用, 创意展示 |
| 性能评级 | 2/5 |
| 可访问性评级 | 2/5 |

**框架实现提示**：
- React: `backdrop-filter` CSS属性，注意浏览器兼容性
- Vue: 降级方案：半透明背景色替代模糊
- Tailwind: `backdrop-blur-lg`, `bg-white/20`, `border border-white/30`

### 12. Frosted Glass

| 属性 | 值 |
|------|-----|
| 关键词 | 霜化, 柔和模糊, 朦胧, 冷色调, 优雅 |
| 最佳场景 | 导航栏, 侧边栏, 卡片叠加, 模态框 |
| 性能评级 | 3/5 |
| 可访问性评级 | 3/5 |

**框架实现提示**：
- React: `backdrop-filter: blur(8px)` + 半透明背景
- Vue: CSS变量控制模糊程度
- Tailwind: `backdrop-blur-md`, `bg-slate-200/60`

### 13. Crystal

| 属性 | 值 |
|------|-----|
| 关键词 | 水晶, 折射, 透明, 光泽, 棱角 |
| 最佳场景 | 奢侈品展示, 高端产品页, 珠宝电商 |
| 性能评级 | 2/5 |
| 可访问性评级 | 2/5 |

**框架实现提示**：
- React: CSS `mix-blend-mode` + 渐变叠加
- Vue: SVG滤镜实现折射效果
- Tailwind: `mix-blend-overlay`, `bg-gradient-to-br`

### 14. Ice

| 属性 | 值 |
|------|-----|
| 关键词 | 冰晶, 冷冽, 通透, 蓝白, 冻结 |
| 最佳场景 | 冬季主题, 冷链物流, 极地探险, 冷饮品牌 |
| 性能评级 | 3/5 |
| 可访问性评级 | 3/5 |

**框架实现提示**：
- React: 蓝白渐变 + 微透明层叠
- Vue: CSS动画实现冰晶闪烁
- Tailwind: `bg-blue-50/80`, `backdrop-blur-sm`, `border-cyan-200`

### 15. Aurora

| 属性 | 值 |
|------|-----|
| 关键词 | 极光, 流动, 色彩变幻, 北极光, 梦幻 |
| 最佳场景 | 创意机构, 音乐应用, 沉浸式体验, 品牌展示 |
| 性能评级 | 2/5 |
| 可访问性评级 | 2/5 |

**框架实现提示**：
- React: CSS动画 + `@keyframes`实现流动渐变
- Vue: Canvas或CSS渐变动画
- Tailwind: `bg-gradient-to-r from-green-400 via-blue-500 to-purple-600 animate-[aurora_8s_ease-in-out_infinite]`

***

## 新拟物类（5种）

### 16. Neumorphism

| 属性 | 值 |
|------|-----|
| 关键词 | 软凸起, 双阴影, 同色系, 柔和, 触感 |
| 最佳场景 | 音乐播放器, 天气应用, 计算器, 智能家居控制 |
| 性能评级 | 4/5 |
| 可访问性评级 | 2/5 |

**框架实现提示**：
- React: 双阴影系统 `box-shadow: 8px 8px 16px #d1d1d1, -8px -8px 16px #ffffff`
- Vue: SCSS mixin生成凸起/凹陷效果
- Tailwind: 自定义shadow令牌 `[box-shadow:8px_8px_16px_#d1d1d1,-8px_-8px_16px_#ffffff]`

### 17. Soft UI

| 属性 | 值 |
|------|-----|
| 关键词 | 柔软, 温和, 微阴影, 舒适, 亲和 |
| 最佳场景 | 健康应用, 冥想应用, 儿童产品, 生活方式 |
| 性能评级 | 4/5 |
| 可访问性评级 | 3/5 |

**框架实现提示**：
- React: 柔和阴影 + 圆角 + 柔和色彩
- Vue: CSS变量控制阴影强度
- Tailwind: `shadow-[0_2px_8px_rgba(0,0,0,0.08)]`, `rounded-2xl`

### 18. Claymorphism

| 属性 | 值 |
|------|-----|
| 关键词 | 粘土, 膨胀, 厚重阴影, 玩具感, 可爱 |
| 最佳场景 | 儿童应用, 游戏界面, 趣味工具, 社交应用 |
| 性能评级 | 3/5 |
| 可访问性评级 | 2/5 |

**框架实现提示**：
- React: 内阴影 + 外阴影组合，大圆角
- Vue: SCSS函数生成粘土效果
- Tailwind: `rounded-3xl`, `shadow-[0_8px_24px_rgba(0,0,0,0.15),inset_0_-4px_8px_rgba(0,0,0,0.1)]`

### 19. Emboss

| 属性 | 值 |
|------|-----|
| 关键词 | 浮雕, 凸刻, 质感, 金属, 印章 |
| 最佳场景 | 奢侈品牌, 证书, 奖章, 高端会员 |
| 性能评级 | 4/5 |
| 可访问性评级 | 3/5 |

**框架实现提示**：
- React: `text-shadow` + `box-shadow`内阴影模拟浮雕
- Vue: CSS滤镜 `filter: drop-shadow()`
- Tailwind: `[text-shadow:1px_1px_0_#fff,-1px_-1px_0_#000]`

### 20. Cushion

| 属性 | 值 |
|------|-----|
| 关键词 | 垫子, 柔软, 按压感, 弹性, 舒适 |
| 最佳场景 | 电商产品页, 家居应用, 舒适型产品 |
| 性能评级 | 4/5 |
| 可访问性评级 | 3/5 |

**框架实现提示**：
- React: `:active`状态变形 + 阴影变化
- Vue: CSS transition模拟按压回弹
- Tailwind: `active:scale-95`, `transition-transform`, `shadow-lg active:shadow-sm`

***

## 大胆表现类（8种）

### 21. Brutalism

| 属性 | 值 |
|------|-----|
| 关键词 | 粗野, 原始, 粗暴, 反装饰, 结构暴露 |
| 最佳场景 | 艺术展览, 实验项目, 独立开发者, 反叛品牌 |
| 性能评级 | 5/5 |
| 可访问性评级 | 2/5 |

**框架实现提示**：
- React: 无CSS框架，原生HTML + 粗边框
- Vue: 最小化样式，黑白高对比
- Tailwind: `border-4 border-black`, `bg-white`, `font-bold`, `no-underline`

### 22. Neo-Brutalism

| 属性 | 值 |
|------|-----|
| 关键词 | 新粗野, 粗边框, 偏移阴影, 鲜艳色, 趣味 |
| 最佳场景 | 创业公司, Z世代产品, 个人品牌, 创意机构 |
| 性能评级 | 5/5 |
| 可访问性评级 | 3/5 |

**框架实现提示**：
- React: 粗边框 + 偏移阴影组件系统
- Vue: CSS变量控制偏移量
- Tailwind: `border-2 border-black shadow-[4px_4px_0_#000]`, `bg-yellow-300`

### 23. Maximalism

| 属性 | 值 |
|------|-----|
| 关键词 | 极繁, 丰富, 层叠, 装饰, 奢华 |
| 最佳场景 | 时尚品牌, 奢侈品, 艺术画廊, 音乐节 |
| 性能评级 | 2/5 |
| 可访问性评级 | 1/5 |

**框架实现提示**：
- React: 复杂组件嵌套 + 动画库
- Vue: 多层叠加 + CSS动画
- Tailwind: 多class组合，渐变 + 阴影 + 变换叠加

### 24. Memphis

| 属性 | 值 |
|------|-----|
| 关键词 | 孟菲斯, 几何, 波点, 锯齿, 撞色 |
| 最佳场景 | 儿童产品, 创意工作室, 时尚品牌, 派对 |
| 性能评级 | 3/5 |
| 可访问性评级 | 2/5 |

**框架实现提示**：
- React: SVG图案 + 几何形状组件
- Vue: CSS `background-image`重复图案
- Tailwind: 自定义背景图案 + `bg-yellow-400`, `border-4 border-black`

### 25. Pop Art

| 属性 | 值 |
|------|-----|
| 关键词 | 波普, 半调, 漫画, 醒目, 夸张 |
| 最佳场景 | 潮牌, 娱乐应用, 活动页面, 青年文化 |
| 性能评级 | 3/5 |
| 可访问性评级 | 2/5 |

**框架实现提示**：
- React: SVG滤镜实现半调效果
- Vue: CSS `mix-blend-mode` + 粗描边
- Tailwind: `border-4`, `contrast-150`, `saturate-150`

### 26. Grunge

| 属性 | 值 |
|------|-----|
| 关键词 | 破碎, 纹理, 粗糙, 噪点, 叛逆 |
| 最佳场景 | 音乐乐队, 地下文化, 滑板品牌, 独立杂志 |
| 性能评级 | 3/5 |
| 可访问性评级 | 1/5 |

**框架实现提示**：
- React: 噪点纹理叠加 + 不规则边框
- Vue: CSS `filter: url()` SVG噪点
- Tailwind: 自定义噪点背景 + `rotate-1`, `skew-x-1`

### 27. Punk

| 属性 | 值 |
|------|-----|
| 关键词 | 朋克, 撕裂, 安全别针, 荧光, 反体制 |
| 最佳场景 | 音乐节, 潮牌, 地下活动, 反文化社区 |
| 性能评级 | 4/5 |
| 可访问性评级 | 1/5 |

**框架实现提示**：
- React: 不规则布局 + 荧光色块
- Vue: CSS `clip-path`实现撕裂效果
- Tailwind: `bg-lime-400`, `clip-path-[polygon(...)]`, `uppercase`

### 28. Dada

| 属性 | 值 |
|------|-----|
| 关键词 | 达达, 荒诞, 随机, 拼贴, 反逻辑 |
| 最佳场景 | 实验艺术, 前卫项目, 概念展示 |
| 性能评级 | 3/5 |
| 可访问性评级 | 1/5 |

**框架实现提示**：
- React: 随机布局生成 + 碰撞检测
- Vue: CSS Grid随机位置 + 旋转
- Tailwind: `rotate-[17deg]`, `translate-x-12`, `z-50`

***

## 渐变色彩类（5种）

### 29. Gradient Mesh

| 属性 | 值 |
|------|-----|
| 关键词 | 网格渐变, 多色融合, 流体, 苹果风, 高级 |
| 最佳场景 | 科技产品, SaaS落地页, 品牌展示, App背景 |
| 性能评级 | 3/5 |
| 可访问性评级 | 3/5 |

**框架实现提示**：
- React: CSS `background`多渐变叠加或Canvas绘制
- Vue: SVG径向渐变组合
- Tailwind: `bg-[radial-gradient(...)]` 自定义渐变

### 30. Holographic

| 属性 | 值 |
|------|-----|
| 关键词 | 全息, 彩虹, 折射, 金属, 幻彩 |
| 最佳场景 | 会员卡, 支付成功, 高级功能, 奖励系统 |
| 性能评级 | 2/5 |
| 可访问性评级 | 2/5 |

**框架实现提示**：
- React: CSS `background-clip: text` + 动画渐变
- Vue: 鼠标跟随渐变角度变化
- Tailwind: `[background-clip:text]`, `[background:linear-gradient(...)]`

### 31. Iridescent

| 属性 | 值 |
|------|-----|
| 关键词 | 虹彩, 变色, 珍珠, 视角, 微光 |
| 最佳场景 | 美妆品牌, 时尚电商, 珠宝展示, 奢侈品 |
| 性能评级 | 2/5 |
| 可访问性评级 | 2/5 |

**框架实现提示**：
- React: 鼠标位置驱动渐变角度
- Vue: CSS `hsl()`动态色相
- Tailwind: 动态style绑定 + `transition-colors`

### 32. Sunset

| 属性 | 值 |
|------|-----|
| 关键词 | 日落, 暖色, 橙紫, 天际, 浪漫 |
| 最佳场景 | 旅行应用, 约会应用, 生活方式, 摄影平台 |
| 性能评级 | 4/5 |
| 可访问性评级 | 3/5 |

**框架实现提示**：
- React: 线性渐变橙→粉→紫
- Vue: CSS渐变 + 微动画
- Tailwind: `bg-gradient-to-br from-orange-400 via-pink-500 to-purple-600`

### 33. Neon Gradient

| 属性 | 值 |
|------|-----|
| 关键词 | 霓虹渐变, 荧光, 赛博, 电光, 冲击 |
| 最佳场景 | 游戏平台, 电子竞技, 夜生活, 科技活动 |
| 性能评级 | 3/5 |
| 可访问性评级 | 2/5 |

**框架实现提示**：
- React: 荧光渐变 + `text-shadow`发光
- Vue: CSS `filter: brightness()` + 渐变
- Tailwind: `bg-gradient-to-r from-cyan-400 via-fuchsia-500 to-yellow-300`, `[text-shadow:0_0_10px_rgba(0,255,255,0.5)]`

***

## 暗色主题类（5种）

### 34. Dark Mode

| 属性 | 值 |
|------|-----|
| 关键词 | 暗色, 护眼, 深色, 夜间, 节能 |
| 最佳场景 | 开发者工具, 媒体播放, 社交应用, 通用产品 |
| 性能评级 | 5/5 |
| 可访问性评级 | 4/5 |

**框架实现提示**：
- React: CSS变量主题切换 `data-theme="dark"`
- Vue: `prefers-color-scheme` + 手动切换
- Tailwind: `dark:bg-gray-900`, `dark:text-gray-100`, `dark:`变体

### 35. OLED Black

| 属性 | 值 |
|------|-----|
| 关键词 | 纯黑, OLED, 省电, 深邃, 极暗 |
| 最佳场景 | 移动应用(OLED屏), 视频播放, 天文应用 |
| 性能评级 | 5/5 |
| 可访问性评级 | 3/5 |

**框架实现提示**：
- React: `#000000`纯黑背景 + 高对比前景
- Vue: CSS变量 `--bg: #000000`
- Tailwind: `bg-black`, `text-white`, `border-gray-800`

### 36. Midnight

| 属性 | 值 |
|------|-----|
| 关键词 | 午夜, 深蓝, 星空, 沉静, 神秘 |
| 最佳场景 | 冥想应用, 天气应用, 睡眠追踪, 夜间模式 |
| 性能评级 | 5/5 |
| 可访问性评级 | 4/5 |

**框架实现提示**：
- React: 深蓝渐变背景 `#0f172a` → `#1e1b4b`
- Vue: 星空粒子效果背景
- Tailwind: `bg-slate-900`, `bg-indigo-950`, `text-slate-200`

### 37. Carbon

| 属性 | 值 |
|------|-----|
| 关键词 | 碳纤维, 纹理, 工业, 高端, 运动 |
| 最佳场景 | 汽车应用, 运动品牌, 高端科技, 工业设计 |
| 性能评级 | 4/5 |
| 可访问性评级 | 3/5 |

**框架实现提示**：
- React: 碳纤维纹理SVG背景 + 暗色主题
- Vue: CSS `background-image`重复纹理
- Tailwind: `bg-gray-900`, 自定义纹理背景

### 38. Shadow

| 属性 | 值 |
|------|-----|
| 关键词 | 阴影, 层次, 深度, 暗调, 戏剧 |
| 最佳场景 | 游戏界面, 影视应用, 悬疑类产品, 暗黑风 |
| 性能评级 | 4/5 |
| 可访问性评级 | 3/5 |

**框架实现提示**：
- React: 多层阴影 + 暗色渐变
- Vue: CSS `box-shadow`层级系统
- Tailwind: `shadow-2xl`, `bg-gray-950`, `ring-1 ring-gray-800`

***

## 复古怀旧类（5种）

### 39. Retro

| 属性 | 值 |
|------|-----|
| 关键词 | 复古, 怀旧, 80年代, 90年代, 复古未来 |
| 最佳场景 | 复古游戏, 怀旧品牌, 主题餐厅, 复古电商 |
| 性能评级 | 4/5 |
| 可访问性评级 | 3/5 |

**框架实现提示**：
- React: 复古色彩 + 像素风字体
- Vue: CSS `image-rendering: pixelated`
- Tailwind: `bg-amber-100`, `text-amber-900`, `font-mono`

### 40. Vintage

| 属性 | 值 |
|------|-----|
| 关键词 | 老式, 经典, 做旧, 泛黄, 优雅 |
| 最佳场景 | 古董电商, 咖啡品牌, 酒庄, 手工艺品 |
| 性能评级 | 4/5 |
| 可访问性评级 | 3/5 |

**框架实现提示**：
- React: Serif字体 + 暖色调 + 纸张纹理
- Vue: CSS `sepia()`滤镜
- Tailwind: `bg-amber-50`, `text-stone-800`, `font-serif`

### 41. Art Deco

| 属性 | 值 |
|------|-----|
| 关键词 | 装饰艺术, 几何, 金色, 对称, 奢华 |
| 最佳场景 | 奢华酒店, 高端地产, 珠宝品牌, 经典影院 |
| 性能评级 | 4/5 |
| 可访问性评级 | 3/5 |

**框架实现提示**：
- React: SVG几何图案 + 金色渐变
- Vue: CSS `border-image` + 几何边框
- Tailwind: `bg-yellow-600`, `border-2 border-yellow-500`, `tracking-widest`

### 42. Steampunk

| 属性 | 值 |
|------|-----|
| 关键词 | 蒸汽朋克, 齿轮, 铜色, 维多利亚, 机械 |
| 最佳场景 | 游戏界面, 主题酒吧, 创意展示, 科幻产品 |
| 性能评级 | 3/5 |
| 可访问性评级 | 2/5 |

**框架实现提示**：
- React: SVG齿轮动画 + 铜色金属质感
- Vue: CSS `@keyframes`旋转齿轮
- Tailwind: `bg-amber-800`, `text-amber-200`, `ring-2 ring-amber-600`

### 43. Pixel

| 属性 | 值 |
|------|-----|
| 关键词 | 像素, 8位, 游戏机, 方块, 复古游戏 |
| 最佳场景 | 独立游戏, 游戏社区, 像素艺术, 编程教育 |
| 性能评级 | 5/5 |
| 可访问性评级 | 3/5 |

**框架实现提示**：
- React: 像素字体 + `image-rendering: pixelated`
- Vue: CSS Grid实现像素网格
- Tailwind: `font-mono`, `space-x-0`, 自定义像素字体

***

## 自然有机类（5种）

### 44. Organic

| 属性 | 值 |
|------|-----|
| 关键词 | 有机, 曲线, 自然, 流动, 不规则 |
| 最佳场景 | 有机食品, 瑜伽应用, 环保品牌, 生态产品 |
| 性能评级 | 3/5 |
| 可访问性评级 | 4/5 |

**框架实现提示**：
- React: `border-radius: 30% 70% 70% 30% / 30% 30% 70% 70%` 不规则圆角
- Vue: SVG曲线路径 + 流动动画
- Tailwind: `rounded-[30%_70%_70%_30%/30%_30%_70%_70%]`, `bg-green-50`

### 45. Biophilic

| 属性 | 值 |
|------|-----|
| 关键词 | 亲生物, 绿植, 自然光, 木材, 生态 |
| 最佳场景 | 室内设计, 建筑公司, 园艺应用, 环保组织 |
| 性能评级 | 3/5 |
| 可访问性评级 | 4/5 |

**框架实现提示**：
- React: 自然色彩 + 木质纹理背景
- Vue: CSS渐变模拟自然光
- Tailwind: `bg-emerald-50`, `text-emerald-900`, `shadow-lg`

### 46. Earthy

| 属性 | 值 |
|------|-----|
| 关键词 | 大地色, 泥土, 暖棕, 陶土, 质朴 |
| 最佳场景 | 陶艺品牌, 咖啡烘焙, 手工制品, 农场 |
| 性能评级 | 5/5 |
| 可访问性评级 | 4/5 |

**框架实现提示**：
- React: 棕色系色彩 + 质感纹理
- Vue: CSS `background-blend-mode`叠加纹理
- Tailwind: `bg-amber-800`, `text-stone-100`, `bg-stone-200`

### 47. Botanical

| 属性 | 值 |
|------|-----|
| 关键词 | 植物, 花卉, 绿叶, 植物学, 花园 |
| 最佳场景 | 花店, 植物护理, 园艺社区, 自然疗法 |
| 性能评级 | 3/5 |
| 可访问性评级 | 4/5 |

**框架实现提示**：
- React: 植物SVG插图 + 绿色系
- Vue: CSS `mask-image`植物形状裁切
- Tailwind: `bg-green-100`, `text-green-800`, `rounded-full`

### 48. Wave

| 属性 | 值 |
|------|-----|
| 关键词 | 波浪, 海洋, 流动, 起伏, 节奏 |
| 最佳场景 | 冲浪品牌, 海洋保护, 水上运动, SPA |
| 性能评级 | 3/5 |
| 可访问性评级 | 4/5 |

**框架实现提示**：
- React: SVG波浪分隔线 + CSS动画
- Vue: Canvas波浪动画
- Tailwind: 自定义SVG背景 + `animate-pulse`

***

## 科技未来类（5种）

### 49. Cyberpunk

| 属性 | 值 |
|------|-----|
| 关键词 | 赛博朋克, 霓虹, 反乌托邦, 高科技低生活, 故障 |
| 最佳场景 | 游戏界面, 科技活动, NFT平台, 赛博主题 |
| 性能评级 | 3/5 |
| 可访问性评级 | 1/5 |

**框架实现提示**：
- React: 故障效果CSS动画 + 霓虹发光
- Vue: CSS `clip-path` + 随机偏移动画
- Tailwind: `text-cyan-400`, `[text-shadow:0_0_10px_#0ff]`, `bg-gray-950`

### 50. Neon

| 属性 | 值 |
|------|-----|
| 关键词 | 霓虹灯, 发光, 荧光管, 夜间, 醒目 |
| 最佳场景 | 夜生活, 酒吧, 音乐节, 娱乐场所 |
| 性能评级 | 3/5 |
| 可访问性评级 | 2/5 |

**框架实现提示**：
- React: `text-shadow`多层发光 + 暗色背景
- Vue: CSS `box-shadow`霓虹边框
- Tailwind: `[text-shadow:0_0_7px_#fff,0_0_10px_#0ff,0_0_21px_#0ff]`

### 51. Synthwave

| 属性 | 值 |
|------|-----|
| 关键词 | 合成波, 80年代, 日落, 网格, 复古未来 |
| 最佳场景 | 音乐应用, 复古游戏, 80年代主题, DJ平台 |
| 性能评级 | 3/5 |
| 可访问性评级 | 2/5 |

**框架实现提示**：
- React: 透视网格 + 日落渐变
- Vue: CSS `perspective` + 网格线
- Tailwind: `bg-gradient-to-b from-purple-600 via-pink-500 to-orange-400`

### 52. Quantum

| 属性 | 值 |
|------|-----|
| 关键词 | 量子, 粒子, 不确定性, 科学, 前沿 |
| 最佳场景 | 科研平台, 量子计算, 前沿科技, 实验室 |
| 性能评级 | 2/5 |
| 可访问性评级 | 3/5 |

**框架实现提示**：
- React: Three.js粒子系统 + 量子态动画
- Vue: Canvas粒子效果
- Tailwind: `bg-indigo-950`, `text-cyan-300`, `blur-sm`

### 53. Holographic UI

| 属性 | 值 |
|------|-----|
| 关键词 | 全息界面, 透明, 投影, 科幻, 浮空 |
| 最佳场景 | 科幻游戏, 未来概念, AR界面, 概念展示 |
| 性能评级 | 2/5 |
| 可访问性评级 | 1/5 |

**框架实现提示**：
- React: 半透明UI + 扫描线效果
- Vue: CSS `background: linear-gradient()` + 动画
- Tailwind: `bg-cyan-500/10`, `border-cyan-400/30`, `backdrop-blur`

***

## 手绘插画类（5种）

### 54. Hand-drawn

| 属性 | 值 |
|------|-----|
| 关键词 | 手绘, 素描, 不规则, 人文, 温暖 |
| 最佳场景 | 教育平台, 儿童应用, 创意工作室, 个人博客 |
| 性能评级 | 4/5 |
| 可访问性评级 | 3/5 |

**框架实现提示**：
- React: Rough.js库生成手绘风格
- Vue: SVG手绘路径 + CSS动画
- Tailwind: `border-dashed`, `rotate-1`, 自定义手绘字体

### 55. Sketch

| 属性 | 值 |
|------|-----|
| 关键词 | 速写, 线条, 草图, 灵动, 创意 |
| 最佳场景 | 设计工具, 创意流程, 白板应用, 头脑风暴 |
| 性能评级 | 4/5 |
| 可访问性评级 | 3/5 |

**框架实现提示**：
- React: Canvas手绘线条 + SVG
- Vue: CSS `stroke-dasharray`手绘效果
- Tailwind: `border-2 border-dashed border-gray-400`, `skew-y-1`

### 56. Watercolor

| 属性 | 值 |
|------|-----|
| 关键词 | 水彩, 渗染, 柔和, 艺术, 流动 |
| 最佳场景 | 艺术教育, 画廊, 文创产品, 美术用品 |
| 性能评级 | 3/5 |
| 可访问性评级 | 3/5 |

**框架实现提示**：
- React: SVG滤镜 `feTurbulence` + `feDisplacementMap`
- Vue: CSS `filter: url(#watercolor)` SVG滤镜
- Tailwind: `bg-blue-200/40`, `blur-[2px]`, 自定义水彩纹理

### 57. Doodle

| 属性 | 值 |
|------|-----|
| 关键词 | 涂鸦, 随手画, 趣味, 休闲, 个性 |
| 最佳场景 | 笔记应用, 任务管理, 学生工具, 休闲游戏 |
| 性能评级 | 4/5 |
| 可访问性评级 | 3/5 |

**框架实现提示**：
- React: SVG涂鸦图标 + 手写字体
- Vue: CSS `border-radius`不规则 + 涂鸦装饰
- Tailwind: `rounded-xl`, `border-2 border-dashed`, 自定义涂鸦字体

### 58. Collage

| 属性 | 值 |
|------|-----|
| 关键词 | 拼贴, 混合, 剪贴, 多材质, 层叠 |
| 最佳场景 | 创意机构, 杂志, 时尚, 艺术项目 |
| 性能评级 | 3/5 |
| 可访问性评级 | 2/5 |

**框架实现提示**：
- React: 绝对定位层叠 + 纸张纹理
- Vue: CSS `transform: rotate()` + `z-index`层叠
- Tailwind: `absolute`, `rotate-3`, `shadow-lg`, `z-10`

***

## 其他类（9种）

### 59. Corporate

| 属性 | 值 |
|------|-----|
| 关键词 | 企业, 专业, 保守, 可信, 正式 |
| 最佳场景 | 企业官网, 金融机构, 咨询公司, 法律服务 |
| 性能评级 | 5/5 |
| 可访问性评级 | 5/5 |

**框架实现提示**：
- React: 标准化组件 + 严格设计令牌
- Vue: Element Plus/Ant Design Vue企业组件
- Tailwind: `bg-white`, `text-gray-800`, `border-b-2 border-blue-600`

### 60. Editorial

| 属性 | 值 |
|------|-----|
| 关键词 | 编辑, 排版, 阅读, 内容, 专栏 |
| 最佳场景 | 新闻网站, 博客平台, 在线杂志, 出版 |
| 性能评级 | 5/5 |
| 可访问性评级 | 5/5 |

**框架实现提示**：
- React: 严格排版系统 + 阅读优化
- Vue: 内容组件 + 阅读进度条
- Tailwind: `prose`, `max-w-3xl`, `leading-relaxed`, `font-serif`

### 61. Magazine

| 属性 | 值 |
|------|-----|
| 关键词 | 杂志, 大图, 标题, 时尚, 视觉冲击 |
| 最佳场景 | 时尚杂志, 生活方式, 旅行杂志, 摄影集 |
| 性能评级 | 3/5 |
| 可访问性评级 | 3/5 |

**框架实现提示**：
- React: 大图Hero + 杂志网格布局
- Vue: CSS Columns多列布局
- Tailwind: `columns-2`, `gap-6`, `text-5xl font-bold`

### 62. Newspaper

| 属性 | 值 |
|------|-----|
| 关键词 | 报纸, 多栏, 标题, 新闻, 传统 |
| 最佳场景 | 新闻门户, 媒体网站, 日报, 通讯 |
| 性能评级 | 5/5 |
| 可访问性评级 | 4/5 |

**框架实现提示**：
- React: CSS Columns + Serif字体
- Vue: Grid布局 + 报纸风格排版
- Tailwind: `columns-3`, `divide-y`, `font-serif`, `text-justify`

### 63. Dashboard-first

| 属性 | 值 |
|------|-----|
| 关键词 | 仪表盘, 数据, 图表, 监控, KPI |
| 最佳场景 | 管理后台, 数据分析, 运维监控, BI工具 |
| 性能评级 | 4/5 |
| 可访问性评级 | 4/5 |

**框架实现提示**：
- React: Recharts/Nivo图表 + Grid布局
- Vue: ECharts集成 + 响应式网格
- Tailwind: `grid grid-cols-4 gap-4`, `bg-gray-50`, `rounded-lg shadow`

### 64. Mobile-first

| 属性 | 值 |
|------|-----|
| 关键词 | 移动优先, 触控, 滑动, 底部导航, 大按钮 |
| 最佳场景 | 移动应用, O2O平台, 社交应用, 即时通讯 |
| 性能评级 | 5/5 |
| 可访问性评级 | 4/5 |

**框架实现提示**：
- React: React Native / Capacitor + 触控优化
- Vue: 移动端组件库(Vant/NutUI)
- Tailwind: `sm:`, `md:`断点优先，`min-h-[44px]`触控目标

### 65. Print-inspired

| 属性 | 值 |
|------|-----|
| 关键词 | 印刷, 纸张, 排版, 留白, 经典 |
| 最佳场景 | 电子书, 在线文档, 出版平台, 简历生成 |
| 性能评级 | 5/5 |
| 可访问性评级 | 5/5 |

**框架实现提示**：
- React: 严格排版 + 页面分页
- Vue: CSS `@media print` + 分页控制
- Tailwind: `max-w-2xl`, `mx-auto`, `prose`, `font-serif`

### 66. Data-driven

| 属性 | 值 |
|------|-----|
| 关键词 | 数据驱动, 可视化, 信息图, 统计, 事实 |
| 最佳场景 | 数据新闻, 研究报告, 金融分析, 科研展示 |
| 性能评级 | 4/5 |
| 可访问性评级 | 4/5 |

**框架实现提示**：
- React: D3.js集成 + 响应式图表
- Vue: ECharts/Vega-Lite数据可视化
- Tailwind: `font-mono`, `text-sm`, `border-l-4 border-blue-500`

### 67. Accessible-first

| 属性 | 值 |
|------|-----|
| 关键词 | 无障碍优先, WCAG, 高对比, 键盘导航, 辅助技术 |
| 最佳场景 | 政务应用, 医疗平台, 教育平台, 通用产品 |
| 性能评级 | 5/5 |
| 可访问性评级 | 5/5 |

**框架实现提示**：
- React: Radix UI / Reach UI无障碍组件
- Vue: 自定义无障碍指令 + ARIA属性
- Tailwind: `focus-visible:ring-2`, `sr-only`, 高对比色彩变量
