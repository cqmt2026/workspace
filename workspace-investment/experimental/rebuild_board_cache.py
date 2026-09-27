# -*- coding: utf-8 -*-
"""
重建板块缓存 — 覆盖90个申万行业板块

目标：
  现有缓存53个板块 → 扩展到RPS的90个板块

方法：
  1. 读取RPS_board_20260703.json的90个板块名称
  2. 对每个板块，用akshare获取成分股
  3. 合并到现有缓存中

输出：
  data/stock_board_cache.json (更新)

注意：
  - akshare可能不稳定，每次查询间隔0.5秒
  - 总耗时预估：90个板块 × 3秒 = 约4.5分钟
"""
import json, os, time, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

WORK_DIR = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment')
CACHE_FILE = WORK_DIR / 'data' / 'stock_board_cache.json'
RPS_FILE = WORK_DIR / 'out_data' / 'rps_history' / 'RPS_board_20260703.json'

print("=" * 60)
print("重建板块缓存")
print("=" * 60)

# 1. 加载现有缓存
if CACHE_FILE.exists():
    with open(CACHE_FILE, encoding='utf-8') as f:
        old_cache = json.load(f)
    print(f"现有缓存: {len(old_cache)}只股票, {len(set(v if isinstance(v,str) else str(v) for v in old_cache.values()))}个板块")
else:
    old_cache = {}
    print("现有缓存: 不存在")

# 2. 读取RPS板块列表
with open(RPS_FILE, encoding='utf-8') as f:
    rps_data = json.load(f)

rps_boards = rps_data.get('rps_data', rps_data.get('data', []))
board_names = [b['name'] for b in rps_boards if 'name' in b]
print(f"RPS板块: {len(board_names)}个")

# 现有板块名
existing_sectors = set()
for v in old_cache.values():
    if isinstance(v, str):
        existing_sectors.add(v)
    elif isinstance(v, dict):
        existing_sectors.add(v.get('board', ''))

missing = [n for n in board_names if n not in existing_sectors]
print(f"需要补充: {len(missing)}个板块 (已有{len(existing_sectors)}个)")
if missing:
    print(f"缺失板块: {missing}")

# 3. 用akshare补充缺失板块
if missing:
    try:
        import akshare as ak
    except ImportError:
        print("akshare未安装，跳过补充")
        missing = []

    new_cache = dict(old_cache)  # 保留现有缓存
    success = 0
    fail = 0

    for i, board_name in enumerate(missing):
        print(f"\n[{i+1}/{len(missing)}] {board_name}...", end=' ', flush=True)
        try:
            df = ak.stock_board_industry_cons_em(symbol=board_name)
            if df is not None and not df.empty:
                # 东财格式：列名通常是 股票代码 或 代码
                code_col = None
                for col in ['股票代码', '代码', 'code']:
                    if col in df.columns:
                        code_col = col
                        break
                if code_col:
                    stocks = df[code_col].tolist()
                else:
                    # 尝试第一列
                    stocks = df.iloc[:, 0].tolist()
            else:
                stocks = []

            if stocks:
                for code_str in stocks:
                    code_str = str(code_str).strip()
                    # 去掉可能的 .后缀
                    code_clean = code_str.split('.')[0] if '.' in code_str else code_str
                    if code_clean.startswith('6'):
                        key = f'sh.{code_clean}'
                    elif code_clean.startswith('0') or code_clean.startswith('3'):
                        key = f'sz.{code_clean}'
                    else:
                        key = code_clean
                    new_cache[key] = board_name
                success += 1
                print(f"✅ {len(stocks)}只")
            else:
                fail += 1
                print(f"⚠️ 无成分股")
        except Exception as e:
            fail += 1
            print(f"❌ {e}")

        time.sleep(0.5)  # 防封

    print(f"\n\n补充完成: 成功{success}, 失败{fail}")
    print(f"新缓存: {len(new_cache)}只股票")

    # 4. 保存
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_cache, f, ensure_ascii=False)
    print(f"已保存: {CACHE_FILE}")

else:
    print("无需补充")

# 5. 验证
print(f"\n{'='*60}")
print("验证")
print('='*60)
with open(CACHE_FILE, encoding='utf-8') as f:
    final_cache = json.load(f)

final_sectors = set()
for v in final_cache.values():
    if isinstance(v, str):
        final_sectors.add(v)
    elif isinstance(v, dict):
        final_sectors.add(v.get('board', ''))
print(f"最终缓存: {len(final_cache)}只股票, {len(final_sectors)}个板块")

# 检查是否覆盖了RPS全部90个
final_missing = [n for n in board_names if n not in final_sectors]
if final_missing:
    print(f"仍未覆盖: {len(final_missing)}个板块")
    for b in final_missing:
        print(f"  {b}")
else:
    print("✅ 全部90个板块已覆盖！")