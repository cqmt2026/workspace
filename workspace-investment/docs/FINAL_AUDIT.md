# 框架最终审查 - 用户场景模拟

> 模拟一个真实用户（主人）使用框架的全过程
> 从安装配置 → 数据准备 → 策略编写 → 回测 → 分析结果 → 上线
> 每个步骤检查：是否可行？是否顺畅？有没有遗漏？

---

## 场景：主人想测试一个新的趋势跟踪策略

### Step 1: 安装和配置

```bash
# 克隆框架
git clone alice_quant
cd alice_quant

# 安装依赖
pip install -r requirements.txt

# 初始化配置
python alice_quant/init.py
```

### 自查

**问**：框架依赖哪些库？requirements.txt有没有定义？

**发现问题1：缺少依赖管理。**
框架需要以下依赖，但文档中没有定义：
- pandas/numpy（数据处理）
- lightgbm/xgboost（ML模型）
- requests（API调用）
- akshare/efinance（数据源）
- pyyaml（配置管理）

这些依赖的版本有没有冲突？比如akshare需要pandas 1.x，但lightgbm需要pandas 2.x？

**修复**：明确依赖列表和版本要求。

---

### Step 2: 数据准备

```bash
# 配置数据源
vim config/data.yaml
```

用户需要配置什么？

**自查**

**问**：用户怎么配置数据源？腾讯API不需要KEY，但akshare不需要配置。用户需要做什么？

**发现问题2：配置流程不清晰。**
用户第一次使用，需要知道：
1. 数据源有哪些？（腾讯/efinance/akshare）
2. 哪个是默认的？（腾讯）
3. 需要配置什么？（腾讯不需要KEY，akshare不需要配置）
4. 如果我想用聚宽/万得的数据，怎么接入？

现在文档里没有**快速开始指南**。用户拿到框架不知道第一步该做什么。

**修复**：添加快速开始指南，明确用户需要做的配置步骤。

---

### Step 3: 查看已有策略

```bash
# 查看预置策略
ls strategies/
# pipeline.py, trend.py, dabanz.py, magic_formula.py, multi_factor.py

# 查看策略说明
python strategies/trend.py --help
```

### 自查

**问**：策略怎么运行？是作为独立脚本运行，还是通过回测引擎运行？

**发现问题3：策略运行方式不明确。**
策略层定义的是策略类，不是可执行脚本。用户不能直接 `python strategies/trend.py` 运行策略。

正确的使用方式是：

```python
# 用户需要写一个回测脚本来运行策略
from alice_quant.backtest import BacktestEngine
from alice_quant.strategies.trend import TrendStrategy

engine = BacktestEngine()
strategy = TrendStrategy(name='my_trend', params={'ma_window': 20})
result = engine.run(strategy, data, start='2019-01-01', end='2024-12-31')
print(result.summary())
```

但框架文档中没有给出**用户如何编写和运行回测的示例代码**。

**修复**：添加用户使用示例代码（run_backtest.py 示例文件）。

---

### Step 4: 编写自定义策略

```python
from alice_quant.strategies.base import BaseStrategy
from alice_quant.core.signal import Signal

class MyStrategy(BaseStrategy):
    def __init__(self, name, params, feature_engine, logger):
        super().__init__(name, params, feature_engine, logger)
        self.depends_on = []  # 无依赖
    
    def on_start(self, context):
        # 声明股票池
        self.watch_codes = ['000001', '000002', '600519']
        # 预加载因子
        self.prefetch_factors(
            codes=self.watch_codes,
            factor_names=['ma_20', 'ma_60', 'rsi_14'],
            dates=context.all_dates
        )
    
    def on_bar(self, data, context):
        signals = []
        for code in self.watch_codes:
            ma20 = self.get_cached_factor(code, 'ma_20', context.current_date)
            ma60 = self.get_cached_factor(code, 'ma_60', context.current_date)
            rsi = self.get_cached_factor(code, 'rsi_14', context.current_date)
            
            if ma20 > ma60 and rsi < 30:
                signals.append(Signal(
                    code=code, direction='buy',
                    price=data['close'], volume=0,
                    confidence=0.7, source=self.name,
                    reason=f'均线多头+RSI超卖'
                ))
        return signals
```

### 自查

**问**：`context.all_dates` 是什么？用户怎么知道context有哪些字段？

**发现问题4：Context对象未定义。**
回测引擎传给策略的context对象，有哪些字段？
- `context.current_date`：当前回测日期
- `context.all_dates`：所有回测日期列表
- `context.candidates`：候选股票列表
- `context.account`：当前账户状态
- 还有别的吗？

这些在文档中都没有定义。用户写策略时不知道context有什么可用。

**修复**：明确定义Context对象的所有字段。

---

### Step 5: 运行回测

```python
# 用户写的回测脚本
from alice_quant.data import DataHub
from alice_quant.features import FeatureEngine
from alice_quant.backtest import BacktestEngine
from my_strategies import MyStrategy

# 初始化
datahub = DataHub(config)
feature = FeatureEngine(config, datahub)
strategy = MyStrategy('my_trend', params, feature, logger)

# 运行回测
engine = BacktestEngine(config, datahub)
result = engine.run(strategy, start='2019-01-01', end='2024-12-31')

# 查看结果
print(result.summary())
```

### 自查

**问**：回测结果result是什么类型？有哪些方法？

**发现问题5：Result对象未定义。**
回测返回的result对象，有哪些字段？
- `result.summary()`：返回什么？
- `result.trades`：交易列表
- `result.daily_returns`：每日收益率
- `result.sharpe`：夏普比率
- `result.analyze()`：详细分析

这些在文档中都没有定义。用户拿到结果不知道怎么用。

**修复**：明确定义Result对象的所有字段和方法。

---

### Step 6: 查看回测报告

```python
# 详细分析
report = result.analyze()
print(report.significance)  # 显著性检验

# 对比多个回测
results = backtest.compare([run1, run2, run3])
print(results.comparison_table)

# 查看最佳参数
best = backtest.best_runs(metric='sharpe', top=5)
```

### 自查

**问**：用户怎么可视化结果？是HTML报告？PDF？还是控制台输出？

**发现问题6：可视化输出方式未定义。**
绩效分析模块有"可视化输出"，但没说具体输出什么格式。是生成HTML文件？Matplotlib图表？还是直接在控制台打印？

对于日线策略的回测，用户最想看的是：
1. 净值曲线图（vs基准）
2. 回撤曲线图
3. 月度收益热力图
4. 交易记录表

这些需要明确输出方式。

**修复**：明确可视化输出格式（HTML报告 + Matplotlib图表 + CSV导出）。

---

### Step 7: 参数优化

```python
# 参数优化
best_params = engine.optimize(
    strategy_class=MyStrategy,
    params_grid={
        'ma_window': [10, 20, 30, 60],
        'rsi_threshold': [20, 25, 30, 35]
    },
    method='nested_cv'
)
print(f"最佳参数: {best_params}")
```

### 自查

**问**：参数优化要跑多久？ma_window有4个值，rsi_threshold有4个值，共16种组合。嵌套CV分5折，每折跑16次回测，总共80次。每次回测7年数据。总共要跑多久？

**发现问题7：参数优化没有进度显示。**
80次回测，如果每次30秒，总共40分钟。用户看着黑屏等待40分钟，不知道进度。

**修复**：参数优化需要进度条显示（tqdm），以及预计剩余时间。

---

### Step 8: Walk-Forward验证

```python
# Walk-Forward分析
wf_result = engine.walk_forward(
    strategy_class=MyStrategy,
    params=best_params,
    train_window=3,  # 3年训练
    test_window=1,   # 1年测试
    step=1           # 1年步长
)
print(f"各段结果: {wf_result.segment_results}")
print(f"综合结果: {wf_result.aggregated_result}")
```

### 自查

**问**：Walk-Forward的训练窗口是3年。如果回测区间是2019-2024，那第一段训练数据是2016-2018。但我们的数据从2019年开始，没有2016年的数据！

**发现问题8：Walk-Forward需要更长的历史数据。**
回测区间2019-2024，Walk-Forward训练窗口3年，第一段需要2016-2018的训练数据。但框架数据从2019年开始，第一段Walk-Forward就跑不了。

这意味着框架需要**至少比回测区间多N年的历史数据**（N=训练窗口长度）。如果训练窗口3年，数据至少要从回测开始前3年开始。

**修复**：明确数据覆盖范围要求——至少比回测区间多3年数据。或者在Walk-Forward中自动调整第一段的训练窗口。

---

### Step 9: 模型训练

```bash
# 训练ML模型
python models/train.py --experiment my_model --config config/models.yaml
```

### 自查

**问**：训练完成后，模型存在哪里？怎么在策略中使用？

**发现问题9：模型训练结果和策略的衔接方式未明确。**
训练脚本输出模型文件，策略需要加载这个模型文件来做预测。这个衔接过程需要明确：

```python
# 训练完成后：
model.save('data/models/my_model_v1.pkl')

# 策略中：
class MLStrategy(BaseStrategy):
    def on_start(self, context):
        # 加载模型
        self.model = ModelRegistry.load('my_model_v1')
    
    def on_bar(self, data, context):
        # 获取ML因子
        ml_prob = self.get_cached_factor(code, 'ml_factor', context.current_date)
        # 使用ML因子
```

但这里有个问题：ML因子是预计算好存在Feature层的，但策略如果要在on_start时加载模型自己做推理，那就绕过了预计算流程。**两种方式（预计算 vs 实时推理）需要明确选择一种。**

**修复**：明确ML因子的使用方式——统一通过Feature层获取预计算好的ML因子，策略不直接加载模型。

---

### Step 10: 模拟交易

```bash
# 启动模拟交易
python execution/run_paper.py --strategy my_trend --params '{"ma_window": 20}'
```

### 自查

**问**：模拟交易是每天定时运行（Cron），还是手动启动后持续运行？如果是持续运行，怎么获取实时数据？

**发现问题10：模拟交易的运行模式未定义。**
模拟交易有两种运行模式：
1. **Cron模式**：每天收盘后运行一次，用当天数据计算信号
2. **实时模式**：持续运行，盘中获取实时数据

对于日线策略，Cron模式就够了。但如果是分钟线策略，需要实时模式。

**修复**：明确模拟交易的运行模式，以及如何获取实时数据（盘中使用腾讯实时API）。

---

## 发现的10个问题汇总

| # | 场景 | 问题 | 严重程度 |
|---|------|------|---------|
| 1 | 安装 | 缺少依赖管理（requirements.txt） | 中等 |
| 2 | 配置 | 缺少快速开始指南，用户不知道第一步做什么 | 严重 |
| 3 | 运行 | 策略运行方式不明确，缺少使用示例 | 严重 |
| 4 | 编写 | Context对象未定义，用户不知道有什么字段可用 | 严重 |
| 5 | 分析 | Result对象未定义，用户不知道怎么用回测结果 | 严重 |
| 6 | 可视化 | 可视化输出格式未明确 | 中等 |
| 7 | 优化 | 参数优化没有进度显示 | 中等 |
| 8 | 验证 | Walk-Forward需要更长的历史数据 | 严重 |
| 9 | ML | 模型训练和策略衔接方式未明确 | 严重 |
| 10 | 交易 | 模拟交易运行模式未定义 | 中等 |

---

## 结论

**这次审查发现的不再是架构问题，而是使用体验问题。**

v4.2的架构已经没有大问题了。10个问题中，有4个是"文档/接口定义不完整"（Context/Result/使用示例/快速开始），有3个是"工程细节不明确"（依赖管理/可视化/进度显示），有2个是"流程衔接不清晰"（ML衔接/模拟交易模式），有1个是"数据覆盖范围考虑不周"（Walk-Forward数据需求）。

**这说明框架已经从一个"设计问题"阶段进入了一个"工程落地"阶段。** 之前每次审查都能发现架构级别的缺陷（模型训练时序/数据版本管理/成交量限制），现在这些问题已经没有了，剩下的都是实现层面的细节。

**框架成熟度：从v4.0的60分 → v4.2的85分 → 现在是90分。** 剩下的10分是需要在实际编码中才能发现的问题。

要不要修完这10个问题再动手，还是先开始 Phase 1，遇到问题再修？

---

_审查: Alice | 2026-07-05_

## 修复状态（2026-07-05）

| # | 问题 | 严重程度 | 修复状态 |
|---|------|---------|---------|
| 1 | 缺少依赖管理 | 中等 | 已修复 |
| 2 | 缺少快速开始指南 | 严重 | 已修复 |
| 3 | 策略运行方式不明确 | 严重 | 已修复 |
| 4 | Context对象字段未定义 | 严重 | 已修复 |
| 5 | Result对象字段未定义 | 严重 | 已修复 |
| 6 | 可视化输出格式未明确 | 中等 | 已修复 |
| 7 | 参数优化无进度显示 | 中等 | 已修复 |
| 8 | Walk-Forward需更长的历史数据 | 严重 | 已修复 |
| 9 | ML训练和策略衔接方式未明确 | 严重 | 已修复 |
| 10 | 模拟交易运行模式未定义 | 中等 | 已修复 |
