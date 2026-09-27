# Scripts Modules 使用指南

> 百都科技销售系统核心模块
> 最后更新：2026-09-06

---

## 📦 模块清单

| 模块文件 | 功能 | 调用方式 |
|---------|------|---------|
| `pipeline_analyzer.py` | Pipeline健康诊断、收入预测 | `generate_pipeline_health_report()` |
| `report_generator.py` | 日报/周报/月报自动生成 | `generate_daily_report()` |
| `baidu_seo_audit.py` | 百度SEO审计、GEO优化指南 | `generate_seo_report(company, industry)` |
| `spin_coach.py` | SPIN提问框架、MEDDPICC评分 | `generate_discovery_script()`, `calculate_meddpicc_score()` |
| `signal_based_dialing.py` | 信号驱动外呼策略 | `generate_signal_based_list(n)` |
| `ab_test.py` | A/B测试框架 | `create_ab_test()`, `get_test_results()` |
| `private_domain_ops.py` | 私域运营流程 | `generate_private_domain_plan()` |

---

## 🚀 快速开始

### 1. Pipeline健康诊断
```python
from scripts.modules.pipeline_analyzer import generate_pipeline_health_report, forecast_revenue

# 生成诊断报告
report = generate_pipeline_health_report()
print(report['velocity_metrics'])
print(report['coverage_analysis'])

# 收入预测
forecast = forecast_revenue(period_days=30)
print(f"Commit: {forecast['commit']:.0f}元")
```

### 2. 自动报表生成
```python
from scripts.modules.report_generator import generate_daily_report, generate_weekly_report, generate_monthly_report

# 生成今日日报
generate_daily_report()  # 保存到 memory/logs/daily_YYYY-MM-DD.md

# 生成周报
generate_weekly_report()  # 保存到 memory/logs/weekly_YYYY-MM-DD.md

# 生成月报
generate_monthly_report()  # 保存到 memory/logs/monthly_YYYY-MM.md
```

### 3. 百度SEO审计
```python
from scripts.modules.baidu_seo_audit import generate_seo_report

# 生成SEO审计报告
report = generate_seo_report('重庆XX医院', '口腔医疗')
print(report)
# 自动保存到 output/seo_report_YYYYMMDD.md
```

### 4. SPIN销售教练
```python
from scripts.modules.spin_coach import generate_discovery_script, calculate_meddpicc_score

# 生成SPIN话术
script = generate_discovery_script('口腔', '获客')
print(script)

# MEDDPICC评分
customer_data = {
    'budget_confirmed': True,
    'decision_maker': True,
    'pain_quantified': False,
    # ...
}
score = calculate_meddpicc_score(customer_data)
print(f"健康度: {score['health_level']}")
```

### 5. 信号驱动外呼
```python
from scripts.modules.signal_based_dialing import generate_signal_based_list

# 生成高优先级外呼清单（Top 20）
top_signals = generate_signal_based_list(20)
for signal in top_signals:
    print(f"{signal['customer_name']} - 信号分: {signal['signal_score']:.1f}")
```

### 6. A/B测试
```python
from scripts.modules.ab_test import create_ab_test, get_test_results

# 创建测试
test_id = create_ab_test(
    test_name="开场白A/B测试",
    script_a="数据驱动型开场白...",
    script_b="痛点切入型开场白...",
    target_customers=100
)

# 获取结果
results = get_test_results(test_id)
print(f"获胜方: {results['winner']}")
print(f"差异: {results['difference']}")
```

### 7. 私域运营
```python
from scripts.modules.private_domain_ops import generate_private_domain_plan

# 生成私域运营计划
plan = generate_private_domain_plan()
print(plan)
# 自动保存到 output/private_domain_plan_YYYYMMDD.md
```

---

## 📊 输出文件位置

```
workspace-baiduagent/
├── memory/logs/
│   ├── daily_YYYY-MM-DD.md      # 日报
│   ├── weekly_YYYY-MM-DD.md     # 周报
│   └── monthly_YYYY-MM.md       # 月报
├── output/
│   ├── seo_report_YYYYMMDD.md   # SEO审计报告
│   └── private_domain_plan_YYYYMMDD.md  # 私域运营计划
└── data/
    └── ab_test_*.json           # A/B测试配置
```

---

## ⚠️ 注意事项

1. **数据库依赖**：所有模块依赖 `data/baidu_crm.db`，确保数据库存在
2. **编码问题**：Windows环境下如需打印emoji，添加 `sys.stdout.reconfigure(encoding='utf-8')`
3. **数据质量**：模块效果依赖CRM数据质量，确保通话记录完整录入
4. **首次运行**：部分模块需要首次运行生成配置，后续自动读取

---

## 🔧 故障排查

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| `no such table: leads` | 数据库表缺失 | 运行 `python scripts/core/init_db.py` |
| 分析0个客户 | 无通话记录 | 先录入通话数据后再分析 |
| 报表生成失败 | 路径问题 | 检查 `memory/logs/` 目录是否存在 |

---

_由小度维护 | 2026-09-06_
