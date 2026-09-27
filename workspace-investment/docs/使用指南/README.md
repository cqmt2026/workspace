# 投资分析策略工厂

> **理念**: AI 驱动研究，而不是 AI 辅助思考  
> **状态**: 🚧 搭建中（最小可用骨架已完成）

---

## 五层架构

| 层级 | 模块 | 状态 | 说明 |
|------|------|------|------|
| **数据入口层** | `src/loaders/` | ✅ 已完成 | AKShare/YahooFinance数据加载器 |
| **信号生成层** | `src/signals/` | ✅ 已完成 | 趋势/波动率/成交量/异常信号 |
| **规则层** | `src/strategies/` | ✅ 已完成 | 趋势跟踪/均值回归策略 |
| **验证层** | `src/backtests/` | ✅ 已完成 | 回测引擎 |
| **反馈层** | `src/reports/` | ⏳ 待实现 | 策略表现记录与分析 |

---

## 快速开始

### 1. 安装依赖

```bash
cd workspace-investment
pip install -e .
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑.env 文件，配置数据源和 AI 接口
```

### 3. 运行测试

```bash
# 测试数据加载
python src/loaders/data_loader.py

# 测试信号生成
python src/signals/signal_generator.py

# 测试策略定义
python src/strategies/strategy_definition.py

# 测试回测引擎
python src/backtests/backtest_engine.py
```

---

## 目录结构

```
workspace-investment/
├─ data/
│  ├─ raw/              # 原始数据
│  └─ processed/        # 处理后数据
├─ notebooks/           # 研究笔记
├─ src/
│  ├─ loaders/          # 数据加载器 ✅
│  ├─ signals/          # 信号生成 ✅
│  ├─ strategies/       # 策略定义 ✅
│  ├─ backtests/        # 回测引擎 ✅
│  └─ reports/          # 报告生成 ⏳
├─ outputs/
│  ├─ charts/           # 图表输出
│  └─ logs/             # 日志
├─ config/              # 配置文件
├─ tests/               # 测试
├─ .env.example         # 环境变量示例
├─ pyproject.toml       # 项目配置
└─ README.md            # 本文件
```

---

## 核心理念

### 交易策略 ≠ 一个想法/Prompt

**交易策略 = 一套可持续运行的研究流水线**

| 错误认知 | 正确认知 |
|---------|---------|
| AI 搜索信息 | AI 压缩数据成结构 |
| 问新闻/走势/观点 | 建立变量连接 |
| 单点使用 | 系统连接 |
| 效率工具 | 认知放大器 |
| 自动交易 | 自动研究 |

---

## 已实现功能

### 1. 数据加载器 (`src/loaders/data_loader.py`)

- ✅ AKShareLoader: A 股数据加载
- ✅ YahooFinanceLoader: 美股/港股数据加载
- ✅ 支持市场数据/宏观数据/新闻

### 2. 信号生成器 (`src/signals/signal_generator.py`)

- ✅ 趋势信号：MA20/MA60/金叉死叉
- ✅ 波动率信号：布林带/波动率状态
- ✅ 成交量信号：量比/量价关系
- ✅ 异常信号：新高新低/涨跌幅异常/缺口

### 3. 策略定义 (`src/strategies/strategy_definition.py`)

- ✅ TrendFollowingStrategy: 趋势跟踪策略
- ✅ MeanReversionStrategy: 均值回归策略
- ✅ 明确的入场/出场/止损/止盈规则
- ✅ 策略失效检测

### 4. 回测引擎 (`src/backtests/backtest_engine.py`)

- ✅ 完整回测流程
- ✅ 收益/回撤/夏普比率计算
- ✅ 交易记录追踪
- ✅ 权益曲线生成

---

## 待实现功能

### 第五层：反馈层 (`src/reports/`)

- [ ] 策略表现分析
- [ ] 失败原因记录
- [ ] 适用市场环境标记
- [ ] 策略迭代建议

### 升级路线

- [ ] 从单策略 → 多策略组合
- [ ] 参数扫描与优化
- [ ] 风控层（仓位管理/止损策略）
- [ ] 自动化报告生成
- [ ] AI 辅助策略优化

---

## 下一步

1. **完善反馈层** - 实现策略表现记录和分析
2. **添加更多策略** - 基于不同信号组合
3. **接入实时数据** - 实现实时监控
4. **AI 集成** - 用 AI 辅助信号压缩和策略优化

---

_基于"99% 的人只会用 AI 搜索，只有 1% 的人在建立核心策略工厂"理念搭建_

**搭建时间**: 2026-04-06 22:20  
**状态**: 最小可用骨架已完成，可以开始运行回测
