# 投资数据获取渠道清单

**检查时间**: 2026-04-06 22:35  
**来源**: H:\.openclaw 现有资源

---

## 📊 已确认的数据获取渠道

### 1. efinance（已使用）✅

**状态**: 已集成（模拟数据）  
**数据类型**: A 股实时数据  
**更新频率**: 每日 01:00 自动更新  
**数据内容**:
- 成交量前 200 股票
- 板块分布
- 实时行情

**证据**:
```
H:\.openclaw\reports\realtime_volume_data_report_20260318_*.md
数据源：efinance（模拟）
```

**用途**: 双策略选股（尾盘选股 + 趋势跟踪）

---

### 2. AKShare（推荐）✅

**状态**: 已在策略工厂集成  
**数据类型**: A 股/港股/美股/宏观/期货/期权  
**特点**: 
- 完全免费
- 数据全面
- 文档完善

**已实现功能**:
```python
# 策略工厂已集成
src/loaders/data_loader.py
- AKShareLoader.load_market_data()  # A 股历史数据
- AKShareLoader.load_macro_data()   # 宏观数据（CPI/PPI/M2/社融）
```

---

### 3. Yahoo Finance（推荐）✅

**状态**: 已在策略工厂集成  
**数据类型**: 美股/港股/国际指数  
**特点**:
- 免费
- 覆盖全球市场
- 历史数据完整

**已实现功能**:
```python
# 策略工厂已集成
src/loaders/data_loader.py
- YahooFinanceLoader.load_market_data()  # 美股/港股数据
```

---

## 📈 现有数据资源

### 1. 股票池管理
**文件**: `stock_pool.json`
- core: 核心持仓
- focus: 重点关注
- observation: 观察池
- reserve: 备选池
- watchlist: 自选列表

### 2. 实时数据
**文件**: `volume_top200_20260318.json` (40KB)
- 成交量前 200 股票
- 板块分布统计

### 3. 历史数据
**文件**: 
- `600602.csv` (2KB) - 个股 OHLCV
- `archive/2026-03/history_data.zip` (20KB) - 历史数据归档

### 4. 交易数据
**文件**:
- `positions.json` - 当前持仓
- `trade_log.json` - 交易记录
- `conditional_orders.json` - 条件单

---

## 🔧 数据获取代码示例

### AKShare（A 股数据）
```python
import akshare as ak

# 获取 A 股历史数据
df = ak.stock_zh_a_hist(
    symbol="000001",
    period="daily",
    start_date="20240101",
    end_date="20241231",
    adjust="qfq"
)

# 获取宏观数据
cpi = ak.macro_china_cpi()
ppi = ak.macro_china_ppi()
m2 = ak.macro_china_money_supply()
```

### Yahoo Finance（美股/港股）
```python
import yfinance as yf

# 获取美股数据
ticker = yf.Ticker("AAPL")
df = ticker.history(start="2024-01-01", end="2024-12-31")

# 获取港股数据
ticker = yf.Ticker("0700.HK")
df = ticker.history(start="2024-01-01")
```

### efinance（实时数据）
```python
import efinance as ef

# 获取实时行情
quotes = ef.stock.get_latest_stock_info()

# 获取成交量排名
volume_rank = ef.stock.get_stock_volume_rank()
```

---

## 📋 策略工厂数据获取方案

### 数据入口层架构
```
src/loaders/
├─ data_loader.py          # 数据加载器基类
├─ akshare_loader.py       # AKShare 数据源 ✅
├─ yahoo_loader.py         # Yahoo Finance 数据源 ✅
├─ efinance_loader.py      # efinance 实时数据 ⏳
└─ crypto_loader.py        # 加密货币数据 ⏳
```

### 数据流
```
数据源 → 数据加载器 → 原始数据 (data/raw/)
                  ↓
         数据清洗/处理
                  ↓
         处理后数据 (data/processed/)
                  ↓
         信号生成层
```

---

## 🎯 建议整合步骤

### 第一步：确认可用数据源
1. ✅ AKShare - 已集成，可立即使用
2. ✅ Yahoo Finance - 已集成，可立即使用
3. ⏳ efinance - 需要确认是否真实可用（当前为模拟数据）

### 第二步：测试数据获取
```bash
cd workspace-investment
python src/loaders/data_loader.py  # 测试 AKShare
python src/signals/signal_generator.py  # 测试信号生成
python src/backtests/backtest_engine.py  # 测试回测
```

### 第三步：整合现有数据
```bash
# 复制 H 盘数据到策略工厂
H:\.openclaw\workspace\stock_pool.json → workspace-investment/data/processed/
H:\.openclaw\workspace\600602.csv → workspace-investment/data/raw/
H:\.openclaw\data\volume_top200_*.json → workspace-investment/data/raw/
```

---

## 📊 数据获取渠道总结

| 数据源 | 状态 | 市场 | 费用 | 策略工厂集成 |
|--------|------|------|------|-------------|
| **AKShare** | ✅ 可用 | A 股/宏观 | 免费 | ✅ 已完成 |
| **Yahoo Finance** | ✅ 可用 | 美股/港股 | 免费 | ✅ 已完成 |
| **efinance** | ⚠️ 模拟 | A 股实时 | 免费 | ⏳ 待确认 |
| **聚宽** | ⏳ 未测试 | A 股 | 免费+付费 | ❌ 未集成 |
| **Tushare** | ⏳ 未测试 | A 股 | 积分制 | ❌ 未集成 |

---

**结论**: 策略工厂已集成 AKShare 和 Yahoo Finance 两个免费数据源，可以立即开始获取市场数据！
