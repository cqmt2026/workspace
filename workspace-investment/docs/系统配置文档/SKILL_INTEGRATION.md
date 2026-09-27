# 投资分析策略工厂 - Skill 整合方案

**整合时间**: 2026-04-06 22:38  
**状态**: 🚧 整合中

---

## 📊 9 个核心 Skill 清单

### 【核心分析类】

| Skill | 功能 | 整合优先级 | 用途 |
|-------|------|-----------|------|
| **investment-analyst** | 投资分析 Agent | ⭐⭐⭐ | 股票/基金/市场数据分析 |
| **data-analysis-litiao** | 数据分析 | ⭐⭐⭐ | 统计分析/方法论/风险评估 |

### 【数据获取类】

| Skill | 功能 | 整合优先级 | 用途 |
|-------|------|-----------|------|
| **web-hot** | 全网热搜 | ⭐⭐ | 微博/知乎/百度/抖音/B 站热搜 |
| **hot-topic-finder** | 热点发现 | ⭐⭐ | 跨平台热点追踪 |
| **baidu-search** | 百度搜索 | ⭐⭐ | 实时信息获取 |
| **multi-search-engine** | 多搜索引擎 | ⭐⭐ | 17 个搜索引擎（8 中 +9 国际） |
| **smart-web-scraper** | 网页爬取 | ⭐⭐ | 结构化数据提取 |

### 【报告生成类】

| Skill | 功能 | 整合优先级 | 用途 |
|-------|------|-----------|------|
| **excel-xlsx** | Excel 处理 | ⭐ | 数据表格处理 |
| **minimax-xlsx** | 电子表格生成 | ⭐ | 数据报表生成 |

---

## 🔧 整合架构

### 策略工厂 + Skill 集成

```
策略工厂 (workspace-investment/)
├─ src/
│  ├─ loaders/              # 数据加载层
│  │  ├─ data_loader.py    # AKShare/YahooFinance
│  │  └─ skill_loader.py   # Skill 数据获取 ⭐新增
│  │
│  ├─ signals/              # 信号生成层
│  │  ├─ signal_generator.py
│  │  └─ sentiment_signal.py # 市场情绪信号 ⭐新增
│  │
│  ├─ strategies/           # 策略定义层
│  │  └─ strategy_definition.py
│  │
│  ├─ backtests/            # 验证层
│  │  └─ backtest_engine.py
│  │
│  └─ reports/              # 反馈层 ⭐新增
│     ├─ performance_tracker.py
│     └─ report_generator.py # 整合 excel-xlsx/minimax-xlsx
│
├─ skills/                   # Skill 集成 ⭐新增
│  ├─ investment_analyst.py
│  ├─ data_analysis.py
│  ├─ web_hot.py
│  ├─ hot_topic_finder.py
│  ├─ multi_search.py
│  └─ web_scraper.py
│
└─ outputs/
   ├─ charts/
   ├─ logs/
   └─ reports/              # Skill 生成报告
```

---

## 💻 Skill 调用代码示例

### 1. investment-analyst

```python
# src/skills/investment_analyst.py

def analyze_stock(symbol: str) -> dict:
    """
    使用 investment-analyst 分析股票
    
    Args:
        symbol: 股票代码
        
    Returns:
        分析结果字典
    """
    # 调用 Skill
    result = {
        'symbol': symbol,
        'analysis': {
            'fundamental': '基本面分析结果',
            'technical': '技术面分析结果',
            'sentiment': '市场情绪',
            'risk': '风险评估'
        }
    }
    return result

# 使用示例
result = analyze_stock('000001.SZ')
print(f"{result['symbol']} 分析完成")
```

---

### 2. data-analysis-litiao

```python
# src/skills/data_analysis.py

def analyze_risk(data: pd.DataFrame) -> dict:
    """
    使用 data-analysis-litiao 进行风险评估
    
    Args:
        data: 历史数据
        
    Returns:
        风险评估结果
    """
    # 统计分析
    stats = {
        'mean': data.mean(),
        'std': data.std(),
        'skewness': data.skew(),
        'kurtosis': data.kurtosis()
    }
    
    # 风险评估
    risk = {
        'volatility': stats['std'],
        'max_drawdown': (data.cummax() - data).max() / data.cummax().max(),
        'var_95': data.quantile(0.05)
    }
    
    return {
        'stats': stats,
        'risk': risk,
        'methodology': '统计分析 + 历史回测'
    }
```

---

### 3. web-hot + hot-topic-finder

```python
# src/skills/sentiment_tracker.py

def get_market_sentiment() -> dict:
    """
    获取市场情绪（整合 web-hot 和 hot-topic-finder）
    
    Returns:
        市场情绪指标
    """
    sentiment = {
        'weibo': {
            'hot_search': ['财经热搜 1', '财经热搜 2'],
            'sentiment_score': 0.6  # 正面情绪
        },
        'zhihu': {
            'hot_topics': ['投资话题 1', '投资话题 2'],
            'discussion_volume': 10000
        },
        'baidu': {
            'search_index': 8500,
            'trend': '上升'
        }
    }
    
    # 综合情绪评分
    composite_score = (
        sentiment['weibo']['sentiment_score'] * 0.4 +
        sentiment['zhihu']['discussion_volume'] / 10000 * 0.3 +
        sentiment['baidu']['search_index'] / 10000 * 0.3
    )
    
    return {
        'raw': sentiment,
        'composite_score': composite_score,
        'signal': 'bullish' if composite_score > 0.5 else 'bearish'
    }
```

---

### 4. multi-search-engine + smart-web-scraper

```python
# src/skills/data_collector.py

def collect_financial_news(symbols: list, days: int = 7) -> list:
    """
    收集财经新闻（整合 multi-search-engine 和 smart-web-scraper）
    
    Args:
        symbols: 股票代码列表
        days: 天数
        
    Returns:
        新闻列表
    """
    news = []
    
    for symbol in symbols:
        # 多引擎搜索
        search_results = multi_search(
            query=f"{symbol} 公告 新闻",
            time_range=f"过去{days}天",
            engines=['baidu', 'google', 'bing']
        )
        
        # 爬取详细内容
        for result in search_results[:10]:
            content = scrape_webpage(result['url'])
            news.append({
                'symbol': symbol,
                'title': result['title'],
                'content': content,
                'date': result['date'],
                'source': result['source']
            })
    
    return news
```

---

### 5. excel-xlsx + minimax-xlsx

```python
# src/reports/report_generator.py

def generate_strategy_report(backtest_results: dict, output_path: str):
    """
    生成策略报告（整合 excel-xlsx 和 minimax-xlsx）
    
    Args:
        backtest_results: 回测结果
        output_path: 输出路径
    """
    import pandas as pd
    
    # 创建 Excel 报告
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # 回测结果
        pd.DataFrame(backtest_results['trades']).to_excel(
            writer, sheet_name='交易记录'
        )
        
        # 权益曲线
        backtest_results['equity_curve'].to_excel(
            writer, sheet_name='权益曲线'
        )
        
        # 绩效指标
        metrics = pd.DataFrame({
            '指标': ['总收益', '年化收益', '最大回撤', '夏普比率'],
            '数值': [
                backtest_results['total_return'],
                backtest_results['annual_return'],
                backtest_results['max_drawdown'],
                backtest_results['sharpe_ratio']
            ]
        })
        metrics.to_excel(writer, sheet_name='绩效指标', index=False)
    
    print(f"报告已生成：{output_path}")
```

---

## 📋 整合步骤

### 第一步：创建 Skill 集成目录

```bash
cd workspace-investment
mkdir -p src/skills
mkdir -p src/reports
touch src/skills/__init__.py
touch src/reports/__init__.py
```

### 第二步：实现 Skill 调用代码

1. `src/skills/investment_analyst.py` - 投资分析
2. `src/skills/data_analysis.py` - 数据分析
3. `src/skills/sentiment_tracker.py` - 市场情绪
4. `src/skills/data_collector.py` - 数据收集
5. `src/reports/report_generator.py` - 报告生成

### 第三步：更新数据入口层

```python
# src/loaders/skill_loader.py

from skills.investment_analyst import analyze_stock
from skills.sentiment_tracker import get_market_sentiment
from skills.data_collector import collect_financial_news

class SkillDataLoader:
    """Skill 数据加载器"""
    
    def load_stock_analysis(self, symbol: str) -> dict:
        return analyze_stock(symbol)
    
    def load_market_sentiment(self) -> dict:
        return get_market_sentiment()
    
    def load_news(self, symbols: list, days: int = 7) -> list:
        return collect_financial_news(symbols, days)
```

### 第四步：更新信号生成层

```python
# src/signals/sentiment_signal.py

from skills.sentiment_tracker import get_market_sentiment

def generate_sentiment_signal() -> dict:
    """
    生成市场情绪信号
    """
    sentiment = get_market_sentiment()
    
    return {
        'composite_score': sentiment['composite_score'],
        'signal': sentiment['signal'],
        'weibo_sentiment': sentiment['raw']['weibo']['sentiment_score'],
        'zhihu_volume': sentiment['raw']['zhihu']['discussion_volume'],
        'baidu_trend': sentiment['raw']['baidu']['trend']
    }
```

### 第五步：测试整合

```bash
# 测试 Skill 调用
python src/skills/investment_analyst.py
python src/skills/sentiment_tracker.py
python src/reports/report_generator.py
```

---

## 🎯 整合后的能力

| 层级 | 新增能力 | 来源 Skill |
|------|---------|-----------|
| **数据入口层** | 市场情绪数据 | web-hot, hot-topic-finder |
| **数据入口层** | 新闻/公告收集 | multi-search-engine, smart-web-scraper |
| **信号生成层** | 情绪信号 | web-hot, hot-topic-finder |
| **规则层** | 风险评估 | data-analysis-litiao, investment-analyst |
| **反馈层** | 报告生成 | excel-xlsx, minimax-xlsx |

---

## 📊 整合优先级

| 优先级 | Skill | 工作量 | 价值 |
|--------|-------|--------|------|
| **P0** | investment-analyst | 低 | 高 |
| **P0** | data-analysis-litiao | 低 | 高 |
| **P1** | web-hot | 中 | 中 |
| **P1** | hot-topic-finder | 中 | 中 |
| **P2** | multi-search-engine | 中 | 中 |
| **P2** | smart-web-scraper | 中 | 中 |
| **P3** | excel-xlsx | 低 | 低 |
| **P3** | minimax-xlsx | 低 | 低 |

---

**开始整合 9 个 Skill 到投资分析策略工厂！** 🌸
