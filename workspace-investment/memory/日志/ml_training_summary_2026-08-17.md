# ML训练摘要 - 2026-08-17 20:00

## 执行时间
- 触发时间：20:00
- 完成时间：21:00
- 总耗时：1406.8秒（约23分钟）

## 训练结果
| 指标 | 数值 |
|------|------|
| AUC | 0.6976 |
| 验证准确率 | 58.47% |
| F1分数 | 0.6783 |
| 精确率 | 54.86% |
| 召回率 | 88.86% |
| 过拟合差距 | 0.64% |
| 评级 | A |

## 执行步骤
1. ✅ `run_train.py` - 模型训练完成（500轮，LightGBM）
2. ✅ `ml_factor_bridge.py` - 因子写入完成（1044条）
3. ✅ `run_ml_predict.py` - 预测执行完成
4. ✅ `ml_factor_bridge.py` - 第二轮因子桥接完成

## 数据概况
- 训练样本：1,085,134个
- 股票数量：4394只
- 正样本率：48.67%
- 特征数量：38个

## 输出文件
- `quant_ml/logs/quant_ml_v1/results.json`
- `quant_ml/logs/quant_ml_v1/model.txt`
- `quant_ml/logs/quant_ml_v1/feature_importance.json`
- `quant_ml/logs/quant_ml_v1/train_run.log`
