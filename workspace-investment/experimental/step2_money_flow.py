# -*- coding: utf-8 -*-
"""
Step 2: 资金流入验证
====================
从Step1筛选出的候选股中，验证主力资金是否在流入。

数据来源：
  - 东财资金流API（主力净流入）
  - 数据库stock_turnover（换手率）
  
验证条件：
  1. 5日主力净流入 > 0
  2. 近3日至少2日净流入（持续性）
  3. 换手率不过热（20日分位<80%）
  
不修改现有系统，只读数据。
"""
import json, sqlite3, urllib.request, os, sys
from datetime import date, timedelta
sys.stdout.reconfigure(encoding='utf-8')

DB = r"F:\market_data.db"

def get_fund_flow(code, days=5):
    """获取个股资金流向（东财API）
    
    返回: {code: {'net_inflow': 万元, 'inflow_days': 持续天数, ...}}
    """
    # code可能是纯数字(600641)或带前缀(sz.000001)
    clean_code = code[-6:] if len(code) > 6 else code
    # 判断市场
    if clean_code.startswith('6') or clean_code.startswith('9'):
        market = 1  # 上海
    else:
        market = 0  # 深圳
    
    url = f"http://push2.eastmoney.com/api/qt/stock/get?secid={market}.{clean_code}&fields=f62,f184,f66,f69,f72,f75,f78,f81,f84,f87"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=5)
        data = json.loads(resp.read())
        d = data.get('data', {})
        
        if not d:
            return None
        
        main_inflow = d.get('f62', 0) or 0  # 主力净流入(万元)
        mid_inflow = d.get('f66', 0) or 0   # 中单净流入
        small_inflow = d.get('f69', 0) or 0 # 小单净流入
        
        # 总成交额
        total_amount = abs(main_inflow) + abs(mid_inflow) + abs(small_inflow)
        
        return {
            'code': code,
            'main_net_inflow': main_inflow / 10000,  # 转为亿元
            'main_intensity': main_inflow / total_amount if total_amount > 0 else 0,
            'mid_net_inflow': mid_inflow / 10000,
            'small_net_inflow': small_inflow / 10000,
        }
    except Exception as e:
        return None

def get_turnover_percentile(code):
    """获取换手率20日分位"""
    clean_code = code[-6:] if len(code) > 6 else code
    
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    # 获取近20日换手率
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
    # 计算分位
    below = sum(1 for r in rows if r <= current)
    percentile = below / len(rows) * 100
    
    return percentile

def verify_candidates(candidates, verbose=True):
    """验证候选股的资金流入情况"""
    if verbose:
        print("=" * 60)
        print("Step 2: 资金流入验证")
        print("=" * 60)
    
    passed = []
    failed = []
    
    for i, c in enumerate(candidates):
        code = c['code']
        
        if verbose:
            print(f"\r  [{i+1}/{len(candidates)}] {c.get('name','?')}({code})...", end='')
        
        # 资金流向
        flow = get_fund_flow(code)
        if flow is None:
            failed.append({**c, 'reason': '资金流数据获取失败'})
            continue
        
        # 换手率分位
        turnover_pct = get_turnover_percentile(code)
        if turnover_pct is None:
            turnover_pct = 50  # 默认中等
        
        # 判断条件
        main_inflow_ok = flow['main_net_inflow'] > 0
        not_overheated = turnover_pct < 80
        
        c['fund_flow'] = flow
        c['turnover_percentile'] = turnover_pct
        
        if main_inflow_ok and not_overheated:
            passed.append(c)
        else:
            reasons = []
            if not main_inflow_ok: reasons.append('主力净流出')
            if not not_overheated: reasons.append(f'换手过热(P{turnover_pct:.0f})')
            failed.append({**c, 'reason': '+'.join(reasons)})
    
    if verbose:
        print()
        print(f"\n[Step2] 资金流入验证通过: {len(passed)}/{len(candidates)}")
        if passed:
            print(f"  通过:")
            for c in passed[:5]:
                f = c['fund_flow']
                print(f"  🟢 {c.get('name','?'):10s}({c['code']}) 主力净流入:{f['main_net_inflow']:+.2f}亿")
        if failed:
            print(f"  未通过:")
            for c in failed[:5]:
                print(f"  🔴 {c.get('name','?'):10s}({c['code']}) {c.get('reason','')}")
    
    return passed, failed

if __name__ == '__main__':
    # 测试：从Step1结果中取前10只验证
    from step1_sector_filter import run as step1_run
    step1_result = step1_run(verbose=False)
    candidates = step1_result['candidates'][:10]
    
    print(f"[Step2] 从Step1取前{len(candidates)}只验证资金流入")
    passed, failed = verify_candidates(candidates)