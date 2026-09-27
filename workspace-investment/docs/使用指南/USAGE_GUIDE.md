# 投资分析策略工厂 - 使用指南

**版本**: 1.0  
**更新时间**: 2026-04-06

---

## 📊 系统能力概览

### 【核心能力】

| 能力 | 说明 | 文件 |
|------|------|------|
| **30 因子量化评分** | 多维度股票评分 | `factor_30_model.py` |
| **专业风险评估** | VaR/CVaR/风险敞口 | `risk_manager.py` |
| **智能信号生成** | 技术面 + 情绪面信号 | `signal_generator_pro.py` |
| **5+2 策略系统** | 5 种基础策略 + 双策略优化 | `multi_strategies.py` |
| **专业回测** | 历史 K 线/实盘回测 | `backtest_engine_pro.py` |
| **AI 辅助** | 信号压缩/策略优化 | `ai_assistant.py` |

---

## 🔄 完整工作流程

```
┌─────────────────────────────────────────────────────────────┐
│                    投资分析策略工厂工作流程                    │
└─────────────────────────────────────────────────────────────┘

1. 数据获取
   ├─ AKShare (A 股)
   ├─ Yahoo Finance (美股/港股)
   └─ 腾讯财经 API (Mock)

         ↓

2. 因子分析 (30 因子模型)
   ├─ 风险因子 (5 个)
   ├─ 资金流因子 (5 个)
   ├─ 成长因子 (5 个)
   ├─ 估值因子 (5 个)
   ├─ 技术因子 (5 个)
   └─ 情绪因子 (5 个)

         ↓

3. 风险评估
   ├─ 个股风险评估
   ├─ 组合 VaR 计算
   └─ 风险敞口分析

         ↓

4. 信号生成
   ├─ 技术面信号
   ├─ 情绪面信号
   └─ 综合信号评分

         ↓

5. 策略决策
   ├─ 趋势跟踪策略
   ├─ 均值回归策略
   ├─ 突破策略
   ├─ 动量策略
   ├─ 反转策略
   └─ 双策略优化

         ↓

6. 回测验证
   ├─ 历史 K 线回测
   ├─ 绩效分析
   └─ 风险评估

         ↓

7. 实盘执行
   ├─ 仓位管理
   ├─ 风险控制
   └─ 交易执行

         ↓

8. 反馈优化
   ├─ 交易记录
   ├─ 表现分析
   └─ 策略优化
```

---

## 💻 使用示例

### 【场景 1: 单只股票分析】

```python
from src.factors.factor_30_model import Factor30Model
from src.risk.risk_manager import RiskManager
from src.signals.signal_generator_pro import SignalGeneratorPro

# 1. 准备数据
import pandas as pd
df = get_stock_data('000001.SZ')  # 获取 K 线数据

# 2. 因子评分
factor_model = Factor30Model()
factor_score = factor_model.calculate_score('000001.SZ', df)

print('综合得分:', factor_score['total'])
print('风险因子:', factor_score['risk_factors'])
print('成长因子:', factor_score['growth_factors'])

# 3. 风险评估
risk = RiskManager()
risk_score = risk.evaluate_stock(df)

print('风险等级:', risk_score['level'])
print('VaR(95%):', risk_score['var_95'])

# 4. 信号生成
signal_gen = SignalGeneratorPro()
signal = signal_gen.generate_signal(df, factor_score)

print('信号方向:', signal['direction'])
print('信号强度:', signal['strength'])

# 5. 综合决策
if factor_score['total'] >= 70 and risk_score['level'] == '低' and signal['direction'] == '买入':
    print('决策：强烈推荐')
elif factor_score['total'] >= 60 and risk_score['level'] in ['低', '中']:
    print('决策：推荐')
else:
    print('决策：观望')
```

---

### 【场景 2: 策略回测】

```python
from src.backtests.backtest_engine_pro import BacktestEnginePro
from src.strategies.multi_strategies import MultiStrategyFactory

# 1. 创建回测引擎
backtest = BacktestEnginePro(initial_capital=100000)

# 2. 创建策略
factory = MultiStrategyFactory()
strategy = factory.create_strategy('trend', '趋势跟踪 v1')

# 3. 生成信号
from src.signals.signal_generator import SignalGenerator
generator = SignalGenerator({})
signals = [generator.generate_all_signals(df.iloc[:i+1]) for i in range(len(df))]

# 4. 运行回测
result = backtest.run_backtest(df, strategy, signals)

# 5. 查看结果
print('总收益:', result['total_return'], '%')
print('年化收益:', result['annual_return'], '%')
print('最大回撤:', result['max_drawdown'], '%')
print('夏普比率:', result['sharpe_ratio'])
print('胜率:', result['win_rate'], '%')
```

---

### 【场景 3: 双策略优化】

```python
from src.strategies.dual_strategy_optimizer import DualStrategyOptimizer

# 1. 创建优化器
optimizer = DualStrategyOptimizer()

# 2. 生成两个策略信号
signal1 = strategy1.generate_signal(df)
signal2 = strategy2.generate_signal(df)

# 3. 优化融合
optimized = optimizer.combine_signals(
    signal1,
    signal2,
    weights=[0.6, 0.4]  # 策略 1 权重 60%, 策略 2 权重 40%
)

# 4. 执行
result = optimizer.execute(optimized, portfolio)
```

---

### 【场景 4: 风险管理】

```python
from src.risk.risk_manager import RiskManager

# 1. 创建风险管理器
risk = RiskManager()

# 2. 计算组合 VaR
var = risk.calculate_var(portfolio, confidence=0.95)
print('VaR(95%):', var)

# 3. 风险敞口分析
exposure = risk.analyze_exposure(portfolio)
print('行业敞口:', exposure['sector'])
print('个股敞口:', exposure['stock'])

# 4. 实时风控
risk_control = risk.realtime_monitoring(positions)
if risk_control['alert']:
    print('风险警报:', risk_control['message'])
    # 执行风控措施
    risk_control.execute_reduce_position()
```

---

### 【场景 5: 完整工作流】

```python
# 完整投资分析流程
from src.factors.factor_30_model import Factor30Model
from src.risk.risk_manager import RiskManager
from src.signals.signal_generator_pro import SignalGeneratorPro
from src.strategies.multi_strategies import MultiStrategyFactory
from src.backtests.backtest_engine_pro import BacktestEnginePro

def analyze_stock(code, df):
    """
    完整股票分析流程
    """
    # 1. 因子评分
    factor_model = Factor30Model()
    factor_score = factor_model.calculate_score(code, df)
    
    # 2. 风险评估
    risk = RiskManager()
    risk_score = risk.evaluate_stock(df)
    
    # 3. 信号生成
    signal_gen = SignalGeneratorPro()
    signal = signal_gen.generate_signal(df, factor_score)
    
    # 4. 策略决策
    factory = MultiStrategyFactory()
    strategy = factory.create_strategy('trend', '趋势跟踪 v1')
    
    signals = generate_signals(df)
    can_enter = strategy.check_entry_condition(signals)
    
    # 5. 综合决策
    decision = {
        'code': code,
        'factor_score': factor_score['total'],
        'risk_level': risk_score['level'],
        'signal': signal['direction'],
        'strategy_signal': can_enter,
        'recommendation': make_recommendation(factor_score, risk_score, signal, can_enter)
    }
    
    return decision

def make_recommendation(factor, risk, signal, strategy):
    """综合决策逻辑"""
    if factor['total'] >= 70 and risk['level'] == '低' and signal['direction'] == '买入' and strategy:
        return '强烈推荐'
    elif factor['total'] >= 60 and risk['level'] in ['低', '中'] and signal['direction'] == '买入':
        return '推荐'
    elif factor['total'] >= 50:
        return '观望'
    else:
        return '不推荐'

# 使用
result = analyze_stock('000001.SZ', df)
print(result)
```

---

## 📋 决策矩阵

### 【买入条件】

| 条件 | 要求 | 权重 |
|------|------|------|
| **因子评分** | ≥70 分 | 40% |
| **风险等级** | 低/中 | 30% |
| **信号方向** | 买入 | 20% |
| **策略确认** | 入场条件满足 | 10% |

### 【卖出条件】

| 条件 | 要求 |
|------|------|
| **止损** | 亏损≥5% |
| **止盈** | 盈利≥15% |
| **信号反转** | 卖出信号 |
| **风险警报** | 高风险警报 |

---

## 🎯 仓位管理

### 【凯利公式】

```python
def calculate_position_size(capital, win_rate, avg_win, avg_loss):
    """
    凯利公式计算仓位
    """
    kelly = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
    position = capital * kelly * 0.5  # 半凯利
    return position
```

### 【风险预算】

| 风险等级 | 最大仓位 | 说明 |
|---------|---------|------|
| **低风险** | 30% | 蓝筹股/指数 ETF |
| **中风险** | 20% | 成长股 |
| **高风险** | 10% | 题材股/小盘股 |

---

## 📊 报告生成

### 【日报】

```python
from src.signals.daily_report_generator import DailyReportGenerator

report_gen = DailyReportGenerator()
report = report_gen.generate_daily_report(
    date='2026-04-06',
    portfolio=portfolio,
    trades=trades,
    performance=performance
)

# 保存报告
report.save('outputs/reports/daily_20260406.pdf')
```

### 【绩效分析】

```python
from src.reports.performance_tracker import PerformanceTracker

tracker = PerformanceTracker()
report = tracker.generate_report()

print(report)
```

---

## ⚠️ 风险提示

### 【使用原则】

1. **不盲信**: 所有评分/信号仅供参考
2. **不黑箱**: 理解决策逻辑，不盲目跟随
3. **不依赖**: 人工监督 + 系统辅助
4. **持续监控**: 定期评估模型有效性

### 【风控措施】

1. **单笔最大亏损**: ≤5%
2. **组合最大回撤**: ≤20%
3. **连续亏损**: ≥3 次暂停交易
4. **高波动环境**: 降低仓位或观望

---

## 📚 学习路径

### 【新手入门】

1. 阅读 `README.md` - 系统概览
2. 运行 `examples/use_advanced_scorer.py` - 评分示例
3. 运行 `tests/test_ml_scorer_simple.py` - 测试简化版
4. 阅读 `docs/因子分析入门.md` - 因子分析基础

### 【进阶学习】

1. 运行 `tests/test_advanced_scorer.py` - 专业版测试
2. 运行 `tests/run_backtest_simple.py` - 回测测试
3. 阅读 `docs/30 因子模型详解.md` - 因子模型
4. 阅读 `docs/风险管理系统.md` - 风控体系

### 【专业使用】

1. 运行完整工作流示例
2. 自定义因子/策略
3. 实盘模拟测试
4. 定期优化调整

---

## 💬 常见问题

### Q: 如何获取股票数据？

A: 使用 `src/loaders/data_loader.py`:
```python
from src.loaders.data_loader import get_loader
loader = get_loader('A')
df = loader.load_market_data('000001.SZ', '2024-01-01', '2024-12-31')
```

### Q: 如何选择合适的策略？

A: 根据市场环境选择:
- **上涨趋势**: 趋势跟踪/动量策略
- **下跌趋势**: 反转策略
- **震荡市**: 均值回归策略

### Q: 如何评估策略有效性？

A: 使用回测引擎:
```python
from src.backtests.backtest_engine_pro import BacktestEnginePro
backtest = BacktestEnginePro()
result = backtest.run_backtest(df, strategy, signals)
print('夏普比率:', result['sharpe_ratio'])
```

---

**使用指南已保存到：**
`workspace-investment/USAGE_GUIDE.md`

**策略工厂提供从数据分析到实盘执行的完整投资解决方案！** 🌸
