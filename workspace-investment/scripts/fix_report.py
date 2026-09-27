# -*- coding: utf-8 -*-
"""修复日报脚本 - 使用实时价格"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))
from data_api import DataAPI
from portfolio_analysis import enrich_holdings, _code_to_db_code

PORTFOLIO = Path(__file__).parent.parent / "data" / "portfolio.json"
OUT_DIR = Path(__file__).parent.parent / "out_data"

# 读取portfolio
with open(PORTFOLIO, 'r', encoding='utf-8') as f:
    pf = json.load(f)

# 从实时API获取今天的价格
today = datetime.now().strftime('%Y-%m-%d')
for h in pf['holdings']:
    code = h['code']
    db_code = _code_to_db_code(code)
    rt = DataAPI.get_realtime(db_code)
    if rt and db_code in rt:
        data = rt[db_code]
        h['current_price'] = data.get('price', h['current_price'])
        h['today_chg'] = data.get('chg_pct', 0)
        entry = h['entry_price']
        current = h['current_price']
        h['profit_pct'] = round((current - entry) / entry * 100, 2) if entry else 0

pf['last_updated'] = f"{today} {datetime.now().strftime('%H:%M')}"
with open(PORTFOLIO, 'w', encoding='utf-8') as f:
    json.dump(pf, f, ensure_ascii=False, indent=2)

print("Portfolio updated:")
for h in pf['holdings']:
    print(f"  {h['name']}: {h['entry_price']} -> {h['current_price']} ({h['today_chg']:+.2f}%) PnL={h['profit_pct']:+.2f}%")
