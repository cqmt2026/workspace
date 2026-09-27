import os
from pathlib import Path

# 工作区路径
ws_path = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment')

# 策略工厂目录结构
structure = {
    'data/raw': '原始数据（市场/宏观/新闻/期权）',
    'data/processed': '处理后数据',
    'notebooks': '研究笔记',
    'src/loaders': '数据加载器',
    'src/signals': '信号生成',
    'src/strategies': '策略定义',
    'src/backtests': '回测引擎',
    'src/reports': '报告生成',
    'outputs/charts': '图表输出',
    'outputs/logs': '日志',
    'config': '配置文件',
    'tests': '测试',
}

print('=' * 70)
print('搭建投资分析策略工厂')
print('=' * 70)
print()

# 创建目录
for dir_path, description in structure.items():
    full_path = ws_path / dir_path
    full_path.mkdir(parents=True, exist_ok=True)
    print(f'[OK] 创建 {dir_path}/ - {description}')

# 创建 README.md
readme_content = '''# 投资分析策略工厂

> **理念**: AI 驱动研究，而不是 AI 辅助思考

---

## 五层架构

| 层级 | 功能 | 说明 |
|------|------|------|
| **数据入口层** | 自动收集市场/宏观/新闻/期权数据 | 没有稳定数据入口，就不存在稳定研究输出 |
| **信号生成层** | AI 压缩数据成可读结构 | 趋势/异常/波动率/流动性变化 |
| **规则层** | 明确交易条件 | 做多/退出/失效环境 |
| **验证层** | 回测/模拟验证 | 回答"如果过去运行会发生什么" |
| **反馈层** | 记录策略表现/失败原因/适用环境 | 系统进化 |

---

## 目录结构

```
strategy_factory/
├─ data/
│  ├─ raw/              # 原始数据
│  └─ processed/        # 处理后数据
├─ notebooks/           # 研究笔记
├─ src/
│  ├─ loaders/          # 数据加载器
│  ├─ signals/          # 信号生成
│  ├─ strategies/       # 策略定义
│  ├─ backtests/        # 回测引擎
│  └─ reports/          # 报告生成
├─ outputs/
│  ├─ charts/           # 图表输出
│  └─ logs/             # 日志
├─ config/              # 配置文件
├─ tests/               # 测试
└─ README.md            # 本文件
```

---

## 核心理念

**交易策略 ≠ 一个想法/Prompt**

**交易策略 = 一套可持续运行的研究流水线**

| 错误认知 | 正确认知 |
|---------|---------|
| AI 搜索信息 | AI 压缩数据成结构 |
| 问新闻/走势/观点 | 建立变量连接 |
| 单点使用 | 系统连接 |
| 效率工具 | 认知放大器 |
| 自动交易 | 自动研究 |

---

## 下一步

1. [ ] 安装依赖（pyproject.toml）
2. [ ] 配置数据源（config/）
3. [ ] 实现数据加载器（src/loaders/）
4. [ ] 实现信号生成（src/signals/）
5. [ ] 定义策略规则（src/strategies/）
6. [ ] 实现回测引擎（src/backtests/）
7. [ ] 实现报告生成（src/reports/）

---

_基于"99% 的人只会用 AI 搜索，只有 1% 的人在建立核心策略工厂"理念搭建_
'''

readme_file = ws_path / 'README.md'
with open(readme_file, 'w', encoding='utf-8') as f:
    f.write(readme_content)

print()
print('[OK] 创建 README.md')

# 创建 pyproject.toml
pyproject_content = '''[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "strategy-factory"
version = "0.1.0"
description = "投资分析策略工厂 - AI 驱动研究"
requires-python = ">=3.10"

dependencies = [
    # 数据处理
    "pandas>=2.0",
    "numpy>=1.24",
    
    # 数据获取
    "akshare>=1.10",  # A 股数据
    "yfinance>=0.2",  # 美股/港股数据
    
    # 技术分析
    "ta-lib>=0.4",
    "pandas-ta>=0.3",
    
    # 回测
    "backtrader>=1.9",
    "vectorbt>=0.25",
    
    # 可视化
    "matplotlib>=3.7",
    "plotly>=5.15",
    
    # AI 接口
    "openai>=1.0",
    
    # 日志
    "loguru>=0.7",
    
    # 配置
    "python-dotenv>=1.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "black>=23.0",
    "flake8>=6.0",
]
'''

pyproject_file = ws_path / 'pyproject.toml'
with open(pyproject_file, 'w', encoding='utf-8') as f:
    f.write(pyproject_content)

print('[OK] 创建 pyproject.toml')

# 创建 .env.example
env_example = '''# 数据源配置
# AKShare (A 股数据，免费)
AKSHARE_ENABLED=true

# Yahoo Finance (美股/港股数据，免费)
YAHOO_FINANCE_ENABLED=true

# 聚宽数据 (A 股数据，需要注册)
JOINQUAN_API_KEY=your_api_key_here

# AI 配置
# OpenAI API (用于信号生成和策略分析)
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4

# 或使用本地模型
# LOCAL_LLM_ENDPOINT=http://localhost:11434
# LOCAL_LLM_MODEL=llama2

# 回测配置
BACKTEST_START_DATE=2020-01-01
BACKTEST_END_DATE=2024-12-31
INITIAL_CAPITAL=100000

# 风控配置
MAX_POSITION_SIZE=0.1  # 最大仓位 10%
MAX_DAILY_LOSS=0.02    # 最大日亏损 2%
'''

env_file = ws_path / '.env.example'
with open(env_file, 'w', encoding='utf-8') as f:
    f.write(env_example)

print('[OK] 创建 .env.example')

print()
print('=' * 70)
print('策略工厂骨架搭建完成！')
print('=' * 70)
print()
print('下一步:')
print('1. 复制 .env.example 为 .env 并配置密钥')
print('2. 安装依赖：pip install -e .')
print('3. 开始实现数据加载器 (src/loaders/)')
