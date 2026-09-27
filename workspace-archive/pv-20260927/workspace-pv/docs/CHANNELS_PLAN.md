# 光伏获客系统 — 渠道扩展方案

## 当前状态
- ✅ L1渠道层：`channel/base.py` 统一接口定义
- ✅ 已实现：抖音、头条（双渠道导出+发布）
- ⏳ 待扩展：微信、百度竞价

## 扩展新渠道的步骤（通用流程）

### 1. 新建渠道模块
复制 `channel/toutiao.py` 模板，修改：
- `CHANNEL_NAME = "wechat"` 
- `_format_for_platform()` 适配目标平台格式
- `get_performance()` 对接对应API或返回空
- `collect_leads()` 对接评论/私信收集

### 2. 注册到流水线
修改 `content_generator.py` 的 `_export_channels()`：
```python
from core.channel.wechat import WechatChannel
channels = [DouyinChannel(), ToutiaoChannel(), WechatChannel()]
```

### 3. 渠道差异化配置
在 `industry_config/solar/` 下新增渠道特定配置：
- 标题字数限制
- 话题标签格式
- 最佳发布时间
- 内容风格偏好

## 候选渠道优先级

| 优先级 | 渠道 | 难度 | 价值 | 说明 |
|--------|------|------|------|------|
| P0 | 微信视频号 | 中 | 高 | 与抖音相似度高，复用度强 |
| P1 | 公众号 | 低 | 中 | 图文为主，适合深度政策解读 |
| P2 | 小红书 | 低 | 中 | 女性用户多，光伏C端潜力大 |
| P3 | 百度竞价 | 高 | 高 | 需要对接API+预算，适合B端 |
| P4 | 私域社群 | 中 | 中 | 需要企业微信+自动化工具 |

## 技术要点

### 统一接口（ChannelAdapter）
所有渠道必须实现：
```python
class ChannelAdapter(ABC):
    def publish(self, content_pack: ContentPack) -> PublishResult
    def get_performance(self, item_id: str) -> PerformanceData
    def collect_leads(self) -> List[Dict]
```

### 内容包结构（ContentPack）
```python
@dataclass
class ContentPack:
    title: str
    hook: str
    body: str
    cta: str
    channel: str      # 渠道标识
    industry: str     # 行业标识
    template_used: str
    tracking_id: str
    media_files: List[str]
```

### 差异化适配示例
| 渠道 | 标题限制 | 正文风格 | 标签格式 |
|------|----------|----------|----------|
| 抖音 | ≤30字+emoji | 短平快 | #话题 |
| 头条 | 20-30字 | 深度解读 | 空格分隔 |
| 微信视频号 | ≤30字 | 口语化 | @话题 |
| 公众号 | ≤64字 | 长文结构 | 无标签 |
| 小红书 | ≤20字 | 种草风 | #话题+表情 |

---
_由可悦🌸 制定，2026-08-19_