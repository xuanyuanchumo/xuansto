# 字体配对数据库

> 版本: 3.0.0 | 更新日期: 2026-05-05 | 编码: UTF-8 | 行尾: LF

## 概述

本文件包含57组字体配对，按情绪分类组织。每组包含标题字体、正文字体、情绪标签、最佳场景和Google Fonts链接。Agent应基于项目情绪和场景按需搜索，不预加载全部数据。

## 搜索策略

- 按情绪关键词搜索匹配字体配对
- BM25排序权重：情绪匹配(40%) + 场景匹配(35%) + 行业适配(25%)
- 每次搜索返回Top 3组配对供推理引擎选择
- 选择后需验证字体加载性能（标题字体≤2个字重，正文字体≤3个字重）

## 配对格式说明

每组配对格式：`#序号 | 标题字体 + 正文字体 | 情绪标签 | 最佳场景 | Google Fonts链接`

***

## 专业/商务（10组）

### 1
- **标题字体**: Inter (600/700)
- **正文字体**: Inter (400/500)
- **情绪标签**: 专业, 现代, 通用
- **最佳场景**: SaaS仪表盘, 企业后台, 管理系统
- **Google Fonts**: https://fonts.google.com/specimen/Inter

### 2
- **标题字体**: Playfair Display (700)
- **正文字体**: Source Sans 3 (400/500/600)
- **情绪标签**: 经典, 优雅, 权威
- **最佳场景**: 律师事务所, 咨询公司, 金融报告
- **Google Fonts**: https://fonts.google.com/specimen/Playfair+Display

### 3
- **标题字体**: DM Sans (600/700)
- **正文字体**: DM Sans (400/500)
- **情绪标签**: 干净, 几何, 专业
- **最佳场景**: 科技公司, B2B平台, 企业官网
- **Google Fonts**: https://fonts.google.com/specimen/DM+Sans

### 4
- **标题字体**: Merriweather (700)
- **正文字体**: Open Sans (400/500/600)
- **情绪标签**: 传统, 可信, 严肃
- **最佳场景**: 政府网站, 银行, 保险
- **Google Fonts**: https://fonts.google.com/specimen/Merriweather

### 5
- **标题字体**: Lora (600/700)
- **正文字体**: Source Sans 3 (400/500)
- **情绪标签**: 编辑, 精致, 商务
- **最佳场景**: 新闻媒体, 出版平台, 杂志
- **Google Fonts**: https://fonts.google.com/specimen/Lora

### 6
- **标题字体**: Outfit (600/700)
- **正文字体**: Outfit (400/500)
- **情绪标签**: 现代, 简洁, 高效
- **最佳场景**: 项目管理, 协作工具, 效率应用
- **Google Fonts**: https://fonts.google.com/specimen/Outfit

### 7
- **标题字体**: Libre Baskerville (700)
- **正文字体**: Libre Franklin (400/500/600)
- **情绪标签**: 学术, 严谨, 传统
- **最佳场景**: 学术期刊, 研究机构, 教育平台
- **Google Fonts**: https://fonts.google.com/specimen/Libre+Baskerville

### 8
- **标题字体**: Plus Jakarta Sans (600/700)
- **正文字体**: Plus Jakarta Sans (400/500)
- **情绪标签**: 当代, 圆润, 友好商务
- **最佳场景**: 创业公司, 现代企业, SaaS产品
- **Google Fonts**: https://fonts.google.com/specimen/Plus+Jakarta+Sans

### 9
- **标题字体**: Cormorant Garamond (600/700)
- **正文字体**: Proza Libre (400/500)
- **情绪标签**: 高端, 经典, 奢华商务
- **最佳场景**: 奢侈品牌, 高端地产, 私人银行
- **Google Fonts**: https://fonts.google.com/specimen/Cormorant+Garamond

### 10
- **标题字体**: IBM Plex Sans (600/700)
- **正文字体**: IBM Plex Sans (400/500)
- **情绪标签**: 工程, 精确, 企业
- **最佳场景**: 工程工具, 数据平台, IBM生态
- **Google Fonts**: https://fonts.google.com/specimen/IBM+Plex+Sans

***

## 现代/科技（10组）

### 11
- **标题字体**: Space Grotesk (600/700)
- **正文字体**: Inter (400/500)
- **情绪标签**: 科技, 前卫, 几何
- **最佳场景**: 科技创业, AI产品, 开发者工具
- **Google Fonts**: https://fonts.google.com/specimen/Space+Grotesk

### 12
- **标题字体**: Sora (600/700)
- **正文字体**: Sora (400/500)
- **情绪标签**: 未来, 流畅, 数字
- **最佳场景**: Web3, 区块链, 数字产品
- **Google Fonts**: https://fonts.google.com/specimen/Sora

### 13
- **标题字体**: JetBrains Mono (600/700)
- **正文字体**: Inter (400/500)
- **情绪标签**: 代码, 开发, 技术
- **最佳场景**: 代码编辑器, DevOps面板, API文档
- **Google Fonts**: https://fonts.google.com/specimen/JetBrains+Mono

### 14
- **标题字体**: Clash Display (600/700)
- **正文字体**: Satoshi (400/500)
- **情绪标签**: 大胆, 现代, 冲击
- **最佳场景**: 科技发布会, 产品发布, 品牌站
- **Google Fonts**: 非Google Fonts, 见 https://www.fontshare.com/fonts/clash-display

### 15
- **标题字体**: Unbounded (600/700)
- **正文字体**: DM Sans (400/500)
- **情绪标签**: 无界, 创新, 突破
- **最佳场景**: 创新实验室, 量子计算, 前沿科技
- **Google Fonts**: https://fonts.google.com/specimen/Unbounded

### 16
- **标题字体**: Chakra Petch (600/700)
- **正文字体**: Nunito Sans (400/500/600)
- **情绪标签**: 赛博, 电子, 未来
- **最佳场景**: 游戏平台, 电竞, 赛博朋克主题
- **Google Fonts**: https://fonts.google.com/specimen/Chakra+Petch

### 17
- **标题字体**: Syne (600/700)
- **正文字体**: Work Sans (400/500)
- **情绪标签**: 实验, 前卫, 艺术
- **最佳场景**: 创意科技, 数字艺术, 实验项目
- **Google Fonts**: https://fonts.google.com/specimen/Syne

### 18
- **标题字体**: Space Mono (700)
- **正文字体**: Space Grotesk (400/500)
- **情绪标签**: 太空, 等宽, 极客
- **最佳场景**: 航天科技, 卫星数据, 极客社区
- **Google Fonts**: https://fonts.google.com/specimen/Space+Mono

### 19
- **标题字体**: Bricolage Grotesque (600/700)
- **正文字体**: Inter (400/500)
- **情绪标签**: 拼贴, 混搭, 新潮
- **最佳场景**: 创意平台, 设计工具, 新媒体
- **Google Fonts**: https://fonts.google.com/specimen/Bricolage+Grotesque

### 20
- **标题字体**: Onest (600/700)
- **正文字体**: Onest (400/500)
- **情绪标签**: 诚实, 直接, 透明
- **最佳场景**: 开源项目, 透明平台, 数据工具
- **Google Fonts**: https://fonts.google.com/specimen/Onest

***

## 友好/亲和（8组）

### 21
- **标题字体**: Nunito (700)
- **正文字体**: Nunito (400/500/600)
- **情绪标签**: 圆润, 温暖, 亲切
- **最佳场景**: 教育应用, 儿童产品, 家庭服务
- **Google Fonts**: https://fonts.google.com/specimen/Nunito

### 22
- **标题字体**: Quicksand (700)
- **正文字体**: Nunito Sans (400/500/600)
- **情绪标签**: 轻盈, 柔和, 友好
- **最佳场景**: 健康应用, 生活方式, 宠物服务
- **Google Fonts**: https://fonts.google.com/specimen/Quicksand

### 23
- **标题字体**: Poppins (600/700)
- **正文字体**: Poppins (400/500)
- **情绪标签**: 活力, 通用, 亲和
- **最佳场景**: 社交应用, 社区平台, 通用产品
- **Google Fonts**: https://fonts.google.com/specimen/Poppins

### 24
- **标题字体**: M PLUS Rounded 1c (700)
- **正文字体**: Noto Sans JP (400/500)
- **情绪标签**: 日系, 可爱, 圆润
- **最佳场景**: 日系产品, 动漫社区, 可爱风格
- **Google Fonts**: https://fonts.google.com/specimen/M+PLUS+Rounded+1c

### 25
- **标题字体**: Comfortaa (700)
- **正文字体**: Nunito (400/500/600)
- **情绪标签**: 舒适, 圆形, 休闲
- **最佳场景**: 休闲游戏, 冥想应用, 睡眠辅助
- **Google Fonts**: https://fonts.google.com/specimen/Comfortaa

### 26
- **标题字体**: Fredoka (600/700)
- **正文字体**: Nunito (400/500/600)
- **情绪标签**: 趣味, 童趣, 活泼
- **最佳场景**: 儿童教育, 游戏应用, 趣味工具
- **Google Fonts**: https://fonts.google.com/specimen/Fredoka

### 27
- **标题字体**: Baloo 2 (700)
- **正文字体**: Nunito Sans (400/500/600)
- **情绪标签**: 快乐, 丰满, 热情
- **最佳场景**: 食品电商, 派对策划, 娱乐应用
- **Google Fonts**: https://fonts.google.com/specimen/Baloo+2

### 28
- **标题字体**: Lexend (600/700)
- **正文字体**: Lexend (400/500)
- **情绪标签**: 可读, 包容, 易读
- **最佳场景**: 无障碍优先, 阅读应用, 教育平台
- **Google Fonts**: https://fonts.google.com/specimen/Lexend

***

## 优雅/高端（8组）

### 29
- **标题字体**: Playfair Display (700/900)
- **正文字体**: Lato (400/500)
- **情绪标签**: 奢华, 经典, 优雅
- **最佳场景**: 奢侈品牌, 高端酒店, 珠宝
- **Google Fonts**: https://fonts.google.com/specimen/Playfair+Display

### 30
- **标题字体**: Cormorant (600/700)
- **正文字体**: Cormorant (400/500)
- **情绪标签**: 诗意, 纤细, 艺术
- **最佳场景**: 艺术画廊, 时尚杂志, 香水品牌
- **Google Fonts**: https://fonts.google.com/specimen/Cormorant

### 31
- **标题字体**: Bodoni Moda (700/900)
- **正文字体**: Jost (400/500)
- **情绪标签**: 时尚, 戏剧, 高对比
- **最佳场景**: 时尚品牌, 时装秀, 高端杂志
- **Google Fonts**: https://fonts.google.com/specimen/Bodoni+Moda

### 32
- **标题字体**: Fraunces (600/700)
- **正文字体**: DM Sans (400/500)
- **情绪标签**: 复古优雅, 温暖, 精致
- **最佳场景**: 精品酒店, 手工品牌, 咖啡馆
- **Google Fonts**: https://fonts.google.com/specimen/Fraunces

### 33
- **标题字体**: EB Garamond (600/700)
- **正文字体**: EB Garamond (400/500)
- **情绪标签**: 古典, 书卷, 典雅
- **最佳场景**: 古籍出版, 文学网站, 博物馆
- **Google Fonts**: https://fonts.google.com/specimen/EB+Garamond

### 34
- **标题字体**: Cinzel (700/900)
- **正文字体**: Raleway (400/500)
- **情绪标签**: 罗马式, 庄严, 宏大
- **最佳场景**: 建筑事务所, 历史遗产, 纪念碑
- **Google Fonts**: https://fonts.google.com/specimen/Cinzel

### 35
- **标题字体**: Yeseva One (400)
- **正文字体**: Josefin Sans (400/500)
- **情绪标签**: 装饰, 复古优雅, 戏剧
- **最佳场景**: 婚礼策划, 高端餐饮, 剧院
- **Google Fonts**: https://fonts.google.com/specimen/Yeseva+One

### 36
- **标题字体**: Vollkorn (700/900)
- **正文字体**: Vollkorn (400/500)
- **情绪标签**: 厚重, 文学, 深度
- **最佳场景**: 图书出版, 长文阅读, 文学平台
- **Google Fonts**: https://fonts.google.com/specimen/Vollkorn

***

## 创意/艺术（7组）

### 37
- **标题字体**: Archivo Black (400)
- **正文字体**: Archivo (400/500/600)
- **情绪标签**: 粗犷, 标题感, 冲击
- **最佳场景**: 海报设计, 活动页面, 品牌宣言
- **Google Fonts**: https://fonts.google.com/specimen/Archivo+Black

### 38
- **标题字体**: Righteous (400)
- **正文字体**: Quicksand (400/500/600)
- **情绪标签**: 复古, 趣味, 个性
- **最佳场景**: 复古游戏, 创意工作室, 主题餐厅
- **Google Fonts**: https://fonts.google.com/specimen/Righteous

### 39
- **标题字体**: Abril Fatface (400)
- **正文字体**: Lato (400/500)
- **情绪标签**: 戏剧, 大标题, 杂志
- **最佳场景**: 杂志封面, 时尚大片, 创意广告
- **Google Fonts**: https://fonts.google.com/specimen/Abril+Fatface

### 40
- **标题字体**: Bungee (400)
- **正文字体**: Barlow (400/500/600)
- **情绪标签**: 街头, 大胆, 城市感
- **最佳场景**: 街头品牌, 城市活动, 滑板文化
- **Google Fonts**: https://fonts.google.com/specimen/Bungee

### 41
- **标题字体**: Permanent Marker (400)
- **正文字体**: Nunito (400/500/600)
- **情绪标签**: 手写, 涂鸦, 随性
- **最佳场景**: 手绘风格, 创意笔记, 儿童产品
- **Google Fonts**: https://fonts.google.com/specimen/Permanent+Marker

### 42
- **标题字体**: Monoton (400)
- **正文字体**: Rajdhani (400/500/600)
- **情绪标签**: 霓虹, 复古未来, 80年代
- **最佳场景**: 复古游戏, 霓虹主题, 80年代风格
- **Google Fonts**: https://fonts.google.com/specimen/Monoton

### 43
- **标题字体**: Press Start 2P (400)
- **正文字体**: Press Start 2P (400)
- **情绪标签**: 像素, 8位, 游戏机
- **最佳场景**: 像素游戏, 复古游戏, 编程教育
- **Google Fonts**: https://fonts.google.com/specimen/Press+Start+2P

***

## 休闲/生活（7组）

### 44
- **标题字体**: Caveat (700)
- **正文字体**: Nunito (400/500/600)
- **情绪标签**: 手写, 温馨, 日常
- **最佳场景**: 笔记应用, 日记, 个人博客
- **Google Fonts**: https://fonts.google.com/specimen/Caveat

### 45
- **标题字体**: Pacifico (400)
- **正文字体**: Quicksand (400/500/600)
- **情绪标签**: 海滩, 放松, 度假
- **最佳场景**: 旅行博客, 海滩酒吧, 度假村
- **Google Fonts**: https://fonts.google.com/specimen/Pacifico

### 46
- **标题字体**: Dancing Script (700)
- **正文字体**: Lato (400/500)
- **情绪标签**: 优雅手写, 浪漫, 轻快
- **最佳场景**: 婚礼网站, 约会应用, 甜品店
- **Google Fonts**: https://fonts.google.com/specimen/Dancing+Script

### 47
- **标题字体**: Indie Flower (400)
- **正文字体**: Nunito (400/500/600)
- **情绪标签**: 独立, 清新, 自然
- **最佳场景**: 手工品牌, 有机食品, 独立书店
- **Google Fonts**: https://fonts.google.com/specimen/Indie+Flower

### 48
- **标题字体**: Sacramento (400)
- **正文字体**: Lato (400/500)
- **情绪标签**: 精致手写, 迷你, 优雅
- **最佳场景**: 请柬设计, 礼品包装, 精品店
- **Google Fonts**: https://fonts.google.com/specimen/Sacramento

### 49
- **标题字体**: Amatic SC (700)
- **正文字体**: Open Sans (400/500/600)
- **情绪标签**: 极简手写, 艺术感, 素描
- **最佳场景**: 艺术展览, 手工制品, 创意市集
- **Google Fonts**: https://fonts.google.com/specimen/Amatic+SC

### 50
- **标题字体**: Shadows Into Light (400)
- **正文字体**: Nunito Sans (400/500/600)
- **情绪标签**: 柔和手写, 温柔, 梦幻
- **最佳场景**: 睡前故事, 冥想应用, 心理咨询
- **Google Fonts**: https://fonts.google.com/specimen/Shadows+Into+Light

***

## 严肃/权威（7组）

### 51
- **标题字体**: Roboto Slab (700)
- **正文字体**: Roboto (400/500)
- **情绪标签**: 机器, 精确, Google
- **最佳场景**: Google生态, 技术文档, Android应用
- **Google Fonts**: https://fonts.google.com/specimen/Roboto+Slab

### 52
- **标题字体**: Source Serif 4 (700)
- **正文字体**: Source Sans 3 (400/500/600)
- **情绪标签**: Adobe, 排版, 专业
- **最佳场景**: Adobe生态, 出版系统, 专业排版
- **Google Fonts**: https://fonts.google.com/specimen/Source+Serif+4

### 53
- **标题字体**: Literata (700)
- **正文字体**: Literata (400/500)
- **情绪标签**: 阅读, 书籍, 沉浸
- **最佳场景**: 电子书阅读器, 长文阅读, 图书平台
- **Google Fonts**: https://fonts.google.com/specimen/Literata

### 54
- **标题字体**: PT Serif (700)
- **正文字体**: PT Sans (400/500)
- **情绪标签**: 公共, 俄罗斯, 传统
- **最佳场景**: 公共服务, 文化机构, 传统媒体
- **Google Fonts**: https://fonts.google.com/specimen/PT+Serif

### 55
- **标题字体**: Spectral (700)
- **正文字体**: Spectral (400/500)
- **情绪标签**: 文学, 编辑, 深度阅读
- **最佳场景**: 文学杂志, 深度报道, 长篇分析
- **Google Fonts**: https://fonts.google.com/specimen/Spectral

### 56
- **标题字体**: Newsreader (700)
- **正文字体**: Newsreader (400/500)
- **情绪标签**: 新闻, 报纸, 信息
- **最佳场景**: 新闻门户, 日报网站, 信息聚合
- **Google Fonts**: https://fonts.google.com/specimen/Newsreader

### 57
- **标题字体**: Libre Baskerville (700)
- **正文字体**: Source Sans 3 (400/500/600)
- **情绪标签**: 学术, 可信, 经典
- **最佳场景**: 学术论文, 研究报告, 知识库
- **Google Fonts**: https://fonts.google.com/specimen/Libre+Baskerville
