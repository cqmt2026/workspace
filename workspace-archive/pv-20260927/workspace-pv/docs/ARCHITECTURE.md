# 多行业获客系统架构设计文档

> **版本**: v0.1  
> **日期**: 2026-08-17  
> **定位**: 光伏行业为测试案例，未来支持多行业插拔扩展的通用获客引擎

---

## 一、系统设计原则

### 1.1 核心原则
1. **通用引擎 + 行业插件** — 系统骨架对行业无感知，行业差异全收敛在配置包
2. **零成本验证优先** — 前期用SQLite单机跑通闭环，验证有效后再迁移到云
3. **模块化边界清晰** — 每个模块单一职责，层间松耦合，接口统一
4. **数据闭环驱动** — 效果数据回流反哺内容策略和渠道投放

### 1.2 不做什么（前期）
- 不做小程序/网站前端（验证阶段不需要）
- 不做付费服务/服务器（SQLite单机够用）
- 不做多行业同时运行（先跑通光伏，模板沉淀后再扩展）

---

## 二、整体架构（六层 + 插件层）

```
┌──────────────────────────────────────────────────────────────┐
│  L6 战略层：目标客群 / 区域 / 产品定位（人工输入）              │
├──────────────────────────────────────────────────────────────┤
│  L5 反馈层：归因分析 / 策略调优 / 数据看板                     │
├──────────────────────────────────────────────────────────────┤
│  L4 线索层：线索收集 / 打分分级 / CRM / 自动跟单               │
├──────────────────────────────────────────────────────────────┤
│  L3 内容层：素材整合 / 模板渲染 / 渠道适配 / 批量生产           │
├──────────────────────────────────────────────────────────────┤
│  L2 数据层：热点采集 / 政策监控 / 竞品情报 / 区域数据           │
├──────────────────────────────────────────────────────────────┤
│  L1 渠道层：抖音 / 头条 / 公众号 / 百度竞价 / 私域             │
├──────────────────────────────────────────────────────────────┤
│  行业插件层：industry_config/<行业>/  ← 可插拔配置包          │
└──────────────────────────────────────────────────────────────┘

数据流：L2→L3→L1→L4→L5→L3/L1（闭环）
```

---

## 三、分层详设（职责、入参、出参、接口）

### L1 渠道层（Channel Layer）
| 模块 | 渠道 | 职责 | 统一接口 |
|------|------|------|---------|
| `channel_base.py` | — | 定义发布/查询/删除接口 | `publish(content_pack) -> {status, item_id}` |
| `channel_douyin.py` | 抖音 | 短视频发布、账号管理、数据查询 | 实现 base 接口 |
| `channel_toutiao.py` | 头条 | 图文发布、信息流投放 | 实现 base 接口 |
| `channel_wechat.py` | 公众号 | 长文发布、引流 | 实现 base 接口 |
| `channel_baidu.py` | 百度竞价 | 关键词投放、表单收集 | 实现 base 接口 |

**关键**：所有渠道实现统一接口 `ChannelAdapter`，换渠道只需新增模块，不改引擎。

### L2 数据层（Data Layer）
| 模块 | 职责 | 数据源 | 出参 | 行业差异 |
|------|------|--------|------|---------|
| `hot_topic_collector.py` | 抓热点 | 百度/索比/能源局/mx-search | PV相关话题 | keywords.json |
| `policy_monitor.py` | 盯政策 | 能源局/行业协会 | 政策条目 | sources.json |
| `competitor.py` | 竞品情报 | 抖音/头条竞品号 | 竞品内容 | 预留接口 |
| `region_data.py` | 区域数据 | 日照/电价/补贴 | 城市画像 | sources.json |

**行业差异点**：关键词词库、采集URL、解析规则 → 全部收进 `industry_config/<行业>/sources.json`

### L3 内容层（Content Layer）
| 模块 | 职责 | 入参 | 出参 | 行业差异 |
|------|------|------|------|---------|
| `material_lib.py` | 素材整合 | L2数据 | 结构化素材 | 无（通用） |
| `template_engine.py` | 模板渲染 | 素材+方向 | 内容脚本 | templates/*.md |
| `channel_adapter.py` | 渠道适配 | 脚本 | 渠道发布包 | 无（通用） |
| `batch_producer.py` | 批量生产 | 渠道包 | 发布队列 | 无（通用） |
| `feedback_hook.py` | 效果吸收 | L5数据 | 模板权重调整 | 无（通用） |

**关键**：模板（template_engine）和AI提示词（prompts/）按行业存储，引擎逻辑完全通用。

### L4 线索层（Lead Layer）
| 模块 | 职责 | 入参 | 出参 | 行业差异 |
|------|------|------|------|---------|
| `lead_collector.py` | 线索收集 | 私信/评论/表单/电话 | 线索记录 | scoring_weights |
| `lead_scoring.py` | 打分分级 | 线索+行为数据 | A/B/C级 | 阈值可配 |
| `crm.py` | 客户管理 | 线索池 | 跟进记录 | 标签体系可配 |
| `auto_followup.py` | 自动跟单 | 线索+策略 | 触达消息 | 话术库行业化 |

**关键**：CRM结构和线索字段定义是通用的（name/phone/source/content_stage），打分权重和跟单话术按行业配置。

### L5 反馈层（Feedback Layer）
| 模块 | 职责 | 入参 | 出参 | 行业差异 |
|------|------|------|------|---------|
| `metrics.py` | 效果统计 | 各层埋点数据 | 关键指标 | 无（通用） |
| `attribution.py` | 归因分析 | 内容ID+线索ID | 渠道/模板ROI | 归因模型可配 |
| `auto_tune.py` | 策略调优 | 归因结果 | 调优指令 | 调优规则可配 |
| `dashboard.py` | 数据看板 | 全量数据 | 可视化报表 | 无（通用） |

**关键**：归因颗粒度 = **内容级**（每条内容打唯一追踪ID），看板字段通用。

### 行业插件层（Industry Plugin Layer）
```
industry_config/
├── template/              # 行业插件模板（新行业照这个建）
│   ├── keywords.json      # 必填：行业关键词
│   ├── sources.json       # 必填：数据源配置
│   ├── templates/         # 必填：内容模板
│   ├── prompts/           # 必填：AI提示词
│   ├── value_prop.md      # 必填：价值主张
│   └── config.yaml        # 选填：其他配置
│
├── solar/                 # 光伏行业（当前）
│   ├── keywords.json      # PV_KEYWORDS 33个词 → 提取到这里
│   ├── sources.json       # 数据源URL/解析规则
│   ├── templates/
│   │   ├── policy.md      # 政策解读模板
│   │   ├── benefit.md     # 收益计算模板
│   │   ├── avoid.md       # 避坑指南模板
│   │   ├── news.md        # 行业新闻模板
│   │   └── tech.md        # 技术科普模板
│   ├── prompts/
│   │   ├── hook.txt       # 钩子生成提示词
│   │   ├── body.txt       # 正文生成提示词
│   │   └── cta.txt        # CTA生成提示词
│   └── value_prop.md      # 光伏价值主张文案
│
└── edu/                   # 教育行业（未来，照模板新建）
    ...
```

**换行业操作**：复制 `template/` → 重命名为新行业目录，修改配置即可，**引擎一行代码不改**。

---

## 四、数据库设计

### 4.1 本地工作库（SQLite，当前使用 pv.db）
存储L2/L3采集素材，单机批处理专用：

| 表 | 用途 | 关键字段 |
|----|------|---------|
| `hot_topics` | 热点话题 | title, source, pv_score, pv_related, collected_at |
| `policies` | 政策 | title, level, policy_type, province, collected_at |
| `system_logs` | 系统日志 | module, action, status, message |

### 4.2 业务数据表（新增，与本地库分离）
线索和客户数据独立表，后续可迁移到云数据库：

| 表 | 用途 | 关键字段 |
|----|------|---------|
| `leads` | 线索池 | id, source_channel, source_content_id, name, phone, level(A/B/C), tags, created_at |
| `customers` | 成交客户 | id, lead_id, status, close_time, amount, source_attribution |
| `content_items` | 内容追踪 | id, content_id, channel, status, plays, clicks, leads_generated |
| `campaigns` | 投放活动 | id, name, channel, budget, start_date, end_date, status |
| `attribution` | 归因记录 | content_id, channel, lead_id, converted, close_amount |

### 4.3 数据流向
```
L2采集 → pv.db (本地工作库)
L3内容生成 → content_items (业务库)
L1发布 → content_items status更新
L4线索收集 → leads表
L5归因 → attribution表 → 反哺L3
```

---

## 五、统一接口定义

### 5.1 渠道适配器接口（ChannelAdapter）
```python
class ChannelAdapter(ABC):
    """渠道统一接口，所有渠道必须实现"""
    
    @abstractmethod
    def publish(self, content_pack: ContentPack) -> PublishResult:
        """发布内容"""
        ...
    
    @abstractmethod
    def get_performance(self, item_id: str) -> PerformanceData:
        """查询效果数据"""
        ...
    
    @abstractmethod
    def collect_leads(self) -> List[Lead]:
        """收集线索（评论/私信/表单）"""
        ...
```

### 5.2 内容包结构（ContentPack）
```python
@dataclass
class ContentPack:
    """内容发布包，通用结构"""
    title: str
    hook: str
    body: str
    cta: str
    channel: str              # douyin/toutiao/wechat/baidu
    industry: str             # solar/edu/...
    template_used: str        # policy/benefit/avoid/...
    tracking_id: str          # 唯一追踪ID（内容级归因）
    media_files: List[str]    # 附件（图片/视频路径）
```

### 5.3 行业插件注册接口（IndustryPlugin）
```python
class IndustryPlugin(ABC):
    """行业插件基类，新行业继承"""
    
    plugin_name: str          # 插件名称（如"solar"）
    keywords: List[str]       # 行业关键词
    sources: Dict             # 数据源配置
    templates: Dict[str, str] # 模板字典
    
    def get_prompts(self) -> Dict[str, str]:
        """返回AI提示词"""
        ...
    
    def get_value_prop(self) -> str:
        """返回价值主张文案"""
        ...
    
    def get_scoring_weights(self) -> Dict:
        """返回线索打分权重"""
        ...
```

---

## 六、建设路径（S1-S5）

### S1：跑通最小闭环（当前）
**范围**：L2数据层 + L3内容层 + SQLite本地库
**验证标准**：每天自动生成≥6条渠道适配内容，保存在发布队列

### S2：首个渠道打穿
**范围**：+L1抖音渠道 + L4线索收集（手动录入）
**验证标准**：发布到抖音后，有人私信/评论，线索能落到leads表

### S3：归因闭环
**范围**：+L5归因分析（内容级追踪ID）
**验证标准**：能回答"哪条内容带来了多少线索"

### S4：行业插件化
**范围**：抽出solar插件到 `industry_config/solar/`，验证引擎通用性
**验证标准**：新建 `industry_config/edu/`，引擎不改一行代码就能生成教育行业内容

### S5：多渠扩张
**范围**：+L1头条/公众号/Baidu
**验证标准**：多渠道统一看板，归因到渠道+内容维度

---

## 七、现有代码与架构对照

| 现有文件 | 对应架构层 | 是否需要重构 |
|---------|-----------|------------|
| `hot_topic_collector.py` | L2 数据层 | ✅ 抽keywords/sources到插件 |
| `policy_monitor.py` | L2 数据层 | ✅ 抽policy sources到插件 |
| `content_generator.py` | L3 内容层 | ✅ 抽templates/prompts到插件 |
| `competitor_monitor.py` | L2 数据层 | 暂不动，后续接入 |
| `content_analyzer.py` | L5 反馈层 | ✅ 改名为metrics.py |
| `database.py` | L2+L4 | 新增业务表（leads/customers等） |
| `pipeline.py` | 编排器 | ✅ 重构为通用Engine |
| `config.py` | — | ✅ 迁移到 `industry_config/solar/sources.json` |

**重构原则**：不推倒重来，按"增量抽离"方式，逐模块迁出行业专属部分到插件目录。

---

## 八、关键决策记录

| 决策 | 选择 | 理由 |
|------|------|------|
| 数据库选型（前期） | SQLite单机（pv.db） | 零成本、验证够用、未来可迁移 |
| 归因颗粒度 | 内容级（唯一追踪ID） | 小程序/网站需要细粒度，有看板价值 |
| 渠道接口 | 统一ChannelAdapter抽象 | 换渠道不改引擎 |
| 行业扩展 | 插件目录 + 注册表 | 抽离行业专属，引擎完全通用 |
| 内容模板 | 框架预置通用骨架 | 行业定制文案/提示词在插件里 |

---

## 九、后续行动

1. **立即行动**：按"七、现有代码与架构对照"逐模块重构，迁出solar插件
2. **本周完成**：S1闭环完整验证（采集→生成→发布队列→线索手动录入）
3. **下周开始**：S2抖音渠道实际发布+线索自动收集（对接抖音开放API或BrowserAct）

---

_由可悦🌸 定稿，2026-08-17_
_本文档为光伏获客系统架构基准，后续变更需走变更流程（记录在本档"决策记录"表）_
