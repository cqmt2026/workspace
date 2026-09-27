# Quant ML Framework

专业量化ML训练框架，基于v7修复逻辑重构。

## 目录结构

```
quant_ml/
├── configs/
│   └── config.yaml          # 统一配置（所有参数在此，无需动代码）
├── src/
│   ├── data_pipeline/       # 数据加载 + 清洗
│   │   ├── loader.py        # 从pickle加载K线数据
│   │   └── preprocessor.py  # 数据质量检查
│   ├── features/
│   │   └── factor_zoo.py    # 因子动物园（配置驱动）
│   ├── models/
│   │   └── lightgbm_model.py # LightGBM封装
│   └── training/
│       └── trainer.py        # 训练流程编排
├── logs/                     # 每次运行输出
└── main.py                  # 入口脚本
```

## 使用方法

```bash
# 默认运行（今晚20:00 Cron自动执行）
python quant_ml/main.py

# 指定实验名
python quant_ml/main.py --exp my_experiment

# 指定配置文件
python quant_ml/main.py --config path/to/config.yaml
```

## 配置系统

所有参数集中在 `configs/config.yaml`：

| 配置节 | 内容 |
|--------|------|
| data | 数据源/最小历史/采样间隔/lookahead |
| data.features | 启用哪些因子（ret_periods/vol_periods/macd/kdj等） |
| data.market | 市场因子配置 |
| model.lightgbm | 所有LightGBM超参 |
| training | 分割比例/早停参数 |
| evaluation | 评估指标 |

**修改行为只需改YAML，不需动Python代码。**

## 核心修复（相比v6/v7）

| 问题 | 修复 |
|------|------|
| 早期停止未触发 | 独立早停验证集（10%从训练末尾切） |
| 特征过拟合 | 配置驱动因子选择，移除ret_240d等不稳健特征 |
| 模型过于复杂 | num_leaves=31, max_depth=6, min_child_samples=60 |
| 早停用错数据 | 独立Xes/y_early_stop，不再与最终验证集重叠 |
| 市场状态缺失 | 新增市场因子（等权指数收益率） |
| 配置散落各处 | 统一YAML，代码只读配置 |

## 输出

每次运行生成：
- `logs/<exp_name>/model.txt` - LightGBM模型
- `logs/<exp_name>/results.json` - 训练结果JSON

## 数据依赖

- 975只股票K线（2018-01-02 ~ 2026-05-15）
- 源文件：`workspace-investment/ml_output_v6/all_kline.pkl`
- Loader自动fallback，无需手动配置路径
