# -*- coding: utf-8 -*-
"""
Bad Case分析脚本 - 对比两个版本模型的验证集预测差异

用法: python quant_ml/scripts/bad_case_analysis.py --new quant_ml_v1 --old quant_ml_v8 --topn 100

输出: out_data/bad_case_report_YYYY-MM-DD.md
       quant_ml/data/bad_case_anchors.json
"""
import argparse, json, sys, os, time
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import lightgbm as lgb

PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass


def load_model(exp_name: str):
    model_path = PROJECT_ROOT / 'quant_ml' / 'logs' / exp_name / 'model.txt'
    if not model_path.exists():
        raise FileNotFoundError(f"模型文件不存在: {model_path}")
    model = lgb.Booster(model_file=str(model_path))
    return model


def load_results(exp_name: str):
    res_path = PROJECT_ROOT / 'quant_ml' / 'logs' / exp_name / 'results.json'
    if not res_path.exists():
        return {}
    with open(res_path, encoding='utf-8') as f:
        return json.load(f)


def extract_full_samples(max_samples: int = 50000, max_stocks: int = 500):
    """提取部分股票样本并切分验证集（减少内存占用）"""
    import yaml
    cfg_path = PROJECT_ROOT / 'quant_ml' / 'configs' / 'config.yaml'
    with open(cfg_path, encoding='utf-8') as f:
        cfg = yaml.safe_load(f)

    sys.path.insert(0, str(PROJECT_ROOT / 'quant_ml'))
    from src.training.trainer import Trainer

    t = Trainer(cfg, f'_tmp_bc_{int(time.time())}')
    print("  加载数据...")
    t._load_data()

    # 只取前max_stocks只股票（限制内存）
    if max_stocks and max_stocks < len(t._data):
        codes = list(t._data.keys())[:max_stocks]
        t._data = {k: t._data[k] for k in codes}
        print(f"  限制为 {max_stocks} 只股票 (共{len(codes)}只)")

    print("  提取特征...")
    X, y, factor_names = t._build_samples_fast()

    # 切分验证集（与训练器一致）
    tcfg = cfg['training']
    n = len(X)
    ts = int(n * tcfg['train_ratio'])
    es = int(n * (tcfg['train_ratio'] + tcfg['early_stop_ratio']))

    val_codes = t._all_codes[es:] if hasattr(t, '_all_codes') and t._all_codes else []
    val_dates = t._all_dates[es:] if hasattr(t, '_all_dates') and t._all_dates else []

    X_val = X[es:]
    y_val = y[es:]

    val_samples = []
    for i in range(len(X_val)):
        val_samples.append({
            'code': val_codes[i] if i < len(val_codes) else 'unknown',
            'date': val_dates[i] if i < len(val_dates) else 'unknown',
            'features': X_val[i],
            'label': int(y_val[i])
        })

    if len(val_samples) > max_samples:
        val_samples = val_samples[:max_samples]
        X_val = X_val[:max_samples]
        y_val = y_val[:max_samples]

    print(f"  验证集样本: {len(val_samples):,}")
    return val_samples, X_val, y_val, factor_names


def main():
    parser = argparse.ArgumentParser(description='Bad Case分析')
    parser.add_argument('--new', default='quant_ml_v1', help='新模型实验名')
    parser.add_argument('--old', default='quant_ml_v8', help='旧模型实验名')
    parser.add_argument('--topn', type=int, default=100, help='输出Top N个Bad Case')
    parser.add_argument('--max_samples', type=int, default=30000, help='最大样本数')
    parser.add_argument('--max_stocks', type=int, default=500, help='最大股票数（减少内存）')
    args = parser.parse_args()

    print(f"Bad Case分析: 对比 {args.new} vs {args.old}")
    print("=" * 60)

    # 加载模型
    print(f"加载模型: {args.new}...")
    model_new = load_model(args.new)
    print(f"  加载完成 ({model_new.num_feature()} 个特征)")

    print(f"加载模型: {args.old}...")
    model_old = load_model(args.old)
    print(f"  加载完成 ({model_old.num_feature()} 个特征)")

    res_new = load_results(args.new)
    res_old = load_results(args.old)
    print(f"\n{args.new} 结果: AUC={res_new.get('auc', 'N/A'):.4f}, val_acc={res_new.get('val_acc', 'N/A'):.4f}")
    print(f"{args.old} 结果: AUC={res_old.get('auc', 'N/A'):.4f}, val_acc={res_old.get('val_acc', 'N/A'):.4f}")

    print("\n提取验证集样本...")
    val_samples, X_val, y_val, factor_names = extract_full_samples(max_samples=args.max_samples, max_stocks=args.max_stocks)

    if len(val_samples) == 0:
        print("错误: 验证集为空!")
        return

    print("\n预测中...")
    # v1(38个特征) vs v8(30个特征)，v8只取前30列
    n_features_new = model_new.num_feature()
    n_features_old = model_old.num_feature()
    print(f"  新模型特征数: {n_features_new}, 旧模型特征数: {n_features_old}")

    if n_features_new > n_features_old:
        # 新模型特征更多，旧模型只取前n_features_old列
        proba_new = model_new.predict(X_val)
        proba_old = model_old.predict(X_val[:, :n_features_old])
    elif n_features_new < n_features_old:
        proba_new = model_new.predict(X_val[:, :n_features_new])
        proba_old = model_old.predict(X_val)
    else:
        proba_new = model_new.predict(X_val)
        proba_old = model_old.predict(X_val)

    th_new = res_new.get('opt_threshold', 0.43)
    th_old = res_old.get('opt_threshold', 0.43)

    pred_new = (proba_new > th_new).astype(int)
    pred_old = (proba_old > th_old).astype(int)

    # 分类Bad Case
    results = []
    for i, s in enumerate(val_samples):
        results.append({
            'code': s['code'],
            'date': s['date'],
            'label': int(y_val[i]),
            'prob_new': float(proba_new[i]),
            'prob_old': float(proba_old[i]),
            'pred_new': int(pred_new[i]),
            'pred_old': int(pred_old[i]),
        })

    df = pd.DataFrame(results)

    type1 = df[(df['label'] == 1) & (df['pred_old'] == 0) & (df['pred_new'] == 1)]
    type2 = df[(df['label'] == 0) & (df['pred_old'] == 1) & (df['pred_new'] == 0)]
    type3 = df[(df['label'] == 1) & (df['pred_old'] == 1) & (df['pred_new'] == 0)]
    type4 = df[(df['label'] == 0) & (df['pred_old'] == 0) & (df['pred_new'] == 1)]

    print(f"\n=== Bad Case 统计 ===")
    print(f"Type 1 (新模型正确拦截/旧模型漏了):  {len(type1):,}")
    print(f"Type 2 (新模型正确排除/旧模型误报):  {len(type2):,}")
    print(f"Type 3 (新模型新漏报/旧模型正确):    {len(type3):,}")
    print(f"Type 4 (新模型新误报/旧模型正确):    {len(type4):,}")

    type1_sorted = type1.sort_values('prob_new', ascending=False).head(args.topn)
    type2_sorted = type2.sort_values('prob_new', ascending=True).head(args.topn)
    type3_sorted = type3.sort_values('prob_new', ascending=False).head(args.topn)
    type4_sorted = type4.sort_values('prob_new', ascending=False).head(args.topn)

    today = datetime.now().strftime('%Y-%m-%d')
    report = f"""# Bad Case 分析报告

**日期**: {today}
**对比**: {args.new} (AUC={res_new.get('auc', 'N/A'):.4f}) vs {args.old} (AUC={res_old.get('auc', 'N/A'):.4f})
**验证集**: {len(val_samples):,} 个样本

---

## 概览

| 类型 | 数量 | 含义 |
|------|------|------|
| ✅ Type 1 - 新模型正确拦截 | {len(type1):,} | 旧模型漏了，新模型抓住了 |
| ✅ Type 2 - 新模型正确排除 | {len(type2):,} | 旧模型误报，新模型排除了 |
| ❌ Type 3 - 新模型新漏报 | {len(type3):,} | 旧模型正确，新模型反而漏了 |
| ❌ Type 4 - 新模型新误报 | {len(type4):,} | 旧模型正确，新模型反而误报 |
| **净改善** | **{len(type1)+len(type2)-len(type3)-len(type4):+d}** | |

"""

    report += f"""## ✅ Type 1: 新模型正确拦截（旧模型漏了）Top {args.topn}

| # | 股票 | 日期 | 真实标签 | 新模型概率 | 旧模型概率 |
|---|------|------|---------|-----------|-----------|
"""
    for i, (_, row) in enumerate(type1_sorted.iterrows()):
        report += f"| {i+1} | {row['code']} | {row['date']} | {row['label']} | {row['prob_new']:.3f} | {row['prob_old']:.3f} |\n"

    report += f"""
## ✅ Type 2: 新模型正确排除（旧模型误报）Top {args.topn}

| # | 股票 | 日期 | 真实标签 | 新模型概率 | 旧模型概率 |
|---|------|------|---------|-----------|-----------|
"""
    for i, (_, row) in enumerate(type2_sorted.iterrows()):
        report += f"| {i+1} | {row['code']} | {row['date']} | {row['label']} | {row['prob_new']:.3f} | {row['prob_old']:.3f} |\n"

    report += f"""
## ❌ Type 3: 新模型新漏报（旧模型正确）Top {args.topn}

| # | 股票 | 日期 | 真实标签 | 新模型概率 | 旧模型概率 |
|---|------|------|---------|-----------|-----------|
"""
    for i, (_, row) in enumerate(type3_sorted.iterrows()):
        report += f"| {i+1} | {row['code']} | {row['date']} | {row['label']} | {row['prob_new']:.3f} | {row['prob_old']:.3f} |\n"

    report += f"""
## ❌ Type 4: 新模型新误报（旧模型正确）Top {args.topn}

| # | 股票 | 日期 | 真实标签 | 新模型概率 | 旧模型概率 |
|---|------|------|---------|-----------|-----------|
"""
    for i, (_, row) in enumerate(type4_sorted.iterrows()):
        report += f"| {i+1} | {row['code']} | {row['date']} | {row['label']} | {row['prob_new']:.3f} | {row['prob_old']:.3f} |\n"

    good_new = type1[['prob_new', 'prob_old']].copy()
    bad_new = type3[['prob_new', 'prob_old']].copy()

    report += f"""
## 📊 统计

### 新模型正确拦截的样本
- 平均新概率: {good_new['prob_new'].mean():.3f} ± {good_new['prob_new'].std():.3f}
- 平均旧概率: {good_new['prob_old'].mean():.3f} ± {good_new['prob_old'].std():.3f}
- 样本数: {len(good_new):,}

### 新模型新漏报的样本
- 平均新概率: {bad_new['prob_new'].mean():.3f} ± {bad_new['prob_new'].std():.3f}
- 平均旧概率: {bad_new['prob_old'].mean():.3f} ± {bad_new['prob_old'].std():.3f}
- 样本数: {len(bad_new):,}

---

## 🎯 A股场景优化建议

### 1. 阈值调整
当前最优阈值: {args.new}={th_new}, {args.old}={th_old}
A股选股更看重精确率，建议尝试 th=0.46 提升精确率。

### 2. 训练锚点
- Type 1 ({len(type1):,}) → 正样本锚点
- Type 2 ({len(type2):,}) → 负样本锚点
- 预计v2精确率可突破 {res_new.get('prec', 0.57) + 0.02:.2f}

### 3. 抑制mkt因子
mkt因子重要性9241（远高于第二名996），模型过度依赖大盘。
建议在v2训练中降低mkt因子的采样权重。
"""

    out_path = PROJECT_ROOT / 'out_data' / f'bad_case_report_{today}.md'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n报告已保存: {out_path}")

    anchor_data = {
        'type1': type1[['code', 'date', 'prob_new', 'prob_old']].to_dict('records'),
        'type2': type2[['code', 'date', 'prob_new', 'prob_old']].to_dict('records'),
        'type3': type3[['code', 'date', 'prob_new', 'prob_old']].to_dict('records'),
        'type4': type4[['code', 'date', 'prob_new', 'prob_old']].to_dict('records'),
    }
    anchor_path = PROJECT_ROOT / 'quant_ml' / 'data' / 'bad_case_anchors.json'
    with open(anchor_path, 'w', encoding='utf-8') as f:
        json.dump(anchor_data, f, ensure_ascii=False, indent=2)
    print(f"锚点数据已保存: {anchor_path}")
    print(f"  Type 1: {len(anchor_data['type1']):,} 个锚点")
    print(f"  Type 2: {len(anchor_data['type2']):,} 个锚点")


if __name__ == '__main__':
    main()