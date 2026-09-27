# AliceQuant v0.1.1 快速开始指南

> 最后更新：2026-07-06
> 本指南帮助你从0到1运行第一个回测

---

## 1. 安装依赖

```bash
# 进入框架目录
cd alice_quant

# 安装依赖
pip install -r requirements.txt
```

requirements.txt 已包含所有依赖：
- pandas, numpy（数据处理）
- lightgbm（ML模型）
- requests, akshare, efinance（数据源）
- pyyaml（配置管理）

---

## 2. 配置数据源

框架支持多个数据源，默认使用腾讯API：

```yaml
# config/data.yaml
data:
  default_source: "tencent"
  
  sources:
    tencent:
      enabled: true
      # 腾讯API不需要API Key，开箱即用
      
    efinance:
      enabled: true
      # efinance 不需要配置
      
    akshare:
      enabled: true
      # akshare 不需要配置
```

**数据本地缓存**：`F:\market_data.db`（已在Hermes系统中维护）

---

## 3. 查看预置策略

```bash
ls strategies/
# pipeline.py, trend.py, dabanz.py, magic_formula.py, multi_factor.py
```

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| TrendStrategy | 趋势跟踪（均线系统） | 主升趋势 |
| DaBanStrategy | 打板策略 | 涨停接力 |
| MagicFormula | 神奇公式 | 价值投资 |
| PipelineV2 | 多因子综合评分 | 全市场选股 |

---

## 4. 运行第一个回测

最简单的方式——直接用回测引擎运行预置策略：

```python
from alice_quant.backtest import BacktestEngine
from alice_quant.strategies.trend import TrendStrategy
from alice_quant.core.context import Context

# 运行趋势策略回测
engine = BacktestEngine()
strategy = TrendStrategy(name='my_trend', params={'ma_window': 20})
result = engine.run(strategy, start='2019-01-01', end='2024-12-31')

# 查看结果
print(result.summary())
```

**一行命令版**（已准备好的示例脚本）：

```bash
python scripts/run_backtest_example.py
```

---

## 5. Context对象字段说明

策略在 `on_start()` 和 `on_bar()` 中接收 `context` 对象，可用字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `current_date` | str | 当前回测日期 "2024-01-01" |
| `all_dates` | list[str] | 所有回测日期列表 |
| `candidates` | list[str] | 当前候选股票列表 |
| `account` | Account | 当前账户状态（可用现金/持仓） |
| `config` | dict | 回测配置参数 |

使用示例：

```python
def on_bar(self, data, context):
    # 获取今天日期
    today = context.current_date
    # 遍历候选股票
    for code in context.candidates:
        pass
    # 查看账户可用现金
    cash = context.account.cash
```

---

## 6. Result对象字段说明

回测完成后返回的 `Result` 对象，包含：

| 属性 | 类型 | 说明 |
|------|------|------|
| `summary()` | str | 回测摘要（收益率/胜率/回撤等） |
| `equity_curve` | pd.DataFrame | 权益曲线 |
| `trades` | pd.DataFrame | 交易记录 |
| `metrics` | dict | 绩效指标字典 |
| `win_rate` | float | 胜率 |
| `total_return` | float | 总收益率 |
| `max_drawdown` | float | 最大回撤 |

使用示例：

```python
result = engine.run(strategy, ...)

# 打印摘要
print(result.summary())

# 查看交易记录
print(result.trades)

# 查看胜率
print(f"胜率: {result.win_rate:.2%}")
```

---

## 7. 常见问题

**Q: 回测数据从哪里来？**
A: 默认从 `F:\market_data.db` 读取，由Hermes系统每日维护。

**Q: 策略参数怎么改？**
A: 通过 `params` 字典传入：

```python
strategy = TrendStrategy(
    name='my_trend',
    params={
        'ma_window': 20,      # 均线周期
        'rsi_period': 14,     # RSI周期
        'stop_loss': -0.05,   # 止损线
    }
)
```

**Q: 如何添加自定义因子？**
A: 参考 `features/calculators/` 目录，继承 `BaseCalculator` 并注册到 `FactorRegistry`。

---

## 8. ML因子 8. ML因子使用说明

框架的ML因子（LightGBM/MSTNN预测概率）**不是由策略实时推理的**，而是通过Feature层预计算后缓存。

### 计算流程

```
每日收盘后16:45 → FactorEngine计算全市场因子
  → 其中 ml_prob_lgb / ml_prob_mstnn 因子
  → 从预训练模型加载预测结果
  → 写入 factors.db
```

### 策略中使用

```python
def on_bar(self, data, context):
    # 获取预计算好的ML因子（不需要自己加载模型）
    ml_prob = self.get_cached_factor(code, 'ml_prob_lgb', context.current_date)
    
    # 结合其他因子使用
    if ml_prob > 0.6 and score > 70:
        signals.append(...)
```

### 注意

- 策略**不直接加载模型文件**，统一通过Feature层获取
- 模型训练在20:00由 `unified_train.py` 完成
- 次日开盘时，前一天的ML因子已可用

---

## 9. 数据要求

| 要求 | 说明 |
|------|------|
| 数据源 | `F:\\market_data.db`（Hermes系统维护） |
| 最小数据量 | 至少3年日K线（支持Walk-Forward训练窗口） |
| 推荐数据量 | 2019年至今（约7年数据） |
| Walk-Forward | 框架自动调整训练窗口以适应可用数据长度 |

---

## 10. 下一步"}]

- [ ] 运行示例回测：`python scripts/run_backtest_example.py`
- [ ] 查看策略代码：`strategies/trend.py`
- [ ] 编写自定义策略
- [ ] 对接实时交易

---

_最后更新: 2026-07-06_