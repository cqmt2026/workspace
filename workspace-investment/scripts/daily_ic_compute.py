# -*- coding: utf-8 -*-
"""
每日因子IC计算 + 状态更新脚本
================================
功能：
  1. 读取DB当日全市场K线数据
  2. 计算每个注册因子的当日值（仅价量类因子）
  3. 计算T+1收益（次日涨幅）
  4. 计算每个因子的Spearman IC
  5. 写入 ic_history 表
  6. 更新 factor_status 表（含自动淘汰判定）
  7. 输出IC报告到 out_data/

执行时机：收盘后16:50（K线入库后，因子计算后）
用法：python scripts/daily_ic_compute.py [--date 2026-07-05]
"""
import io
import sys
import os
import json
import sqlite3
import inspect
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

# 添加workspace到路径
WORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORK_DIR)

# ─── DataFrame包装器（IC脚本需要，因为注册中心存的是原始类方法签名）───

# 各因子的参数映射：factor_name -> (列名列表)
# 与 FeatureEngine._register_builtin_factors 保持一致
_FACTOR_DF_MAP = {
    'ma_5': ('close',),
    'ma_10': ('close',),
    'ma_20': ('close',),
    'ma_60': ('close',),
    'rsi_14': ('close',),
    'vol_ratio': ('volume',),
    'pct_chg_1d': ('close',),
    'pct_chg_5d': ('close',),
    'pct_chg_10d': ('close',),
    'atr_14': ('high', 'low', 'close'),
    'obv': ('close', 'volume'),
    'wr_14': ('close', 'high', 'low'),
    'cci_20': ('close', 'high', 'low'),
    'vwap_5': ('close', 'volume'),
    'volatility_20': ('close',),
    'macd_bar': ('close',),
    'macd_cross': ('close',),
    'macd_second_peak': ('close',),
    'acceleration': ('close',),
    'breakout_strength': ('close', 'high'),
    'avg_cost': ('close', 'volume'),
    'profit_ratio': ('close', 'volume'),
    'concentration': ('close', 'volume'),
}


def _make_df_calculator(factor_name: str, calculator, params=None) -> Optional[Callable]:
    """将注册中心存储的计算器包装成接受DataFrame的函数。

    判断逻辑：
    1. 如果calculator首参数名为'df'（FeatureEngine注册的lambda），直接使用
    2. 否则按因子名映射为Series提取器（registry.py的原始类方法）
    """
    if params is None:
        params = {}

    # 检测是否已是DataFrame接受器
    try:
        sig = inspect.signature(calculator)
        first_param = list(sig.parameters.keys())[0] if sig.parameters else ''
        if first_param == 'df':
            return calculator  # 已经是DataFrame接受器，直接返回
    except (ValueError, TypeError):
        pass

    cols = _FACTOR_DF_MAP.get(factor_name)
    if cols is None:
        return None

    def wrapped(df: pd.DataFrame) -> pd.Series:
        window = params.get('window', 20)
        periods = params.get('periods', 1)

        if factor_name == 'acceleration':
            close = df['close'].astype(float)
            returns = close.pct_change()
            return (returns.rolling(5).mean() - returns.rolling(20).mean()).fillna(0)
        if factor_name == 'macd_bar':
            close = df['close'].astype(float)
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            dif = ema12 - ema26
            dea = dif.ewm(span=9, adjust=False).mean()
            return 2 * (dif - dea)
        if factor_name == 'macd_cross':
            close = df['close'].astype(float)
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            dif = ema12 - ema26
            dea = dif.ewm(span=9, adjust=False).mean()
            cross = (dif.shift(1) - dea.shift(1)) * (dif - dea)
            return cross
        if factor_name == 'macd_second_peak':
            close = df['close'].astype(float)
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            dif = ema12 - ema26
            return dif.diff().diff().fillna(0)
        if factor_name == 'profit_ratio':
            close = df['close'].astype(float)
            price = close.iloc[-1]
            ma20 = close.rolling(20).mean().iloc[-1]
            ma60 = close.rolling(60).mean().iloc[-1] if len(close) >= 60 else np.nan
            ratio = 0.0
            if not np.isnan(ma20):
                ratio += 0.5 * (1 if price > ma20 else 0)
            if not np.isnan(ma60):
                ratio += 0.5 * (1 if price > ma60 else 0)
            return ratio
        if factor_name == 'avg_cost':
            close = df['close'].astype(float)
            volume = df['volume'].astype(float)
            avg = (close * volume).sum() / volume.sum() if volume.sum() > 0 else np.nan
            return (close.iloc[-1] - avg) / avg if not np.isnan(avg) else np.nan
        if factor_name == 'concentration':
            close = df['close'].astype(float)
            vol = df['volume'].astype(float)
            total_vol = vol.sum()
            if total_vol <= 0:
                return np.nan
            hist_vol = vol.tail(20).sum() if len(vol) >= 20 else vol.sum()
            return hist_vol / total_vol
        if factor_name == 'breakout_strength':
            close = df['close'].astype(float)
            high = df['high'].astype(float)
            max_high_60 = high.rolling(60).max()
            return (close - max_high_60.shift(1)) / max_high_60.shift(1)
        if factor_name == 'vwap_5':
            close = df['close'].astype(float)
            volume = df['volume'].astype(float)
            vwap = (close * volume).rolling(5).sum() / volume.rolling(5).sum()
            return (close - vwap) / vwap
        if factor_name == 'volatility_20':
            close = df['close'].astype(float)
            return close.pct_change().rolling(20).std()
        if factor_name == 'vol_ratio':
            volume = df['volume'].astype(float)
            return volume / volume.rolling(20).mean()
        if factor_name == 'wr_14':
            high = df['high'].astype(float)
            low = df['low'].astype(float)
            close = df['close'].astype(float)
            tr = high - low
            rh = high - high.shift(1)
            rl = low.shift(1) - low
            tr = tr.combine(pd.Series({'close': close}), lambda x, y: max(x, y, z))
            return -100 * (tr / (high - low).rolling(14).sum())
        if factor_name == 'cci_20':
            close = df['close'].astype(float)
            high = df['high'].astype(float)
            low = df['low'].astype(float)
            tp = (high + low + close) / 3
            mad = tp.rolling(20).apply(lambda x: abs(x - x.mean()).mean())
            return (tp - tp.rolling(20).mean()) / (0.015 * mad)
        if factor_name == 'obv':
            close = df['close'].astype(float)
            volume = df['volume'].astype(float)
            obv = (np.sign(close.diff()) * volume).cumsum()
            return obv / obv.abs().max() if obv.abs().max() > 0 else obv
        if factor_name == 'rsi_14':
            close = df['close'].astype(float)
            delta = close.diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
        if factor_name in ('ma_5', 'ma_10', 'ma_20', 'ma_60'):
            close = df['close'].astype(float)
            period = int(factor_name.split('_')[1])
            return close / close.rolling(period).mean() - 1
        if factor_name in ('pct_chg_1d', 'pct_chg_5d', 'pct_chg_10d'):
            close = df['close'].astype(float)
            period = int(factor_name.split('_')[2])
            return close.pct_change(periods=period)
        if factor_name == 'atr_14':
            high = df['high'].astype(float)
            low = df['low'].astype(float)
            close = df['close'].astype(float)
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            return tr.rolling(14).mean()
        # 默认：取最后一列
        return df[cols[-1]].astype(float)

    return wrapped


class DailyICCompute:
    """每日IC计算"""

    def __init__(self, db_path='F:/market_data.db'):
        self.db_path = db_path
        self._real_conn = None
        self._engine = None
        self._log_buffer = []

    @property
    def _conn(self):
        if self._real_conn is None:
            self._real_conn = sqlite3.connect(self.db_path)
        return self._real_conn

    def _get_trading_dates(self, end_date: str, count: int = 120) -> List[str]:
        """获取最近的交易日期列表"""
        conn = self._conn
        rows = conn.execute(
            "SELECT DISTINCT date FROM daily_k WHERE date <= ? "
            "ORDER BY date DESC LIMIT ?",
            (end_date, count + 60)  # 多取一些，因为有ST等
        ).fetchall()
        dates = sorted([r[0] for r in rows])
        return dates[-count:] if len(dates) > count else dates

    def _get_all_codes(self, date: str) -> List[str]:
        """获取某日正常交易的全部股票"""
        conn = self._conn
        rows = conn.execute(
            "SELECT code FROM daily_k WHERE date = ? "
            "AND code NOT LIKE 'bj.%%' "
            "AND code NOT LIKE 'sh.8%%' "
            "AND code NOT LIKE 'sh.9%%' "
            "AND code NOT LIKE 'sh.4%%' "
            "AND code NOT LIKE 'sh.68%%' "
            "AND close > 0 AND volume > 0",
            (date,)
        ).fetchall()
        return [r[0] for r in rows]

    def _get_forward_returns(self, codes: List[str], date: str) -> Dict[str, float]:
        """获取T+1收益（次日涨幅）

        返回: {code: 次日涨跌幅}
        注意：DB数据可能不完整，只返回能配对到的股票
        """
        conn = self._conn
        # 找下一个有足够数据的交易日（>100只股票）
        next_dates = conn.execute(
            "SELECT date, COUNT(*) as cnt FROM daily_k "
            "WHERE date > ? GROUP BY date HAVING cnt > 100 "
            "ORDER BY date ASC LIMIT 1",
            (date,)
        ).fetchall()

        if not next_dates:
            return {}

        next_date = next_dates[0][0]

        forward_rets = {}
        # 批量JOIN获取T+1收益
        rows = conn.execute(
            "SELECT a.code, (a.close - b.close) / b.close as ret "
            "FROM daily_k a "
            "INNER JOIN daily_k b ON a.code = b.code AND b.date = ? "
            "WHERE a.date = ? "
            "AND a.code NOT LIKE 'bj.%%' "
            "AND b.close > 0 AND a.close > 0",
            (next_date, date)
        ).fetchall()

        for code, ret in rows:
            if ret is not None:
                forward_rets[code] = float(ret)

        return forward_rets

    def _compute_factor_values(self, date: str, codes: List[str]) -> Dict[str, Dict[str, float]]:
        """计算技术因子的当日值

        只计算价量相关的因子（technical类别），其他因子独立计算。
        返回: {code: {factor_name: value}}
        """
        if self._engine is None:
            from alice_quant.features.registry import FactorRegistry
            self._engine = FactorRegistry()

        results = {}
        batch_size = 50

        for i in range(0, len(codes), batch_size):
            batch = codes[i:i + batch_size]
            placeholders = ','.join(['?' for _ in batch])

            # 获取各股票最近60个交易日的K线
            klines = {}
            for code in batch:
                rows = self._conn.execute(
                    "SELECT date, close, high, low, volume FROM daily_k "
                    "WHERE code = ? AND date >= ? ORDER BY date ASC",
                    (code, (pd.Timestamp(date) - timedelta(days=120)).strftime('%Y-%m-%d'))
                ).fetchall()
                if len(rows) >= 20:
                    df = pd.DataFrame(rows, columns=['date', 'close', 'high', 'low', 'volume'])
                    klines[code] = df

            # 计算各因子
            factor_names = [
                'ma_5', 'ma_10', 'ma_20', 'ma_60', 'rsi_14', 'vol_ratio',
                'pct_chg_1d', 'pct_chg_5d', 'pct_chg_10d', 'atr_14', 'obv',
                'wr_14', 'cci_20', 'vwap_5', 'volatility_20',
                'macd_bar', 'macd_cross', 'macd_second_peak',
                'acceleration', 'breakout_strength',
                'avg_cost', 'profit_ratio', 'concentration',
            ]

            for code, df in klines.items():
                if code not in results:
                    results[code] = {}

                for factor_name in factor_names:
                    calc_func = _make_df_calculator(factor_name, None, {})
                    if calc_func is None:
                        continue
                    try:
                        vals = calc_func(df)
                        if isinstance(vals, pd.Series):
                            val = vals.iloc[-1]
                        else:
                            val = vals
                        if not np.isnan(val) and np.isfinite(val):
                            results[code][factor_name] = float(val)
                    except Exception:
                        pass

            if (i // batch_size) % 10 == 0:
                self._log(f"  进度: {min(i + batch_size, len(codes))}/{len(codes)}")

        return results

    def compute_ic_for_date(self, date: str) -> List[Dict]:
        """计算指定日期的所有因子IC"""
        self._log(f"\n计算 {date} 的因子IC...")

        # 1. 获取所有股票代码
        codes = self._get_all_codes(date)
        self._log(f"  股票数: {len(codes)}")

        if len(codes) < 100:
            self._log("  数据不足（需要至少100只），跳过")
            return []

        # 2. 获取T+1收益
        forward_rets = self._get_forward_returns(codes, date)
        self._log(f"  有T+1数据的股票: {len(forward_rets)}")

        if len(forward_rets) < 50:
            self._log("  T+1数据不足，跳过")
            return []

        # 3. 计算因子值
        factor_values = self._compute_factor_values(date, list(forward_rets.keys()))

        # 4. 计算每个因子的IC
        records = []
        all_factors = set()
        for fv in factor_values.values():
            all_factors.update(fv.keys())

        for factor_name in sorted(all_factors):
            factor_vals = []
            rets = []
            valid_codes = []

            for code, fv in factor_values.items():
                if factor_name in fv and code in forward_rets:
                    factor_vals.append(fv[factor_name])
                    rets.append(forward_rets[code])
                    valid_codes.append(code)

            if len(factor_vals) < 30:
                continue

            # Spearman IC
            ic, p_value = spearmanr(factor_vals, rets)

            records.append({
                'date': date,
                'factor_name': factor_name,
                'ic': float(ic),
                'p_value': float(p_value) if not np.isnan(p_value) else None,
                'n_stocks': len(factor_vals),
                'valid_codes': valid_codes[:5],  # 仅记录前5个用于验证
            })

            self._log(f"  {factor_name}: IC={ic:.4f}, p={p_value:.4f}")

        return records

    def save_ic_records(self, records: List[Dict], db_path: str):
        """保存IC记录到factors.db"""
        if not records:
            return

        conn = sqlite3.connect(db_path)

        # 创建表（如果不存在）
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ic_history (
                date TEXT,
                factor_name TEXT,
                ic REAL,
                p_value REAL,
                n_stocks INTEGER,
                PRIMARY KEY (date, factor_name)
            )
        """)

        # 删除旧记录
        for record in records:
            conn.execute(
                "DELETE FROM ic_history WHERE date = ? AND factor_name = ?",
                (record['date'], record['factor_name'])
            )

        # 插入新记录
        for record in records:
            conn.execute(
                """INSERT INTO ic_history (date, factor_name, ic, p_value, n_stocks)
                   VALUES (?, ?, ?, ?, ?)""",
                (record['date'], record['factor_name'], record['ic'],
                 record['p_value'], record['n_stocks'])
            )

        conn.commit()
        conn.close()
        self._log(f"保存 {len(records)} 条IC记录到 {db_path}")

    def update_factor_status(self, db_path: str, window: int = 20):
        """更新因子状态（含自动淘汰）"""
        conn = sqlite3.connect(db_path)

        # 检查旧表结构，兼容不同版本
        cols_info = conn.execute('PRAGMA table_info(factor_status)').fetchall()
        col_names = [c[1] for c in cols_info]

        # 如果表存在但列不匹配，重建表
        if 'factor_name' in col_names:
            expected = {'factor_name', 'mean_ic', 'ic_ir', 'positive_ratio', 'n_days', 'status', 'last_updated'}
            actual = set(col_names)
            if not expected.issubset(actual):
                self._log(f"  factor_status 表结构不匹配，重建表")
                conn.execute('DROP TABLE IF EXISTS factor_status')
                conn.execute("""
                    CREATE TABLE factor_status (
                        factor_name TEXT PRIMARY KEY,
                        category TEXT,
                        mean_ic REAL,
                        ic_ir REAL,
                        positive_ratio REAL,
                        n_days INTEGER,
                        status TEXT,
                        last_updated TEXT
                    )
                """)

        # 计算统计
        rows = conn.execute(
            "SELECT factor_name, ic, p_value FROM ic_history ORDER BY date DESC"
        ).fetchall()

        factor_stats = {}
        for factor_name, ic, p_value in rows:
            if factor_name not in factor_stats:
                factor_stats[factor_name] = {'ics': [], 'p_values': []}
            factor_stats[factor_name]['ics'].append(ic)
            if p_value is not None:
                factor_stats[factor_name]['p_values'].append(p_value)

        for factor_name, stats in factor_stats.items():
            ics = stats['ics'][:window]
            p_values = stats['p_values']

            if not ics:
                continue

            mean_ic = float(np.mean(ics))
            abs_ics = [abs(x) for x in ics]
            ic_ir = mean_ic / float(np.std(ics)) if np.std(ics) > 0 else 0.0
            positive_ratio = sum(1 for x in ics if x > 0) / len(ics)
            n_days = len(ics)

            # 淘汰判定：IC均值绝对值<0.02且p>0.1
            status = 'active'
            if abs(mean_ic) < 0.02 and p_values and np.mean(p_values) > 0.1:
                status = 'eliminated'

            conn.execute("""
                INSERT INTO factor_status (factor_name, category, mean_ic, ic_ir, positive_ratio, n_days, status, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(factor_name) DO UPDATE SET
                    mean_ic = excluded.mean_ic,
                    ic_ir = excluded.ic_ir,
                    positive_ratio = excluded.positive_ratio,
                    n_days = excluded.n_days,
                    status = excluded.status,
                    last_updated = excluded.last_updated
            """, (factor_name, 'technical', mean_ic, ic_ir, positive_ratio, n_days, status, datetime.now().strftime('%Y-%m-%d')))

        conn.commit()
        conn.close()
        self._log(f"因子状态更新完成")

    def generate_report(self, records: List[Dict]):
        """生成IC报告"""
        output_dir = os.path.join(WORK_DIR, 'out_data')
        os.makedirs(output_dir, exist_ok=True)

        date = records[0]['date'] if records else datetime.now().strftime('%Y-%m-%d')
        output_path = os.path.join(output_dir, f'ic_report_{date}.json')

        # 按日期分组统计
        report = {
            'date': date,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_factors': len(records),
            'records': records,
            'summary': {
                'avg_ic': float(np.mean([r['ic'] for r in records])) if records else 0.0,
                'max_ic': float(max([r['ic'] for r in records], key=abs)) if records else 0.0,
                'min_ic': float(min([r['ic'] for r in records])) if records else 0.0,
                'significant_count': sum(1 for r in records if r['p_value'] is not None and r['p_value'] < 0.05),
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        self._log(f"报告已生成: {output_path}")
        self._log(f"  摘要: {report['summary']}")

        return report

    def _log(self, msg: str):
        print(msg)
        self._log_buffer.append(msg)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='每日因子IC计算')
    parser.add_argument('--date', type=str, default=None, help='计算日期 (YYYY-MM-DD)')
    parser.add_argument('--days', type=int, default=1, help='回算天数（默认1天，指定>1则滚动计算）')
    parser.add_argument('--report-only', action='store_true', help='仅生成报告，不重新计算')
    args = parser.parse_args()

    calc = DailyICCompute()

    if args.date:
        target_date = args.date
    else:
        # 用DB最新日期，但IC计算需要前一个交易日的因子×当日涨幅
        # 所以用 "上一个交易日" 作为因子日期
        conn = sqlite3.connect(calc.db_path)
        max_date = conn.execute("SELECT MAX(date) FROM daily_k").fetchone()[0]
        # 找max_date之前的上一个交易日
        prev_date = conn.execute(
            "SELECT MAX(date) FROM daily_k WHERE date < ?",
            (max_date,)
        ).fetchone()[0]
        conn.close()
        target_date = prev_date or max_date

    if args.report_only:
        # 从DB读取已有记录
        store_path = os.path.join(WORK_DIR, 'data', 'factors.db')
        if os.path.exists(store_path):
            conn = sqlite3.connect(store_path)
            rows = conn.execute(
                "SELECT date, factor_name, ic, p_value, n_stocks FROM ic_history"
            ).fetchall()
            conn.close()
            records = [
                {'date': r[0], 'factor': r[1], 'ic': r[2],
                 'p_value': r[3], 'n_stocks': r[4]} for r in rows
            ]
            calc.generate_report(records)
        else:
            print('factors.db 不存在，请先运行计算')
        return

    print(f'=' * 60)
    print(f'  每日因子IC计算 @ {target_date}')
    print(f'=' * 60)

    # 计算
    records = calc.compute_ic_for_date(target_date)
    if not records:
        print('  当日无IC记录（可能是非交易日或数据不足）')
        return

    # 保存到factors.db
    store_path = os.path.join(WORK_DIR, 'data', 'factors.db')
    calc.save_ic_records(records, store_path)

    # 生成报告
    calc.generate_report(records)

    # 如果指定了-days，则滚动计算历史IC
    if args.days > 1:
        print(f"\n滚动计算过去 {args.days} 天IC...")
        dates = calc._get_trading_dates(target_date, args.days)
        for d in dates[:-1]:  # 跳过最后一天（已计算）
            recs = calc.compute_ic_for_date(d)
            if recs:
                calc.save_ic_records(recs, store_path)

    # 更新因子状态
    calc.update_factor_status(store_path)

    print(f"\n完成！共计算 {len(records)} 个因子IC")


if __name__ == '__main__':
    main()
