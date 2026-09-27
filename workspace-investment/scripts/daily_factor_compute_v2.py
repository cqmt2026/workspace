# -*- coding: utf-8 -*-
"""
每日因子全量计算（优化版，避免API卡死）
================================
功能：
  1. 技术因子（全市场，本地计算）
  2. 板块因子（全市场，批量SQL避免频繁DB连接）
  3. 资金流因子（前1000只，跳过）
  4. 基本面因子（跳过）

执行时机：收盘后16:45
"""
import io
import sys
import os
import sqlite3
import time
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

# 立即刷新输出
import builtins as _builtins
print = lambda *a, **kw: _builtins.print(*a, **kw, flush=True)

WORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORK_DIR)

DB_PATH = r'F:\market_data.db'
FACTORS_DB = os.path.join(WORK_DIR, 'data', 'factors.db')

from alice_quant.features.calculators import (
    TechnicalFactors, MoneyFlowFactors, SectorFactors,
    MomentumFactors, ChipFactors
)

# RPS历史文件路径
HIST_DIR = os.path.join(WORK_DIR, 'out_data', 'rps_history')
CACHE_FILE = os.path.join(WORK_DIR, 'data', 'stock_board_cache.json')


def _compute_code_factors(code: str, date: str, df: pd.DataFrame, tf: 'TechnicalFactors', mf: 'MomentumFactors', cf: 'ChipFactors', recs: list):
    """计算单只股票的所有技术因子"""
    s5 = tf.ma(df['close'], 5)
    if not s5.empty and not np.isnan(s5.iloc[-1]):
        recs.append((date, code, 'ma_5', float(s5.iloc[-1])))
    s20 = tf.ma(df['close'], 20)
    if not s20.empty and not np.isnan(s20.iloc[-1]):
        recs.append((date, code, 'ma_20', float(s20.iloc[-1])))
    s60 = tf.ma(df['close'], 60)
    if not s60.empty and not np.isnan(s60.iloc[-1]):
        recs.append((date, code, 'ma_60', float(s60.iloc[-1])))
    sr = tf.rsi(df['close'], 14)
    if not sr.empty and not np.isnan(sr.iloc[-1]):
        recs.append((date, code, 'rsi_14', float(sr.iloc[-1])))
    sv = tf.volume_ratio(df['volume'], 5)
    if not sv.empty and not np.isnan(sv.iloc[-1]):
        recs.append((date, code, 'vol_ratio', float(sv.iloc[-1])))
    pc1 = tf.pct_change(df['close'], 1)
    if not pc1.empty and not np.isnan(pc1.iloc[-1]):
        dates = df['date'].values
        day_gap = False
        if len(dates) >= 2:
            try:
                last_date = datetime.strptime(str(dates[-1])[:10], '%Y-%m-%d')
                prev_date = datetime.strptime(str(dates[-2])[:10], '%Y-%m-%d')
                if (last_date - prev_date).days > 1:
                    day_gap = True
            except:
                pass
        if not day_gap:
            recs.append((date, code, 'pct_chg_1d', float(pc1.iloc[-1])))
    pc5 = tf.pct_change(df['close'], 5)
    if not pc5.empty and not np.isnan(pc5.iloc[-1]):
        recs.append((date, code, 'pct_chg_5d', float(pc5.iloc[-1])))
    satr = tf.atr(df['high'], df['low'], df['close'], 14)
    if not satr.empty and not np.isnan(satr.iloc[-1]):
        recs.append((date, code, 'atr_14', float(satr.iloc[-1])))
    sobv = tf.obv(df['close'], df['volume'])
    if not sobv.empty and not np.isnan(sobv.iloc[-1]):
        recs.append((date, code, 'obv', float(sobv.iloc[-1])))
    swr = tf.wr(df['close'], df['high'], df['low'], 14)
    if not swr.empty and not np.isnan(swr.iloc[-1]):
        recs.append((date, code, 'wr_14', float(swr.iloc[-1])))
    scci = tf.cci(df['close'], df['high'], df['low'], 20)
    if not scci.empty and not np.isnan(scci.iloc[-1]):
        recs.append((date, code, 'cci_20', float(scci.iloc[-1])))
    svwap = tf.vwap(df['close'], df['volume'], 5)
    if not svwap.empty and not np.isnan(svwap.iloc[-1]):
        recs.append((date, code, 'vwap_5', float(svwap.iloc[-1])))
    svol = tf.volatility(df['close'], 20)
    if not svol.empty and not np.isnan(svol.iloc[-1]):
        recs.append((date, code, 'volatility_20', float(svol.iloc[-1])))
    # 动量加速度因子
    smacd = mf.macd_bar(df['close'], 12, 26, 9)
    if not smacd.empty and not np.isnan(smacd.iloc[-1]):
        recs.append((date, code, 'macd_bar', float(smacd.iloc[-1])))
    scross = mf.macd_cross(df['close'], 12, 26, 9)
    if not scross.empty and not np.isnan(scross.iloc[-1]):
        recs.append((date, code, 'macd_cross', float(scross.iloc[-1])))
    smacd2 = mf.macd_second_peak(df['close'], 12, 26, 9)
    if not smacd2.empty and not np.isnan(smacd2.iloc[-1]):
        recs.append((date, code, 'macd_second_peak', float(smacd2.iloc[-1])))
    saccel = mf.acceleration(df['close'], 5, 10)
    if not saccel.empty and not np.isnan(saccel.iloc[-1]):
        recs.append((date, code, 'acceleration', float(saccel.iloc[-1])))
    sbreakout = mf.breakout_strength(df['close'], df['high'], 20)
    if not sbreakout.empty and not np.isnan(sbreakout.iloc[-1]):
        recs.append((date, code, 'breakout_strength', float(sbreakout.iloc[-1])))
    # 筹码分布因子
    savg = cf.avg_cost(df['close'], df['volume'], 60)
    if not savg.empty and not np.isnan(savg.iloc[-1]):
        recs.append((date, code, 'avg_cost', float(savg.iloc[-1])))
    sprofit = cf.profit_ratio(df['close'], savg)
    if not sprofit.empty and not np.isnan(sprofit.iloc[-1]):
        recs.append((date, code, 'profit_ratio', float(sprofit.iloc[-1])))
    sconc = cf.concentration(df['close'], df['volume'], 20)
    if not sconc.empty and not np.isnan(sconc.iloc[-1]):
        recs.append((date, code, 'concentration', float(sconc.iloc[-1])))


class DailyFactorComputeOptimized:
    """每日因子全量计算（优化版）"""

    def __init__(self, db_path: str = DB_PATH, factors_db: str = FACTORS_DB):
        self.db_path = db_path
        self.factors_db = factors_db
        self._conn = None
        self._fdb_conn = None
        self._rps_cache = None
        self._rps_date = None
        self._board_mapping = None

    def _log(self, msg: str):
        print(f'  [Factor] {msg}')

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, timeout=30)
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

    def _load_rps(self):
        """加载RPS数据（一次性）"""
        if self._rps_cache is not None:
            return
        if not os.path.exists(HIST_DIR):
            self._rps_cache = []
            return
        import json
        files = sorted([f for f in os.listdir(HIST_DIR)
                       if f.startswith('RPS_board_') and f.endswith('.json')])
        if not files:
            self._rps_cache = []
            return
        with open(os.path.join(HIST_DIR, files[-1]), 'r', encoding='utf-8') as f:
            data = json.load(f)
        self._rps_cache = data.get('rps_data', [])
        self._rps_date = files[-1].replace('RPS_board_', '').replace('.json', '')
        self._log(f'RPS: {self._rps_date}, {len(self._rps_cache)}板块')

    def _load_board_mapping(self):
        """加载股票→板块映射（一次性）"""
        if self._board_mapping is not None:
            return
        import json
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                self._board_mapping = json.load(f)
            self._log(f'板块映射: {len(self._board_mapping)}只')
        else:
            self._board_mapping = {}

    def _code_to_db_code(self, code: str) -> str:
        """代码转为数据库格式"""
        clean = code.replace('sh.', '').replace('sz.', '').replace('bj.', '')
        return 'sh.' + clean if clean.startswith('6') else 'sz.' + clean

    def compute_technical(self, date: str, codes: List[str]) -> int:
        """批量计算技术因子（全市场）"""
        conn = self._get_conn()
        fdb = self._get_fdb()
        tf = TechnicalFactors()
        mf = MomentumFactors()
        cf = ChipFactors()
        total = 0
        batch_size = 500

        for bs in range(0, len(codes), batch_size):
            batch = codes[bs:bs + batch_size]
            ph = ','.join(['?'] * len(batch))
            params = [self._code_to_db_code(c) for c in batch]
            params.append(date)
            rows = conn.execute(
                "SELECT code, date, close, volume, high, low FROM daily_k "
                f"WHERE code IN ({ph}) AND date>='2026-01-01' AND date<=? "
                "ORDER BY code, date ASC",
                params
            ).fetchall()

            cd: Dict[str, list] = {}
            for r in rows:
                c = r[0]
                if c not in cd:
                    cd[c] = []
                cd[c].append({'date': r[1], 'close': r[2], 'volume': r[3], 'high': r[4], 'low': r[5]})

            recs = []
            for code in batch:
                k = cd.get(self._code_to_db_code(code), [])
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
            if (bs + batch_size) % 2000 == 0 or bs + batch_size >= len(codes):
                self._log(f'技术因子: {min(bs+batch_size, len(codes))}/{len(codes)}, {total:,}条')

        return total

    def compute_sector(self, date: str, codes: List[str]) -> int:
        """批量计算板块因子（一次性加载数据，避免频繁DB连接）"""
        self._log(f'开始计算板块因子 {len(codes)}只...')
        fdb = self._get_fdb()
        conn = self._get_conn()

        # 1. 加载RPS数据
        self._load_rps()
        rps_map = {b['name']: b for b in (self._rps_cache or [])}

        # 2. 加载板块映射
        self._load_board_mapping()

        # 3. 批量获取所有股票5日涨幅
        self._log('批量获取5日涨幅...')
        stock_ret: Dict[str, float] = {}
        batch_size = 500
        for bs in range(0, len(codes), batch_size):
            batch = codes[bs:bs + batch_size]
            db_codes = [self._code_to_db_code(c) for c in batch]
            ph = ','.join(['?'] * len(db_codes))
            rows = conn.execute(
                f"SELECT code, date, close FROM daily_k WHERE code IN ({ph}) ORDER BY code, date DESC",
                db_codes
            ).fetchall()
            # 按代码聚合
            from collections import defaultdict
            cd: Dict[str, list] = defaultdict(list)
            for r in rows:
                cd[r[0]].append((r[1], r[2]))
            for db_code, closes in cd.items():
                if len(closes) < 2:
                    continue
                closes.sort(key=lambda x: x[0])
                recent = closes[-5:] if len(closes) >= 5 else closes
                if len(recent) >= 2 and recent[0][1] > 0:
                    ret = (recent[-1][1] - recent[0][1]) / recent[0][1] * 100
                    # 找到原始code
                    for c in batch:
                        if self._code_to_db_code(c) == db_code:
                            stock_ret[c] = ret
                            break

        # 4. 计算板块因子
        total = 0
        recs_phase = []
        recs_rps5 = []
        recs_rs = []
        for code in codes:
            clean = code.replace('sh.', '').replace('sz.', '').replace('bj.', '')
            board = self._board_mapping.get(clean)
            if not board or board not in rps_map:
                continue
            b = rps_map[board]
            rps_5d = b.get('rps_5d', 50)
            rps_10d = b.get('rps_10d', 50)
            # 分类
            acc = rps_5d > rps_10d + 5
            if rps_5d >= 80:
                phase = 8 if acc else 5
            elif rps_5d >= 60:
                phase = 4 if acc else 1
            elif rps_5d >= 40:
                phase = 2 if acc else 0
            elif rps_5d >= 20:
                phase = 1 if acc else -2
            else:
                phase = -1 if acc else -5
            board_ret = b.get('returns', {}).get('5', 0.0)
            s_ret = stock_ret.get(code, 0.0)
            rs = s_ret - board_ret

            recs_phase.append((date, code, 'sector_phase', float(phase)))
            recs_rps5.append((date, code, 'sector_rps_5d', float(rps_5d)))
            recs_rs.append((date, code, 'relative_strength', float(rs)))

        if recs_phase:
            fdb.executemany("INSERT OR REPLACE INTO factors VALUES (?,?,?,?,datetime('now'))", recs_phase)
            fdb.executemany("INSERT OR REPLACE INTO factors VALUES (?,?,?,?,datetime('now'))", recs_rps5)
            fdb.executemany("INSERT OR REPLACE INTO factors VALUES (?,?,?,?,datetime('now'))", recs_rs)
            fdb.commit()
            total = len(recs_phase) * 3

        self._log(f'板块因子: {total}条')
        return total

    def compute_date(self, date: str) -> dict:
        """计算指定日期"""
        t0 = time.time()
        self._log(f'开始计算 {date}...')
        codes = []
        conn = self._get_conn()
        for bs in range(0, 5000, 500):
            rows = conn.execute(
                "SELECT code FROM daily_k WHERE date=? AND code NOT LIKE 'bj.%' "
                "AND code NOT LIKE 'sh.8%' AND code NOT LIKE 'sh.9%' AND close>0 AND volume>0 "
                "LIMIT 500 OFFSET ?",
                (date, bs)
            ).fetchall()
            codes.extend([r[0] for r in rows])
        if not codes:
            self._log('无数据')
            return {'date': date, 'n_codes': 0, 'n_factors': 0, 'n_records': 0}

        self._log(f'股票: {len(codes)}只')

        # 1. 技术因子
        t1 = time.time()
        n_tech = self.compute_technical(date, codes)
        self._log(f'技术因子: {n_tech}条, 耗时{time.time()-t1:.0f}s')

        # 2. 板块因子
        t2 = time.time()
        n_sector = self.compute_sector(date, codes)
        self._log(f'板块因子: {n_sector}条, 耗时{time.time()-t2:.0f}s')

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
        return {'date': date, 'n_codes': row[0], 'n_factors': row[1], 'n_records': row[2], 'elapsed': round(elapsed, 1)}

    def close(self):
        if self._fdb_conn:
            self._fdb_conn.close()
        if self._conn:
            self._conn.close()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='每日因子全量计算（优化版）')
    parser.add_argument('--date', type=str, default=None)
    args = parser.parse_args()

    calc = DailyFactorComputeOptimized()

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
    result = calc.compute_date(target)
    print(f'\n结果: {result["n_codes"]}只股票, {result["n_factors"]}个因子, {result["n_records"]:,}条记录')
    print(f'耗时: {result["elapsed"]}s')
    calc.close()


if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()
