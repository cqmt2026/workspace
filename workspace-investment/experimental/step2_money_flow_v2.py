# -*- coding: utf-8 -*-
"""
Step 2: 资金流入验证 (v2 - 使用fflow/daykline接口)
====================================================
从Step1筛选出的候选股中，验证主力资金是否在流入。

条件：
  1. 近5日主力净流入 > 0
  2. 近3日中至少2日净流入（持续性）
  3. 换手率20日分位 < 80%（不过热）
"""
import json, sqlite3, urllib.request, os, sys
sys.stdout.reconfigure(encoding='utf-8')

DB = r"F:\market_data.db"

def get_fund_flow_fflow(code, days=5):
    """使用fflow/daykline接口获取资金流向
    
    返回格式: 日期,主力净流入,超级主力净流入,散户净流入,大单净流入,中单净流入,...
    正数=流入, 负数=流出
    """
    clean_code = code[-6:] if len(code) > 6 else code
    market = 1 if (clean_code.startswith('6') or clean_code.startswith('9')) else 0
    
    # 用his接口可以获取多天数据
    url = f"http://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get?secid={market}.{clean_code}&fields1=f1,f2,f3,f7,f8,f9&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60&lmt={days}"
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://quote.eastmoney.com/'
        })
        resp = urllib.request.urlopen(req, timeout=5)
        data = json.loads(resp.read())
        klines = data.get('data', {}).get('klines', [])
        
        if not klines:
            return None
        
        result = {
            'code': code,
            'daily_flows': [],
            'total_main_inflow': 0,
            'positive_days': 0,
            'latest_main_inflow': 0,
        }
        
        for kline in klines:
            parts = kline.split(',')
            if len(parts) < 6:
                continue
            date_str = parts[0]
            main_inflow = float(parts[1]) if parts[1] else 0
            super_main = float(parts[2]) if parts[2] else 0
            retail = float(parts[3]) if parts[3] else 0
            big_order = float(parts[4]) if parts[4] else 0
            mid_order = float(parts[5]) if parts[5] else 0
            
            result['daily_flows'].append({
                'date': date_str,
                'main_inflow': round(main_inflow / 100000000, 2),  # 转为亿
                'super_main': round(super_main / 100000000, 2),
                'retail': round(retail / 100000000, 2),
            })
            
            if main_inflow > 0:
                result['positive_days'] += 1
        
        result['total_main_inflow'] = sum(d['main_inflow'] for d in result['daily_flows'])
        result['latest_main_inflow'] = result['daily_flows'][-1]['main_inflow'] if result['daily_flows'] else 0
        
        return result
    except Exception as e:
        return None

def get_turnover_percentile(code):
    """获取换手率20日分位"""
    clean_code = code[-6:] if len(code) > 6 else code
    
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    c.execute("""
        SELECT turnover FROM stock_turnover 
        WHERE code LIKE ? 
        ORDER BY date DESC LIMIT 20
    """, (f'%{clean_code}',))
    
    rows = [r[0] for r in c.fetchall() if r[0] is not None]
    conn.close()
    
    if len(rows) < 5:
        return None
    
    current = rows[0]
    below = sum(1 for r in rows if r <= current)
    percentile = below / len(rows) * 100
    
    return percentile

def verify_candidates(candidates, verbose=True):
    """验证候选股的资金流入情况"""
    if verbose:
        print("=" * 60)
        print("Step 2: 资金流入验证 (fflow接口)")
        print("=" * 60)
    
    passed = []
    failed = []
    
    for i, c in enumerate(candidates):
        code = c['code']
        name = c.get('name', code)
        
        if verbose:
            print(f"\r  [{i+1}/{len(candidates)}] {name}({code})...", end='')
        
        # 资金流向（5日）
        flow = get_fund_flow_fflow(code, days=5)
        if flow is None:
            failed.append({**c, 'reason': '资金流数据获取失败'})
            continue
        
        # 换手率分位
        turnover_pct = get_turnover_percentile(code)
        if turnover_pct is None:
            turnover_pct = 50  # 默认中等
        
        c['fund_flow'] = flow
        c['turnover_percentile'] = turnover_pct
        
        # 判断条件
        total_positive = flow['total_main_inflow'] > 0  # 5日总净流入>0
        sustained = flow['positive_days'] >= 2  # 至少2天净流入
        not_overheated = turnover_pct < 80  # 换手不过热
        
        if total_positive and sustained and not_overheated:
            passed.append(c)
        else:
            reasons = []
            if not total_positive: reasons.append(f'5日净流出{flow["total_main_inflow"]:+.2f}亿')
            if not sustained: reasons.append(f'仅{flow["positive_days"]}天净流入')
            if not not_overheated: reasons.append(f'换手过热(P{turnover_pct:.0f})')
            failed.append({**c, 'reason': '+'.join(reasons)})
    
    if verbose:
        print()
        print(f"\n[Step2] 资金流入验证通过: {len(passed)}/{len(candidates)}")
        if passed:
            print(f"  通过:")
            for c in passed[:5]:
                f = c['fund_flow']
                print(f"  🟢 {c.get('name','?'):10s}({c['code']}) 5日净流入:{f['total_main_inflow']:+.2f}亿 持续{f['positive_days']}天")
        if failed:
            print(f"  未通过:")
            for c in failed[:5]:
                print(f"  🔴 {c.get('name','?'):10s}({c['code']}) {c.get('reason','')}")
    
    return passed, failed

if __name__ == '__main__':
    # 测试
    from step1_sector_filter import run as step1_run
    step1_result = step1_run(verbose=False)
    candidates = step1_result['candidates'][:10]
    print(f"[Step2] 从Step1取前{len(candidates)}只验证资金流入")
    passed, failed = verify_candidates(candidates)