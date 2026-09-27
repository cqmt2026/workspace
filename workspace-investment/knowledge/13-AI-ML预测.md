# AI/ML预测模块

**标签**: 机器学习 | 预测 | sklearn
**文件**: `scripts/ml_predictor.py`
**状态**: ✅ 已完成（sklearn验证通过）

---

## 模型说明

| 项目 | 内容 |
|------|------|
| 算法 | GradientBoostingClassifier |
| 特征 | return_1d/5d, mom_5d, vol_ratio, ma5_ratio |
| 目标 | 预测3日后涨跌 |
| 训练样本 | 181个 |

---

## 特征工程

| 特征 | 说明 |
|------|------|
| return_1d | 1日收益率 |
| return_5d | 5日收益率 |
| mom_5d | 5日动量 |
| vol_ratio | 量比（当前/均值） |
| ma5_ratio | 收盘/MA5 |

---

## 使用方法

```python
from ml_predictor import StockMLPredictor

# 训练+预测
predictor = StockMLPredictor('600519')
result = predictor.train()
print(result)
print(predictor.predict())

# 保存/加载
predictor.save()
predictor.load()
```

---

## 限制

1. 需要sklearn库（已安装）
2. 实时数据需要网络连接
3. 模型仅供参考，不构成投资建议