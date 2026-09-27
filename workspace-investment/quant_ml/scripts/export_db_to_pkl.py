# -*- coding: utf-8 -*-
"""
从market_data.db导出全量K线数据到pickle
覆盖: 沪市主板(1648) + 科创板(598) + 深市主板(1439) + 创业板(1382) = 5069只
输出: all_kline_full.pkl (供quant_ml框架使用)
"""
import sys, os, io, time, pickle, sqlite3
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

WORK = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\quant_ml')
DB = r'F:\market_data.db'
OUTPUT = WORK / 'data' / 'all_kline_full.pkl'
os.makedirs(WORK / 'data', exist_ok=True)

MIN_HISTORY_DAYS = 250  # 同quant_ml配置

def convert_code(raw_code: str) -> str:
    """'sh.600000' -> '600000', 'sz.000001' -> '000001'"""
    if '.' in raw_code:
        return raw_code.split('.')[1]
    return raw_code

def export_all_kline():
    print("=" * 60)
    print("从 market_data.db 导出全量K线数据")
    print("=" * 60)

    conn = sqlite3.connect(DB)
    print(f"\n[1] 扫描全量股票...")

    # 获取所有股票代码
    codes = [r[0] for r in conn.execute(
        "SELECT DISTINCT code FROM daily_k ORDER BY code"
    ).fetchall()]
    print(f"  DB总股票: {len(codes)}")

    # 转换代码格式
    all_codes = [convert_code(c) for c in codes]
    print(f"  覆盖范围:")
    sh_main = [c for c in all_codes if c.startswith('6') and not c.startswith('688')]
    kc = [c for c in all_codes if c.startswith('688')]
    sz_main = [c for c in all_codes if len(c) == 6 and not c.startswith('6') and not c.startswith('3') and c.startswith('0')]
    cy = [c for c in all_codes if c.startswith('3')]
    print(f"    沪市主板: {len(sh_main)}")
    print(f"    科创板: {len(kc)}")
    print(f"    深市主板: {len(sz_main)}")
    print(f"    创业板: {len(cy)}")

    print(f"\n[2] 逐股票导出(流式读取)...")
    t0 = time.time()
    result = {}
    batch = 500
    total = len(codes)

    for batch_start in range(0, total, batch):
        batch_end = min(batch_start + batch, total)
        batch_codes = codes[batch_start:batch_end]

        # 批量查询
        placeholders = ','.join(['?' for _ in batch_codes])
        rows = conn.execute(
            f"SELECT code, date, open, high, low, close, volume "
            f"FROM daily_k WHERE code IN ({placeholders}) ORDER BY code, date",
            batch_codes
        ).fetchall()

        # 按股票分组
        stock_data = {}
        for code, date, o, h, l, c, v in rows:
            sym = convert_code(code)
            if sym not in stock_data:
                stock_data[sym] = []
            stock_data[sym].append({
                'date': date, 'open': o, 'high': h, 'low': l, 'close': c, 'volume': v
            })

        # 过滤+写入
        for sym, rows2 in stock_data.items():
            if len(rows2) >= MIN_HISTORY_DAYS:
                import pandas as pd
                df = pd.DataFrame(rows2)
                df = df.sort_values('date').reset_index(drop=True)
                result[sym] = df

        elapsed = time.time() - t0
        speed = batch_end / elapsed if elapsed > 0 else 0
        eta = (total - batch_end) / speed / 60 if speed > 0 else 0
        print(f"  {batch_end}/{total} ({batch_end/total:.0%}) | 有效: {len(result)} | 速度: {speed:.0f}只/秒 | ETA: {eta:.1f}分钟", flush=True)

    conn.close()

    print(f"\n[3] 保存结果...")
    # 写入pickle
    with open(OUTPUT, 'wb') as f:
        pickle.dump(result, f)

    size_mb = os.path.getsize(OUTPUT) / 1024 / 1024
    total_rows = sum(len(v) for v in result.values())
    total_codes = len(result)
    print(f"  路径: {OUTPUT}")
    print(f"  股票: {total_codes} 只")
    print(f"  总行数: {total_rows:,}")
    print(f"  文件大小: {size_mb:.1f} MB")
    print(f"  耗时: {time.time()-t0:.0f}秒")

    # 市场分布
    sh = len([c for c in result if c.startswith('6') and not c.startswith('688')])
    kcb = len([c for c in result if c.startswith('688')])
    sz = len([c for c in result if len(c) == 6 and c.startswith('0')])
    cyb = len([c for c in result if c.startswith('3')])
    print(f"\n  有效股票分布:")
    print(f"    沪市主板: {sh}")
    print(f"    科创板: {kcb}")
    print(f"    深市主板: {sz}")
    print(f"    创业板: {cyb}")

    # 预估样本量
    # 每只股票约 1700 个交易日，每 8 天采一个样本
    est_samples = sum(max(0, len(v) - 250) // 8 for v in result.values())
    print(f"  预估样本量: ~{est_samples:,} (每8日采样)")

    print("\n完成!")

if __name__ == '__main__':
    export_all_kline()
