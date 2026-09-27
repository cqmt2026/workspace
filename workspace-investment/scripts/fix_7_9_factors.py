# -*- coding: utf-8 -*-
"""立即修复7/9因子"""
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

# 修复打印问题
import builtins
old_print = builtins.print
builtins.print = lambda *a, **kw: old_print(*a, **kw, flush=True)

FD = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\data\factors.db'

# 1. 删除7/9所有旧因子
fconn = sqlite3.connect(FD)
before = fconn.execute("SELECT COUNT(*) FROM factors WHERE date='2026-07-09'").fetchone()[0]
fconn.execute("DELETE FROM factors WHERE date='2026-07-09'")
fconn.commit()
print('删除7/9旧因子: {}条'.format(before))

# 2. 直接调用因子计算函数
sys.path.insert(0, r'C:\Users\Administrator\.openclaw\workspace\workspace-investment')
from scripts.daily_factor_compute import DailyFactorCompute

calc = DailyFactorCompute()
# 手动计算技术因子和板块因子
codes = calc._get_codes('2026-07-09')
print('计算7/9因子，共{}只股票'.format(len(codes)))

n_tech = calc.compute_technical('2026-07-09', codes)
print('技术因子: {}条'.format(n_tech))

n_sector = calc.compute_sector('2026-07-09', codes)
print('板块因子: {}条'.format(n_sector))

after = fconn.execute("SELECT COUNT(*) FROM factors WHERE date='2026-07-09'").fetchone()[0]
print(f'\n7/9因子记录: {after}条')

print('\n=== 持仓因子验证 ===')
for code in ['sh.688102','sh.600845','sz.300593']:
    f = fconn.execute(
        "SELECT value FROM factors WHERE code=? AND date='2026-07-09' AND factor_name='pct_chg_1d'",
        (code,)
    ).fetchone()
    if f:
        print(f'  {code}: pct_chg_1d={f[0]:.2f}%')
    else:
        print(f'  {code}: pct_chg_1d=无（跳日跳过 ✅）')

fconn.close()
calc.close()