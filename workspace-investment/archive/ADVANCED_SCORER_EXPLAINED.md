# advanced_scorer.py 详解

**来源**: H 盘 stock-tools/advanced_scorer.py  
**文件大小**: 15,985 bytes  
**功能**: 股票评分系统 V2.0

---

## 📊 核心功能

### 1. 多维度评分体系

| 维度 | 权重 | 说明 |
|------|------|------|
| **trend** | 18% | 趋势分（MA20） |
| **momentum** | 15% | 动量分（5 日收益率） |
| **relative_strength** | 15% | 相对强弱（新增） |
| **volume** | 12% | 成交量分（量比） |
| **macd** | 12% | MACD 指标 |
| **rsi** | 8% | RSI 指标 |
| **boll** | 8% | 布林带位置 |
| **position** | 7% | 股价相对位置 |
| **sector** | 5% | 板块权重 |

---

### 2. 技术指标计算

#### MACD 分析

```python
def calculate_macd(prices, fast=12, slow=26, signal=9):
    # 计算 EMA
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    
    # 计算 DIFF/DEA/MACD 柱
    diff = ema_fast - ema_slow
    dea = diff.ewm(span=signal).mean()
    macd_bar = (diff - dea) * 2
    
    # 评分逻辑
    if diff > dea:  # 金叉
        score += 20
        if macd_bar > 0:  # 零轴上金叉
            score += 15
    else:  # 死叉
        score -= 20
        if macd_bar < 0:  # 零轴下死叉
            score -= 15
```

#### RSI 分析 (2026-03-25 优化)

```python
def calculate_rsi(prices, period=14):
    # 计算 RSI
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    # 优化：上涨趋势中 RSI>70 不应大幅扣分
    if rsi > 80:
        score = 45  # 极端超买，适度扣分
    elif rsi > 70:
        score = 55  # 超买但可能是强势延续（原 30，上调）
    elif rsi > 50:
        score = 60 + (rsi - 50) * 1.0  # 强势区间加大分数
    elif rsi > 30:
        score = 40 + (rsi - 30) * 0.8  # 中性
    else:
        score = 70  # 超卖，机会好
```

#### 布林带分析

```python
def calculate_boll(prices, period=20, std_dev=2):
    # 计算布林带
    ma = prices.rolling(period).mean()
    std = prices.rolling(period).std()
    upper = ma + std_dev * std
    lower = ma - std_dev * std
    
    # 计算位置 (0-1 之间)
    position = (price - lower) / (upper - lower)
    
    # 评分
    if position < 0.1:  # 接近下轨
        score = 80  # 超卖机会
    elif position < 0.3:
        score = 60
    elif position < 0.7:
        score = 50  # 中性
    elif position < 0.9:
        score = 40
    else:  # 接近上轨
        score = 20  # 超买风险
```

---

### 3. 消息面评分 (未实现)

| 类型 | 权重 | 说明 |
|------|------|------|
| **policy** | 40% | 政策利好 |
| **industry** | 30% | 行业利好 |
| **company** | 20% | 公司利好 |
| **market** | 10% | 市场情绪 |

---

## 🔧 依赖模块

```python
from realtime_data import TencentDataAPI  # 腾讯财经 API
import pandas as pd
import numpy as np
```

**问题**: `realtime_data` 模块不存在，导致无法直接导入使用。

---

## 📈 与简化版对比

| 维度 | advanced_scorer | simple_scorer |
|------|----------------|---------------|
| **代码量** | ~400 行 | ~150 行 |
| **依赖** | realtime_data (不存在) | 无依赖 |
| **技术指标** | MACD/RSI/布林带/量比 | 均线/动量/波动率 |
| **消息面** | 支持 (未实现) | 不支持 |
| **板块权重** | 支持 | 不支持 |
| **可用性** | ⚠️ 需修复依赖 | ✅ 立即可用 |
| **复杂度** | 高 | 低 |

---

## 💡 使用建议

### 【advanced_scorer】

**优势**:
- 技术指标更全面 (MACD/RSI/布林带)
- 权重配置更精细
- 支持板块权重
- 支持消息面分析 (需实现)

**劣势**:
- 依赖 `realtime_data` 模块 (不存在)
- 需要腾讯财经 API
- 代码复杂度高

**适用场景**:
- 需要精确技术分析
- 有实时数据源
- 专业投资分析

---

### 【simple_scorer】

**优势**:
- 无依赖，立即可用
- 代码简洁，易于理解
- 核心逻辑完整
- 已整合到策略工厂

**劣势**:
- 技术指标较少
- 无 MACD/RSI 等高级指标
- 无板块权重

**适用场景**:
- 快速原型开发
- 策略工厂整合
- 辅助决策参考

---

## 🎯 整合方案

### 方案 A: 使用简化版 (当前) ✅

```python
from src.ai.simple_scorer import SimpleStockScorer

scorer = SimpleStockScorer()
score = scorer.score_stock('000001.SZ', df)
```

**状态**: 已完成，测试通过

---

### 方案 B: 修复 advanced_scorer (后续)

```python
# 1. 创建 mock 模块
class MockTencentAPI:
    def get_kline_data(self, code, period, count):
        # 返回模拟数据
        return pd.DataFrame(...)

# 2. 修改导入
# from realtime_data import TencentDataAPI
# 改为
from mock_data import MockTencentAPI as TencentDataAPI

# 3. 使用
from advanced_scorer import StockScorer
scorer = StockScorer()
score = scorer.score_stock('000001.SZ', df)
```

**状态**: 待实现

---

### 方案 C: 混合使用 (推荐)

```python
# 日常使用简化版
from src.ai.simple_scorer import SimpleStockScorer
scorer = SimpleStockScorer()
score = scorer.score_stock('000001.SZ', df)

# 需要详细分析时使用 advanced
if score['total'] >= 70:  # 初筛通过
    from advanced_scorer import DetailedAnalyzer
    analyzer = DetailedAnalyzer()
    detailed_score = analyzer.analyze('000001.SZ', df)
```

**状态**: 待实现

---

## 📋 总结

**advanced_scorer 是什么？**

- 一个**专业的股票评分系统**
- 包含**9 个技术指标**，权重精细配置
- 支持**消息面分析**和**板块权重**
- 因依赖缺失，**创建了简化版**替代

**当前状态**:
- advanced_scorer: ⚠️ 依赖问题，需修复
- simple_scorer: ✅ 已完成，测试通过

**建议**:
- 日常使用 simple_scorer
- 需要详细分析时修复 advanced_scorer
- 两者可以互补使用

---

**advanced_scorer 是 H 盘的专业评分系统，我们创建了简化版以便立即可用！** 🌸
