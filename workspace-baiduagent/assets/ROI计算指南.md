# 百都科技·客户提案ROI计算指南

> 用途：销售提案时向客户展示投放效果预期
> 核心逻辑：简化版归因 + ROI计算 + 预算建议
> 更新：2026-09-06

---

## 一、ROI计算模块说明

### 1.1 核心公式

```
ROI = (营收 - 预算) / 预算 × 100%

其中：
营收 = 点击数 × 点击率 × 转化率 × 客单价
点击数 = 预算 / CPC（平均点击成本）
```

### 1.2 使用方式

**方式一：命令行工具**
```bash
python scripts/modules/roi_calculator.py
```

**方式二：Python调用**
```python
from scripts.modules.roi_calculator import calculate_roi, generate_proposal_template

# 计算ROI
roi_result = calculate_roi(
    budget=5000,           # 月度预算
    cpc=8,                 # 平均点击成本
    click_rate=3.5,       # 点击率（%）
    conversion_rate=2.5,  # 转化率（%）
    avg_order_value=50000 # 平均订单金额
)

# 生成提案
proposal = generate_proposal_template(
    industry='机械制造',
    company_name='重庆XX机械公司',
    budget=5000
)
```

### 1.3 输出字段

| 字段 | 说明 | 示例 |
|------|------|------|
| budget | 月度预算 | 5000元 |
| clicks | 预计点击数 | 625次 |
| leads | 预计线索数 | 21.9个 |
| conversions | 预计成交数 | 0.55单 |
| revenue | 预计营收 | 27,500元 |
| roi | 投资回报率 | 450% |

---

## 二、归因分析模型

### 2.1 简化版归因逻辑

参考Google lightweight_mmm理念，采用简化版归因：

**首次接触归因（First Touch）**
- 将线索归功于第一次接触渠道
- 适合：品牌认知阶段评估

**最终转化归因（Last Touch）**
- 将成交归功于最后一次互动渠道
- 适合：销售转化效率评估

### 2.2 归因分析脚本

```python
from scripts.modules.roi_calculator import attribution_analysis

# 分析各渠道贡献
attribution = attribution_analysis(customers, call_logs)

for channel, data in attribution.items():
    print(f"{channel}: 线索{data['leads']}个，转化{data['conversions']}个，转化率{data['conversion_rate']}%")
```

### 2.3 渠道效果对比表

| 渠道 | 线索数 | 转化数 | 转化率 | 归因类型 |
|------|--------|--------|--------|----------|
| 百度搜索 | 45 | 8 | 17.8% | 首次接触 |
| 老客户转介绍 | 30 | 12 | 40.0% | 最终转化 |
| 展会 | 20 | 5 | 25.0% | 首次接触 |

---

## 三、预算优化建议

### 3.1 优化逻辑

参考lightweight_mmm的预算优化算法：

```python
from scripts.modules.roi_calculator import calculate_budget_optimization

# 输入：当前预算 + ROI历史数据
optimization = calculate_budget_optimization(
    current_budget=5000,
    roi_history=[
        {'roi': 320, 'month': '2026-07'},
        {'roi': 280, 'month': '2026-08'},
        {'roi': 350, 'month': '2026-09'}
    ]
)
```

### 3.2 优化建议规则

| 平均ROI | 建议预算调整 | 策略建议 |
|---------|-------------|----------|
| > 300% | +50% | ROI优秀，加大投入 |
| 200-300% | +20% | 表现良好，适度增加 |
| 100-200% | 0% | 收支平衡，保持现状 |
| 0-100% | -20% | 略有亏损，优化策略 |
| < 0% | -30% | 亏损严重，重新评估 |

---

## 四、行业基准数据

### 4.1 机械制造行业

| 指标 | 数值 | 说明 |
|------|------|------|
| CPC | 8元 | 平均点击成本 |
| 点击率 | 3.5% | 行业平均水平 |
| 转化率 | 2.5% | 从线索到成交 |
| 客单价 | 50,000元 | 平均订单金额 |
| 回本周期 | 2-3个月 | 从投放到成交 |

### 4.2 医疗器械行业

| 指标 | 数值 | 说明 |
|------|------|------|
| CPC | 15元 | 竞争较激烈 |
| 点击率 | 2.8% | 精准流量 |
| 转化率 | 3.2% | 决策周期长 |
| 客单价 | 100,000元 | 高价值客户 |
| 回本周期 | 3-6个月 | 需要培育 |

### 4.3 如何获取行业基准

1. **历史数据** — 从CRM中统计实际投放数据
2. **行业报告** — 参考百度营销行业报告
3. **竞品分析** — 观察竞品投放情况
4. **A/B测试** — 小预算测试后调整

---

## 五、客户提案模板

### 5.1 提案结构

```
【客户名称】百度推广投放方案

一、投放目标
- 品牌曝光：提升百度搜索可见度
- 线索获取：每月获取XX个有效询盘
- 成交转化：预计带来XX万元营收

二、投放策略
- 关键词策略：核心词+长尾词组合
- 地域定位：重庆主城区+周边区县
- 时段设置：工作时间优先（9:00-18:00）

三、预算建议
- 月度预算：XXXX元
- 测试期：1个月（3000-5000元）
- 正式期：根据效果调整

四、效果预期（ROI测算）
- 预计点击：XXX次
- 预计线索：XX个
- 预计成交：X单
- 预计营收：XX万元
- 预期ROI：XXX%

五、投放周期
- 建议周期：至少3个月
- 优化周期：第1个月调试，第2-3个月稳定
- 评估节点：每月复盘一次

六、风险提示
- 行业竞争激烈，CPC可能上涨
- 转化率受落地页质量影响
- 成交周期较长，需持续跟进
```

### 5.2 自动生成提案

```python
from scripts.modules.roi_calculator import generate_proposal_template

# 生成提案
proposal = generate_proposal_template(
    industry='机械制造',
    company_name='重庆XX机械制造有限公司',
    budget=5000
)

# 输出文本版提案
print(proposal_to_text(proposal))
```

---

## 六、增值 servi ces

### 6.1 基础服务（免费）
- ROI测算
- 行业基准数据
- 提案模板

### 6.2 进阶服务（收费）
- 完整MMM分析（预算>1万/月）
- 多渠道归因模型
- 实时数据看板
- 月度优化报告

### 6.3 如何推广
在客户提案时，主动提出：
> "我们可以帮您做详细的ROI测算，让您清楚知道投多少能赚多少。"

---

## 七、注意事项

1. **数据真实性** — 基准数据仅供参考，实际效果因企业而异
2. **保守估计** — 提案时建议用保守值，避免过度承诺
3. **持续优化** — ROI会随投放时间变化，需持续监控
4. **客户教育** — 帮助客户理解搜索广告的价值，不只看短期ROI

---

_由小度维护 | 2026-09-06更新_
