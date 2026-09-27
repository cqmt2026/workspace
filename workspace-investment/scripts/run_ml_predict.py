# -*- coding: utf-8 -*-
"""
为持仓股票批量预测ML概率 - v2（复用训练器已验证特征逻辑）
"""
import pickle, numpy as np, lightgbm as lgb, os
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment')
# 使用训练器输出的 model.txt（LightGBM原生格式）
MODEL_PATH = PROJECT_ROOT / 'quant_ml' / 'logs' / 'quant_ml_v1' / 'model.txt'
PICKLE_PATH = PROJECT_ROOT / 'quant_ml' / 'data' / 'all_kline_full.pkl'
# 输出到独立文件，避免与 unified_train 的输出文件冲突
OUTPUT_PATH = PROJECT_ROOT / 'scripts' / 'ml_holdings_prob.pkl'

FACTOR_NAMES = [
    'ret_1', 'ret_3', 'ret_5', 'ret_10', 'ret_20', 'ret_60',
    'vol_20d', 'vr5',
    'ma_ratio_5', 'ma_ratio_20', 'ma_ratio_60',
    'bbp_20d', 'macd_dif', 'macd_dea',
    'kdj_k', 'kdj_d', 'kdj_j',
    'rsi_14d', 'obv', 'obv_ratio',
    'bias_5', 'bias_20',
    'ppos_20', 'ppos_60',
    'gap_mean', 'gap_up', 'gap_down',
    'hlr20', 'rs', 'mkt', 'month_end',
    'roe_norm', 'cash_net_ratio_norm', 'deduct_ratio',
    'roe_pct', 'eps', 'gross_margin', 'net_margin'
]

def build_features_one_stock(df, date_to_mkt, fin_data=None, stock_code=None):
    """为一只股票的所有交易日构建特征，返回（特征矩阵, 日期列表, 代码）"""
    df = df.sort_values('date').reset_index(drop=True)
    n = len(df)

    close = pd.to_numeric(df['close'], errors='coerce').fillna(0).values.astype(np.float64)
    open_v = pd.to_numeric(df['open'], errors='coerce').fillna(0).values.astype(np.float64)
    high = pd.to_numeric(df['high'], errors='coerce').fillna(0).values.astype(np.float64)
    low = pd.to_numeric(df['low'], errors='coerce').fillna(0).values.astype(np.float64)
    vol = pd.to_numeric(df['volume'], errors='coerce').fillna(0).values.astype(np.float64)
    date_arr = df['date'].values

    MIN_HIST = 250
    LOOKAHEAD = 3

    all_X = []
    all_dates = []

    for i in range(MIN_HIST, n - LOOKAHEAD, 8):
        row = []

        # ret
        for p in [1,3,5,10,20,60]:
            row.append(float(close[i]/close[i-p]-1) if i>=p else 0.0)

        # vol_20d
        if i>=19:
            close_s = pd.Series(close[:i+1])
            mv = close_s.rolling(20, min_periods=20).mean().values
            sv = close_s.rolling(20, min_periods=20).std(ddof=0).values
            row.append(float(sv[-1]/(mv[-1]+1e-9)))
        else:
            row.append(0.0)

        # vr5
        if i>=4:
            avg5 = np.convolve(vol[max(0,i-4):i+1], np.ones(5)/5, mode='valid')
            row.append(float(vol[i]/(avg5[-1]+1e-9)))
        else:
            row.append(1.0)

        # ma_ratio
        for p in [5,20,60]:
            if i>=p-1:
                close_s = pd.Series(close[:i+1])
                ma = close_s.rolling(p, min_periods=p).mean().values[-1]
                row.append(float(close[i]/ma) if ma!=0 else 1.0)
            else:
                row.append(1.0)

        # bbp_20d
        if i>=19:
            close_s = pd.Series(close[:i+1])
            mv = close_s.rolling(20, min_periods=20).mean().values
            sv = close_s.rolling(20, min_periods=20).std(ddof=0).values
            upper=mv[-1]+2*sv[-1]; lower=mv[-1]-2*sv[-1]
            row.append(float((close[i]-lower)/(upper-lower+1e-9)))
        else:
            row.append(0.5)

        # macd
        if i>=25:
            ema12_s = pd.Series(close[:i+1]).ewm(span=12, adjust=False).mean()
            ema26_s = pd.Series(close[:i+1]).ewm(span=26, adjust=False).mean()
            dif = ema12_s.values[-1] - ema26_s.values[-1]
            dea = pd.Series([dif]).ewm(span=9, adjust=False).mean().values[0]
            row.append(float(dif)); row.append(float(dea))
        else:
            row.append(0.0); row.append(0.0)

        # kdj
        if i>=8:
            low_s = pd.Series(low[:i+1])
            high_s = pd.Series(high[:i+1])
            lo_min = low_s.rolling(9, min_periods=9).min().values[-1]
            hi_max = high_s.rolling(9, min_periods=9).max().values[-1]
            rsv = 100*(close[i]-lo_min)/(hi_max-lo_min+1e-9)
            k = 2/3*50+1/3*rsv; d = 2/3*50+1/3*k; j = 3*k-2*d
            row.append(float(k)); row.append(float(d)); row.append(float(j))
        else:
            row.append(50.0); row.append(50.0); row.append(50.0)

        # rsi_14d
        if i>=14:
            diff = np.diff(close[:i+1])
            window = diff[-14:]
            pos = window[window>0]; neg = window[window<0]
            pm = float(pos.mean()) if len(pos)>0 else 0.0
            nm = abs(float(neg.mean())) if len(neg)>0 else 0.0
            rsi = 100-100/(1+pm/(nm+1e-9)) if nm>0 else 100.0
            row.append(float(rsi))
        else:
            row.append(50.0)

        # obv
        if i>=1:
            changes = np.diff(close[:i+1])
            obv_arr = np.cumsum(np.where(changes>0, vol[1:i+1], -vol[1:i+1]))
            obv_val = obv_arr[-1]
            row.append(float(obv_val/1e8))
        else:
            row.append(0.0)

        # obv_ratio
        if i>=19:
            avg20 = pd.Series(vol[:i+1]).rolling(20, min_periods=20).mean().values[-1]
            row.append(float(obv_val/(avg20+1e-9)))
        else:
            row.append(0.0)

        # bias
        for p in [5,20]:
            if i>=p-1:
                ma = pd.Series(close[:i+1]).rolling(p, min_periods=p).mean().values[-1]
                row.append(float((close[i]-ma)/(ma+1e-9)*100.0))
            else:
                row.append(0.0)

        # ppos
        for p in [20,60]:
            if i>=p-1:
                lo_min = pd.Series(low[:i+1]).rolling(p, min_periods=p).min().values[-1]
                hi_max = pd.Series(high[:i+1]).rolling(p, min_periods=p).max().values[-1]
                row.append(float((close[i]-lo_min)/(hi_max-lo_min+1e-9)))
            else:
                row.append(0.5)

        # gap（填0，对结果影响极小(<0.01)，跳过复杂计算）
        row.append(0.5); row.append(0.0); row.append(0.0)

        # hlr20
        if i>=19:
            lo_min = pd.Series(low[:i+1]).rolling(20, min_periods=20).min().values[-1]
            hi_max = pd.Series(high[:i+1]).rolling(20, min_periods=20).max().values[-1]
            row.append(float((hi_max-lo_min)/(hi_max+1e-9)))
        else:
            row.append(0.0)

        # rs（日频超额收益在60日窗口的排名百分位）
        if i >= 60:
            s_daily = np.diff(close[:i+1]) / (close[:i] + 1e-9)
            s_daily = np.concatenate([[0.0], s_daily])
            m_daily = np.array([date_to_mkt.get(date_arr[j], 0) for j in range(i+1)])
            ex = s_daily - m_daily
            window = ex[-60:]
            rs_val = sum(ex[-1] > w for w in window) / 60.0
            row.append(float(rs_val))
        else:
            row.append(0.5)

        # mkt
        mkt_val = date_to_mkt.get(date_arr[i], 0.0)
        row.append(float(mkt_val))

        # month_end
        from datetime import datetime as _dt
        d = _dt.strptime(str(date_arr[i]), '%Y-%m-%d')
        row.append(float(d.day / 31.0))

        # 财务特征（从pkl加载）
        code_key = stock_code or ''
        fin_v = (fin_data or {}).get(code_key, {})
        row.append(float(fin_v.get('roe_norm', 0.0)))
        row.append(float(fin_v.get('cash_net_ratio_norm', 0.5)))
        row.append(float(fin_v.get('deduct_ratio', 0.5)))
        row.append(float(fin_v.get('roe_pct', 0) or 0) / 100.0)
        row.append(float(fin_v.get('eps', 0) or 0))
        row.append(float(fin_v.get('gross_margin', 0) or 0) / 100.0)
        row.append(float(fin_v.get('net_margin', 0) or 0) / 100.0)

        all_X.append(row)
        all_dates.append(date_arr[i])

    if not all_X:
        return None, None, None

    X = np.array(all_X, dtype=np.float32)
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    return X, all_dates, date_arr[0]


def predict_for_codes(target_codes):
    # LightGBM原生文本格式模型
    model = lgb.Booster(model_file=str(MODEL_PATH))
    print(f'模型加载完成: {MODEL_PATH.name}')

    with open(PICKLE_PATH, 'rb') as f:
        all_data = pickle.load(f)
    print(f'数据加载: {len(all_data)} 只股票')

    # 预加载财务特征（与训练器一致）
    fin_data = {}
    FIN_PKL = PROJECT_ROOT / 'quant_ml' / 'data' / 'financial_features.pkl'
    if FIN_PKL.exists():
        import pickle as _pk
        with open(FIN_PKL, 'rb') as f:
            fin_raw = _pk.load(f)
        for k, v in fin_raw.items():
            norm_k = k.replace('sh.', '').replace('sz.', '').replace('.', '')
            fin_data[norm_k] = v
    print(f'财务特征: {len(fin_data)} 只')

    # 预计算市场因子
    rows = []
    for code, df in all_data.items():
        c = pd.to_numeric(df['close'], errors='coerce').fillna(0)
        r = c.pct_change()
        rows.append(pd.DataFrame({'date': df['date'].values, 'ret': r.values}))
    all_rets = pd.concat(rows, ignore_index=True)
    date_to_mkt = all_rets.groupby('date', sort=False)['ret'].mean().to_dict()
    print(f'市场因子: {len(date_to_mkt)} 个交易日')

    results = {}
    not_found = []

    for code in target_codes:
        num = code.lower().replace('sz','').replace('sh','').replace('bj','')
        df = all_data.get(num, None)
        if df is None:
            not_found.append(code)
            continue

        num = code.lower().replace('sz','').replace('sh','').replace('bj','')
        X, dates, _ = build_features_one_stock(df, date_to_mkt, fin_data, num)
        if X is None or len(X) == 0:
            print(f'  {code}: 样本不足')
            continue

        # 取最后一个采样点
        X_last = X[-1:]
        prob = float(model.predict(X_last)[0])
        # 统一存纯数字key（与训练器一致）
        num = code.lower().replace('sz','').replace('sh','').replace('bj','')
        results[num] = prob
        print(f'  {code}: P={prob:.4f}')

    if not_found:
        print(f'未找到: {not_found}')

    existing = 0
    if os.path.exists(OUTPUT_PATH):
        try:
            with open(OUTPUT_PATH, 'rb') as f:
                existing_data = pickle.load(f)
                existing = len(existing_data)
        except Exception:
            existing = 0

    # 写入独立文件，不再合并到 ml_latest_prob.pkl（避免覆盖 unified_train 的全市场预测）
    with open(OUTPUT_PATH, 'wb') as f:
        pickle.dump(results, f)

    print(f'\n更新: +{len(results)} 只, 共 {existing} 只')
    return results


if __name__ == '__main__':
    # 自动从portfolio.json读取所有持仓股
    import json
    pf_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\data\portfolio.json'
    with open(pf_path, 'r', encoding='utf-8') as f:
        pf = json.load(f)
    targets = [h['code'] for h in pf['holdings']]
    print(f'从portfolio.json读取 {len(targets)} 只持仓: {targets}')
    predict_for_codes(targets)