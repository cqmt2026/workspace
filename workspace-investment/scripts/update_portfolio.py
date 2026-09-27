# -*- coding: utf-8 -*-
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))
from data_api import DataAPI

PORTFOLIO = Path(__file__).parent.parent / "data" / "portfolio.json"

with open(PORTFOLIO, 'r', encoding='utf-8') as f:
    pf = json.load(f)

for h in pf['holdings']:
    code = h['code']
    db_code = f'sz.{code}' if code.startswith('00') or code.startswith('30') else f'sh.{code}'
    rt = DataAPI.get_realtime(db_code)
    if rt:
        data = rt.get(db_code, {})
        h['current_price'] = data.get('price', h['current_price'])
        h['today_chg'] = data.get('chg_pct', 0)
        entry = h['entry_price']
        current = h['current_price']
        h['profit_pct'] = round((current - entry) / entry * 100, 2)
        print(f"{h['name']}: {entry} -> {current} ({h['today_chg']:+.2f}%) PnL={h['profit_pct']:+.2f}%")

pf['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M')
with open(PORTFOLIO, 'w', encoding='utf-8') as f:
    json.dump(pf, f, ensure_ascii=False, indent=2)
print('Portfolio updated!')
