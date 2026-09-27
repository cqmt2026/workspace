# -*- coding: utf-8 -*-
"""
每日因子全量计算 + 持久化脚本（优化版）
================================
功能：
  1. 从DB读取当日全市场K线数据（只加载最近120天）
  2. 计算技术因子（全市场，批量高效）
  3. 计算板块因子（全市场，本地RPS数据）
  4. 批量写入 factors.db 的 factors 表

执行时机：收盘后16:35（K线入库后），建议16:45
用法：
  python scripts/daily_factor_compute.py                      # 当日计算
  python scripts/daily_factor_compute.py --date 2026-07-03    # 指定日期
  python scripts/daily_factor_compute.py --status              # 查看覆盖状态
  python scripts/daily_factor_compute.py --backfill 7         # 回填7天
  python scripts/daily_factor_compute.py --moneyflow          # 补充资金流因子
"""
import io
import sys
import os
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import numpy as np
import pandas as pd

# 立即刷新输出（兼容Windows的__builtins__可能为dict的情况）
import builtins as _builtins
print = lambda *a, **kw: _builtins.print(*a, **kw, flush=True)

WORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORK_DIR)

DB_PATH = r'F:\market_data.db'
FACTORS_DB = os.path.join(WORK_DIR, 'data', 'factors.db')

from alice_quant.features.calculators import (
    TechnicalFactors, MoneyFlowFactors, SectorFactors,
    FundamentalFactors, SentimentFactors,
    MomentumFactors, ChipFactors
)

# 最大数据窗口（天），足够计算所有因子
MAX_DATA_DAYS = 120


def _compute_code_factors(code: str, date: str, df: pd.DataFrame, tf: 'TechnicalFactors', mf: 'MomentumFactors', cf: 'ChipFactors', recs: list):
    """计算单只股票的所有技术因子（辅助函数，避免缩进问题）
    
    Args:
        tf, mf, cf: 已创建的计算器实例（调用方复用，避免每只股票重建）
    """
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    volume = df['volume'].values

    # 基础技术因子
    s5 = tf.ma(pd.Series(close), 5)
    if not s5.empty and not np.isnan(s5.iloc[-1]):
        recs.append((date, code, 'ma_5', float(s5.iloc[-1])))
    s20 = tf.ma(pd.Series(close), 20)
    if not s20.empty and not np.isnan(s20.iloc[-1]):
        recs.append((date, code, 'ma_20', float(s20.iloc[-1])))
    s60 = tf.ma(pd.Series(close), 60)
    if not s60.empty and not np.isnan(s60.iloc[-1]):
        recs.append((date, code, 'ma_60', float(s60.iloc[-1])))
    sr = tf.rsi(pd.Series(close), 14)
    if not sr.empty and not np.isnan(sr.iloc[-1]):
        recs.append((date, code, 'rsi_14', float(sr.iloc[-1])))
    sv = tf.volume_ratio(pd.Series(volume), 5)
    if not sv.empty and not np.isnan(sv.iloc[-1]):
        recs.append((date, code, 'vol_ratio', float(sv.iloc[-1])))
    # pct_chg_1d: 检测日期连续性，如有跳日则跳过（不写入错误值）
    pc1 = tf.pct_change(pd.Series(close), 1)
    if not pc1.empty and not np.isnan(pc1.iloc[-1]):
        # 检查最近两行日期是否连续
        dates = df['date'].values
        day_gap = False
        if len(dates) >= 2:
            try:
                from datetime import datetime, timedelta
                last_date = datetime.strptime(str(dates[-1])[:10], '%Y-%m-%d')
                prev_date = datetime.strptime(str(dates[-2])[:10], '%Y-%m-%d')
                if (last_date - prev_date).days > 1:
                    day_gap = True
            except:
                pass
        if not day_gap:
            recs.append((date, code, 'pct_chg_1d', float(pc1.iloc[-1])))
    pc5 = tf.pct_change(pd.Series(close), 5)
    if not pc5.empty and not np.isnan(pc5.iloc[-1]):
        recs.append((date, code, 'pct_chg_5d', float(pc5.iloc[-1])))

    # 新技术因子
    satr = tf.atr(pd.Series(high), pd.Series(low), pd.Series(close), 14)
    if not satr.empty and not np.isnan(satr.iloc[-1]):
        recs.append((date, code, 'atr_14', float(satr.iloc[-1])))
    sobv = tf.obv(pd.Series(close), pd.Series(volume))
    if not sobv.empty and not np.isnan(sobv.iloc[-1]):
        recs.append((date, code, 'obv', float(sobv.iloc[-1])))
    swr = tf.wr(pd.Series(close), pd.Series(high), pd.Series(low), 14)
    if not swr.empty and not np.isnan(swr.iloc[-1]):
        recs.append((date, code, 'wr_14', float(swr.iloc[-1])))
    scci = tf.cci(pd.Series(close), pd.Series(high), pd.Series(low), 20)
    if not scci.empty and not np.isnan(scci.iloc[-1]):
        recs.append((date, code, 'cci_20', float(scci.iloc[-1])))
    svwap = tf.vwap(pd.Series(close), pd.Series(volume), 5)
    if not svwap.empty and not np.isnan(svwap.iloc[-1]):
        recs.append((date, code, 'vwap_5', float(svwap.iloc[-1])))
    svol = tf.volatility(pd.Series(close), 20)
    if not svol.empty and not np.isnan(svol.iloc[-1]):
        recs.append((date, code, 'volatility_20', float(svol.iloc[-1])))

    # 动量加速度因子
    smacd = mf.macd_bar(pd.Series(close), 12, 26, 9)
    if not smacd.empty and not np.isnan(smacd.iloc[-1]):
        recs.append((date, code, 'macd_bar', float(smacd.iloc[-1])))
    scross = mf.macd_cross(pd.Series(close), 12, 26, 9)
    if not scross.empty and not np.isnan(scross.iloc[-1]):
        recs.append((date, code, 'macd_cross', float(scross.iloc[-1])))
    smacd2 = mf.macd_second_peak(pd.Series(close), 12, 26, 9)
    if not smacd2.empty and not np.isnan(smacd2.iloc[-1]):
        recs.append((date, code, 'macd_second_peak', float(smacd2.iloc[-1])))
    saccel = mf.acceleration(pd.Series(close), 5, 10)
    if not saccel.empty and not np.isnan(saccel.iloc[-1]):
        recs.append((date, code, 'acceleration', float(saccel.iloc[-1])))
    sbreakout = mf.breakout_strength(pd.Series(close), pd.Series(high), 20)
    if not sbreakout.empty and not np.isnan(sbreakout.iloc[-1]):
        recs.append((date, code, 'breakout_strength', float(sbreakout.iloc[-1])))

    # 筹码分布因子
    savg = cf.avg_cost(pd.Series(close), pd.Series(volume), 60)
    if not savg.empty and not np.isnan(savg.iloc[-1]):
        recs.append((date, code, 'avg_cost', float(savg.iloc[-1])))
    sprofit = cf.profit_ratio(pd.Series(close), savg)
    if not sprofit.empty and not np.isnan(sprofit.iloc[-1]):
        recs.append((date, code, 'profit_ratio', float(sprofit.iloc[-1])))
    sconc = cf.concentration(pd.Series(close), pd.Series(volume), 20)
    if not sconc.empty and not np.isnan(sconc.iloc[-1]):
        recs.append((date, code, 'concentration', float(sconc.iloc[-1])))


class DailyFactorCompute:
    """每日因子全量计算（优化版）"""

    def __init__(self, db_path: str = DB_PATH, factors_db: str = FACTORS_DB):
        self.db_path = db_path
        self.factors_db = factors_db
        self._conn = None
        self._fdb_conn = None

    def _log(self, msg: str):
        print(f'  [Factor] {msg}')

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
        return self._conn

    def _get_fdb(self) -> sqlite3.Connection:
        if self._fdb_conn is None:
            os.makedirs(os.path.dirname(self.factors_db), exist_ok=True)
            self._fdb_conn = sqlite3.connect(self.factors_db, timeout=30)
            self._fdb_conn.execute("""CREATE TABLE IF NOT EXISTS factors (
                date TEXT, code TEXT, factor_name TEXT, value REAL,
                updated_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (date, code, factor_name)
            )""")
            self._fdb_conn.execute("""CREATE TABLE IF NOT EXISTS factor_coverage (
                date TEXT PRIMARY KEY, n_codes INTEGER, n_factors INTEGER,
                n_records INTEGER, elapsed_sec REAL
            )""")
        return self._fdb_conn

    def _get_codes(self, date: str) -> List[str]:
        conn = self._get_conn()
        return [r[0] for r in conn.execute(
            "SELECT code FROM daily_k WHERE date=? AND code NOT LIKE 'bj.%' "
            "AND code NOT LIKE 'sh.8%' AND code NOT LIKE 'sh.9%' AND close>0 AND volume>0",
            (date,)
        ).fetchall()]

    def _get_trading_dates(self, end_date: str, count: int = 30) -> List[str]:
        """获取最近的完整交易日列表"""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT date, COUNT(*) as cnt FROM daily_k "
            "WHERE date <= ? GROUP BY date HAVING cnt > 1000 "
            "ORDER BY date DESC LIMIT ?",
            (end_date, count + 10)
        ).fetchall()
        dates = sorted([r[0] for r in rows])
        return dates[-count:] if len(dates) > count else dates

    def compute_technical(self, date: str, codes: List[str]) -> int:
        """批量计算技术因子（全市场），返回记录数
        
        优化：只加载最近MAX_DATA_DAYS天的数据，足够所有因子计算
        """
        conn = self._get_conn()
        fdb = self._get_fdb()
        tf = TechnicalFactors()
        mf = MomentumFactors()
        cf = ChipFactors()
        total = 0
        batch_size = 500

        # 计算数据起始日期（只加载必要窗口）
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        start_date = (date_obj - timedelta(days=MAX_DATA_DAYS)).strftime('%Y-%m-%d')

        for bs in range(0, len(codes), batch_size):
            batch = codes[bs:bs + batch_size]
            ph = ','.join(['?'] * len(batch))
            rows = conn.execute(
                "SELECT code, date, close, volume, high, low FROM daily_k "
                f"WHERE code IN ({ph}) AND date>=? AND date<=? "
                "ORDER BY code, date ASC",
                batch + [start_date, date]
            ).fetchall()

            cd: Dict[str, list] = {}
            for r in rows:
                c = r[0]
                if c not in cd:
                    cd[c] = []
                cd[c].append({'date': r[1], 'close': r[2], 'volume': r[3], 'high': r[4], 'low': r[5]})

            recs = []
            for code in batch:
                k = cd.get(code, [])
                if len(k) < 10:
                    continue
                df = pd.DataFrame(k)
                try:
                    _compute_code_factors(code, date, df, tf, mf, cf, recs)
                except Exception:
                    pass

            if recs:
                fdb.executemany(
                    "INSERT OR REPLACE INTO factors VALUES (?,?,?,?,datetime('now'))", recs)
                fdb.commit()
            total += len(recs)

            # 进度显示
            if (bs + batch_size) % 1000 == 0 or bs + batch_size >= len(codes):
                self._log(f'技术因子: {min(bs+batch_size, len(codes))}/{len(codes)}')

        return total

    def compute_money_flow(self, date: str, codes: List[str], limit: int = 1000) -> int:
        """资金流因子（前limit只样本，API请求较慢）"""
        fdb = self._get_fdb()
        sample = codes[:limit]
        total = 0
        for fname in ['flow_intensity', 'flow_persistence']:
            recs = []
            for i, code in enumerate(sample):
                try:
                    val = getattr(MoneyFlowFactors, fname)(code, None)
                    if val is not None and not np.isnan(val):
                        recs.append((date, code, fname, float(val)))
                except Exception:
                    pass
                if (i + 1) % 100 == 0:
                    self._log(f'  资金流[{fname}]: {i+1}/{len(sample)}')
            if recs:
                fdb.executemany(
                    "INSERT OR REPLACE INTO factors VALUES (?,?,?,?,datetime('now'))", recs)
                fdb.commit()
                total += len(recs)
            self._log(f'  资金流[{fname}]: {len(recs)}条')
        return total

    def compute_sector(self, date: str, codes: List[str]) -> int:
        """板块因子（全市场，本地RPS数据）"""
        fdb = self._get_fdb()
        total = 0
        for fname in ['sector_phase', 'sector_rps_5d', 'relative_strength']:
            recs = []
            for code in codes:
                try:
                    val = getattr(SectorFactors, fname)(code, None)
                    if val is not None and not np.isnan(val):
                        recs.append((date, code, fname, float(val)))
                except Exception:
                    pass
            if recs:
                fdb.executemany(
                    "INSERT OR REPLACE INTO factors VALUES (?,?,?,?,datetime('now'))", recs)
                fdb.commit()
                total += len(recs)
            self._log(f'  {fname}: {len(recs)}条')
        return total

    def compute_date(self, date: str, skip_money_flow: bool = False, skip_fundamental: bool = False) -> dict:
        """计算指定日期的所有因子

        Args:
            date: 日期
            skip_money_flow: 是否跳过资金流因子（API慢）
            skip_fundamental: 是否跳过基本面因子
        """
        t0 = time.time()
        self._log(f'开始计算 {date}...')

        codes = self._get_codes(date)
        if not codes:
            self._log('无数据')
            return {'date': date, 'n_codes': 0, 'n_factors': 0, 'n_records': 0}

        self._log(f'股票: {len(codes)}只')

        # 1. 技术因子（全市场，本地计算）
        t1 = time.time()
        n_tech = self.compute_technical(date, codes)
        self._log(f'技术因子: {n_tech}条, 耗时{time.time()-t1:.0f}s')

        # 2. 板块因子（全市场，本地数据）
        t2 = time.time()
        n_sector = self.compute_sector(date, codes)
        self._log(f'板块因子: {n_sector}条, 耗时{time.time()-t2:.0f}s')

        # 3. 资金流因子（可选，依赖API，默认跳过）
        n_flow = 0
        if not skip_money_flow:
            t3 = time.time()
            n_flow = self.compute_money_flow(date, codes, limit=500)
            self._log(f'资金流因子: {n_flow}条, 耗时{time.time()-t3:.0f}s')

        # 统计
        fdb = self._get_fdb()
        row = fdb.execute(
            "SELECT COUNT(DISTINCT code), COUNT(DISTINCT factor_name), COUNT(*) "
            "FROM factors WHERE date=?", (date,)
        ).fetchone()
        elapsed = time.time() - t0
        fdb.execute(
            "INSERT OR REPLACE INTO factor_coverage VALUES (?,?,?,?,?)",
            (date, row[0], row[1], row[2], round(elapsed, 1))
        )
        fdb.commit()

        self._log(f'完成! 股票{row[0]}只, 因子{row[1]}个, 记录{row[2]:,}条, 总耗时{elapsed:.0f}s')

        return {
            'date': date, 'n_codes': row[0], 'n_factors': row[1],
            'n_records': row[2], 'elapsed': round(elapsed, 1),
        }

    def get_coverage(self) -> dict:
        fdb = self._get_fdb()
        try:
            r = fdb.execute(
                "SELECT MIN(date), MAX(date), COUNT(DISTINCT date), "
                "SUM(n_records), AVG(n_codes) FROM factor_coverage"
            ).fetchone()
            return {'min_date': r[0] or '', 'max_date': r[1] or '',
                    'n_days': r[2] or 0, 'total_records': r[3] or 0,
                    'avg_codes': round(r[4] or 0, 0)}
        except Exception:
            return {}

    def close(self):
        if self._fdb_conn:
            self._fdb_conn.close()
        if self._conn:
            self._conn.close()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='每日因子全量计算')
    parser.add_argument('--date', type=str, default=None)
    parser.add_argument('--backfill', type=int, default=0, help='回填N天')
    parser.add_argument('--status', action='store_true')
    parser.add_argument('--moneyflow', action='store_true', help='补充资金流因子')
    args = parser.parse_args()

    calc = DailyFactorCompute()

    if args.backfill:
        print(f'回填最近{args.backfill}天...')
        conn = sqlite3.connect(DB_PATH)
        latest = conn.execute("SELECT MAX(date) FROM daily_k").fetchone()[0]
        conn.close()
        dates = calc._get_trading_dates(latest, args.backfill)
        print(f'日期范围: {dates[0]} ~ {dates[-1]}, 共{len(dates)}天')
        print('注意: 回填跳过资金流因子（依赖API），仅在每日Cron中计算')
        for i, d in enumerate(dates):
            print(f'[{i+1}/{len(dates)}] {d}')
            calc.compute_date(d, skip_money_flow=True, skip_fundamental=True)
        calc.close()
        return

    # 正常模式：默认跳过资金流（API慢），可用--moneyflow补充
    if args.status:
        s = calc.get_coverage()
        print(f'因子覆盖状态:')
        print(f'  日期范围: {s["min_date"]} ~ {s["max_date"]}')
        print(f'  天数: {s["n_days"]}')
        print(f'  总记录数: {s["total_records"]:,}')
        print(f'  日均股票: {s["avg_codes"]:.0f}')
        calc.close()
        return

    if args.date:
        target = args.date
    else:
        conn = sqlite3.connect(DB_PATH)
        target = conn.execute("SELECT MAX(date) FROM daily_k").fetchone()[0]
        conn.close()
    if not target:
        print('无法获取最新交易日')
        return

    print(f'=' * 60)
    print(f'  每日因子全量计算 @ {target}')
    print(f'=' * 60)

    result = calc.compute_date(target, skip_money_flow=not args.moneyflow)
    print(f'\n结果: {result["n_codes"]}只股票, {result["n_factors"]}个因子, {result["n_records"]:,}条记录')
    print(f'耗时: {result["elapsed"]}s')

    calc.close()


if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()
