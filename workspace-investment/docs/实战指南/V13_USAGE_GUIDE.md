# V13 系统使用指南

**更新时间**: 2026-03-14 22:53  
**说明**: V10 系统已删除，当前仅保留 V13 系统

---

## 🎯 V13 系统定位

**V13.0** - 专业股票分析系统

- 10 个专业小助手提供深度分析
- 支持技术分析、动量分析、缠论分析
- 支持 Qlib 量化回测
- 适用于深度研究和策略开发

---

## 📁 核心文件

### 主入口
```
stock_v13_system.py - V13 主系统入口
```

### 小助手模块 (stock_assistants/)
```
data_assistant.py              - 数据获取
technical_analysis_assistant.py - 技术分析
momentum_assistant.py          - 动量指标
volume_assistant.py            - 成交量分析
chan_theory_assistant.py       - 缠论分析
news_assistant.py              - 新闻事件
stock_pool_assistant.py        - 股票池管理
strategy_assistant.py          - 策略回测
qlib_assistant.py              - Qlib 量化
score_assistant.py             - 综合评分
```

### 工具脚本
```
scan_by_v13_system.py - 股票扫描工具
test_v13_fixed.py     - 测试脚本
```

---

## 🚀 快速开始

### 1. 初始化 V13 系统
```python
from stock_v13_system import StockV13System

# 初始化系统（自动加载 10 个小助手）
system = StockV13System()
```

### 2. 分析单只股票
```python
# 全面分析股票
result = system.analyze_stock('000001')
```

### 3. 使用小助手
```python
# 获取实时数据
price = system.data.get_realtime_price('000001')

# 技术分析
kline = system.ta.get_kline_data('000001', days=30)
ma = system.ta.calculate_ma(kline['prices'])

# 动量分析
rsi = system.momentum.calculate_rsi(kline['prices'])

# 股票池管理
system.pool.add_stock('000001', '平安银行')
```

---

## 📊 功能模块

### 数据助手 (DataAssistant)
- 获取实时行情
- 获取 K 线数据
- 获取财务数据

### 技术分析助手 (TechnicalAnalysisAssistant)
- MA/EMA/MACD
- KDJ/RSI/BOLL
- 支撑位/压力位

### 动量助手 (MomentumAssistant)
- RSI 相对强弱
- 动量指标
- 超买超卖判断

### 缠论助手 (ChanTheoryAssistant)
- 笔/段识别
- 中枢分析
- 买卖点判断

### Qlib 助手 (QlibAssistant)
- 模型训练
- 策略回测
- 预测分析

---

## ⚠️ 注意事项

### V13 不具备的功能
- ❌ 自动交易执行
- ❌ 持仓管理
- ❌ 止损止盈监控
- ❌ 尾盘选股策略

### 如需交易功能
V13 是**分析系统**，不是**交易系统**。如需实盘交易功能，需要：
1. 手动执行交易
2. 或重新开发交易模块

---

## 📋 日常使用流程

### 盘前分析 (9:00-9:30)
```python
system = StockV13System()

# 分析持仓股票
for stock in holdings:
    result = system.analyze_stock(stock)
    print(f"{stock}: {result['recommendation']}")
```

### 盘中监控 (10:00-14:00)
```python
# 使用新闻助手监控事件
news = system.news.get_stock_news('000001')

# 使用股票池助手管理观察池
system.pool.refresh_pool()
```

### 盘后复盘 (15:00-16:00)
```python
# 使用策略助手回测
backtest = system.strategy.backtest('momentum_strategy')

# 使用 Qlib 助手训练模型
system.qlib.train_model()
```

---

## 🔧 高级用法

### 自定义分析流程
```python
# 组合多个小助手
def custom_analysis(stock_code):
    # 1. 获取数据
    data = system.data.get_realtime_price(stock_code)
    
    # 2. 技术分析
    ta = system.ta.analyze(data['kline'])
    
    # 3. 动量分析
    momentum = system.momentum.analyze(data['prices'])
    
    # 4. 综合评分
    score = system.score.calculate(ta, momentum)
    
    return {
        'code': stock_code,
        'score': score,
        'recommendation': 'buy' if score > 70 else 'hold'
    }
```

### 批量分析
```python
# 批量分析股票池
stocks = ['000001', '600000', '000002']
results = []

for stock in stocks:
    result = system.analyze_stock(stock)
    results.append(result)

# 按评分排序
results.sort(key=lambda x: x['score'], reverse=True)
```

---

## 📄 文档索引

| 文档 | 说明 |
|------|------|
| V13_系统架构.md | 系统架构设计 |
| V13_KPI 执行计划.md | KPI 目标 |
| 股票 V13 系统小助手团队详细功能报告.md | 小助手功能详情 |

---

## 🆚 与 V10 的区别

| 特性 | V10 (已删除) | V13 (当前) |
|------|-------------|-----------|
| 定位 | 交易系统 | 分析系统 |
| 自动交易 | ✅ | ❌ |
| 持仓管理 | ✅ | ❌ |
| 深度分析 | ⚠️ 基础 | ✅ 专业 |
| 小助手数量 | 1 | 10 |
| 量化回测 | ⚠️ 基础 | ✅ Qlib |

---

**使用建议**: V13 专注于深度分析和策略研究，交易决策需手动执行。

**技术支持**: 查看 `stock_assistants/` 目录下各小助手源码了解详细功能。
