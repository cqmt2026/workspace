#!/usr/bin/env python3
"""
基本面因子采集 (Fundamentals Fetcher v2)
=========================================
每天收盘后采集基本面数据，写入factors.db。

采集的因子（7个）：
  行情快照（万得）：pe_ttm, pb, market_cap
  东方财富财报：roe, gross_margin, debt_ratio, revenue_growth

用法：
    python scripts/wind_fundamentals.py                    # 全量采集
    python scripts/wind_fundamentals.py 2026-07-10         # 指定日期
    python scripts/wind_fundamentals.py --test sh600845    # 测试单只
"""
import sys, os, json, sqlite3, time, urllib.request
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

WORK_DIR = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment')
SKILL_DIR = os.path.expanduser('~/.agents/skills/wind-mcp-skill')
DB = r'F:\market_data.db'
FACTORS_DB = WORK_DIR / 'data' / 'factors.db'

# 7个因子
FACTOR_NAMES = ['pe_ttm', 'pb', 'market_cap', 'roe', 'gross_margin', 'debt_ratio', 'revenue_growth']

# ─── 万得行情快照（PE/PB/市值）─────────────────────
SNAPSHOT_INDEXES = '总市值2,市盈率(TTM),市净率'


def code_to_wind(code: str) -> str:
    if code.startswith('sh.'): return code[3:] + '.SH'
    elif code.startswith('sz.'): return code[3:] + '.SZ'
    elif code.startswith('bj.'): return code[3:] + '.BJ'
    return code


def wind_price_indicators(windcode: str) -> Optional[Dict]:
    """万得行情快照：市值/PE/PB（不消耗查询额度，仅调用次数）"""
    params = json.dumps({'windcode': windcode, 'indexes': SNAPSHOT_INDEXES}, ensure_ascii=False)
    try:
        result = subprocess.run(
            ['node', 'scripts/cli.mjs', 'call', 'stock_data', 'get_stock_price_indicators', params],
            capture_output=True, text=True, cwd=SKILL_DIR, encoding='utf-8', timeout=15
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        text = data.get('content', [{}])[0].get('text', '{}')
        inner = json.loads(text)
        rows = inner.get('data', {}).get('rows', [])
        if rows and len(rows[0]) >= 3:
            return {
                'market_cap': float(rows[0][0]) if rows[0][0] else None,
                'pe_ttm': float(rows[0][1]) if rows[0][1] else None,
                'pb': float(rows[0][2]) if rows[0][2] else None,
            }
    except:
        pass
    return None


# ─── 东方财富财报（ROE/毛利率/负债率/营收增速）─────────

def eastmoney_fundamentals(code: str) -> Optional[Dict]:
    """从东方财富API拿ROE/毛利率/负债率/营收增速
    
    API: https://datacenter-web.eastmoney.com/api/data/v1/get
    报表类型：主要指标（报期编码 RESTATE 表示最新一期）
    """
    # 去掉sh./sz.前缀
    clean = code.replace('sh.', '').replace('sz.', '').replace('bj.', '')
    market = 1 if code.startswith('sh.6') or clean.startswith('6') else 0
    
    url = (
        'https://datacenter-web.eastmoney.com/api/data/v1/get'
        f'?reportName=RPT_LICO_FN_CPD&columns=SECUCODE,SECURITY_NAME_ABBR,REPORT_DATE,BASIC_EPS,ROEJQ,GROSS_PROFIT_RATIO,ASSET_LIAB_RATIO,TOTAL_OPERATE_INCOME,IS_LEGAL_PERSON'
        f'&filter=(SECUCODE="{clean}.{market}")'
        '&pageNumber=1&pageSize=1&sortTypes=-1&sortColumns=REPORT_DATE'
    )
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'
        })
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode('utf-8'))
        rows = data.get('result', {}).get('data', [])
        if rows:
            row = rows[0]
            roe = row.get('ROEJQ', None)
            gross = row.get('GROSS_PROFIT_RATIO', None)
            debt = row.get('ASSET_LIAB_RATIO', None)
            # 营收增速：需要两期对比
            revenue = row.get('TOTAL_OPERATE_INCOME', None)
            result = {}
            if roe is not None:
                result['roe'] = round(float(roe), 4) if roe else None
            if gross is not None:
                result['gross_margin'] = round(float(gross), 4) if gross else None
            if debt is not None:
                result['debt_ratio'] = round(float(debt), 4) if debt else None
            # 营收增速需查上一期
            if revenue is not None:
                prev_url = (
                    'https://datacenter-web.eastmoney.com/api/data/v1/get'
                    f'?reportName=RPT_LICO_FN_CPD&columns=SECUCODE,REPORT_DATE,TOTAL_OPERATE_INCOME'
                    f'&filter=(SECUCODE="{clean}.{market}")'
                    '&pageNumber=2&pageSize=1&sortTypes=-1&sortColumns=REPORT_DATE'
                )
                try:
                    prev_req = urllib.request.Request(prev_url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
                    prev_resp = urllib.request.urlopen(prev_req, timeout=10)
                    prev_data = json.loads(prev_resp.read().decode('utf-8'))
                    prev_rows = prev_data.get('result', {}).get('data', [])
                    if prev_rows and prev_rows[0].get('TOTAL_OPERATE_INCOME'):
                        prev_rev = float(prev_rows[0]['TOTAL_OPERATE_INCOME'])
                        if prev_rev > 0:
                            growth = (float(revenue) - prev_rev) / prev_rev
                            result['revenue_growth'] = round(growth, 4)
                except:
                    pass
            return result if result else None
    except:
        pass
    return None


# ─── 数据库操作 ──────────────────────────────────

def get_all_codes() -> List[str]:
    conn = sqlite3.connect(DB)
    codes = [r[0] for r in conn.execute('SELECT DISTINCT code FROM daily_k').fetchall()]
    conn.close()
    return codes


def ensure_factors_table():
    """确保factors.db有fundamental因子表"""
    conn = sqlite3.connect(str(FACTORS_DB))
    conn.execute('''
        CREATE TABLE IF NOT EXISTS factors (
            code TEXT, date TEXT, factor_name TEXT, value REAL,
            PRIMARY KEY (code, date, factor_name)
        )
    ''')
    conn.commit()
    conn.close()


def save_to_factors(code: str, date: str, data: Dict):
    conn = sqlite3.connect(str(FACTORS_DB))
    for fname, value in data.items():
        if value is not None:
            conn.execute(
                'INSERT OR REPLACE INTO factors (code, date, factor_name, value) VALUES (?,?,?,?)',
                (code, date, fname, round(float(value), 4))
            )
    conn.commit()
    conn.close()


def fetch_single(code: str, date: str) -> Dict:
    """获取单只股票的全部7个因子"""
    result = {}

    # 1. 万得行情快照（PE/PB/市值）— 免费
    windcode = code_to_wind(code)
    price_data = wind_price_indicators(windcode)
    if price_data:
        result.update(price_data)

    # 2. 东方财富财报（ROE/毛利率/负债率/营收增速）
    fund_data = eastmoney_fundamentals(code)
    if fund_data:
        result.update(fund_data)

    return result


def run_batch(codes: List[str], date: str, batch_size: int = 100):
    total = len(codes)
    saved = 0
    failed = 0

    for i in range(0, total, batch_size):
        batch = codes[i:i + batch_size]
        print(f'  批次 {i // batch_size + 1}: {i}~{i + len(batch)}', flush=True)

        for code in batch:
            data = fetch_single(code, date)
            if data:
                save_to_factors(code, date, data)
                saved += 1
            else:
                failed += 1
            time.sleep(0.1)

        print(f'    已保存{saved} 失败{failed}', flush=True)

    return saved, failed


def test_single(code: str, date: str):
    print(f'测试 {code}...')
    windcode = code_to_wind(code)
    print(f'  Wind代码: {windcode}')

    price_data = wind_price_indicators(windcode)
    print(f'  行情快照: {price_data}')

    fund_data = eastmoney_fundamentals(code)
    print(f'  东方财富财报: {fund_data}')

    if price_data or fund_data:
        combined = {}
        if price_data: combined.update(price_data)
        if fund_data: combined.update(fund_data)
        save_to_factors(code, date, combined)
        print(f'  已保存到factors.db')
        print(f'  合计因子: {list(combined.keys())}')
    else:
        print(f'  ⚠️ 获取失败')


if __name__ == '__main__':
    import argparse, subprocess
    parser = argparse.ArgumentParser(description='基本面因子采集')
    parser.add_argument('date', nargs='?', help='日期 YYYY-MM-DD')
    parser.add_argument('--test', type=str, help='测试单只股票代码')
    parser.add_argument('--batch', type=int, default=100, help='每批数量')
    args = parser.parse_args()

    date = args.date or datetime.now().strftime('%Y-%m-%d')
    ensure_factors_table()

    if args.test:
        test_single(args.test, date)
    else:
        codes = get_all_codes()
        print(f'全量采集 {len(codes)}只股票, 日期{date}...')
        saved, failed = run_batch(codes, date, args.batch)
        print(f'\n完成! 保存{saved}只, 失败{failed}只')