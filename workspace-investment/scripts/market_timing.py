# -*- coding: utf-8 -*-
"""
大盘择时开关 (Market Timing)
============================
bob框架启发：大盘不好时自动降低仓位或空仓。

基于三个维度综合判断：
1. 涨停家数（市场情绪）
2. 全市场成交量（资金活跃度）
3. 指数趋势（大盘方向）

用法：
    python scripts/market_timing.py               # 今天
    python scripts/market_timing.py 2026-07-09    # 指定日期
    python scripts/market_timing.py --status       # 查看近期趋势
"""
import sys, os, json, sqlite3, urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB = r'F:\market_data.db'
OUT_DIR = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\out_data')
os.makedirs(OUT_DIR, exist_ok=True)


def _fetch_index_from_tencent(code: str) -> dict:
    """从统一接口获取指数实时行情"""
    from scripts.data_api import DataAPI
    try:
        idx = DataAPI.get_index(code)
        if idx:
            return {
                'price': idx['price'],
                'chg_pct': idx['chg_pct'],
            }
    except:
        pass
    return {}


def _get_index_data_from_wind(date: str) -> dict:
    """从万得获取指数数据（兜底方案）"""
    import subprocess, json
    cli = r'C:\Users\Administrator\.agents\skills\wind-mcp-skill\scripts\cli.mjs'
    import os
    if not os.path.exists(cli):
        return {}
    try:
        # 取最近5个交易日的K线
        # 用date往前推30天确保能取到数据
        from datetime import datetime, timedelta
        dt = datetime.strptime(date, '%Y-%m-%d')
        start = (dt - timedelta(days=30)).strftime('%Y%m%d')
        end = dt.strftime('%Y%m%d')
        params = json.dumps({"windcode": "000001.SH", "begin_date": start, "end_date": end})
        cmd_list = ['node', cli, 'call', 'index_data', 'get_index_kline', params]
        proc = subprocess.run(cmd_list, capture_output=True, timeout=10,
                              encoding='utf-8', errors='replace')
        result = json.loads(proc.stdout)
        if not result.get('isError') and result.get('content'):
            text = result['content'][0]['text']
            data = json.loads(text)
            if data.get('data') and data['data'].get('rows'):
                rows = data['data']['rows']
                # 找date对应的行
                for row in rows:
                    trade_date = row[0][:10]  # '2026-07-09T...' -> '2026-07-09'
                    if trade_date == date:
                        close = float(row[2])
                        # 计算涨跌幅
                        if len(rows) >= 2:
                            prev_close = float(rows[-2][2])
                            chg_pct = round((close - prev_close) / prev_close * 100, 2)
                        else:
                            chg_pct = 0.0
                        return {'code': '000001.SH', 'close': close, 'chg_pct': chg_pct, 'source': 'wind'}
                # 没找到精确日期，用最新一行
                if rows:
                    last = rows[-1]
                    close = float(last[2])
                    return {'code': '000001.SH', 'close': close, 'chg_pct': 0.0, 'source': 'wind_latest'}
    except Exception:
        pass
    return {}


def _get_index_data_from_mx(date: str) -> dict:
    """从MX妙想搜索获取指数数据（第三级兜底）"""
    import sys, re
    mx_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts', 'mx_search_daily.py')
    if not os.path.exists(mx_path):
        return {}
    try:
        sys.path.insert(0, os.path.dirname(mx_path))
        from mx_search_daily import call_mx_search
        result = call_mx_search(f'上证指数{date}收盘价涨跌幅')
        if not result:
            return {}
        # 从搜索结果提取指数数据
        # 格式1: "沪指跌1%" 或 "沪指涨0.5%"
        m = re.search(r'沪指[跌涨]\s*([\d.]+)%', result)
        if m:
            chg_pct = float(m.group(1))
            if '跌' in m.group():
                chg_pct = -chg_pct
            # 提取收盘价
            m2 = re.search(r'收盘价为?(\d{3,5}\.?\d*)点', result)
            close = float(m2.group(1)) if m2 else 0
            return {'code': '000001.SH', 'close': close, 'chg_pct': chg_pct, 'source': 'mx'}
        # 格式2: "上证综合指数（点） 4,098.64 4,027.26 -1.74%"
        m = re.search(r'上证综合指数.*?([\d,]+\.[\d]+).*?([\d,]+\.[\d]+).*?([\-\d.]+)%', result)
        if m:
            close = float(m.group(2).replace(',', ''))
            chg_pct = float(m.group(3))
            return {'code': '000001.SH', 'close': close, 'chg_pct': chg_pct, 'source': 'mx'}
    except Exception:
        pass
    return {}


def _get_index_data(date: str) -> dict:
    """获取指数数据（万得优先，腾讯API备用，MX搜索兜底）"""
    # 万得：数据最准确，支持历史数据
    wind = _get_index_data_from_wind(date)
    if wind and wind.get('close'):
        return wind
    # 腾讯实时API（仅交易日有效）
    live = _fetch_index_from_tencent('sh000001')
    if live and live.get('price'):
        return {'code': 'sh000001', 'close': live['price'], 'chg_pct': live['chg_pct'], 'source': 'live'}
    # MX搜索兜底（周末/非交易时间）
    mx = _get_index_data_from_mx(date)
    if mx and mx.get('close'):
        return mx
    # 所有数据源均不可用，返回空数据（禁止用其他数据模拟大盘指数）
    return {'code': 'unknown', 'close': 0, 'chg_pct': 0, 'chg_5d': 0, 'source': 'none'}


def get_market_timing(date: str) -> Dict:
    """
    综合判断大盘环境

    返回:
        regime: '做多' / '谨慎' / '规避'
        position_limit: 仓位上限 (1.0 / 0.5 / 0.0)
        reason: 判断理由
        details: 各维度数据
    """
    conn = sqlite3.connect(DB)

    # 1. 涨停家数（市场情绪）
    # 优先从daily_zt表读取，如果没有则从daily_k自行计算
    today_zt = conn.execute(
        "SELECT COUNT(*) FROM daily_zt WHERE trade_date=?", (date,)
    ).fetchone()[0] or 0

    if today_zt == 0:
        # 兜底：从daily_k自行计算涨幅>9.5%的股票数
        today_zt = conn.execute(
            "SELECT COUNT(*) FROM daily_k WHERE date=? AND open>0 AND (close-open)/open*100 > 9.5",
            (date,)
        ).fetchone()[0] or 0

    prev_date = (datetime.strptime(date, '%Y-%m-%d') - timedelta(days=3)).strftime('%Y-%m-%d')
    prev_zt = conn.execute(
        "SELECT COUNT(*) FROM daily_zt WHERE trade_date=?", (prev_date,)
    ).fetchone()[0] or 0

    # 2. 指数趋势（以上证指数为准，腾讯API实时获取）
    idx_data = _get_index_data(date)
    idx_chg_5d = idx_data.get('chg_5d', 0) or idx_data.get('chg_pct', 0)
    idx_trend = 'unknown'
    if idx_data['source'] != 'none':
        if idx_chg_5d > 2:
            idx_trend = 'up'
        elif idx_chg_5d < -2:
            idx_trend = 'down'
        else:
            idx_trend = 'flat'

    # 3. 全市场成交量（近5日对比）
    vol_rows = conn.execute(
        "SELECT date, SUM(volume) FROM daily_k WHERE date<=? GROUP BY date ORDER BY date DESC LIMIT 5",
        (date,)
    ).fetchall()

    vol_trend = 'unknown'
    if len(vol_rows) >= 5:
        vols = [r[1] or 0 for r in reversed(vol_rows)]
        avg_vol = sum(vols) / len(vols)
        if avg_vol > 0:
            latest_vol_ratio = vols[-1] / avg_vol
            if latest_vol_ratio > 1.2:
                vol_trend = '放量'
            elif latest_vol_ratio < 0.8:
                vol_trend = '缩量'
            else:
                vol_trend = '正常'

    conn.close()

    # 综合判断
    zt_score = 0
    if today_zt >= 30:
        zt_score = 2
    elif today_zt >= 15:
        zt_score = 1
    else:
        zt_score = 0

    idx_score = 0
    if idx_trend == 'up':
        idx_score = 2
    elif idx_trend == 'flat':
        idx_score = 1
    else:
        idx_score = 0

    vol_score = 0
    if vol_trend == '放量':
        vol_score = 2
    elif vol_trend == '正常':
        vol_score = 1
    else:
        vol_score = 0

    total_score = zt_score + idx_score + vol_score

    # 判定
    if total_score >= 5:
        regime = '做多'
        position_limit = 1.0
        reason = f'涨停{today_zt}家+指数{idx_chg_5d:+.1f}%+{vol_trend}'
    elif total_score >= 3:
        regime = '谨慎'
        position_limit = 0.5
        reason = f'涨停{today_zt}家+指数{idx_chg_5d:+.1f}%+{vol_trend}'
    else:
        regime = '规避'
        position_limit = 0.0
        reason = f'涨停{today_zt}家+指数{idx_chg_5d:+.1f}%+{vol_trend}'

    return {
        'date': date,
        'regime': regime,
        'position_limit': position_limit,
        'reason': reason,
        'details': {
            'zt_count': today_zt,
            'zt_prev': prev_zt,
            'idx_chg_5d': round(idx_chg_5d, 2),
            'idx_trend': idx_trend,
            'vol_trend': vol_trend,
            'zt_score': zt_score,
            'idx_score': idx_score,
            'vol_score': vol_score,
            'total_score': total_score,
        },
    }


def get_recent_trend(days: int = 10) -> list:
    """获取近期趋势"""
    conn = sqlite3.connect(DB)
    dates = conn.execute(
        "SELECT DISTINCT date FROM daily_k ORDER BY date DESC LIMIT ?", (days,)
    ).fetchall()
    conn.close()

    results = []
    for d in dates:
        results.append(get_market_timing(d[0]))

    return results


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='大盘择时开关')
    parser.add_argument('date', nargs='?', help='日期 YYYY-MM-DD')
    parser.add_argument('--status', action='store_true', help='查看近期趋势')
    args = parser.parse_args()

    if args.status:
        trends = get_recent_trend(10)
        print(f'\n📊 大盘择时趋势（最近{len(trends)}天）:')
        for t in trends:
            emoji = '🟢' if t['regime'] == '做多' else '🟡' if t['regime'] == '谨慎' else '🔴'
            d = t['details']
            print(f'  {emoji} {t["date"]}: {t["regime"]} (仓位{t["position_limit"]*100:.0f}%) | 涨停{d["zt_count"]}家 | 指数{d["idx_chg_5d"]:+.1f}% | {d["vol_trend"]}')
    elif args.date:
        result = get_market_timing(args.date)
        d = result['details']
        emoji = '🟢' if result['regime'] == '做多' else '🟡' if result['regime'] == '谨慎' else '🔴'
        print(f'\n{emoji} 大盘择时 — {result["date"]}')
        print(f'  判定: {result["regime"]} | 仓位上限: {result["position_limit"]*100:.0f}%')
        print(f'  理由: {result["reason"]}')
        print(f'  涨停: {d["zt_count"]}家 | 指数5日: {d["idx_chg_5d"]:+.1f}% | 量能: {d["vol_trend"]}')
        print(f'  评分: 情绪{d["zt_score"]} + 趋势{d["idx_score"]} + 量能{d["vol_score"]} = {d["total_score"]}/6')
    else:
        result = get_market_timing(datetime.now().strftime('%Y-%m-%d'))
        d = result['details']
        emoji = '🟢' if result['regime'] == '做多' else '🟡' if result['regime'] == '谨慎' else '🔴'
        print(f'\n{emoji} 大盘择时 — {result["date"]}')
        print(f'  判定: {result["regime"]} | 仓位上限: {result["position_limit"]*100:.0f}%')
        print(f'  理由: {result["reason"]}')
        print(f'  涨停: {d["zt_count"]}家 | 指数5日: {d["idx_chg_5d"]:+.1f}% | 量能: {d["vol_trend"]}')
        print(f'  评分: 情绪{d["zt_score"]} + 趋势{d["idx_score"]} + 量能{d["vol_score"]} = {d["total_score"]}/6')