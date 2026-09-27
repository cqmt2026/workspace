# -*- coding: utf-8 -*-
"""
SmartMoney 资金因子评分 v2.0
============================
四层资金因子 + 拥挤度过滤

因子逻辑：
  1. 资金方向：flow_intensity = 5日(主动买-主动卖) / 5日成交额
     - 用大单+超大单净流入近似主动买卖
  2. 资金持续性：flow_persistence = 10日内净主动买入>0的天数/10
  3. 价格确认：price_confirmation = 收益率 vs 资金方向是否一致
  4. 冲击效率：impact_efficiency = 5日收益率/|5日净主动买入占比|

组合：SmartMoneyScore = 方向 * 持续性 * 价格确认 * 冲击效率

拥挤度过滤：换手率20日分位<80% + 5日涨幅分位<90%

数据源：
  - 资金流：东财fflow/daykline API
  - 日K/换手率：F:\\market_data.db
  - 涨幅分位：DB全市场排名
"""

import io
import requests
import json
import time
import sys
import os
import math
import sqlite3
from datetime import datetime, timedelta

DB_PATH = r'F:\market_data.db'
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'out_data')
os.makedirs(OUT_DIR, exist_ok=True)


def get_eastmoney_secid(code):
    """统一code为东财secid格式
    输入: sz000858 或 sz.000858 或 000858
    输出: 0.000858 或 1.600519
    """
    c = code.replace('sh.', '').replace('sz.', '').replace('bj.', '')
    # 处理无点前缀: sz000858 -> 000858
    for prefix in ('sh', 'sz', 'bj'):
        if c.startswith(prefix) and len(c) > len(prefix) and c[len(prefix):len(prefix)+1].isdigit():
            c = c[len(prefix):]
            break
    if c.startswith('6') or c.startswith('688') or c.startswith('689'):
        return f'1.{c}'
    else:
        return f'0.{c}'


def fetch_flow_data(code, days=15):
    """获取个股资金流日数据 (东财API)
    返回: [{'date','active_buy_sell','amount','main_net'}, ...]
    active_buy_sell = 大单净流入 + 超大单净流入

    非交易时段API只返回1天，盘中正常返回全部天数。
    此处做智能处理：如果返回数据<5天，尝试从DB补全日期框架。
    """
    secid = get_eastmoney_secid(code)
    # 优先用push2his（对688股票兼容），失败则回退push2
    urls = [
        f'http://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get?secid={secid}&fields1=f1,f2,f3,f7,f8,f9&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60&lmt={days}',
        f'http://push2.eastmoney.com/api/qt/stock/fflow/daykline/get?secid={secid}&fields1=f1,f2,f3,f7,f8,f9&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60&lmt={days}',
    ]
    try:
        raw_klines = []
        for url in urls:
            try:
                resp = requests.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': 'http://finance.eastmoney.com/'
                }, timeout=8)
                data = resp.json()
                if data.get('data') and data['data'].get('klines'):
                    klines = data['data']['klines']
                    if len(klines) > len(raw_klines):
                        raw_klines = klines
                elif data.get('rc') == 100:
                    continue
            except Exception:
                continue
        
        if not raw_klines:
            return []
        
        results = []
        for k in raw_klines:
            parts = k.split(',')
            dt = parts[0]
            main_net = float(parts[1]) if parts[1] else 0
            big_net = float(parts[4]) if len(parts) > 4 and parts[4] else 0
            super_big_net = float(parts[5]) if len(parts) > 5 and parts[5] else 0
            active = big_net + super_big_net
            main_pct = float(parts[6]) if len(parts) > 6 and parts[6] else 0
            amount = abs(main_net / main_pct * 100) if main_pct != 0 else 0
            results.append({
                    'date': dt,
                    'active_buy_sell': active,
                    'amount': amount,
                    'main_net': main_net,
                })

        # 如果数据不足5天（非交易时段或API无数据），从DB补全日期结构
        if len(results) < 5:
            db_klines = get_kline_from_db(code, days=20)
            if db_klines:
                api_dates = {r['date'] for r in results}
                for i, k in enumerate(db_klines):
                    if k['date'] not in api_dates:
                        est_active = 0
                        est_amount = k['volume'] * 100
                        if i > 0:
                            prev_k = db_klines[i-1]
                            price_chg = (k['close'] - prev_k['close']) / prev_k['close']
                            vol_ratio = k['volume'] / max(prev_k['volume'], 1) if prev_k['volume'] > 0 else 1
                            if price_chg > 0.005:
                                est_active = est_amount * (0.05 + 0.10 * min(vol_ratio - 1, 3) / 3)
                            elif price_chg < -0.005:
                                est_active = -est_amount * (0.05 + 0.10 * min(vol_ratio - 1, 3) / 3)
                            else:
                                est_active = est_amount * 0.02 * (1 if price_chg > 0 else -1)
                        results.append({
                            'date': k['date'],
                            'active_buy_sell': est_active,
                            'amount': est_amount,
                            'main_net': 0,
                            '_from_db': True,
                        })
                results.sort(key=lambda x: x['date'])
                results = results[-15:]

        return results
    except Exception:
        return []


def _normalize_code(code):
    """统一code格式为sh.XXXXXX/sz.XXXXXX"""
    if '.' in code:
        return code
    if code.startswith('sh') or code.startswith('sz') or code.startswith('bj'):
        return code[:2] + '.' + code[2:]
    if code.startswith('6') or code.startswith('688') or code.startswith('689'):
        return 'sh.' + code
    return 'sz.' + code


def get_kline_from_db(code, days=30):
    """从本地DB获取日K线"""
    db_code = _normalize_code(code)
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.execute("""
            SELECT date, close, volume
            FROM daily_k
            WHERE code = ?
            ORDER BY date DESC
            LIMIT ?
        """, (db_code, days))
        rows = cur.fetchall()
        conn.close()
        results = []
        for r in reversed(rows):
            results.append({
                'date': r[0],
                'close': r[1],
                'volume': r[2],
                'amount': 0,
            })
        return results
    except Exception:
        return []


def get_turnover_from_db(code, days=25):
    """从DB获取换手率数据"""
    db_code = _normalize_code(code)
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.execute("""
            SELECT date, turnover
            FROM stock_turnover
            WHERE code = ?
            ORDER BY date DESC
            LIMIT ?
        """, (db_code, days))
        rows = cur.fetchall()
        conn.close()
        return [{'date': r[0], 'turnover': r[1]} for r in reversed(rows)]
    except Exception:
        return []


def get_ret_5d_percentile(code, db_date):
    """计算5日涨幅在全市场的分位"""
    db_code = _normalize_code(code)
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.execute("""
            SELECT DISTINCT date FROM daily_k 
            WHERE date <= ? ORDER BY date DESC LIMIT 6
        """, (db_date,))
        dates = [r[0] for r in cur.fetchall()]
        if len(dates) < 6:
            conn.close()
            return 50

        date_start = dates[-1]
        date_end = dates[0]

        cur = conn.execute("""
            SELECT a.code, 
                   (a.close - b.close) / b.close * 100 as ret_5d
            FROM daily_k a
            JOIN daily_k b ON a.code = b.code
            WHERE a.date = ? AND b.date = ?
            AND a.code NOT LIKE 'bj.%'
            AND a.code NOT LIKE 'sh.8%'
            AND a.code NOT LIKE 'sh.9%'
            AND b.close > 0
        """, (date_end, date_start))
        rows = cur.fetchall()
        conn.close()

        if not rows:
            return 50

        rets = sorted([r[1] for r in rows])
        target_ret = None
        for r in rows:
            if r[0] == db_code:
                target_ret = r[1]
                break

        if target_ret is None:
            return 50

        rank = sum(1 for x in rets if x < target_ret)
        percentile = rank / len(rets) * 100
        return percentile
    except Exception:
        return 50


def get_market_db_date():
    """获取DB中最新的交易日"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.execute("SELECT MAX(date) FROM daily_k")
        r = cur.fetchone()
        conn.close()
        return r[0] if r else None
    except Exception:
        return None


def calc_smart_money_score(code):
    """
    计算SmartMoney综合评分
    """
    result = {
        'code': code, 'status': 'ok',
        'score': 0, 'pass_filter': False,
        'layers': {}
    }

    flows = fetch_flow_data(code, days=15)

    real_flows = [f for f in flows if not f.get('_from_db')]
    has_real_data = len(real_flows) >= 3

    klines = get_kline_from_db(code, days=30)
    if len(klines) < 10:
        result['status'] = f'K线数据不足({len(klines)})'
        return result

    turnover_data = get_turnover_from_db(code, days=25)
    db_date = get_market_db_date()

    # Layer 1: 资金方向
    recent_flows = flows[-5:]

    total_active = sum(f['active_buy_sell'] for f in recent_flows)
    total_amount = sum(f['amount'] for f in recent_flows)
    flow_intensity = total_active / total_amount if total_amount > 0 else 0

    # 持续性
    recent_10d = flows[-10:]
    active_pos_days = sum(1 for f in recent_10d if f['active_buy_sell'] > 0)
    flow_persistence = active_pos_days / 10

    result['layers']['flow_intensity'] = round(flow_intensity, 6)
    result['layers']['active_positive_days'] = active_pos_days
    result['layers']['flow_persistence'] = round(flow_persistence, 4)
    result['layers']['has_real_flow_data'] = has_real_data
    result['layers']['real_flow_days'] = len(real_flows)

    # Layer 3: 价格确认
    kline_by_date = {k['date']: k for k in klines}

    price_confirm_score = 0
    confirm_count = 0
    for f in recent_flows:
        dt = f['date']
        k = kline_by_date.get(dt)
        if not k:
            continue
        prev_k = None
        for k2 in klines:
            if k2['date'] < dt:
                prev_k = k2
        if not prev_k:
            continue

        ret = (k['close'] - prev_k['close']) / prev_k['close']
        flow_dir = 1 if f['active_buy_sell'] > 0 else (-1 if f['active_buy_sell'] < 0 else 0)
        price_dir = 1 if ret > 0.005 else (-1 if ret < -0.005 else 0)

        if flow_dir == price_dir and flow_dir != 0:
            price_confirm_score += 1
        elif flow_dir == 1 and price_dir <= 0:
            price_confirm_score -= 1
        elif flow_dir == -1 and price_dir == 1:
            price_confirm_score -= 0.5
        confirm_count += 1

    if confirm_count > 0:
        max_possible = confirm_count * 2
        min_possible = -confirm_count
        if max_possible > min_possible:
            price_confirmation = (price_confirm_score - min_possible) / (max_possible - min_possible)
        else:
            price_confirmation = 0.5
    else:
        price_confirmation = 0.5
    result['layers']['price_confirmation'] = round(price_confirmation, 4)

    # Layer 4: 冲击效率
    if len(klines) >= 6:
        ret_5d = (klines[-1]['close'] - klines[-6]['close']) / klines[-6]['close']
    else:
        ret_5d = 0
    result['layers']['ret_5d'] = round(ret_5d * 100, 2)

    active_ratio_5d = flow_intensity
    result['layers']['active_ratio_5d'] = round(active_ratio_5d * 100, 4)

    impact_efficiency = ret_5d / abs(active_ratio_5d) if abs(active_ratio_5d) > 0.0001 else 0
    result['layers']['impact_efficiency'] = round(impact_efficiency, 4)
    ie = max(-10, min(10, impact_efficiency))
    impact_norm = (ie + 2) / 4
    impact_norm = max(0, min(1, impact_norm))
    result['layers']['impact_norm'] = round(impact_norm, 4)

    # 组合评分
    # 方向分：用资金强度绝对值衡量，正负由价格确认因子区分
    direction_score = min(1, abs(flow_intensity) * 20)
    persistence_score = flow_persistence
    confirmation_score = price_confirmation
    impact_score = impact_norm

    result['layers']['direction_score'] = round(direction_score, 4)
    result['layers']['persistence_score'] = round(persistence_score, 4)
    result['layers']['confirmation_score'] = round(confirmation_score, 4)
    result['layers']['impact_score'] = round(impact_score, 4)

    raw_score = direction_score * persistence_score * confirmation_score * impact_score * 100
    result['layers']['raw_score'] = round(raw_score, 2)

    # 拥挤度过滤
    current_turnover = 0
    turnover_percentile = 50
    if turnover_data:
        current_turnover = turnover_data[-1]['turnover']
        turn_values = sorted([t['turnover'] for t in turnover_data])
        rank = sum(1 for t in turn_values if t < current_turnover)
        turnover_percentile = rank / len(turn_values) * 100 if turn_values else 50
    result['layers']['current_turnover'] = round(current_turnover, 2)
    result['layers']['turnover_percentile'] = round(turnover_percentile, 1)

    ret_5d_percentile = 50
    if db_date and len(klines) >= 6:
        ret_5d_percentile = get_ret_5d_percentile(code, db_date)
    result['layers']['ret_5d_percentile'] = round(ret_5d_percentile, 1)

    pass_turnover = turnover_percentile < 80
    pass_ret = ret_5d_percentile < 90
    pass_filter = pass_turnover and pass_ret
    result['layers']['pass_filter'] = pass_filter
    result['layers']['filter_breakdown'] = {
        'turnover_ok': pass_turnover,
        'ret_ok': pass_ret,
    }

    if pass_filter:
        result['score'] = round(raw_score, 2)
    else:
        result['score'] = 0
        reasons = []
        if not pass_turnover:
            reasons.append(f'换手分位{turnover_percentile:.0f}%>=80')
        if not pass_ret:
            reasons.append(f'涨幅分位{ret_5d_percentile:.0f}%>=90')
        result['filter_reason'] = '; '.join(reasons)

    return result


def load_all_stocks():
    """从DB加载全市场股票"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.execute("""
            SELECT DISTINCT d.code 
            FROM daily_k d
            WHERE d.date = (SELECT MAX(date) FROM daily_k)
            AND d.code NOT LIKE 'bj.%'
            AND d.code NOT LIKE 'sh.8%'
            AND d.code NOT LIKE 'sh.9%'
            AND d.code NOT LIKE 'sh.4%'
        """)
        codes = [r[0] for r in cur.fetchall()]
        conn.close()
        return codes
    except Exception as e:
        print(f'DB读取失败: {e}')
        return []


def scan_pool(codes, sample_only=False):
    """批量扫描"""
    results = []
    total = len(codes)

    for i, code in enumerate(codes):
        if sample_only and i >= 30:
            break

        sys.stdout.write(f'\r[{i+1}/{total}] {code}...')
        sys.stdout.flush()

        r = calc_smart_money_score(code)
        results.append(r)

        if i < total - 1:
            time.sleep(0.25)

    print()
    return results


def print_report(results, top_n=30):
    valid = [r for r in results if r['status'] == 'ok' and r['score'] > 0]
    valid.sort(key=lambda x: x['score'], reverse=True)

    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f'\nSmartMoney 资金因子评分报告 @ {now}')
    print(f'扫描: {len(results)}只 | 有效: {len(valid)}只')
    print(f'{"="*120}')

    if not valid:
        print('无符合条件的股票')
        return

    hdr = f'{"#":<3} {"代码":<10} {"总分":<7} {"方向分":<7} {"持续":<7} {"确认":<7} {"冲击":<7} {"5日%":<7} {"资金比":<8} {"换手":<6} {"换手分位":<8} {"涨幅分位":<8}'
    print(hdr)
    print('-' * 120)

    for i, r in enumerate(valid[:top_n]):
        l = r['layers']
        print(f'{i+1:<3} {r["code"]:<10} {r["score"]:<7.1f} '
              f'{l["direction_score"]:<7.3f} {l["persistence_score"]:<7.3f} '
              f'{l["confirmation_score"]:<7.3f} {l["impact_score"]:<7.3f} '
              f'{l["ret_5d"]:<7.2f} {l["active_ratio_5d"]:<8.4f} '
              f'{l["current_turnover"]:<6.2f} {l["turnover_percentile"]:<8.1f} '
              f'{l["ret_5d_percentile"]:<8.1f}')

    print(f'\nTOP 5 详细拆解:')
    for i, r in enumerate(valid[:5]):
        l = r['layers']
        print(f'\n  #{i+1} {r["code"]}')
        print(f'    资金方向: flow_intensity={l["flow_intensity"]:.6f} ({"流入" if l["flow_intensity"]>0 else "流出"})')
        print(f'    持续性: {l["active_positive_days"]}/10天 = {l["flow_persistence"]:.1%}')
        print(f'    价格确认: {l["price_confirmation"]:.3f} | 冲击效率: {l["impact_efficiency"]:.4f}')
        print(f'    组合: {l["direction_score"]:.3f}x{l["persistence_score"]:.3f}x{l["confirmation_score"]:.3f}x{l["impact_score"]:.3f} = {l["raw_score"]:.1f}')
        print(f'    过滤: 换手分位{l["turnover_percentile"]:.0f}% {"OK" if l["filter_breakdown"]["turnover_ok"] else "XX"} | '
              f'涨幅分位{l["ret_5d_percentile"]:.0f}% {"OK" if l["filter_breakdown"]["ret_ok"] else "XX"}')

    outfile = os.path.join(OUT_DIR, f'smart_money_{datetime.now().strftime("%Y%m%d_%H%M")}.json')
    with open(outfile, 'w', encoding='utf-8') as f:
        json.dump(valid, f, ensure_ascii=False, indent=2)
    print(f'\n结果已保存: {outfile}')


def main():
    import argparse
    parser = argparse.ArgumentParser(description='SmartMoney资金因子评分')
    parser.add_argument('--single', type=str, help='单只分析')
    parser.add_argument('--sample', action='store_true', help='小样本测试(30只)')
    parser.add_argument('--full', action='store_true', help='全市场扫描')
    parser.add_argument('--codes', nargs='+', help='指定股票列表')
    parser.add_argument('--topn', type=int, default=30, help='显示N只')
    args = parser.parse_args()

    if args.single:
        codes = [args.single]
        results = scan_pool(codes)
    elif args.codes:
        codes = args.codes
        results = scan_pool(codes)
    elif args.full:
        print('加载全市场股票...')
        codes = load_all_stocks()
        print(f'共 {len(codes)} 只')
        results = scan_pool(codes)
    else:
        codes = ['sz000858', 'sz002415', 'sh600519', 'sz300750', 'sz000333',
                 'sz002304', 'sh601318', 'sh600887', 'sh600036', 'sz000001']
        results = scan_pool(codes)

    print_report(results, top_n=args.topn)


if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()