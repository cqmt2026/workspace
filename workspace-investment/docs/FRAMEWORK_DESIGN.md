# AliceQuant 框架设计蓝图 v4.3

> 目标：模块化、标准化、可插拔的A股量化框架
> 参考：Qlib(架构) + Backtrader(事件循环) + vnpy(模块化)
> 时间：2026-07-05 | v4.3

---

## 设计原则（铁律）

1. **层间单向依赖** — 只能上层调下层，不能反向，不能跨层
2. **配置不硬编码** — 所有参数通过 ConfigManager 读取
3. **接口标准化** — 模块间通过标准数据格式通信，不直接调用内部方法
4. **模块可插拔** — 替换一个模块不影响其他模块
5. **问题可追溯** — 每个操作都有日志，每次回测都有记录
6. **回测可复现** — 每次回测记录数据版本+参数版本，确保结果可复现
7. **数据时间旅行** — 回测时只能看到T日及之前的数据，杜绝前瞻偏误
8. **成交真实模拟** — 成交价/成交量必须模拟真实市场，不虚高

---

## 一、整体架构（同v4.2，无变化）

```
7层架构: DataHub → Feature → ModelTrain → Strategy → Portfolio → Backtest → Execute
         └─────────────────────────── Dashboard ──────────────────────────────┘
         └─────────────────── ConfigManager / Logger ─────────────────────────┘
```

---

## 二、修复说明

### 修复1: 依赖管理

**问题**：缺少依赖管理，用户不知道要装什么。

**修复**：明确requirements.txt，定义所有依赖及版本范围。

```python
# requirements.txt
pandas>=1.5.0,<2.0.0
numpy>=1.23.0
pyyaml>=6.0
requests>=2.28.0
lightgbm>=3.3.0
xgboost>=1.7.0
scikit-learn>=1.2.0
scipy>=1.9.0
akshare>=1.10.0
efinance>=1.2.0
tqdm>=4.64.0           # 进度条
matplotlib>=3.6.0      # 可视化
```

### 修复2: 快速开始指南

**问题**：用户拿到框架不知道第一步做什么。

**修复**：添加快速开始指南（README.md 和 docs/QUICKSTART.md）。

```
快速开始指南:
  1. 安装: pip install -r requirements.txt
  2. 配置: cp config/default.yaml config/custom.yaml
  3. 数据: python alice_quant/init.py (自动下载基础数据)
  4. 回测: python examples/run_backtest.py
  5. 查看: 打开 reports/backtest_report.html
```

### 修复3: 策略运行方式 + 使用示例

**问题**：策略是类不是脚本，用户不知道怎么运行。

**修复**：提供完整的示例脚本 examples/run_backtest.py。

```python
# examples/run_backtest.py - 完整的回测运行示例
"""
使用方法:
  python examples/run_backtest.py
  python examples/run_backtest.py --strategy pipeline --start 2019-01-01 --end 2024-12-31
"""
import argparse
from alice_quant.core.config import ConfigManager
from alice_quant.core.logger import Logger
from alice_quant.data.datahub import DataHub
from alice_quant.features.engine import FeatureEngine
from alice_quant.backtest.engine import BacktestEngine
from alice_quant.strategies.pipeline import PipelineStrategy

def main():
    parser = argparse.ArgumentParser(description='运行回测')
    parser.add_argument('--strategy', default='pipeline', help='策略名称')
    parser.add_argument('--start', default='2019-01-01', help='开始日期')
    parser.add_argument('--end', default='2024-12-31', help='结束日期')
    parser.add_argument('--capital', default=1000000, type=float, help='初始资金')
    args = parser.parse_args()

    # 1. 加载配置
    config = ConfigManager()
    config.load('config/custom.yaml')
    
    # 2. 初始化组件
    logger = Logger(config)
    datahub = DataHub(config)
    feature = FeatureEngine(config, datahub)
    
    # 3. 创建策略
    strategy = PipelineStrategy(
        name=args.strategy,
        params=config.get(f'strategies.{args.strategy}', {}),
        feature_engine=feature,
        logger=logger
    )
    
    # 4. 运行回测
    engine = BacktestEngine(config, datahub, logger)
    result = engine.run(
        strategy=strategy,
        start=args.start,
        end=args.end,
        initial_capital=args.capital
    )
    
    # 5. 输出结果
    print(result.summary())
    result.save_report('reports/backtest_report.html')
    result.export_trades('reports/trades.csv')

if __name__ == '__main__':
    main()
```

### 修复4: Context对象定义

**问题**：用户写策略时不知道context有什么字段。

**修复**：明确定义Context对象。

```python
# core/context.py
@dataclass
class Context:
    """回测上下文 - 回测引擎传给策略的运行时信息"""
    current_date: str               # 当前回测日期 (YYYY-MM-DD)
    all_dates: List[str]            # 所有回测日期列表
    start_date: str                 # 回测开始日期
    end_date: str                   # 回测结束日期
    watch_codes: List[str]          # 策略声明的候选股票列表
    account: 'Account'              # 当前账户状态 (只读)
    portfolio_signals: List[Signal] # 其他策略在本日产生的信号 (用于依赖策略)
    data_version: str               # 当前使用的数据版本
    is_backtesting: bool            # 是否在回测中 (True) 还是实盘 (False)

    def get_dates_before(self, n: int) -> List[str]:
        """获取当前日期前N个交易日"""
        idx = self.all_dates.index(self.current_date)
        return self.all_dates[max(0, idx-n):idx]
```

### 修复5: Result对象定义

**问题**：用户拿到回测结果不知道怎么用。

**修复**：明确定义Result对象。

```python
# core/result.py
@dataclass
class BacktestResult:
    """回测结果"""
    # 基本信息
    strategy_name: str
    params: dict
    start_date: str
    end_date: str
    data_version: str
    config_version: str
    
    # 核心指标
    total_return: float          # 总收益率
    annual_return: float         # 年化收益率
    sharpe: float                # 夏普比率
    max_drawdown: float          # 最大回撤
    win_rate: float              # 胜率
    profit_loss_ratio: float     # 盈亏比
    total_trades: int            # 总交易次数
    
    # 详细数据
    daily_returns: pd.Series     # 每日收益率序列
    equity_curve: pd.Series      # 净值曲线
    drawdown_curve: pd.Series    # 回撤曲线
    trades: List[dict]           # 交易记录列表
    monthly_returns: pd.DataFrame # 月度收益矩阵
    
    # 显著性检验
    significance: dict           # 显著性检验结果
    
    def summary(self) -> str:
        """返回文本摘要"""
        pass
    
    def save_report(self, path: str):
        """保存HTML报告"""
        pass
    
    def export_trades(self, path: str):
        """导出交易记录CSV"""
        pass
    
    def plot_equity_curve(self):
        """绘制净值曲线"""
        pass
    
    def plot_drawdown(self):
        """绘制回撤曲线"""
        pass
    
    def plot_monthly_returns(self):
        """绘制月度收益热力图"""
        pass
```

### 修复6: 可视化输出格式

**问题**：可视化输出格式未明确。

**修复**：明确HTML报告和Matplotlib图表的输出规范。

```
回测报告输出:
  1. HTML报告 (默认)
     - 生成 reports/backtest_YYYYMMDD_HHMMSS.html
     - 包含: 摘要指标 / 净值曲线图 / 回撤曲线图 / 月度热力图 / 交易记录表
     - 使用 Chart.js 或 Plotly 生成交互式图表
  
  2. Matplotlib图表 (可选)
     - 保存为 PNG 图片
     - 输出路径: reports/charts/
  
  3. CSV导出 (可选)
     - 交易记录: reports/trades.csv
     - 每日净值: reports/daily_returns.csv
  
  4. 控制台输出 (最小)
     - 回测结束后打印关键指标
     - 进度条显示回测进度
```

### 修复7: 参数优化进度显示

**问题**：参数优化没有进度显示，用户不知道要等多久。

**修复**：使用tqdm进度条。

```python
from tqdm import tqdm

class BacktestEngine:
    def optimize(self, strategy_class, params_grid, data, method='nested_cv'):
        # 计算总任务数
        total_combinations = self._count_combinations(params_grid)
        if method == 'nested_cv':
            total_combinations *= self.cv_folds
        
        # 进度条
        with tqdm(total=total_combinations, desc='参数优化') as pbar:
            for params in self._generate_combinations(params_grid):
                result = self.run(strategy_class, params, data)
                self._record_result(params, result)
                pbar.update(1)
                pbar.set_postfix({
                    '当前最佳': f"夏普={self._best_sharpe:.2f}",
                    '剩余': f"{pbar.total - pbar.n}个"
                })
```

### 修复8: Walk-Forward数据覆盖范围

**问题**：Walk-Forward需要比回测区间更长的历史数据。

**修复**：明确数据要求 + 自动调整。

```python
class WalkForwardAnalyzer:
    def __init__(self, train_window=3, test_window=1, step=1):
        self.train_window = train_window  # 年
        self.test_window = test_window    # 年
        self.step = step                  # 年
    
    def analyze(self, strategy, data, backtest_start, backtest_end):
        """
        Walk-Forward分析
        数据要求: 数据开始日期 <= backtest_start - train_window
        例如: 回测2019-2024, 训练窗口3年, 需要2016年开始的数据
        """
        required_start = self._subtract_years(backtest_start, self.train_window)
        if data.start_date > required_start:
            raise DataInsufficientError(
                f"Walk-Forward需要从{required_start}开始的数据, "
                f"但数据从{data.start_date}开始"
            )
        
        # 自动调整第一段的训练窗口
        segments = []
        current = backtest_start
        while current < backtest_end:
            train_start = self._subtract_years(current, self.train_window)
            train_end = current
            test_start = current
            test_end = self._add_years(current, self.test_window)
            
            # 如果数据不足，缩短训练窗口
            if train_start < data.start_date:
                train_start = data.start_date
                logger.warning(f"训练窗口缩短: {train_start}~{train_end}")
            
            segments.append({
                'train': (train_start, train_end),
                'test': (test_start, test_end)
            })
            current = self._add_years(current, self.step)
        
        return self._run_segments(strategy, data, segments)
```

### 修复9: ML因子使用方式

**问题**：ML因子可以通过预计算或实时推理两种方式获取，未明确选哪种。

**修复**：统一为预计算方式，策略不直接加载模型。

```python
# 明确ML因子的使用流程:

"""
ML因子使用方式: 预计算

训练时:
  ModelTrain.train() → 训练模型
  ModelTrain.precompute_inference() → 推理历史每天ML因子
  推理结果存入 Feature 层的因子存储中 (作为普通因子)

回测时:
  Strategy.on_bar():
    ml_prob = self.get_cached_factor(code, 'ml_factor', date)
    # 像使用MA/RSI一样使用ML因子

推理时(每日):
  ModelTrain.inference() → 用最新模型推理今日ML因子
  结果存入 Feature 层
  策略下次运行时自动获取最新的ML因子

禁止的操作:
  ❌ 策略中直接加载模型文件 (.pkl)
  ❌ 策略中自己调用模型推理
  ❌ 回测中训练模型
"""
```

### 修复10: 模拟交易运行模式

**问题**：模拟交易是Cron模式还是实时模式，未定义。

**修复**：明确为Cron模式（日线策略）+ 预留实时模式。

```
模拟交易运行模式:

  默认模式: Cron模式 (适用于日线策略)
    触发: 每天14:45 (Cron任务)
    流程:
      1. 检查数据是否更新到当日
      2. 获取当日因子值
      3. 运行策略 on_bar() → 生成信号
      4. 组合管理器融合信号 + 计算仓位
      5. 风控检查
      6. 生成订单
      7. 记录交易
    数据: 使用腾讯实时API获取当日行情
  
  预留模式: 实时模式 (适用于分钟线策略)
    触发: 持续运行 (独立进程)
    流程: 同上，但每N分钟运行一次
    数据: 使用腾讯实时API + 分钟线数据
  
  配置:
    config.yaml:
      paper_trading:
        mode: cron                    # cron / realtime
        cron_time: "45 14 * * 1-5"    # 周一~五 14:45
        output_dir: data/paper_trading/
        report: true                  # 每次交易后生成报告
```

---

## 三、模块详解（仅列出变更）

### 3.1 核心模块 core/

```python
# core/context.py - 回测上下文
@dataclass
class Context:
    current_date: str
    all_dates: List[str]
    start_date: str
    end_date: str
    watch_codes: List[str]
    account: 'Account'                # 只读
    portfolio_signals: List[Signal]    # 其他策略今日信号
    data_version: str
    is_backtesting: bool
    
    def get_dates_before(self, n: int) -> List[str]: ...

# core/result.py - 回测结果
@dataclass
class BacktestResult:
    strategy_name: str
    params: dict
    start_date: str
    end_date: str
    data_version: str
    config_version: str
    total_return: float
    annual_return: float
    sharpe: float
    max_drawdown: float
    win_rate: float
    profit_loss_ratio: float
    total_trades: int
    daily_returns: pd.Series
    equity_curve: pd.Series
    drawdown_curve: pd.Series
    trades: List[dict]
    monthly_returns: pd.DataFrame
    significance: dict
    
    def summary(self) -> str: ...
    def save_report(self, path: str): ...
    def export_trades(self, path: str): ...
    def plot_equity_curve(self): ...
    def plot_drawdown(self): ...
    def plot_monthly_returns(self): ...
```

### 3.2 其他模块

其余模块设计同v4.2，无变化。

---

## 四、依赖清单

```
# requirements.txt
pandas>=1.5.0,<2.0.0
numpy>=1.23.0
pyyaml>=6.0
requests>=2.28.0
lightgbm>=3.3.0
xgboost>=1.7.0
scikit-learn>=1.2.0
scipy>=1.9.0
akshare>=1.10.0
efinance>=1.2.0
tqdm>=4.64.0
matplotlib>=3.6.0
plotly>=5.10.0          # 交互式图表
```

---

## 五、快速开始指南

```
# README.md / docs/QUICKSTART.md

# AliceQuant - A股量化框架

## 快速开始

### 1. 安装
pip install -r requirements.txt

### 2. 配置
cp config/default.yaml config/custom.yaml
# 修改 custom.yaml 中的配置（如数据路径、初始资金等）

### 3. 初始化
python alice_quant/init.py
# 自动下载基础数据（股票列表、交易日历等）

### 4. 运行示例回测
python examples/run_backtest.py
# 使用尾盘策略回测2019-2024年
# 结果保存在 reports/backtest_report.html

### 5. 运行自己的策略
# 参考 examples/run_backtest.py 编写自己的回测脚本
# 参考 strategies/pipeline.py 编写自己的策略

## 目录结构
alice_quant/        # 框架核心代码
examples/           # 示例代码
config/             # 配置文件
data/               # 数据存储
reports/            # 回测报告输出
docs/               # 文档
```

---

## 六、目录结构

```
alice_quant/
├── core/                       # 核心
│   ├── __init__.py
│   ├── config.py               # ConfigManager + 热更新
│   ├── logger.py               # Logger + 结构化日志
│   ├── context.py              # Context 对象定义 (新增)
│   ├── result.py               # BacktestResult 对象定义 (新增)
│   ├── signal.py / order.py / account.py / exceptions.py
├── data/                       # 数据层
│   ├── datahub.py / version.py / snapshot.py / quality.py
│   ├── metadata.py / adjustment.py / cache.py
│   └── sources/ (base/tencent/efinance/akshare/db/csv)
├── features/                   # 特征工程
│   ├── engine.py / registry.py / auto_feature.py
│   ├── selection.py / store.py / ic_monitor.py
│   └── calculators/ (technical/fundamental/money_flow/sentiment/macro/ml_factor)
├── models/                     # 模型训练
│   ├── sample_manager.py / feature_manager.py
│   ├── registry.py / evaluator.py / inference.py / monitor.py
│   ├── precompute.py / scheduler.py
│   └── trainers/ (base/lightgbm/xgboost/mstnn/ensemble)
├── strategies/                 # 策略层
│   ├── base.py / portfolio.py
│   ├── pipeline.py / trend.py / dabanz.py
│   └── magic_formula.py / multi_factor.py
├── backtest/                   # 回测层
│   ├── engine.py / order_manager.py / account_manager.py
│   ├── commission.py / slippage.py / performance.py
│   ├── overfitting.py / data_validator.py / result_db.py / reporter.py
│   └── walk_forward.py         # Walk-Forward (含数据范围校验)
├── execution/                  # 执行层
│   ├── signal_handler.py / risk_manager.py
│   ├── paper_trading.py / live_trading.py / executor.py
│   ├── emergency_stop.py / risk_feedback.py
├── dashboard/                  # 监控层
│   ├── performance.py / risk_panel.py / alerts.py
│   ├── monitor.py / reporter.py / settings.py / auto_report.py
├── examples/                   # 示例代码 (新增)
│   ├── run_backtest.py         # 回测运行示例
│   ├── create_strategy.py      # 创建自定义策略示例
│   └── run_optimization.py     # 参数优化示例
├── config/                     # 配置文件
│   ├── default.yaml / data.yaml / features.yaml / models.yaml
│   ├── strategies/ / backtest.yaml / risk.yaml / versions/
├── data/                       # 数据存储
│   ├── raw/ / factors/ / models/ / results/ / logs/ / snapshots/
│   └── paper_trading/          # 模拟交易记录
├── reports/                    # 报告输出 (新增)
│   ├── charts/                 # 图表
│   └── backtest_*.html         # 回测报告
├── docs/                       # 文档
│   ├── QUICKSTART.md           # 快速开始 (新增)
│   ├── FRAMEWORK_DESIGN.md     # 框架设计
│   └── API.md                  # API文档 (待开发)
├── requirements.txt            # 依赖清单 (新增)
├── init.py                     # 初始化脚本 (新增)
└── README.md                   # 项目说明 (含快速开始)
```

---

## 七、实施路线（更新版）

### Phase 1: 基础设施 (3天)
1. 目录结构搭建 + requirements.txt + README.md
2. ConfigManager + 热更新 + Logger + 结构化日志
3. 数据标准 (Signal/Order/Account/Context/Result)
4. 异常类 + 配置模板 + 初始化脚本

### Phase 2: 数据层核心 (4天)
5. 适配器基类 + 数据源监控 + 按需加载 + LRU缓存
6. 数据版本管理 + 时间旅行快照 + 数据质量降级
7. 元数据 + 复权 + 指数数据

### Phase 3: 回测引擎 (6天)
8. 事件循环 + 尾盘模拟 + 策略依赖解析
9. 订单管理 (成交量限制 + 止盈止损 + 前瞻检测)
10. 账户管理 + 滑点/手续费 + 数据校验
11. 绩效分析 + 显著性检验 (默认)
12. 过拟合检测 (Walk-Forward + 嵌套CV + 敏感性)
13. 结果数据库 + 报告生成 (HTML + 图表)

### Phase 4: 特征工程 (4天)
14. 因子注册中心 + 基础因子库 + 计算引擎
15. 自动特征 + 因子筛选 + 因子存储 (修正顺序)
16. 滚动IC监控 + 因子预加载 + LRU缓存

### Phase 5: 模型训练 (5天)
17. 样本管理 + 特征管理 + 模型注册
18. LightGBM/MSTNN训练器 + 评估
19. 预计算推理 + 调度管理 + 模型管理

### Phase 6: 策略 + 组合 (3天)
20. BaseStrategy (LRU缓存 + 依赖声明 + 置信度校准)
21. Pipeline迁移 (修正卖出逻辑)
22. Portfolio独立层 (依赖解析 + 仓位计算 + 策略相关性 + 再平衡)

### Phase 7: 执行层 (3天)
23. 信号处理器 + 订单优先级/时效性
24. 风控模块 (白名单/多维黑名单/行业相关性)
25. 模拟交易 (Cron模式) + 紧急停止 + 风控回传

### Phase 8: 监控层 + 文档 (3天)
26. 绩效面板 + 风险面板 + 告警系统
27. 系统监控 + 自动化报告
28. 示例代码 (run_backtest/create_strategy/run_optimization)
29. API文档 + 快速开始指南

### Phase 9: 集成测试 (3天)
30. 端到端回测 + 尾盘模拟验证 + 前瞻检测验证
31. 模型预计算+回测全流程 + Walk-Forward验证
32. 结果库查询对比 + 嵌套CV验证 + 紧急停止测试

**总预计工期: 34天 (约1个月)**

---

_设计: Alice | 2026-07-05 | v4.3_