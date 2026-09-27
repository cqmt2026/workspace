# 框架流程模拟 - 逐环节深度自查

> 模拟一个真实场景：我要回测"尾盘策略"在2019-2024年的表现
> 每个环节都停下来反问："这里有没有问题？"
> 时间：2026-07-05

---

## 场景设定

**策略**：尾盘策略
- 买入条件：涨幅3%~5%、量比>1、近3日涨幅0%~10%、MA20向上、换手率3%~10%
- 排除条件：北交所、ST股
- 买入时间：14:50，收盘价买入
- 卖出时间：次日最高价卖出
- 回测区间：2019-01-01 ~ 2024-12-31
- 初始资金：100万

---

## Step 1: 数据准备

### 需要的数据
- 全市场日K线（open/close/high/low/volume）
- ST状态（排除ST股）
- 换手率数据
- 板块分类（排除北交所）

### 模拟流程

```python
# 1. 获取数据版本
data_version = datahub.get_latest_version()  # v20260704.1

# 2. 获取2017-2024的数据（需要2年预热算MA20）
bars = datahub.get_bars_batch(
    codes='all', 
    start='2017-01-01', 
    end='2024-12-31',
    freq='1d'
)
```

### 自查

**问**：get_bars_batch(codes='all') 会返回多少条数据？
- 全市场约5000只股票，8年约2000个交易日
- 5000 × 2000 = 1000万条K线
- 每次回测都要加载1000万条数据到内存？

**发现问题1：全量数据加载内存不足。**
1000万条K线，每条至少8个字段（date/open/close/high/low/volume/code/freq），约需500MB~1GB内存。如果同时跑多个策略，内存会爆。

**修复**：DataHub需要支持**按需加载**——只加载策略需要的股票和时间段，不是全量。策略在on_start时声明需要的股票列表，DataHub只加载这些股票的数据。

---

## Step 2: 数据校验

```python
# 3. 数据质量检查
quality_report = datahub.get_data_quality_report('2024-12-31')
if quality_report.score < 70:
    raise DataQualityError("数据质量不足，请检查数据源")
```

### 自查

**问**：数据质量分数低于70就抛异常？那如果某天腾讯API数据延迟，整个回测跑不了？

**发现问题2：质量检查太严格，没有降级机制。**
如果主数据源质量差，应该自动切换到备用数据源重新获取，而不是直接报错。如果所有数据源都差，才报错。

**修复**：DataHub增加自动降级机制——主源质量差→切备用源→备用源也差→报错。降级过程记录日志。

---

## Step 3: 时间旅行

```python
# 4. 回测引擎每天通过时间旅行获取数据
class BacktestEngine:
    def _pre_day(self, date):
        # 获取该日期的数据快照（只能看到T日及之前的数据）
        snapshot = datahub.snapshot(date)
        # snapshot 包含截至 date 的所有数据
```

### 自查

**问**：snapshot(date) 怎么实现的？每次调用都复制一遍全量数据？

**发现问题3：快照实现方式未定义，可能导致性能灾难。**
如果snapshot()每次返回全量数据的深拷贝，回测7年约2000天，就要复制2000次全量数据。

**修复**：快照应该是**轻量级的引用**——不是复制数据，而是标记"截至T日"。所有get_bars调用都带上当前回测日期参数，DataHub自动过滤。

```python
# 正确实现：不是复制数据，是加日期过滤
bars = datahub.get_bars('000001', '2019-01-01', '2024-12-31', 
                         snapshot_date='2024-12-31')
# 内部自动过滤：只返回 <= snapshot_date 的数据
```

---

## Step 4: 因子计算

```python
# 5. 策略在on_start时预加载因子
class PipelineStrategy(BaseStrategy):
    def on_start(self, context):
        codes = context.get('candidates', [])  # 候选股票列表
        # 预加载所有需要的因子
        self.prefetch_factors(
            codes=codes,
            factor_names=['ma_20', 'vol_ratio', 'turnover', 'pct_chg_1d', 'pct_chg_3d'],
            dates=context.get('dates', [])
        )
```

### 自查

**问**：预加载的因子存哪里？内存中？如果策略有100只候选股票、5个因子、2000个交易日，缓存多大？
- 100 × 5 × 2000 = 100万个因子值
- 每个值约8字节 → 8MB
- 如果候选股票是5000只 → 400MB

**发现问题4：缓存膨胀。**
候选股票太多时缓存会爆炸。策略只需要关注一小部分股票（比如当日涨幅3%~5%的），不应该预加载所有股票的因子。

**修复**：策略在on_bar中动态筛选候选股票，只对候选股票调用get_cached_factor。缓存使用LRU策略，超过上限自动淘汰。

---

## Step 5: 策略信号生成

```python
# 6. 每日on_bar中计算信号
def on_bar(self, data, context):
    signals = []
    for code in context.candidates:
        # 检查ST
        if datahub.get_st_status(code, context.current_date):
            continue
        
        # 获取因子
        pct_chg = self.get_cached_factor(code, 'pct_chg_1d', context.current_date)
        vol_ratio = self.get_cached_factor(code, 'vol_ratio', context.current_date)
        turnover = self.get_cached_factor(code, 'turnover', context.current_date)
        ma20 = self.get_cached_factor(code, 'ma_20', context.current_date)
        pct_chg_3d = self.get_cached_factor(code, 'pct_chg_3d', context.current_date)
        
        # 条件判断
        if (3 <= pct_chg <= 5 and vol_ratio > 1 and 
            0 <= pct_chg_3d <= 10 and ma20 > 0 and 
            3 <= turnover <= 10):
            signal = Signal(
                code=code, direction='buy', 
                price=data['close'], volume=0,  # 按资金比例
                confidence=0.8, source='pipeline',
                reason=f'尾盘策略: 涨幅{pct_chg:.1f}%'
            )
            signals.append(signal)
    
    return signals
```

### 自查

**问**：策略在14:50买入，用的是收盘价。但回测中怎么知道14:50的价格？日线数据只有开盘价、收盘价、最高价、最低价。

**发现问题5：日线回测无法模拟"尾盘买入"。**
日线回测中，我们不知道14:50的价格。用收盘价代替，但实际交易中14:50的价格可能和收盘价不同。如果策略是"尾盘买入、次日卖出"，用收盘价代替会导致回测不准确。

**修复**：对于需要特定时间点交易的策略，应该使用分钟线数据。或者在回测中增加"尾盘模拟"——用收盘价买入，但加一个尾盘滑点（比如0.1%）。

---

## Step 6: 组合管理

```python
# 7. 组合管理器接收所有策略信号
portfolio_signals = portfolio.get_portfolio_signal(date)
# 如果只有尾盘策略一个策略，直接返回策略信号
```

### 自查

**问**：组合管理器在回测中怎么工作？每次on_bar都调portfolio.get_portfolio_signal()？如果多个策略，是不是每个策略都要跑完on_bar再传给portfolio？

**发现问题6：组合管理器和回测引擎的协作时序不明确。**
回测引擎每天要做的事：
1. 调策略A.on_bar() → 得到信号A
2. 调策略B.on_bar() → 得到信号B
3. 调策略C.on_bar() → 得到信号C
4. 调portfolio.get_portfolio_signal() → 融合信号
5. 执行融合后的信号 → 更新账户

但现在的设计中没有明确这个顺序。如果策略A和策略B相互依赖（策略B需要策略A的信号作为输入），顺序就更复杂了。

**修复**：明确回测引擎中策略执行的顺序：先执行所有独立策略，再执行依赖策略，最后传给组合管理器。回测引擎需要有一个策略依赖解析器。

---

## Step 7: 订单执行

```python
# 8. 回测引擎处理信号 -> 生成订单 -> 成交判断
for signal in final_signals:
    order = Order(
        code=signal.code, 
        direction=signal.direction,
        price=signal.price,
        volume=calculate_volume(signal, account)
    )
    
    # 风控检查
    risk_check = risk_manager.check_before_trade(order)
    if not risk_check.passed:
        logger.warning(f"风控拒绝: {risk_check.reason}")
        continue
    
    # 成交判断
    fill_price, fill_volume = order_manager.execute(order, market_data)
```

### 自查

**问**：calculate_volume() 怎么算？策略说"按资金比例"，但比例是多少？

**发现问题7：仓位计算逻辑在策略层和组合层之间不明确。**
策略发出信号时只说了"买"没说"买多少"。仓位计算应该在组合层（组合管理器有资金管理模块）还是执行层（信号处理器）？

**修复**：仓位计算统一在组合管理器中完成。策略只输出"买/卖"和"置信度"，组合管理器根据资金管理规则计算具体仓位。

---

## Step 8: 成交判断

```python
# 9. 尾盘策略：14:50买入，用收盘价成交
# 次日卖出：用最高价成交
```

### 自查

**问**：次日最高价卖出，这个"最高价"是当天的最高价吗？如果是，那策略在回测中相当于"提前知道当天的最高价"，有前瞻偏误！

**发现问题8：尾盘策略的卖出逻辑有前瞻偏误！**
"次日最高价卖出"意味着策略在回测中知道次日的最高价。但实际交易中，我们不可能在开盘前就知道今天的最高价。这是一个**经典的前瞻偏误**。

正确的做法是：策略在次日设定一个**止盈单**（比如+3%），回测中按止盈单成交。或者更保守一点，按次日开盘价卖出。

**修复**：策略的卖出逻辑不能使用"未来价格"。必须改为基于条件的卖出（止盈/止损/收盘卖出），或者按开盘价卖出。

---

## Step 9: 绩效分析

```python
# 10. 回测结束，生成绩效报告
result = backtest.analyze()
print(f"年化收益: {result.annual_return:.2%}")
print(f"夏普比率: {result.sharpe:.2f}")
print(f"最大回撤: {result.max_drawdown:.2%}")
print(f"胜率: {result.win_rate:.2%}")
```

### 自查

**问**：这个结果可信吗？有没有做统计显著性检验？

**发现问题9：没有默认的显著性检验。**
绩效分析模块有显著性检验功能，但如果使用者不主动调用，就不会执行。应该默认对所有回测结果进行显著性检验，并在报告中显著标注"统计显著"或"可能是运气"。

**修复**：回测引擎在analyze()中默认执行显著性检验，结果中自动包含p值和置信区间。

---

## Step 10: 参数优化

```python
# 11. 参数优化：调整量比阈值、换手率范围等
best_params = backtest.optimize(
    strategy=PipelineStrategy,
    params_grid={
        'vol_ratio': [1.0, 1.2, 1.5, 2.0],
        'turnover_min': [3, 5],
        'turnover_max': [8, 10, 15],
        'pct_chg_min': [2, 3, 4],
        'pct_chg_max': [5, 6, 7]
    }
)
```

### 自查

**问**：参数优化是在全量数据上跑的吗？如果是，那优化出来的参数很可能过拟合。

**发现问题10：参数优化默认用全量数据，没有嵌套交叉验证。**
正确的做法：参数优化只在训练集上跑，选出的最优参数在测试集上验证。但现在没有这个流程。

**修复**：optimize() 函数应该默认使用嵌套交叉验证——内部循环做参数优化（在训练集上），外部循环做验证（在测试集上）。用户也可以手动指定训练集和测试集。

---

## 发现的10个问题汇总

| # | 环节 | 问题 | 严重程度 |
|---|------|------|---------|
| 1 | 数据准备 | 全量加载内存不足 | 严重 |
| 2 | 数据校验 | 质量检查太严格，无降级 | 中等 |
| 3 | 时间旅行 | 快照实现方式未定义 | 严重 |
| 4 | 因子计算 | 缓存膨胀 | 中等 |
| 5 | 策略信号 | 日线无法模拟尾盘交易 | 致命 |
| 6 | 组合管理 | 多策略执行时序不明确 | 严重 |
| 7 | 订单执行 | 仓位计算位置不明确 | 中等 |
| 8 | 成交判断 | 尾盘策略有前瞻偏误 | 致命 |
| 9 | 绩效分析 | 无默认显著性检验 | 中等 |
| 10 | 参数优化 | 无嵌套交叉验证 | 严重 |

---

## 结论

**只是走了一遍最简单的尾盘策略回测流程，就发现了10个问题，其中2个是致命的（尾盘模拟、前瞻偏误）。**

如果走更复杂的流程（ML策略回测、多策略组合回测），问题只会更多。

**这就是为什么每次检查都能发现问题——因为我之前根本没走过这个流程。** 我的设计都是"我觉得这里应该有个模块"，而不是"这里要处理一个具体的工程问题"。

现在我要把这些问题修到v4.2。要现在修吗？

---

_自查: Alice | 2026-07-05_