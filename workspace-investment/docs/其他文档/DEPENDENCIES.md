# 股票系统 V14.0 依赖清单

**创建时间**: 2026-03-26  
**最后更新**: 2026-03-26  
**系统版本**: V14.0  
**状态**: ✅ 生效

---

## 📊 Python 环境要求

| 项目 | 要求 | 说明 |
|------|------|------|
| **Python 版本** | ≥3.11 | 推荐 3.11+ |
| **操作系统** | Windows 10/11 | 支持 macOS/Linux |
| **内存** | ≥8GB | 推荐 16GB+（数据处理） |
| **磁盘空间** | ≥2GB | 推荐 5GB+（历史数据） |

---

## 📦 Python 依赖库

### 核心依赖（必需）

| 库名 | 版本 | 用途 | 安装命令 |
|------|------|------|---------|
| `pathlib` | 内置 | 路径处理 | 无需安装 |
| `json` | 内置 | JSON 处理 | 无需安装 |
| `datetime` | 内置 | 日期时间 | 无需安装 |

### 可选依赖（按需安装）

| 库名 | 版本 | 用途 | 安装命令 |
|------|------|------|---------|
| `pandas` | ≥1.5 | 数据分析 | `pip install pandas` |
| `numpy` | ≥1.23 | 数值计算 | `pip install numpy` |
| `requests` | ≥2.28 | HTTP 请求 | `pip install requests` |

**说明**: 系统主要使用 Python 标准库，可选依赖用于增强功能

---

## 📁 核心目录（必需）

| 目录 | 用途 | 状态 |
|------|------|------|
| `stock-tools/` | 主工作目录 | ✅ 存在 |
| `stock-tools/factor_backtest/` | 因子回测 | ✅ 存在 |
| `stock-tools/data/` | 数据存储 | ✅ 存在 |
| `stock-tools/reports/` | 报告输出 | ✅ 存在 |
| `stock-tools/models/` | ML 模型 | ✅ 存在 |
| `backup/auto/` | 自动备份 | ✅ 存在（全系统） |

---

## 📄 核心文件（必需）

### 主系统（16 个核心模块）

| 文件 | 用途 | 状态 |
|------|------|------|
| `stock_v14_system.py` | V14 主系统 | ✅ 存在 |
| `simulation_trader.py` | 模拟交易 | ✅ 存在 |
| `self_evolution_system.py` | 自主进化 | ✅ 存在 |
| `performance_monitor.py` | 绩效监控 | ✅ 存在 |
| `backtest_engine.py` | 回测引擎 | ✅ 存在 |
| `test_framework.py` | 测试框架 | ✅ 存在 |
| `advanced_scorer.py` | 高级评分 | ✅ 存在 |
| `factor_30_model.py` | 30 因子模型 | ✅ 存在 |
| `eastmoney_api.py` | 东方财富 API | ✅ 存在 |
| `sector_tracker.py` | 板块追踪 | ✅ 存在 |
| `realtime_data.py` | 实时数据 | ✅ 存在 |
| `realtime_tracker.py` | 实时追踪 | ✅ 存在 |
| `risk_manager.py` | 风险管理 | ✅ 存在 |
| `stock_pool_updater.py` | 股票池更新 | ✅ 存在 |
| `stock_pool_200.py` | 200 股票池 | ✅ 存在 |
| `signal_realtime.py` | 实时信号 | ✅ 存在 |

### 辅助脚本

| 文件 | 用途 | 状态 |
|------|------|------|
| `scripts/auto_backup.py` | 自动备份 | ✅ 存在 |
| `scripts/performance_monitor.py` | 性能监控 | ✅ 存在 |
| `scripts/weekly_health_check.py` | 周度检查 | ✅ 存在 |

---

## 🎯 系统功能

### 核心功能（16 个模块）

| 模块 | 功能 | 状态 |
|------|------|------|
| **V14 主系统** | 信号生成 + 交易决策 | ✅ 正常 |
| **模拟交易** | 模拟交易 + 绩效跟踪 | ✅ 正常 |
| **自主进化** | 系统自学习优化 | ✅ 正常 |
| **绩效监控** | 交易绩效分析 | ✅ 正常 |
| **回测引擎** | 策略历史回测 | ✅ 正常 |
| **测试框架** | 系统测试验证 | ✅ 正常 |
| **高级评分** | 股票综合评分 | ✅ 正常 |
| **30 因子模型** | 多因子选股 | ✅ 正常 |
| **东方财富 API** | 数据采集 | ✅ 正常 |
| **板块追踪** | 行业板块分析 | ✅ 正常 |
| **实时数据** | 实时行情获取 | ✅ 正常 |
| **实时追踪** | 实时信号追踪 | ✅ 正常 |
| **风险管理** | 风险预警 + 控制 | ✅ 正常 |
| **股票池更新** | 自动更新股票池 | ✅ 正常 |
| **200 股票池** | 核心股票池 | ✅ 正常 |
| **实时信号** | 实时交易信号 | ✅ 正常 |

---

## 🔒 安全性

| 安全项 | 状态 | 说明 |
|--------|------|------|
| **自动备份** | ✅ 已覆盖 | 全系统自动备份（24h/10KB） |
| **灾难恢复** | ✅ 已整合 | DISASTER_RECOVERY.md（全系统） |
| **依赖清单** | ✅ 已创建 | 本文档 |
| **版本管理** | ⏳ 待创建 | 计划本周内完成 |
| **实时风险监控** | ✅ 已有 | realtime_risk_control.py |

---

## 📋 安装检查清单

### 首次安装验证

```bash
# 1. 检查 Python 版本
python --version  # 应显示 Python 3.11.x

# 2. 检查核心目录
ls stock-tools/  # 应显示 16 个核心模块
ls stock-tools/factor_backtest/  # 应显示回测相关

# 3. 运行测试
cd stock-tools
python stock_v14_system.py  # 应正常运行
```

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 确认 Python 版本
python --version

# 确认可选依赖（按需安装）
pip install pandas numpy requests
```

### 2. 运行系统

```bash
# 运行主系统
cd stock-tools
python stock_v14_system.py

# 运行回测
python factor_backtest/backtest_engine.py
```

### 3. 查看状态

```bash
# 查看系统状态
python -c "import sys; print('Python', sys.version)"

# 查看数据目录
ls stock-tools/data/
```

---

## ⚠️ 常见问题

### Q1: Python 版本不兼容

**症状**: 运行脚本报错 `SyntaxError`  
**解决**: 升级到 Python 3.11+

### Q2: 数据文件找不到

**症状**: `FileNotFoundError`  
**解决**: 检查 data/目录是否存在

### Q3: 权限不足

**症状**: `PermissionError`  
**解决**: 以管理员身份运行

---

## 📊 依赖版本历史

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| V1.0 | 2026-03-26 | 初始版本，记录核心依赖 |

---

## 🔄 更新说明

**更新频率**: 按需更新（新增依赖时）  
**负责人**: 系统管理员  
**审核**: 版本迭代时同步更新

---

**文档状态**: ✅ 生效  
**下次审查**: 2026-04-26（1 个月后）

---

*小智 AI 助手 - 股票系统 V14.0 依赖清单 V1.0*
