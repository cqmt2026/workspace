# H盘工具整合说明

**整合日期**: 2026-04-21
**来源**: H盘 `小智×老板交易体系/99-工具/`
**目标目录**: `src/tools_h/`

---

## 已整合工具清单

### 选股工具

| 文件 | 功能 | 状态 |
|------|------|------|
| `screen_eastmoney_top200.py` | 东方财富量价齐升TOP200筛选 | ✅ 已整合 |
| `screen_eastmoney_gain200.py` | 东方财富涨幅TOP200筛选 | ✅ 已整合 |
| `six_dim_screener.py` | 六维选股器（完整版） | ✅ 已整合 |
| `six_dim_screener_extended.py` | 六维选股器（扩展版） | ✅ 已整合 |
| `short_term_screener.py` | 短线选股器 | ✅ 已整合 |

### 缠论工具

| 文件 | 功能 | 状态 |
|------|------|------|
| `chan_tools.py` | 缠论核心工具 | ✅ 已整合 |
| `chan_analysis.py` | 缠论结构分析 | ✅ 已整合 |
| `chan_beichi.py` | 缠论背驰检测 | ✅ 已整合 |

### 情绪工具

| 文件 | 功能 | 状态 |
|------|------|------|
| `sentiment_realtime.py` | 实时情绪监控 | ✅ 已整合 |
| `sentiment_tool.py` | 情绪分析工具 | ✅ 已整合 |

### 热点工具

| 文件 | 功能 | 状态 |
|------|------|------|
| `hot_topics.py` | 热点题材追踪 | ✅ 已整合 |

---

## 启动脚本参考（start.py）

来源: `H盘 小智×老板交易体系/99-工具/start.py`

### 功能
- 一键完成盘前准备/盘后复盘
- 检查工具就绪状态
- 读取配置文件
- 执行每日任务

### 模式值得借鉴
```
1. check_tools() → 检查所有工具是否就绪
2. load_config() → 读取 config.yaml
3. pre_market() → 盘前：筛选/情绪/热点
4. after_market() → 盘后：复盘/更新股票池
```

### 在 workspace-investment 中的对应
| H盘 start.py | workspace-investment |
|--------------|---------------------|
| check_tools() | 启动时自检 |
| pre_market() | `src/signals/daily_report_generator.py` |
| after_market() | `src/portfolio/daily_report.py` |
| short_term_screener | `src/signals/signal_generator_pro.py` |
| sentiment_tool | `src/skills/sentiment_tracker.py` |

---

## 下一步

建议将 H盘 start.py 的「工具就绪检查」模式融入 workspace-investment 的每日启动流程，参考 `scripts/fetch_market_final.py` 的架构。