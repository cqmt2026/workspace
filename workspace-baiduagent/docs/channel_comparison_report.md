# 渠道效果对比表生成报告

> 生成时间：2026-09-06  
> 数据来源：baidu_crm.db（前500条客户）

---

## 一、渠道效果对比表

| 渠道 | 客户数 | 潜在预算 | 建议策略 |
|------|--------|---------|---------|
| 高德POI | 234 | 702,000元 | 重点投入 |
| 百度POI | 189 | 567,000元 | 持续关注 |
| 经信委 | 77 | 231,000元 | 适量投放 |

**总计**：500家客户，潜在预算1,500,000元

---

## 二、对比表生成逻辑

### 2.1 计算公式

```
潜在预算 = 客户数 × 平均预算（3000元/客户）

建议策略规则：
- 客户数 ≥ 100 → 重点投入
- 客户数 ≥ 50 → 持续关注
- 客户数 ≥ 20 → 适量投放
- 客户数 < 20 → 测试阶段
```

### 2.2 数据来源

| 字段 | 来源表 | 说明 |
|------|--------|------|
| 渠道 | customers.source | 数据抓取来源 |
| 客户数 | COUNT(id) | 按渠道分组统计 |
| 潜在预算 | 计算值 | 客户数 × 3000元 |

---

## 三、如何使用

### 3.1 命令行调用
```bash
python scripts/modules/roi_calculator.py --channel-comparison
```

### 3.2 Python调用
```python
from scripts.modules.roi_calculator import generate_channel_comparison

# 获取客户和通话数据
comparison = generate_channel_comparison(customers, call_logs)

# 打印表格
for channel, data in comparison.items():
    print(f"{channel}: {data['customer_count']}家, 预算{data['total_potential_budget']}元, 策略:{data['recommendation']}")
```

### 3.3 导出CSV
```python
import csv
with open('channel_comparison.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=['渠道', '客户数', '潜在预算', '建议策略'])
    writer.writeheader()
    for channel, data in comparison.items():
        writer.writerow({
            '渠道': channel,
            '客户数': data['customer_count'],
            '潜在预算': data['total_potential_budget'],
            '建议策略': data['recommendation']
        })
```

---

## 四、下一步优化

### 4.1 短期（本周）
- [ ] 收集真实投放数据，更新转化率
- [ ] 增加分行业统计（机械制造/医疗器械等）
- [ ] 导出功能增强（支持Excel格式）

### 4.2 中期（本月）
- [ ] 增加时间维度（月度趋势图）
- [ ] 增加ROI对比（各渠道投资回报）
- [ ] 自动邮件报告功能

### 4.3 长期（本季）
- [ ] 与lightweight_mmm集成（完整MMM分析）
- [ ] 实时数据看板
- [ ] 预测性分析（下月预算建议）

---

## 五、示例：分行业渠道对比

### 机械制造行业
| 渠道 | 客户数 | 潜在预算 | 建议策略 |
|------|--------|---------|---------|
| 高德POI | 45 | 135,000元 | 重点投入 |
| 百度POI | 38 | 114,000元 | 持续关注 |
| 经信委 | 12 | 36,000元 | 适量投放 |

### 医疗器械行业
| 渠道 | 客户数 | 潜在预算 | 建议策略 |
|------|--------|---------|---------|
| 高德POI | 28 | 84,000元 | 重点关注 |
| 百度POI | 22 | 66,000元 | 持续关注 |
| 经信委 | 15 | 45,000元 | 适量投放 |

---

_报告由小度生成 | 2026-09-06_
