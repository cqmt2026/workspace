#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Magic Formula V2.1 - with trend filter + volume confirmation"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import os, sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
import winreg

WORKSPACE = r'C:\Users\Administrator\.openclaw\workspace'
INVEST_DIR = os.path.join(WORKSPACE, 'workspace-investment')
OUT_DATA = os.path.join(INVEST_DIR, 'out_data')
DB = r'F:\market_data.db'
os.makedirs(OUT_DATA, exist_ok=True)

def get_mx_key():
    for hive, path in [(winreg.HKEY_CURRENT_USER, r'Environment'),
                        (winreg.HKEY_LOCAL_MACHINE,
                         r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment')]:
        try:
            with winreg.OpenKey(hive, path) as h:
                val, _ = winreg.QueryValueEx(h, 'MX_APIKEY')
                if val: return val
        except:
            pass
    return None

MX_KEY = get_mx_key()

def parse_value(val):
    if not val: return 0.0
    v = str(val).strip()
    if '|' in v: v = v.split('|')[0]
    for u in ['亿', '万', '%', '倍']: v = v.replace(u, '')
    try: return float(v)
    except: return 0.0

def code_to_db(code):
    code = str(code).strip()
    if '.' in code: return code
    if code.startswith('6') or code.startswith('688'): return f"sh.{code}"
    elif code.startswith('3') or code.startswith('001') or code.startswith('002') or code.startswith('000'):
        return f"sz.{code}"
    elif code.startswith('8') or code.startswith('920'): return f"bj.{code}"
    return f"sh.{code}"

def get_trend_from_db(code):
    try:
        db_code = code_to_db(code)
        con = sqlite3.connect(DB)
        df = pd.read_sql(
            f"SELECT date, close, volume FROM daily_k WHERE code='{db_code}' AND close>0 ORDER BY date DESC LIMIT 25",
            con)
        con.close()
        if df.empty or len(df) < 10: return None
        df = df.sort_values('date')
        c = df['close'].values
        v = df['volume'].values
        ma5 = float(np.mean(c[-5:]))
        ma10 = float(np.mean(c[-10:]))
        ma20 = float(np.mean(c))
        p = float(c[-1])
        above_ma5 = (p / ma5 - 1) * 100
        above_ma10 = (p / ma10 - 1) * 100
        chg_5d = (p / c[-5] - 1) * 100 if len(c) >= 5 else 0.0

        # 均线排列
        if ma5 > ma10 > ma20: arrangement = '多头排列'
        elif ma5 < ma10 < ma20: arrangement = '空头排列'
        else: arrangement = '交叉缠绕'

        # ---- 量价分析 ----
        vol_surge = False
        vol_shrink = False
        vol_confirm = False
        if len(v) >= 6:
            recent_vol = v[-3:].mean()
            avg_vol = v[:-3].mean()
            if avg_vol > 0:
                vol_surge = recent_vol > avg_vol * 1.2
                vol_shrink = recent_vol < avg_vol * 0.7
            # 最近3天价格方向
            if len(c) >= 3:
                price_up = c[-1] > c[-3]
                price_down = c[-1] < c[-3]
                vol_confirm = price_up and vol_surge  # 放量上涨，确认信号

        # ---- 趋势判断 ----
        if arrangement == '空头排列' and (above_ma5 < -2 or above_ma10 < -5) and chg_5d < -3:
            status = '下跌趋势'; valid = False
        elif arrangement == '空头排列' and abs(above_ma5) < 2 and chg_5d > -2:
            status = '企稳'; valid = True
        elif arrangement == '交叉缠绕' and above_ma10 > -1 and chg_5d > -3:
            status = '企稳'; valid = True
        elif arrangement == '空头排列' and above_ma5 > 1:
            status = '反转'; valid = True
        elif arrangement == '多头排列' and above_ma5 > 0:
            status = '上涨趋势'; valid = True
        elif abs(chg_5d) < 5 and abs(above_ma10) < 3:
            status = '震荡'; valid = True
        else:
            status = '其他'; valid = True

        return {
            'trend_status': status, 'is_valid': valid,
            'ma_arrangement': arrangement,
            'above_ma5': above_ma5, 'chg_5d': chg_5d,
            'latest_price': p, 'ma5': ma5, 'ma10': ma10, 'ma20': ma20,
            'vol_surge': vol_surge, 'vol_shrink': vol_shrink, 'vol_confirm': vol_confirm
        }
    except:
        return None

def run():
    date = datetime.now().strftime('%Y-%m-%d')
    print('=' * 60)
    print('Magic Formula V2.1 - ' + date)
    print('=' * 60)

    if not MX_KEY: print('MX_KEY not set'); return None
    sys.path.insert(0, r'C:\Users\Administrator\AppData\Roaming\npm\node_modules\openclaw\skills\mx-xuangu')
    from mx_xuangu import MXSelectStock
    xuangu = MXSelectStock(api_key=MX_KEY)
    rows, _, err = MXSelectStock.extract_data(
        xuangu.search('A股ROIC大于5%，PE_TTM在5到30之间，市值大于50亿，排除ST股和金融股的股票'))
    if err or not rows: print('No results:', err); return None
    print(f'Raw: {len(rows)}')

    stocks = []; excluded = 0
    for row in rows:
        code = row.get('代码','').strip(); name = row.get('名称','').strip()
        if name.startswith('*ST') or name.startswith('ST') or '退市' in name: continue
        roic = parse_value(row.get('投入资本回报率(%) 截至2026.06.25最新',''))
        pe = parse_value(row.get('市盈率(TTM)(倍) 2026.06.25',''))
        mc = parse_value(row.get('总市值(元) 2026.06.25',''))
        if roic <= 5 or pe < 5 or pe > 30 or mc < 50: continue
        industry = row.get('申万行业分类','')
        t = get_trend_from_db(code)
        if t is None: continue
        if not t['is_valid']:
            excluded += 1
            if excluded <= 10:
                print(f"  [EX] {code} {name} {t['trend_status']} MA:{t['ma_arrangement']} chg5d:{t['chg_5d']:.1f}%")
            continue
        stocks.append({
            'code': code, 'name': name,
            'roic': roic, 'pe_ttm': pe, 'market_cap': mc,
            'industry': industry,
            'trend_status': t['trend_status'],
            'ma_arrangement': t['ma_arrangement'],
            'vol_confirm': t['vol_confirm'],
            'vol_surge': t['vol_surge'],
            'vol_shrink': t['vol_shrink'],
            'chg_5d': t['chg_5d'],
            'above_ma5': t['above_ma5'],
            'ma5': t['ma5'], 'ma10': t['ma10'], 'ma20': t['ma20']
        })

    if not stocks: print(f'Empty. Excluded: {excluded}'); return None
    print(f'Passed: {len(stocks)}, Excluded: {excluded}')
    vol_confirmed = sum(1 for s in stocks if s['vol_confirm'])
    vol_surge_count = sum(1 for s in stocks if s['vol_surge'])
    print(f'  Volume confirmed(放量上涨): {vol_confirmed}')
    print(f'  Volume surge(放量): {vol_surge_count}')

    df = pd.DataFrame(stocks)
    df['roic_rank'] = df['roic'].rank(ascending=False)
    df['ey'] = 1.0 / df['pe_ttm']
    df['ey_rank'] = df['ey'].rank(ascending=False)

    # 趋势分权重
    trend_bonus_map = {'反转': 2, '企稳': 1, '震荡': 0, '其他': 0, '上涨趋势': 2}
    df['trend_bonus'] = df['trend_status'].map(trend_bonus_map).fillna(0)
    df['ma_bonus'] = df['ma_arrangement'].apply(lambda x: 1 if x == '交叉缠绕' else 0)
    # 量价确认加分：放量上涨 +2
    df['vol_bonus'] = df['vol_confirm'].apply(lambda x: 2 if x else 0)

    df['score'] = df['roic_rank'] + df['ey_rank'] - df['trend_bonus'] * 3 - df['ma_bonus'] * 2 - df['vol_bonus'] * 2
    df['rank'] = df['score'].rank()
    df = df.sort_values('rank')

    print(f"\n{'='*60}")
    print(f"{'Rank':<6}{'Code':<10}{'Name':<10}{'ROIC':<8}{'PE':<8}{'Score':<8}{'Trend':<10}{'Vol':<10}{'MA':<10}")
    print(f"{'-'*60}")
    for _, r in df.iterrows():
        vol_mark = ''
        if r['vol_confirm']: vol_mark = '放量涨✅'
        elif r['vol_surge']: vol_mark = '放量'
        elif r['vol_shrink']: vol_mark = '缩量'
        print(f"{int(r['rank']):<6}{r['code']:<10}{r['name']:<10}{r['roic']:<8.1f}{r['pe_ttm']:<8.1f}{r['score']:<8.0f}{r['trend_status']:<10}{vol_mark:<10}{r['ma_arrangement']:<10}")

    print(f"\nStats: {len(df)} stocks | Avg ROIC: {df['roic'].mean():.1f}% | Avg PE: {df['pe_ttm'].mean():.1f}")
    print(f"\nTrend:")
    for t, c in df['trend_status'].value_counts().items(): print(f'  {t}: {c}')
    print(f"\nTop industries:")
    for ind, c in df['industry'].value_counts().head(10).items(): print(f'  {ind}: {c}')

    df.to_csv(os.path.join(OUT_DATA, f'magic_formula_{date}.csv'), index=False, encoding='utf-8-sig')
    print(f'\nSaved: out_data/magic_formula_{date}.csv')
    return df

if __name__ == '__main__':
    run()