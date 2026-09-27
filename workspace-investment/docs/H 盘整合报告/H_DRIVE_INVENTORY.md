# H:\.openclaw 投资相关资源清单

**检查时间**: 2026-04-06 22:30  
**目的**: 寻找对投资分析策略工厂有用的文档和数据

---

## 📊 核心投资数据

### 1. 股票池管理
**文件**: `stock_pool.json` (497 bytes)
```json
{
  "core": [],        // 核心持仓
  "focus": [],       // 重点关注
  "observation": [], // 观察池
  "reserve": [],     // 备选池
  "watchlist": []    // 自选列表
}
```
**用途**: 策略工厂的股票池管理参考

---

### 2. 持仓数据
**文件**: `positions.json` (720 bytes)
- 当前持仓：2 只股票
- 示例：`{'code': '002837', 'name': '英维克', 'entry_price': 100.86, 'entry_date': '2026-03-16'}`

**用途**: 持仓管理模块参考

---

### 3. 交易记录
**文件**: `trade_log.json` (668 bytes)
- 交易记录：3 条
- 示例：`{'order_id': 1, 'code': '000591', 'name': '太阳能', 'action': 'sell', 'shares': 1000, 'price': 6.8}`

**用途**: 交易记录格式参考，反馈层数据源

---

### 4. 条件单
**文件**: `conditional_orders.json` (1,492 bytes)
- 条件单：4 个
- 示例：`{'id': 1, 'code': '000591', 'condition_type': 'price_above', 'trigger_price': 6.8}`

**用途**: 条件单系统参考，策略执行层参考

---

## 📈 市场数据

### 1. 成交量数据
**文件**: `H:\.openclaw\data\volume_top200_20260318.json` (40KB)
- 数据结构：`{'time', 'data_source', 'total', 'stocks'}`
- 内容：成交量前 200 只股票数据

**用途**: 数据入口层测试数据，成交量信号验证

---

### 2. 个股历史数据
**文件**: `600602.csv` (2KB)
- 列：`date, open, close, high, low, volume, amount`
- 数据范围：2026-01 起

**用途**: 回测引擎测试数据

---

### 3. 实时成交量报告
**文件**: `H:\.openclaw\reports\realtime_volume_data_report_*.md` (3 份)
- 采集时间：2026-03-18
- 数据源：efinance
- 内容：成交量前 10 名股票

**用途**: 报告生成层参考格式

---

## 📁 归档数据

### 1. 历史数据
**文件**: `archive/2026-03/history_data.zip` (20KB)
**用途**: 可能需要解压用于回测

### 2. 回测结果
**文件**: `backtest/backtest_20260309_131904.json` (2KB)
**用途**: 回测结果格式参考

### 3. 归档索引
**文件**: `archive/2026-03/ARCHIVE_INDEX.json` (3KB)
**用途**: 了解归档内容结构

---

## 🔧 可复用组件

### 1. 策略优化配置
**文件**: `策略优化配置.json`
**用途**: 策略参数优化参考

### 2. 系统状态
**文件**: `.openclaw/workspace-state.json`
**用途**: 系统状态管理参考

---

## 💡 对策略工厂的价值

### 数据入口层
- ✅ 已有股票池管理格式参考
- ✅ 已有成交量数据格式
- ✅ 已有个股 CSV 数据格式

### 信号生成层
- ✅ 可复用成交量数据分析逻辑

### 规则层
- ✅ 条件单系统可参考
- ✅ 持仓管理逻辑可参考

### 验证层
- ✅ 已有回测结果格式参考
- ✅ 已有历史数据可供测试

### 反馈层
- ✅ 交易记录格式可直接使用
- ✅ 持仓数据格式可直接使用

---

## 📋 建议整合步骤

1. **复制现有数据格式**
   - stock_pool.json → data/processed/stock_pools/
   - positions.json → outputs/logs/positions.json
   - trade_log.json → outputs/logs/trades.json

2. **利用现有测试数据**
   - 600602.csv → data/raw/测试数据
   - volume_top200_*.json → data/raw/成交量数据

3. **参考现有格式**
   - 条件单系统 → 策略执行层参考
   - 回测结果 → 回测报告格式参考

4. **整合现有逻辑**
   - 如果有现有策略代码，可参考其规则定义方式

---

**总结**: H:\.openclaw 包含完整的投资交易系统雏形，可直接作为策略工厂的参考和测试数据源！
