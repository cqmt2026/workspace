# AliceQuant - A股量化框架

模块化、标准化、可插拔的A股量化框架。

## 快速开始

```bash
# 1. 安装
pip install -r requirements.txt

# 2. 配置
cp config/default.yaml config/custom.yaml

# 3. 运行示例回测
python examples/run_backtest.py
```

## 目录结构

```
alice_quant/
├── core/           # 核心: 配置/日志/数据标准
├── data/           # 数据层: 数据源/版本管理/质量
├── features/       # 特征工程: 因子计算/筛选/IC监控
├── models/         # 模型训练: 样本/训练/评估/管理
├── strategies/     # 策略层: 策略基类/预置策略/组合管理
├── backtest/       # 回测层: 事件循环/订单/绩效/过拟合检测
├── execution/      # 执行层: 信号/风控/模拟交易
├── dashboard/      # 监控层: 绩效/风险/告警/报告
├── config/         # 配置文件
├── examples/       # 示例代码
├── data/           # 数据存储
└── reports/        # 报告输出
```

## 设计原则

1. 层间单向依赖，禁止跨层调用
2. 所有配置通过 ConfigManager 读取
3. 所有日志通过 Logger 写入
4. 模块间通过标准数据格式通信
5. 回测可复现（数据版本绑定）
6. 成交真实模拟（成交量限制+前瞻检测）

详细设计见 `docs/FRAMEWORK_DESIGN.md`