# -*- coding: utf-8 -*-
"""
因子动物园 - 所有因子定义
量化系统最核心的模块
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any


class FactorZoo:
    """
    所有技术因子定义
    每个方法 = 一个因子族，输入numpy数组，输出因子值
    """

    def __init__(self, config: dict):
        self.cfg = config['data']['features']
        # 根据配置决定启用哪些因子
        self._build_factor_list()

    def _build_factor_list(self):
        """根据配置文件构建因子列表"""
        self.factor_names = []
        # 收益率
        for p in self.cfg['ret_periods']:
            self.factor_names.append(f'ret_{p}d')
        # 波动率
        for p in self.cfg.get('vol_periods', []):
            self.factor_names.append(f'vol_{p}d')
        # 均线比
        for ma in self.cfg.get('ma_periods', []):
            self.factor_names.append(f'ma{ma}_ratio')
        # 布林带
        for p in self.cfg.get('bbp_periods', []):
            self.factor_names.append(f'bbp_{p}d')
        # MACD
        if self.cfg.get('macd'):
            self.factor_names.extend(['macd_d', 'macd_dea'])
        # KDJ
        if self.cfg.get('kdj'):
            self.factor_names.extend(['kdj_k', 'kdj_d', 'kdj_j'])
        # RSI
        for p in self.cfg.get('rsi_periods', []):
            self.factor_names.append(f'rsi_{p}d')
        # OBV
        if self.cfg.get('obv'):
            self.factor_names.extend(['obv', 'obv_roc'])
        # 乖离率
        for ma in self.cfg.get('bias_periods', []):
            self.factor_names.append(f'bias{ma}')
        # 位置
        for p in self.cfg.get('ppos_periods', []):
            self.factor_names.append(f'ppos_{p}d')
        # 缺口特征
        if self.cfg.get('gap_features'):
            self.factor_names.extend(['up_r', 'gup_c', 'gdn_c'])
        # 换手率区间
        self.factor_names.append('hlr20')
        # 市场因子
        if self.cfg.get('market_factor'):
            self.factor_names.append(self.cfg.get('market_factor_col', 'mkt_ret1'))

    def compute_all(self, df: pd.DataFrame, market_ret: float = 0.0) -> List[float]:
        """
        计算某一时点的所有因子值
        df: 单只股票历史DataFrame（已排序）
        i: 当前索引位置
        market_ret: 当日市场收益率（用于市场因子）
        """
        n = len(df)
        if n < 250:
            return [0.0] * len(self.factor_names)

        c = df['close'].values.astype(np.float64)
        o = df['open'].values.astype(np.float64)
        h = df['high'].values.astype(np.float64)
        l = df['low'].values.astype(np.float64)
        v = df['volume'].values.astype(np.float64)
        i = n - 1  # 取最新

        values = []

        # ---- 收益率因子 ----
        for p in self.cfg['ret_periods']:
            values.append((c[i]/c[i-p]-1) if i >= p else 0.0)

        # ---- 波动率因子 ----
        for p in self.cfg.get('vol_periods', []):
            if i >= p:
                mean = np.mean(c[i-p:i+1])
                values.append(np.std(c[i-p:i+1])/mean if mean != 0 else 0)
            else:
                values.append(0)

        # ---- 均线比因子 ----
        for ma in self.cfg.get('ma_periods', []):
            if i >= ma:
                m = np.mean(c[i-ma:i+1])
                values.append(c[i]/m if m != 0 else 1)
            else:
                values.append(1)

        # ---- 布林带因子 ----
        for p in self.cfg.get('bbp_periods', []):
            if i >= p:
                ma_val = np.mean(c[i-p:i+1])
                std_val = np.std(c[i-p:i+1])
                upper = ma_val + 2*std_val
                lower = ma_val - 2*std_val
                values.append((c[i]-lower)/(upper-lower+1e-9))
            else:
                values.append(0.5)

        # ---- MACD ----
        if self.cfg.get('macd'):
            if i >= 26:
                ema12 = pd.Series(c[:i+1]).ewm(span=12).mean().iloc[i]
                ema26 = pd.Series(c[:i+1]).ewm(span=26).mean().iloc[i]
                dif = ema12 - ema26
                dea = pd.Series([dif]).ewm(span=9).mean().iloc[0]
                values.extend([dif, dea])
            else:
                values.extend([0, 0])

        # ---- KDJ ----
        if self.cfg.get('kdj'):
            if i >= 9:
                lo = np.min(l[i-8:i+1])
                hi = np.max(h[i-8:i+1])
                rsv = (c[i]-lo)/(hi-lo+1e-9)*100
                k = 2/3*50 + 1/3*rsv
                d = 2/3*50 + 1/3*k
                j = 3*k - 2*d
                values.extend([k, d, j])
            else:
                values.extend([50, 50, 50])

        # ---- RSI ----
        for p in self.cfg.get('rsi_periods', []):
            if i >= p:
                d_val = np.diff(c[i-p:i+1])
                g = np.mean(d_val[d_val>0]) if len(d_val[d_val>0]) > 0 else 0
                l_loss = abs(np.mean(d_val[d_val<0])) if len(d_val[d_val<0]) > 0 else 0
                values.append(100-(100/(1+g/l_loss+1e-9)) if l_loss != 0 else 50)
            else:
                values.append(50)

        # ---- OBV ----
        if self.cfg.get('obv'):
            if i >= 1:
                obv_val = np.sum(np.where(np.diff(c[:i+1])>0, v[1:i+1], -v[1:i+1]))
                values.append(obv_val/1e8)
                if i >= 20:
                    obv_roc = (obv_val - np.mean(v[i-19:i+1])) / (np.mean(v[i-19:i+1])+1e-9)
                else:
                    obv_roc = 0
                values.append(obv_roc)
            else:
                values.extend([0, 0])

        # ---- 乖离率 ----
        for ma in self.cfg.get('bias_periods', []):
            if i >= ma:
                m = np.mean(c[i-ma:i+1])
                values.append((c[i]-m)/m*100 if m != 0 else 0)
            else:
                values.append(0)

        # ---- 位置 ----
        for p in self.cfg.get('ppos_periods', []):
            if i >= p:
                hi = np.max(h[i-p:i+1])
                lo = np.min(l[i-p:i+1])
                values.append((c[i]-lo)/(hi-lo+1e-9))
            else:
                values.append(0.5)

        # ---- 缺口特征 ----
        if self.cfg.get('gap_features'):
            if i >= 20:
                r = np.diff(c[i-20:i]) / c[i-20:i-1]
                values.append(np.mean(r > 0))
                g = (o[i-19:i] - c[i-20:i-1]) / (c[i-20:i-1]+1e-9)
                values.append(np.sum(g > 0.02))
                values.append(np.sum(g < -0.02))
            else:
                values.extend([0.5, 0, 0])

        # ---- 换手率区间 ----
        if i >= 20:
            hlr = (np.max(h[i-20:i+1]) - np.min(l[i-20:i+1])) / (np.max(h[i-20:i+1])+1e-9)
            values.append(hlr)
        else:
            values.append(0)

        # ---- 市场因子 ----
        if self.cfg.get('market_factor'):
            values.append(market_ret)

        return values

    def get_names(self) -> List[str]:
        return self.factor_names

    def count(self) -> int:
        return len(self.factor_names)
