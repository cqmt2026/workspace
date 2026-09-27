# -*- coding: utf-8 -*-
"""
训练器 - 编排整个训练流程
优化版: 预计算所有特征 → 向量化 → 采样
兼容背景进程（检测stdout是否可缓冲）
"""
import os, sys, io, json, time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import gc
import numpy as np
import pandas as pd
import lightgbm as lgb

# Safe stdout setup (兼容无TTY的背景进程)
try:
    if sys.stdout is not None and hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
except Exception:
    pass
try:
    if sys.stderr is not None and hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
except Exception:
    pass

PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))


class Trainer:
    def __init__(self, config: dict, experiment_name: str = None):
        self.cfg = config
        self.exp_name = experiment_name or f"exp_{int(time.time())}"
        self.out_dir = PROJECT_ROOT / 'logs' / self.exp_name
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.results: Dict[str, Any] = {}
        self._data: Optional[Dict] = None
        self._splits: Optional[Dict] = None
        self._model: Optional[Any] = None
        self._val_codes: Optional[List] = None
        self._val_dates: Optional[List] = None
        self._factor_names: Optional[List] = None
        self._t0: float = 0.0

    def _load_data(self) -> Dict:
        from src.data_pipeline import DataLoader
        loader = DataLoader(self.cfg)
        data = loader.load()
        data = loader.filter_min_history(data)
        self._data = data
        return data

    def run(self) -> Dict:
        self._t0 = time.time()
        self._print("=" * 60)
        self._print(f"Quant ML Trainer - {self.exp_name}")
        self._print("=" * 60)
        data = self._load_data()
        X, y, factor_names = self._build_samples_fast()
        self._factor_names = factor_names
        splits = self._split_data(X, y)
        self._splits = splits
        self._do_train(splits)
        self._do_evaluate(splits)
        self._do_save()
        elapsed = time.time() - self._t0
        self._print(f"\n完成! 耗时: {elapsed:.1f}秒")
        self._print("=" * 60)
        return self.results

    def _print(self, msg: str) -> None:
        print(msg, flush=True)

    def _build_samples_fast(self) -> tuple:
        cfg = self.cfg['data']
        fcfg = cfg['features']
        interval = cfg['sample_interval']
        lookahead = cfg['lookahead']
        min_hist = cfg['min_history_days']

        stocks = list(self._data.items())
        total = len(stocks)
        t0 = time.time()
        last_print = 0

        # ---- 预计算市场因子（所有股票等权均值，纯numpy替代pandas groupby） ----
        self._print("  预计算市场因子...")
        # 用dict聚合避免pandas+pyarrow内存问题
        date_to_sum = {}
        date_to_cnt = {}
        for code, df in stocks:
            c = pd.to_numeric(df['close'], errors='coerce').fillna(0).values
            r = np.diff(c) / (c[:-1] + 1e-9)
            r = np.concatenate([[0.0], r])
            dates = df['date'].values
            for i in range(len(dates)):
                d = dates[i]
                date_to_sum[d] = date_to_sum.get(d, 0.0) + r[i]
                date_to_cnt[d] = date_to_cnt.get(d, 0) + 1
        date_to_mkt = {d: date_to_sum[d] / date_to_cnt[d] for d in date_to_sum}
        self._print(f"  市场因子: {len(date_to_mkt)} 个交易日")

        FIN_FIELDS = ['roe_norm', 'cash_net_ratio_norm', 'deduct_ratio']
        FIN_RAW_FIELDS = ['净资产收益率(%)', '摊薄每股收益(元)', '销售毛利率(%)', '销售净利率(%)']

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

        # 预分配numpy数组，避免Python list-of-lists内存爆炸
        MAX_SAMPLES_ESTIMATE = 1_500_000
        n_features = len(FACTOR_NAMES)
        X_buf = np.zeros((MAX_SAMPLES_ESTIMATE, n_features), dtype=np.float32)
        y_buf = np.zeros(MAX_SAMPLES_ESTIMATE, dtype=np.int32)
        code_buf = [''] * MAX_SAMPLES_ESTIMATE
        date_buf = [''] * MAX_SAMPLES_ESTIMATE
        sample_idx = 0

        # 预加载财务特征
        self._print("  加载财务特征...")
        fin_data = {}
        FIN_PKL = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\quant_ml\data\financial_features.pkl')
        if FIN_PKL.exists():
            import pickle as _pk
            with open(FIN_PKL, 'rb') as f:
                fin_raw = _pk.load(f)
            # 归一化code格式
            for k, v in fin_raw.items():
                norm_k = k.replace('sh.', '').replace('sz.', '').replace('.', '')
                fin_data[norm_k] = v
        self._print(f"  财务特征: {len(fin_data)} 只")

        for idx, (code, df) in enumerate(stocks):
            df = df.sort_values('date').reset_index(drop=True)
            n = len(df)
            if n < min_hist:
                continue

            close = pd.to_numeric(df['close'], errors='coerce').fillna(0).values.astype(np.float64)
            open_v = pd.to_numeric(df['open'], errors='coerce').fillna(0).values.astype(np.float64)
            high = pd.to_numeric(df['high'], errors='coerce').fillna(0).values.astype(np.float64)
            low = pd.to_numeric(df['low'], errors='coerce').fillna(0).values.astype(np.float64)
            vol = pd.to_numeric(df['volume'], errors='coerce').fillna(0).values.astype(np.float64)
            date_arr = df['date'].values

            # ---- 预计算个股60日滚动beta（已废弃，v5用原始收益标签） ----
            rolling_beta = np.full(n, 1.0)

            if (n - min_hist) // interval == 0:
                continue

            # ---- 预计算全部特征 (O(n) per stock) ----

            # ret
            ret = {}
            for p in fcfg['ret_periods']:
                arr = np.zeros(n, dtype=np.float64)
                if n > p:
                    arr[p:] = close[p:] / close[:-p] - 1
                ret[p] = arr

            # vol_20d: rolling std/mean
            vol_20d = np.zeros(n, dtype=np.float64)
            if n >= 20:
                close_series = pd.Series(close)
                mv = close_series.rolling(20, min_periods=20).mean().values
                sv = close_series.rolling(20, min_periods=20).std(ddof=0).values
                mv_safe = np.where(mv == 0, 1, mv)
                ratio = sv / mv_safe
                vol_20d[19:] = ratio[19:]

            # vr5: numpy convolve
            vr5 = np.ones(n, dtype=np.float64)
            if n >= 5:
                avg_vol5 = np.convolve(vol, np.ones(5) / 5, mode='valid')
                vr5[4:] = vol[4:] / (avg_vol5 + 1e-9)

            # ma_ratio
            ma_ratio = {}
            for p in fcfg['ma_periods']:
                arr = np.ones(n, dtype=np.float64)
                if n >= p:
                    close_series = pd.Series(close)
                    ma_vals = close_series.rolling(p, min_periods=p).mean().values  # shape (n,)
                    slice_start = p - 1
                    ma_slice = ma_vals[slice_start:]
                    close_slice = close[slice_start:]
                    mask = ma_slice != 0
                    arr[slice_start:][mask] = close_slice[mask] / ma_slice[mask]
                ma_ratio[p] = arr

            # bbp_20d
            bbp_20d = np.full(n, 0.5, dtype=np.float64)
            if n >= 20:
                close_series = pd.Series(close)
                mv_vals = close_series.rolling(20, min_periods=20).mean().values
                sv_vals = close_series.rolling(20, min_periods=20).std(ddof=0).values
                slice_start = 19
                mv_slice = mv_vals[slice_start:]
                sv_slice = sv_vals[slice_start:]
                upper_slice = mv_slice + 2 * sv_slice
                lower_slice = mv_slice - 2 * sv_slice
                denom_slice = upper_slice - lower_slice
                close_slice = close[slice_start:]
                mask = denom_slice != 0
                bbp_20d[slice_start:][mask] = (close_slice[mask] - lower_slice[mask]) / denom_slice[mask]

            # macd: ewm
            macd_dif = np.zeros(n, dtype=np.float64)
            macd_dea = np.zeros(n, dtype=np.float64)
            if n >= 26:
                ema12 = pd.Series(close).ewm(span=12, adjust=False).mean().values
                ema26 = pd.Series(close).ewm(span=26, adjust=False).mean().values
                macd_dif[25:] = ema12[25:] - ema26[25:]
                macd_dea[25:] = pd.Series(macd_dif[25:]).ewm(span=9, adjust=False).mean().values

            # kdj: rolling
            kdj_k = np.full(n, 50.0, dtype=np.float64)
            kdj_d = np.full(n, 50.0, dtype=np.float64)
            kdj_j = np.full(n, 50.0, dtype=np.float64)
            if n >= 9:
                low_series = pd.Series(low)
                high_series = pd.Series(high)
                lo_min = low_series.rolling(9, min_periods=9).min().values
                hi_max = high_series.rolling(9, min_periods=9).max().values
                denom = hi_max - lo_min + 1e-9
                rsv_k = 100.0 * (close - lo_min) / denom
                k_start = 8
                kdj_k[k_start:] = 2.0/3.0 * 50.0 + 1.0/3.0 * rsv_k[k_start:]
                kdj_d[k_start:] = 2.0/3.0 * 50.0 + 1.0/3.0 * kdj_k[k_start:]
                kdj_j[k_start:] = 3.0 * kdj_k[k_start:] - 2.0 * kdj_d[k_start:]

            # rsi_14d: 向量化Wilder RSI（EMA形式，等效14日）
            rsi_14d = np.full(n, 50.0, dtype=np.float64)
            if n >= 15:
                diff_arr = np.diff(close)
                # 用pandas ewm实现Wilder RSI（alpha=1/14）
                gains = pd.Series(np.where(diff_arr > 0, diff_arr, 0.0))
                losses = pd.Series(np.where(diff_arr < 0, -diff_arr, 0.0))
                avg_gains = gains.ewm(alpha=1.0/14, adjust=False).mean()
                avg_losses = losses.ewm(alpha=1.0/14, adjust=False).mean()
                rs = avg_gains / (avg_losses + 1e-9)
                rsi_vals = 100.0 - (100.0 / (1.0 + rs))
                rsi_14d[14:] = rsi_vals.values[13:]

            # obv
            obv = np.zeros(n, dtype=np.float64)
            if n >= 2:
                changes = np.diff(close)
                obv[1:] = np.cumsum(np.where(changes > 0, vol[1:], -vol[1:]))
            avg_vol20 = np.zeros(n, dtype=np.float64)
            if n >= 20:
                vol_series = pd.Series(vol)
                avg_vol20[19:] = vol_series.rolling(20, min_periods=20).mean().values[19:]
            obv_ratio = np.zeros(n, dtype=np.float64)
            for i in range(20, n):
                if avg_vol20[i] > 1e-9:
                    obv_ratio[i] = obv[i] / avg_vol20[i]

            # bias
            bias = {}
            for p in fcfg['bias_periods']:
                arr = np.zeros(n, dtype=np.float64)
                if n >= p:
                    close_series = pd.Series(close)
                    ma_vals = close_series.rolling(p, min_periods=p).mean().values
                    for i in range(p - 1, n):
                        mv = ma_vals[i]
                        if mv > 1e-9:
                            arr[i] = (close[i] - mv) / mv * 100.0
                bias[p] = arr

            # ppos
            ppos = {}
            for p in [20, 60]:
                arr = np.full(n, 0.5, dtype=np.float64)
                if n >= p:
                    lo_series = pd.Series(low)
                    hi_series = pd.Series(high)
                    lo_min = hi_series.rolling(p, min_periods=p).min().values
                    hi_max = hi_series.rolling(p, min_periods=p).max().values
                    for i in range(p - 1, n):
                        denom = hi_max[i] - lo_min[i] + 1e-9
                        arr[i] = (close[i] - lo_min[i]) / denom
                ppos[p] = arr

            # gap
            gap_mean = np.full(n, 0.5, dtype=np.float64)
            gap_up = np.zeros(n, dtype=np.float64)
            gap_down = np.zeros(n, dtype=np.float64)
            if n >= 21:
                close_prev = close[:n-1]
                ret_arr = np.diff(close) / (close_prev + 1e-9)
                oc_arr = open_v[1:n] - close_prev
                for i in range(20, n):
                    r_w = ret_arr[i-20:i]
                    oc_w = oc_arr[i-20:i]
                    gap_mean[i] = np.mean((r_w > 0).astype(float))
                    gap_up[i] = np.sum(oc_w > 0.02 * close_prev[i-20:i])
                    gap_down[i] = np.sum(oc_w < -0.02 * close_prev[i-20:i])

            # hlr20
            hlr20 = np.zeros(n, dtype=np.float64)
            if n >= 20:
                lo_series = pd.Series(low)
                hi_series = pd.Series(high)
                lo_min = lo_series.rolling(20, min_periods=20).min().values
                hi_max = hi_series.rolling(20, min_periods=20).max().values
                for i in range(19, n):
                    denom = hi_max[i] + 1e-9
                    hlr20[i] = (hi_max[i] - lo_min[i]) / denom

            # ---- 相对市场强度（个股超额收益 vs 市场，滚动排名百分位） ----
            # 注意：用循环替代 sliding_window_view，避免创建大中间数组导致内存碎片
            rs = np.full(n, 0.5, dtype=np.float64)
            if n >= 61:
                stock_daily_ret = np.diff(close) / (close[:-1] + 1e-9)
                stock_daily_ret = np.concatenate([[0.0], stock_daily_ret])
                mkt_daily = np.array([date_to_mkt.get(d, 0) for d in date_arr])
                ex_ret = stock_daily_ret - mkt_daily
                # 滑动窗口内排名百分位：对每个位置j，统计ex_ret[j-60:j]中<=ex_ret[j-1]的比例
                # 循环方式避免一次性创建(n-59,60)的bool数组
                half = 30
                # 循环替代 sliding_window_view，避免创建大中间数组导致内存碎片
                for j in range(60, n):
                    k = j - 59
                    w = ex_ret[k:k+60]  # 窗口共60个元素
                    center = ex_ret[k+29]  # 窗口中心元素
                    rs[j] = (np.sum(w <= center) - 1.0) / 59.0

            # ---- 采样 ----
            for i in range(min_hist, n - lookahead, interval):
                # ---- 样本质量过滤（P3: 减少噪声样本） ----
                # 过滤价格异常（<2元的penny stock）
                if close[i] < 2.0:
                    continue
                # 过滤流动性异常（量比<0.3，过于清淡）
                if vr5[i] < 0.3:
                    continue
                # 过滤涨跌停次日（ret_1>9.5%或<-9.5%，高噪声）
                if abs(ret[1][i]) > 0.095:
                    continue
                # 过滤即将停牌（成交量异常低）
                if vol[i] < 10000:
                    continue

                row = []
                for p in fcfg['ret_periods']:
                    row.append(float(ret[p][i]))
                row.append(float(vol_20d[i]))
                row.append(float(vr5[i]))
                for p in fcfg['ma_periods']:
                    row.append(float(ma_ratio[p][i]))
                row.append(float(bbp_20d[i]))
                row.append(float(macd_dif[i]))
                row.append(float(macd_dea[i]))
                row.append(float(kdj_k[i]))
                row.append(float(kdj_d[i]))
                row.append(float(kdj_j[i]))
                row.append(float(rsi_14d[i]))
                row.append(float(obv[i] / 1e8))
                row.append(float(obv_ratio[i]))
                for p in fcfg['bias_periods']:
                    row.append(float(bias[p][i]))
                for p in [20, 60]:
                    row.append(float(ppos[p][i]))
                row.append(float(gap_mean[i]))
                row.append(float(gap_up[i]))
                row.append(float(gap_down[i]))
                row.append(float(hlr20[i]))
                row.append(float(rs[i]))
                mkt_val = date_to_mkt.get(date_arr[i], 0.0)
                row.append(float(mkt_val))
                # ---- 月末效应（因子库新增：越接近月末收益越高） ----
                d = datetime.strptime(str(date_arr[i]), '%Y-%m-%d')
                month_end_score = d.day / 31.0  # 0~1，越大=越接近月末
                row.append(float(month_end_score))

                # ---- 财务特征 ----
                norm_code = code.replace('sh.', '').replace('sz.', '').replace('.', '')
                fin_v = fin_data.get(norm_code, {})
                row.append(float(fin_v.get('roe_norm', 0.0)))
                row.append(float(fin_v.get('cash_net_ratio_norm', 0.5)))
                row.append(float(fin_v.get('deduct_ratio', 0.5)))
                row.append(float(fin_v.get('净资产收益率(%)', 0) or 0) / 100.0)
                row.append(float(fin_v.get('摊薄每股收益(元)', 0) or 0))
                row.append(float(fin_v.get('销售毛利率(%)', 0) or 0) / 100.0)
                row.append(float(fin_v.get('销售净利率(%)', 0) or 0) / 100.0)

                # ---- 原始收益标签（v5: 预测10日后涨跌方向） ----
                stock_ret = close[i+lookahead] / close[i] - 1
                label = 1 if stock_ret > 0 else 0

                # 直接填入预分配数组
                for j, val in enumerate(row):
                    X_buf[sample_idx, j] = float(val)
                y_buf[sample_idx] = label
                code_buf[sample_idx] = code
                date_buf[sample_idx] = date_arr[i]
                sample_idx += 1

            elapsed = time.time() - t0
            if idx - last_print >= 500 or idx == total - 1:
                self._print(f"  股票 {idx+1}/{total}, 累计样本{sample_idx:,}, {elapsed:.0f}s")
                last_print = idx
                gc.collect()

        # 裁剪到实际大小
        X = X_buf[:sample_idx]
        y = y_buf[:sample_idx]
        self._all_codes = code_buf[:sample_idx]
        self._all_dates = date_buf[:sample_idx]
        # 原地处理NaN/Inf，避免OOM（小内存环境下再分配157MiB可能失败）
        np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0, copy=False)
        pos_rate = float(np.mean(y))
        self._print(f"  样本{len(X):,} 正样本率{pos_rate:.2%}")
        return X, y, FACTOR_NAMES

    def _split_data(self, X, y) -> Dict:
        tcfg = self.cfg['training']
        n = len(X)
        ts = int(n * tcfg['train_ratio'])
        es = int(n * (tcfg['train_ratio'] + tcfg['early_stop_ratio']))
        val_codes = self._all_codes[es:] if hasattr(self, '_all_codes') and self._all_codes else []
        val_dates = self._all_dates[es:] if hasattr(self, '_all_dates') and self._all_dates else []
        return dict(
            Xt=X[:ts], yt=y[:ts],
            Xes=X[ts:es], yes=y[ts:es],
            Xv=X[es:], yv=y[es:],
            val_codes=val_codes, val_dates=val_dates
        )

    def _do_train(self, splits: Dict) -> None:
        from src.models import LightGBMModel
        model = TrainerLightGBM(self.cfg, self._factor_names)
        model.train(splits)
        self._model = model
        self._print(f"  完成{model.best_iter()}轮")

    def _find_optimal_threshold(self, proba: np.ndarray, y_true: np.ndarray) -> float:
        """在早停集上搜索最优阈值（最大化F1）"""
        from sklearn.metrics import f1_score
        thresholds = np.arange(0.30, 0.70, 0.01)
        best_f1, best_th = 0, 0.5
        for th in thresholds:
            pred = (proba > th).astype(int)
            f1 = f1_score(y_true, pred, zero_division=0)
            if f1 > best_f1:
                best_f1 = f1
                best_th = th
        return best_th, best_f1

    def _do_evaluate(self, splits: Dict) -> None:
        from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score
        model = self._model
        # 在早停集上找最优阈值
        es_proba = model.predict_proba(splits['Xes'])
        opt_th, es_f1 = self._find_optimal_threshold(es_proba, splits['yes'])
        self._print(f"  最优阈值={opt_th:.2f} (早停集F1={es_f1:.4f})")

        # 用最优阈值在验证集上评估
        proba = model.predict_proba(splits['Xv'])
        pred = (proba > opt_th).astype(int)
        acc = float((pred == splits['yv']).mean())
        auc = roc_auc_score(splits['yv'], proba)
        f1 = f1_score(splits['yv'], pred, zero_division=0)
        prec = precision_score(splits['yv'], pred, zero_division=0)
        rec = recall_score(splits['yv'], pred, zero_division=0)
        train_proba = model.predict_proba(splits['Xt'])
        train_acc = float(((train_proba > opt_th).astype(int) == splits['yt']).mean())
        gap = train_acc - acc
        rating = 'A' if auc >= 0.65 else 'B' if auc >= 0.58 else 'C' if auc >= 0.52 else 'D'
        self.results = dict(val_acc=acc, auc=auc, f1=f1, prec=prec, rec=rec,
                           train_acc=train_acc, gap=gap, rating=rating,
                           opt_threshold=round(opt_th, 2))
        self._print(f"  val_acc={acc:.4f} auc={auc:.4f} gap={gap:.4f} {rating}")
        # ---- P5: 因子重要性分析 ----
        importance = model.feature_importance()
        feat_imp = sorted(zip(self._factor_names, importance), key=lambda x: x[1], reverse=True)
        self._print("\n  【因子重要性TOP15】")
        for fname, imp in feat_imp[:15]:
            bar = '█' * int(imp / feat_imp[0][1] * 20)
            self._print(f"    {fname:<20} {bar} {imp:>6.0f}")
        # 保存完整因子重要性
        imp_file = self.out_dir / 'feature_importance.json'
        with open(imp_file, 'w', encoding='utf-8') as f:
            json.dump([{'factor': fname, 'importance': int(imp)} for fname, imp in feat_imp],
                      f, ensure_ascii=False, indent=2)
        # 找出低 importance 特征（< 5% of top）供后续优化参考
        threshold = feat_imp[0][1] * 0.05
        weak = [fname for fname, imp in feat_imp if imp < threshold]
        if weak:
            self._print(f"  ⚠️ 低重要性特征({len(weak)}个): {weak}")

    def _do_save(self) -> None:
        model = self._model
        model.save(self.out_dir / 'model.txt')
        with open(self.out_dir / 'results.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        try:
            import pickle
            splits = self._splits
            proba = model.predict_proba(splits['Xv'])
            val_codes = splits.get('val_codes', [])
            latest_dict: Dict[str, float] = {}
            for i, code in enumerate(val_codes[:len(proba)]):
                latest_dict[str(code)] = float(proba[i])
            cache_path = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\scripts\ml_latest_prob.pkl')
            with open(cache_path, 'wb') as f:
                pickle.dump(latest_dict, f)
            self._print(f"  ML概率已保存: {len(latest_dict)}只")
        except Exception as e:
            self._print(f"  ML概率保存失败: {e}")


class TrainerLightGBM:
    def __init__(self, cfg: Dict, names: List[str]):
        self.cfg = cfg['model']['lightgbm']
        self.names = names
        self._model: Any = None

    def train(self, splits: Dict) -> None:
        params = dict(self.cfg)
        params.pop('n_estimators', None)
        params.pop('verbose', None)
        dtrain = lgb.Dataset(splits['Xt'], label=splits['yt'])
        de = lgb.Dataset(splits['Xes'], label=splits['yes'], reference=dtrain)
        callbacks = [
            lgb.early_stopping(30, verbose=False),
            lgb.log_evaluation(50)
        ]
        self._model = lgb.train(
            dict(params), dtrain,
            num_boost_round=self.cfg.get('n_estimators', 500),
            valid_sets=[dtrain, de], valid_names=['train', 'es'],
            callbacks=callbacks
        )

    def best_iter(self) -> int:
        return self._model.best_iteration if hasattr(self._model, 'best_iteration') else 0

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self._model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.predict(X)

    def save(self, path: Path) -> None:
        self._model.save_model(str(path))

    def feature_importance(self) -> np.ndarray:
        return self._model.feature_importance()


if __name__ == '__main__':
    import yaml
    cfg = yaml.safe_load(open(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\quant_ml\configs\config.yaml', encoding='utf-8'))
    t = Trainer(cfg, 'quant_ml_v1')
    t.run()